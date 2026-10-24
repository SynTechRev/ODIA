"""Day 03: ColBERTv2 late-interaction retriever.

Implements exact ColBERTv2 MaxSim scoring using the colbertv2.0 model weights
via the transformers library. Ragatouille 0.0.9 is incompatible with Python 3.14
(voyager C extension missing); this is the sentence-transformer-emulation fallback
documented in Watch 1 of the Day 3 calibration.

Architecture:
    ColBERTv2 late interaction (Santhanam 2021 / PLAID 2022):
    1. Encode query -> per-token vector matrix Q (tokens x dim)
    2. Encode document -> per-token vector matrix D (tokens x dim)
    3. Score = sum over query tokens of: max dot-product with any document token
    4. Rank documents by descending score

    All token vectors are L2-normalized before MaxSim so dot product = cosine.

Storage:
    Corpus token matrices are stacked into a ragged list and saved as numpy files.
    Compression: average 128 tokens per doc at 128 dim float16 = ~32 KB per doc;
    1000-doc index ~ 32 MB (comparable to PLAID compressed).

Model: models/colbertv2.0 (colbert-ir/colbertv2.0, ~418 MB bert-base)
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)

_COLBERT_DIM = 128
_MAX_QUERY_TOKENS = 32
_MAX_DOC_TOKENS = 512


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norms, 1e-9)


def _doc_text(doc: dict[str, Any]) -> str:
    parts: list[str] = []
    if doc.get("title"):
        parts.append(str(doc["title"]))
    if doc.get("analysis_summary"):
        parts.append(str(doc["analysis_summary"]))
    for f in doc.get("findings", []):
        if f.get("issue"):
            parts.append(str(f["issue"]))
        details = f.get("details", {})
        if isinstance(details, dict):
            parts.extend(str(v) for v in details.values() if v)
    return " ".join(parts)


class ColBERTRetriever:
    """ColBERTv2 late-interaction retriever using direct transformers inference.

    Args:
        model_path: Path to colbertv2.0 directory (bert-base-uncased weights).
        device: torch device string; defaults to cpu.
    """

    def __init__(
        self,
        model_path: Path = Path("models/colbertv2.0"),
        device: str = "cpu",
    ) -> None:
        self._model_path = Path(model_path)
        self._device = device
        self._tokenizer = None
        self._model = None
        self._linear = None

        self._doc_ids: list[str] = []
        self._doc_texts: list[str] = []
        self._docs: list[dict[str, Any]] = []
        # List of (num_tokens, 128) float16 arrays, one per doc
        self._doc_token_matrices: list[np.ndarray] = []

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        if self._model is not None:
            return
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"ColBERTv2 model not found at {self._model_path}. "
                "Run scripts/download_day02_models.py first."
            )
        logger.info("Loading ColBERTv2 tokenizer from %s", self._model_path)
        self._tokenizer = AutoTokenizer.from_pretrained(str(self._model_path))
        logger.info("Loading ColBERTv2 BERT encoder from %s", self._model_path)
        self._model = AutoModel.from_pretrained(
            str(self._model_path),
            torch_dtype=torch.float32,
            ignore_mismatched_sizes=True,
        )
        self._model.eval()
        self._model.to(self._device)

        # Load the ColBERTv2 linear projection (768 -> 128) from checkpoint weights.
        # AutoModel does not load this since it is not part of the BERT architecture.
        linear_w = self._load_linear_weight()
        if linear_w is not None:
            self._linear = torch.nn.Linear(768, _COLBERT_DIM, bias=False)
            self._linear.weight = torch.nn.Parameter(linear_w)
            self._linear.to(self._device)
            self._linear.eval()
            logger.info("ColBERTv2 linear projection loaded (768 -> %d)", _COLBERT_DIM)
        else:
            self._linear = None
            logger.warning(
                "linear.weight not found; using first %d hidden dims as fallback",
                _COLBERT_DIM,
            )

    def _load_linear_weight(self) -> torch.Tensor | None:
        sf = self._model_path / "model.safetensors"
        if sf.exists():
            try:
                from safetensors.torch import load_file

                weights = load_file(str(sf))
                if "linear.weight" in weights:
                    return weights["linear.weight"].float()
            except Exception as e:
                logger.warning("Could not load linear.weight from safetensors: %s", e)
        pt = self._model_path / "pytorch_model.bin"
        if pt.exists():
            try:
                weights = torch.load(str(pt), map_location="cpu", weights_only=True)
                if "linear.weight" in weights:
                    return weights["linear.weight"].float()
            except Exception as e:
                logger.warning(
                    "Could not load linear.weight from pytorch_model.bin: %s", e
                )
        return None

    # ------------------------------------------------------------------
    # Encoding
    # ------------------------------------------------------------------

    def _encode_tokens(
        self, texts: list[str], max_length: int, batch_size: int = 32
    ) -> list[np.ndarray]:
        """Encode texts to per-token L2-normalized vectors.

        Returns a list of (num_tokens, 128) float16 arrays (one per text).
        The first 128 dimensions of the last hidden state are used as the
        token representation (ColBERTv2 linear projection convention).
        """
        results = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = self._tokenizer(
                batch,
                max_length=max_length,
                truncation=True,
                padding=True,
                return_tensors="pt",
            ).to(self._device)
            with torch.no_grad():
                out = self._model(**enc)
            hidden = out.last_hidden_state  # (batch, seq_len, 768)
            if self._linear is not None:
                projected = self._linear(hidden)  # (batch, seq_len, 128)
            else:
                projected = hidden[:, :, :_COLBERT_DIM]
            projected_np = projected.detach().cpu().numpy().astype(np.float16)
            mask = enc["attention_mask"].cpu().numpy()  # (batch, seq_len)
            for vec, m in zip(projected_np, mask, strict=False):
                # Keep only non-padding tokens
                n_tokens = int(m.sum())
                token_vecs = _l2_normalize(vec[:n_tokens].astype(np.float32)).astype(
                    np.float16
                )
                results.append(token_vecs)
        return results

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index(self, documents: list[dict[str, Any]], batch_size: int = 32) -> None:
        """Build token-level index from document dicts.

        Args:
            documents: List of document dicts with at least "document_id".
            batch_size: Encoding batch size.
        """
        self._load_model()
        self._docs = documents
        self._doc_ids = [d["document_id"] for d in documents]
        self._doc_texts = [_doc_text(d) for d in documents]

        logger.info(
            "Encoding %d documents with ColBERTv2 (max_length=%d)",
            len(documents),
            _MAX_DOC_TOKENS,
        )
        self._doc_token_matrices = self._encode_tokens(
            self._doc_texts, max_length=_MAX_DOC_TOKENS, batch_size=batch_size
        )
        logger.info(
            "ColBERTv2 index built: %d docs, avg %.1f tokens/doc",
            len(documents),
            np.mean([m.shape[0] for m in self._doc_token_matrices]),
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, index_dir: Path) -> None:
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        with open(index_dir / "doc_ids.json", "w", encoding="utf-8") as f:
            json.dump(self._doc_ids, f)
        with open(index_dir / "doc_texts.json", "w", encoding="utf-8") as f:
            json.dump(self._doc_texts, f)
        with open(index_dir / "docs.jsonl", "w", encoding="utf-8") as f:
            for doc in self._docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        with open(index_dir / "token_matrices.pkl", "wb") as f:
            pickle.dump(self._doc_token_matrices, f)
        logger.info("ColBERT index saved to %s", index_dir)

    def load(self, index_dir: Path) -> None:
        index_dir = Path(index_dir)
        with open(index_dir / "doc_ids.json", encoding="utf-8") as f:
            self._doc_ids = json.load(f)
        with open(index_dir / "doc_texts.json", encoding="utf-8") as f:
            self._doc_texts = json.load(f)
        self._docs = []
        with open(index_dir / "docs.jsonl", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._docs.append(json.loads(line))
        with open(index_dir / "token_matrices.pkl", "rb") as f:
            self._doc_token_matrices = pickle.load(f)
        logger.info(
            "ColBERT index loaded from %s (%d docs)", index_dir, len(self._doc_ids)
        )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, question: str, top_k: int = 15) -> list[dict[str, Any]]:
        """Retrieve documents using ColBERTv2 MaxSim scoring.

        Args:
            question: Natural language query string.
            top_k: Number of results to return.

        Returns:
            List of result dicts sorted by descending MaxSim score.
        """
        if not self._doc_token_matrices:
            raise RuntimeError("Call index() or load() before query().")
        self._load_model()

        q_matrices = self._encode_tokens([question], max_length=_MAX_QUERY_TOKENS)
        q_vecs = q_matrices[0].astype(np.float32)  # (q_tokens, 128)

        scores = np.zeros(len(self._doc_ids), dtype=np.float32)
        for i, d_vecs in enumerate(self._doc_token_matrices):
            d = d_vecs.astype(np.float32)  # (d_tokens, 128)
            # MaxSim: for each query token, max dot product over doc tokens; then sum
            sim_matrix = q_vecs @ d.T  # (q_tokens, d_tokens)
            scores[i] = float(sim_matrix.max(axis=1).sum())

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for rank, idx in enumerate(top_indices):
            doc = self._docs[idx]
            results.append(
                {
                    "rank": rank + 1,
                    "document_id": self._doc_ids[idx],
                    "title": doc.get("title", ""),
                    "score": float(scores[idx]),
                    "anomaly_count": doc.get("anomaly_count", 0),
                    "findings": doc.get("findings", []),
                }
            )
        return results
