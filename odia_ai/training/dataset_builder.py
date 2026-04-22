"""Training dataset construction for Layer 2 NER + relational extraction.

Converts the output of odia_ai.backref.ExtractedAlert records into
instruction-tuning-format training examples suitable for fine-tuning
a base LLM (Llama-3.1-8B, Qwen2.5-7B, Mistral-7B) using LoRA/PEFT.

Each training example is a (prompt, completion) pair where:
- prompt: Instructs the model to extract structured information from a
  document passage in ODIA-specific ontology
- completion: Structured JSON matching the ExtractionSchema below

Synthetic augmentation:
- Paraphrase variant generation (through controlled template substitution)
- Jurisdiction transfer (substitute one jurisdiction's names for another's)
- Negative examples (randomly sampled passages that should yield empty extractions)

Held-out splits:
- TRAIN: 7 jurisdictions (random sample by alert_id hash)
- VALIDATION: 1 jurisdiction (TCSO — least municipality-dependent)
- TEST: 1 jurisdiction (Exeter — highest coverage in corpus; strongest test set)

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from odia_ai.backref import ExtractedAlert

SYSTEM_PROMPT = """You are O.D.I.A., a forensic document analyst specialized in auditing law enforcement surveillance procurement for compliance with California SB 524, AB 481, SB 978, Civil Code §1798.90.5x, 28 CFR Part 23, CJIS Security Policy, and federal grant conditions.

Your task is to read a municipal document passage (council agenda item, staff report, resolution, contract, audit finding, or minutes excerpt) and extract structured information. Respond ONLY with valid JSON matching the schema. Do not add explanatory prose.

