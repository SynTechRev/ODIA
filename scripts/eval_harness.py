#!/usr/bin/env python3
"""
Oraculus DI Auditor - Ollama Evaluation Harness

Runs evaluation queries against Ollama models using document context from manifests.
Supports TF-IDF retrieval or naive substring matching for context assembly.

Usage:
    python scripts/eval_harness.py --model llama3-small \\
        --queries queries/sample_queries.json
    python scripts/eval_harness.py --model mistral --top-k 3 \\
        --category irb_consent_check
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import scikit-learn for TF-IDF
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Note: scikit-learn not available, using naive retrieval")

# Try to import requests for HTTP-based Ollama API
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Note: requests not available, will try subprocess-based Ollama CLI")


class DocumentRetriever:
    """Retrieves relevant document context for queries."""

    def __init__(self, use_tfidf: bool = True):
        self.use_tfidf = use_tfidf and SKLEARN_AVAILABLE
        self.documents: list[dict[str, str]] = []
        self.vectorizer: Any | None = None
        self.tfidf_matrix: Any | None = None

    def load_documents(self, manifests_dir: Path, extraction_dir: Path) -> int:
        """Load documents from manifests and extraction files."""
        manifests_path = Path(manifests_dir)
        extraction_path = Path(extraction_dir)

        count = 0
        for manifest_file in manifests_path.glob("*.json"):
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)

                doc_id = manifest.get("document_id", manifest_file.stem)

                # Try to load extracted text
                text_path = extraction_path / f"{doc_id}.txt"
                if text_path.exists():
                    with open(text_path, encoding="utf-8") as tf:
                        text = tf.read()
                else:
                    # Fallback: use manifest notes and flags as text
                    text_parts = []
                    for flag in manifest.get("flags", []):
                        text_parts.append(flag.get("message", ""))
                    for note in manifest.get("notes", []):
                        text_parts.append(note.get("note", ""))
                    text = " ".join(text_parts)

                if text.strip():
                    self.documents.append({"id": doc_id, "text": text})
                    count += 1

            except Exception as e:
                print(f"Warning: Failed to load document {manifest_file}: {e}")

        # Build TF-IDF index if available
        if self.use_tfidf and count > 0:
            self._build_tfidf_index()

        return count

    def _build_tfidf_index(self):
        """Build TF-IDF index for documents."""
        if not SKLEARN_AVAILABLE:
            return

        texts = [doc["text"] for doc in self.documents]

        # Check if any documents have non-empty text
        if not any((text or "").strip() for text in texts):
            # No non-empty documents, fall back to naive retrieval
            self.use_tfidf = False
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        except ValueError:
            # Fallback to naive retrieval if TF-IDF fails
            self.use_tfidf = False
            self.vectorizer = None
            self.tfidf_matrix = None

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Retrieve top-k relevant documents for a query."""
        if self.use_tfidf and self.vectorizer is not None:
            return self._retrieve_tfidf(query, top_k)
        else:
            return self._retrieve_naive(query, top_k)

    def _retrieve_tfidf(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """TF-IDF based retrieval."""
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include non-zero similarities
                doc = self.documents[idx]
                results.append(
                    {
                        "document_id": doc["id"],
                        "text": doc["text"][:2000],  # Truncate for context
                        "score": float(similarities[idx]),
                    }
                )

        return results

    def _retrieve_naive(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Naive substring matching retrieval."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        # Guard against empty query
        if not query_terms:
            return []

        scored_docs = []
        for doc in self.documents:
            text_lower = doc["text"].lower()
            # Count matching terms
            matches = sum(1 for term in query_terms if term in text_lower)
            if matches > 0:
                score = matches / len(query_terms)
                scored_docs.append((score, doc))

        # Sort by score and take top-k
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, doc in scored_docs[:top_k]:
            results.append(
                {
                    "document_id": doc["id"],
                    "text": doc["text"][:2000],  # Truncate
                    "score": score,
                }
            )

        return results


class OllamaClient:
    """Client for interacting with Ollama models."""

    def __init__(
        self, host: str = "localhost", port: int = 11434, model: str = "llama3-small"
    ):
        self.host = host
        self.port = port
        self.model = model
        self.api_url = f"http://{host}:{port}"

    def generate(
        self, prompt: str, system_prompt: str | None = None, timeout: int = 120
    ) -> tuple[str, float, bool]:
        """
        Generate response from Ollama model.
        Returns: (response_text, latency_seconds, success)
        """
        if REQUESTS_AVAILABLE:
            return self._generate_http(prompt, system_prompt, timeout)
        else:
            return self._generate_cli(prompt, system_prompt, timeout)

    def _generate_http(
        self, prompt: str, system_prompt: str | None, timeout: int
    ) -> tuple[str, float, bool]:
        """Generate using HTTP API."""
        url = f"{self.api_url}/api/generate"

        payload = {"model": self.model, "prompt": prompt, "stream": False}

        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.time()
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            latency = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                return result.get("response", ""), latency, True
            else:
                return f"Error: HTTP {response.status_code}", latency, False

        except Exception as e:
            latency = time.time() - start_time
            return f"Error: {str(e)}", latency, False

    def _generate_cli(
        self, prompt: str, system_prompt: str | None, timeout: int
    ) -> tuple[str, float, bool]:
        """Generate using CLI (fallback)."""
        import subprocess

        cmd = ["ollama", "run", self.model, prompt]

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            latency = time.time() - start_time

            if result.returncode == 0:
                return result.stdout.strip(), latency, True
            else:
                return f"Error: {result.stderr}", latency, False

        except subprocess.TimeoutExpired:
            latency = time.time() - start_time
            return "Error: Timeout", latency, False
        except Exception as e:
            latency = time.time() - start_time
            return f"Error: {str(e)}", latency, False


class EvaluationHarness:
    """Orchestrates evaluation runs."""

    def __init__(
        self,
        ollama_client: OllamaClient,
        retriever: DocumentRetriever,
        output_dir: Path,
    ):
        self.client = ollama_client
        self.retriever = retriever
        self.output_dir = output_dir
        self.run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.run_dir = output_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def run_evaluation(
        self, queries: list[dict[str, Any]], top_k: int = 5
    ) -> dict[str, Any]:
        """Run evaluation on a list of queries."""
        results = []

        print(f"\nStarting evaluation run: {self.run_id}")
        print(f"Model: {self.client.model}")
        print(f"Queries: {len(queries)}")
        print(f"Output: {self.run_dir}\n")

        for i, query_obj in enumerate(queries, 1):
            query_id = query_obj.get("id", f"Q{i:03d}")
            query_text = query_obj.get("query", "")
            category = query_obj.get("category", "uncategorized")

            print(f"[{i}/{len(queries)}] {query_id}: {query_text[:60]}...")

            # Retrieve context
            context_docs = self.retriever.retrieve(query_text, top_k=top_k)

            # Assemble prompt
            context_text = "\n\n".join(
                [
                    f"Document {doc['document_id']}:\n{doc['text']}"
                    for doc in context_docs
                ]
            )

            prompt = f"""Context Documents:
{context_text}

Question: {query_text}

Answer:"""

            system_prompt = (
                "You are a legal document analysis assistant. "
                "Provide accurate, factual responses based solely "
                "on the provided context."
            )

            # Generate response
            response, latency, success = self.client.generate(
                prompt, system_prompt=system_prompt
            )

            result = {
                "query_id": query_id,
                "query": query_text,
                "category": category,
                "context_docs": [
                    {"id": doc["document_id"], "score": doc["score"]}
                    for doc in context_docs
                ],
                "response": response,
                "latency_seconds": latency,
                "success": success,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

            results.append(result)

            print(f"  Latency: {latency:.2f}s | Success: {success}")
            if success:
                print(f"  Response: {response[:100]}...")

            # Save individual result
            result_file = self.run_dir / f"{query_id}.json"
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

        # Save summary
        summary = {
            "run_id": self.run_id,
            "model": self.client.model,
            "total_queries": len(queries),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "avg_latency": (
                sum(r["latency_seconds"] for r in results) / len(results)
                if results
                else 0
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "results": results,
        }

        summary_file = self.run_dir / "evaluation_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print("\n[OK] Evaluation complete")
        print(f"  Successful: {summary['successful']}/{summary['total_queries']}")
        print(f"  Avg latency: {summary['avg_latency']:.2f}s")
        print(f"  Results: {self.run_dir}")

        return summary


def load_config(config_path: Path) -> dict[str, Any]:
    """Load Ollama configuration."""
    if config_path.exists():
        try:
            import yaml

            with open(config_path) as f:
                return yaml.safe_load(f)
        except ImportError:
            with open(config_path) as f:
                import json

                return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="Oraculus DI Auditor - Ollama Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all queries with default model
  python scripts/eval_harness.py --queries queries/sample_queries.json

  # Run with specific model and category filter
  python scripts/eval_harness.py --model mistral --category irb_consent_check

  # Custom top-k retrieval
  python scripts/eval_harness.py --model llama3 --top-k 3 \\
      --queries queries/sample_queries.json
        """,
    )

    parser.add_argument(
        "--model", type=str, default="llama3-small", help="Ollama model name"
    )
    parser.add_argument(
        "--queries",
        type=str,
        default="queries/sample_queries.json",
        help="Path to queries JSON file",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Filter queries by category",
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of context documents to retrieve"
    )
    parser.add_argument(
        "--manifests-dir", type=str, default="manifests", help="Manifests directory"
    )
    parser.add_argument(
        "--extraction-dir", type=str, default="extraction", help="Extraction directory"
    )
    parser.add_argument(
        "--output-dir", type=str, default="reports/eval", help="Output directory"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/ollama_config.yaml",
        help="Ollama config file",
    )
    parser.add_argument("--host", type=str, default="localhost", help="Ollama host")
    parser.add_argument("--port", type=int, default=11434, help="Ollama port")

    args = parser.parse_args()

    print("Oraculus DI Auditor - Evaluation Harness")
    print(f"  Model: {args.model}")
    print(f"  TF-IDF available: {SKLEARN_AVAILABLE}")
    print(f"  HTTP API available: {REQUESTS_AVAILABLE}")

    # Load queries
    queries_path = Path(args.queries)
    if not queries_path.exists():
        print(f"Error: Queries file not found: {queries_path}", file=sys.stderr)
        sys.exit(1)

    with open(queries_path) as f:
        queries_data = json.load(f)
        queries = queries_data.get("queries", [])

    # Filter by category if specified
    if args.category:
        queries = [q for q in queries if q.get("category") == args.category]
        print(f"  Filtered to category: {args.category} ({len(queries)} queries)")

    if not queries:
        print("Error: No queries to evaluate", file=sys.stderr)
        sys.exit(1)

    # Initialize retriever and load documents
    print("\nLoading documents...")
    retriever = DocumentRetriever(use_tfidf=SKLEARN_AVAILABLE)
    doc_count = retriever.load_documents(
        Path(args.manifests_dir), Path(args.extraction_dir)
    )
    print(f"  Loaded {doc_count} document(s)")

    if doc_count == 0:
        print("Warning: No documents loaded. Evaluation will have no context.")

    # Initialize Ollama client
    ollama_client = OllamaClient(host=args.host, port=args.port, model=args.model)

    # Initialize harness
    harness = EvaluationHarness(
        ollama_client=ollama_client,
        retriever=retriever,
        output_dir=Path(args.output_dir),
    )

    # Run evaluation
    harness.run_evaluation(queries, top_k=args.top_k)


if __name__ == "__main__":
    main()
