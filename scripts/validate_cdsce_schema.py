#!/usr/bin/env python3
"""
CDSCE Schema Validator.

Validates CDSCE semiotic corpus files against the JSON schema.
"""

import json
import sys
from pathlib import Path

import jsonschema


def validate_cdsce_schema() -> bool:
    """
    Validate CDSCE semiotic corpus against schema.

    Returns:
        True if validation passes, False otherwise
    """
    repo_root = Path(__file__).parent.parent
    schema_path = repo_root / "schemas" / "cdsce_schema.json"
    corpus_path = repo_root / "legal" / "semiotics" / "SEMIOTIC_CORPUS.json"

    # Check if files exist
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False

    if not corpus_path.exists():
        print(f"⚠️  Corpus file not found: {corpus_path}")
        print("   This is acceptable if CDSCE has not been run yet.")
        return True

    try:
        # Load schema
        with open(schema_path) as f:
            schema = json.load(f)

        # Load corpus
        with open(corpus_path) as f:
            corpus = json.load(f)

        # Validate
        jsonschema.validate(instance=corpus, schema=schema)

        print("✅ CDSCE schema validation passed")
        print(f"   Corpus version: {corpus.get('version', 'unknown')}")
        print(f"   Total terms: {corpus.get('total_terms', 0)}")

        return True

    except jsonschema.ValidationError as e:
        print("❌ CDSCE schema validation failed:")
        print(f"   {e.message}")
        print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        return False

    except json.JSONDecodeError as e:
        print("❌ JSON parsing error:")
        print(f"   {e}")
        return False

    except Exception as e:
        print("❌ Validation error:")
        print(f"   {e}")
        return False


def main() -> int:
    """Main entry point."""
    success = validate_cdsce_schema()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