Schema fields:
- vendors: list of surveillance/tech vendor names mentioned
- persons: list of {name, role, agency} objects for named officials
- dollar_amounts: list of {amount_usd, vendor, context} objects
- statutes_cited: list of statutory citations
- procurement_instruments: list of {type, number, date} objects (resolutions, ordinances, agreements)
- governance_bodies: list of named oversight committees, task forces, or advisory bodies
- anomaly_candidates: list of {category, severity, reasoning} objects where category is F-1 through F-12
"""


EXTRACTION_INSTRUCTION = (
    "Extract structured information from the following document passage. "
    "Return only JSON matching the ODIA schema."
)


@dataclass
class TrainingExample:
    """A single fine-tuning example in instruction-response format."""

    example_id: str
    system: str
    instruction: str
    input_text: str  # document passage
    output_json: dict  # structured extraction
    jurisdiction: str  # for held-out splits
    source_alert_id: str | None  # traceability back to the MAS record
    split: str = "train"  # train | validation | test
    is_synthetic: bool = False
    synthesis_method: str = (
        ""  # "paraphrase" | "jurisdiction_transfer" | "negative" | ""
    )

    def to_dict(self) -> dict:
        return asdict(self)

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_openai_format(self) -> dict:
        """Format for OpenAI/Anthropic fine-tuning API."""
        return {
            "messages": [
                {"role": "system", "content": self.system},
                {
                    "role": "user",
                    "content": f"{self.instruction}\n\n---\n{self.input_text}",
                },
                {
                    "role": "assistant",
                    "content": json.dumps(self.output_json, ensure_ascii=False),
                },
            ]
        }

    def to_alpaca_format(self) -> dict:
        """Format for Alpaca-style fine-tuning (common with Llama/Qwen LoRA)."""
        return {
            "instruction": self.instruction,
            "input": self.input_text,
            "output": json.dumps(self.output_json, ensure_ascii=False),
            "system": self.system,
        }


def _alert_to_output_json(alert: ExtractedAlert) -> dict:
    """Convert an ExtractedAlert into the Layer 2 extraction output JSON."""
    # Build anomaly_candidates: the alert itself IS the anomaly
    anomaly_candidates: list[dict] = []
    if alert.severity or alert.finding_category:
        anomaly_candidates.append(
            {
                "category": alert.finding_category or "unspecified",
                "severity": alert.severity or "MEDIUM",
                "reasoning": alert.title,
            }
        )

    # Build dollar_amounts
    dollar_amounts: list[dict] = []
    for d in alert.dollar_amounts:
        # Best-effort vendor pairing: attach first mentioned vendor
        vendor = alert.vendors_mentioned[0] if alert.vendors_mentioned else None
        dollar_amounts.append(
            {
                "amount_raw": d,
                "vendor": vendor,
                "context": alert.title[:100],
            }
        )

    # Build procurement_instruments from resolution mentions
    procurement_instruments: list[dict] = []
    for r in alert.resolutions_mentioned:
        procurement_instruments.append(
            {
                "type": "resolution_or_agreement",
                "number": r,
                "date": None,
            }
        )

    return {
        "vendors": alert.vendors_mentioned,
        "persons": [],  # Layer 2 NER will populate via LLM-assisted extraction
        "dollar_amounts": dollar_amounts,
        "statutes_cited": alert.statutes_mentioned,
        "procurement_instruments": procurement_instruments,
        "governance_bodies": [],  # surfaced downstream via F-11 detector
        "anomaly_candidates": anomaly_candidates,
    }


def alert_to_training_example(alert: ExtractedAlert) -> TrainingExample:
    """Convert an ExtractedAlert to a TrainingExample."""
    example_id = hashlib.sha256(
        f"{alert.alert_id}|{alert.body[:200]}".encode()
    ).hexdigest()[:16]

    return TrainingExample(
        example_id=example_id,
        system=SYSTEM_PROMPT,
        instruction=EXTRACTION_INSTRUCTION,
        input_text=alert.body,
        output_json=_alert_to_output_json(alert),
        jurisdiction=alert.jurisdiction,
        source_alert_id=alert.alert_id,
        split="train",
        is_synthetic=False,
    )


# ------------------------------------------------------------------
# Synthetic augmentation
# ------------------------------------------------------------------

# Jurisdiction-name substitution map for synthesis
JURISDICTION_SUBSTITUTIONS: list[tuple[str, str]] = [
    ("Visalia", "Ridgecrest"),
    ("Porterville", "Lemoore"),
    ("Tulare", "Hanford"),
    ("Lindsay", "Corcoran"),
    ("Farmersville", "Avenal"),
    ("Woodlake", "Arvin"),
    ("Dinuba", "McFarland"),
    ("Exeter", "Delano"),
]


def _make_synthetic_id(base_id: str, method: str, salt: int) -> str:
    raw = f"synthetic|{base_id}|{method}|{salt}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def jurisdiction_transfer(
    example: TrainingExample, target_jurisdiction_pair: tuple[str, str]
) -> TrainingExample | None:
    """Produce a jurisdiction-transferred synthetic copy of an example.

    Substitutes the source jurisdiction name with an adjacent-county name
    throughout the input_text and output_json. Returns None if substitution
    had no effect (example did not mention the source jurisdiction).
    """
    source_name, target_name = target_jurisdiction_pair
    if source_name.lower() not in example.input_text.lower():
        return None

    # Case-preserving substitution
    pattern = re.compile(re.escape(source_name), re.IGNORECASE)
    new_input = pattern.sub(target_name, example.input_text)

    # Reserialize output_json with the substitution applied
    output_str = json.dumps(example.output_json, ensure_ascii=False)
    new_output_str = pattern.sub(target_name, output_str)
    new_output_json = json.loads(new_output_str)

    return TrainingExample(
        example_id=_make_synthetic_id(example.example_id, "jurisdiction_transfer", 0),
        system=example.system,
        instruction=example.instruction,
        input_text=new_input,
        output_json=new_output_json,
        jurisdiction=target_name,
        source_alert_id=example.source_alert_id,
        split="train",
        is_synthetic=True,
        synthesis_method=f"jurisdiction_transfer:{source_name}->{target_name}",
    )


def negative_example(
    document_text: str, base_id: str, jurisdiction: str = "Unknown"
) -> TrainingExample:
    """Construct a negative example where the document should yield empty extractions.

    Negative examples teach the model that most municipal prose is routine
    and does not trigger anomaly detection. The input is a document passage
    and the expected output is a schema with empty lists.
    """
    empty_output = {
        "vendors": [],
        "persons": [],
        "dollar_amounts": [],
        "statutes_cited": [],
        "procurement_instruments": [],
        "governance_bodies": [],
        "anomaly_candidates": [],
    }
    return TrainingExample(
        example_id=_make_synthetic_id(base_id, "negative", 0),
        system=SYSTEM_PROMPT,
        instruction=EXTRACTION_INSTRUCTION,
        input_text=document_text,
        output_json=empty_output,
        jurisdiction=jurisdiction,
        source_alert_id=None,
        split="train",
        is_synthetic=True,
        synthesis_method="negative",
    )


# ------------------------------------------------------------------
# Dataset assembly with deterministic splits
# ------------------------------------------------------------------


def _hash_to_float(s: str) -> float:
    """Deterministic hash → [0, 1) float for split assignment."""
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def assign_split(
    example: TrainingExample,
    *,
    holdout_validation: str = "TCSO",
    holdout_test: str = "Exeter",
) -> str:
    """Return split assignment: train | validation | test.

    Held-out jurisdiction policy:
    - TCSO → validation (constitutional-officer jurisdiction, structurally distinct)
    - Exeter → test (highest coverage, strongest test-set signal)
    - All others → train

    This is deliberate, not random: random-split would leak neighboring
    document context across splits because MAS versions cite prior findings.
    Jurisdictional hold-out tests actual generalization.
    """
    if example.jurisdiction == holdout_test:
        return "test"
    if example.jurisdiction == holdout_validation:
        return "validation"
    return "train"


def build_dataset(
    alerts: list[ExtractedAlert],
    *,
    enable_jurisdiction_transfer: bool = True,
    enable_negatives: bool = False,  # negatives need a document passage corpus
    negative_passages: list[str] | None = None,
    random_seed: int = 42,
) -> list[TrainingExample]:
    """Build the full training dataset from extracted alerts.

    Args:
        alerts: output of odia_ai.backref.extract_corpus
        enable_jurisdiction_transfer: produce synthetic adjacent-county variants
        enable_negatives: include negative (non-anomaly) examples
        negative_passages: raw document passages to treat as negatives
        random_seed: seed for sampling synthetic transfers

    Returns:
        List of TrainingExample objects with splits assigned.
    """
    rng = random.Random(random_seed)
    examples: list[TrainingExample] = []

    # Real examples from extracted alerts
    for alert in alerts:
        if alert.body_char_length < 80:
            # Skip alerts with too little text (usually just IDs in tables)
            continue
        ex = alert_to_training_example(alert)
        ex.split = assign_split(ex)
        examples.append(ex)

    # Synthetic: jurisdiction transfer on training examples only
    if enable_jurisdiction_transfer:
        train_examples = [
            e for e in examples if e.split == "train" and not e.is_synthetic
        ]
        for ex in train_examples:
            # Pick a random substitution pair
            pair = rng.choice(JURISDICTION_SUBSTITUTIONS)
            transferred = jurisdiction_transfer(ex, pair)
            if transferred is not None:
                examples.append(transferred)

    # Synthetic: negative examples
    if enable_negatives and negative_passages:
        for i, passage in enumerate(negative_passages):
            neg = negative_example(passage, base_id=f"neg_{i}")
            neg.split = "train"
            examples.append(neg)

    return examples


def split_summary(examples: list[TrainingExample]) -> dict:
    """Return counts by split, synthesis method, and jurisdiction."""
    by_split: dict[str, int] = {}
    by_jurisdiction_split: dict[str, dict[str, int]] = {}
    by_synthesis: dict[str, int] = {}

    for e in examples:
        by_split[e.split] = by_split.get(e.split, 0) + 1
        j = e.jurisdiction
        by_jurisdiction_split.setdefault(j, {})
        by_jurisdiction_split[j][e.split] = by_jurisdiction_split[j].get(e.split, 0) + 1
        method = e.synthesis_method or "real"
        by_synthesis[method] = by_synthesis.get(method, 0) + 1

    return {
        "total": len(examples),
        "by_split": by_split,
        "by_jurisdiction_split": by_jurisdiction_split,
        "by_synthesis": by_synthesis,
    }


def write_dataset_splits(
    examples: list[TrainingExample],
    output_dir: Path,
    format: str = "alpaca",
) -> dict[str, int]:
    """Write training dataset to split-specific JSONL files.

    Args:
        examples: list of TrainingExample objects
        output_dir: directory to write splits into
        format: 'alpaca' | 'openai' | 'raw'

    Returns:
        Dict mapping split name to count written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    splits: dict[str, list[TrainingExample]] = {}
    for e in examples:
        splits.setdefault(e.split, []).append(e)

    counts: dict[str, int] = {}
    for split_name, split_examples in splits.items():
        out_path = output_dir / f"{split_name}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for e in split_examples:
                if format == "openai":
                    line = json.dumps(e.to_openai_format(), ensure_ascii=False)
                elif format == "alpaca":
                    line = json.dumps(e.to_alpaca_format(), ensure_ascii=False)
                else:
                    line = e.to_jsonl()
                f.write(line + "\n")
        counts[split_name] = len(split_examples)
    return counts
