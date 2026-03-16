# ruff: noqa: E402
"""Regenerate legal/lexicon/case_law_definitions.json from full case set."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from oraculus_di_auditor.legal.case_law_builder import CaseLawBuilder  # noqa: E402
from oraculus_di_auditor.legal.definition_extractor import (
    DefinitionExtractor,  # noqa: E402
)

cases_dir = REPO_ROOT / "legal" / "cases"
builder = CaseLawBuilder(cases_dir)
extractor = DefinitionExtractor(builder)

dictionary = extractor.build_case_law_dictionary()

out: dict = {
    "version": dictionary.version,
    "generated_at": dictionary.generated_at,
    "term_count": dictionary.term_count,
    "case_count": dictionary.case_count,
    "terms": {
        term: {
            "term": defn.term,
            "definition": defn.definition,
            "case_name": defn.case_name,
            "citation": defn.citation,
            "year": defn.year,
            "court": defn.court,
            "context": defn.context,
            "is_holding": defn.is_holding,
            "superseded_by": defn.superseded_by,
        }
        for term, defn in dictionary.terms.items()
    },
}

out_path = REPO_ROOT / "legal" / "lexicon" / "case_law_definitions.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"Wrote {out_path}")
print(f"Terms: {dictionary.term_count}, Cases: {dictionary.case_count}")
superseded = [t for t, d in dictionary.terms.items() if d.superseded_by]
print(f"Superseded terms: {superseded}")
