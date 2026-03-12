# Corpus Directory

This directory stores the legislative corpus data for analysis. Each subdirectory represents a legislative item with the following structure:

```
corpus/
  <corpus_id>/
    index.json          # Corpus metadata and file manifest
    metadata/
      corpus.json       # Extended metadata
    agendas/            # Agenda PDFs
    minutes/            # Meeting minutes PDFs
    staff_reports/      # Staff report PDFs
    attachments/        # Additional attachments
    extracted/          # Extracted text files
```

## Getting Started

To create a corpus for your jurisdiction:

```bash
# Initialize corpus structure for a Legistar-based jurisdiction
python scripts/corpus_manager.py init --jurisdiction "Your City" --source-url "https://yourcity.legistar.com"

# Ingest documents
python scripts/ingest_and_index.py --source data/sources --analyze
```

See [docs/PHASE6_INGESTION.md](../docs/PHASE6_INGESTION.md) for detailed documentation.
