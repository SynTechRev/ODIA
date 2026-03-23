# O.D.I.A. Quick Start

## See It In 60 Seconds

```bash
git clone https://github.com/SynTechRev/ODIA.git
cd ODIA
pip install -e .
python scripts/run_audit.py --source data/demo/ --output reports/demo/
```

Open `reports/demo/audit_report.md` to see the findings.

The demo dataset contains 10 synthetic documents that trigger O.D.I.A.'s anomaly
detectors across procurement, signature, fiscal, governance, surveillance,
constitutional, and administrative categories.

---

## Analyze Your Own Documents

**Step 1 — Copy and configure the jurisdiction config:**

```bash
cp config/jurisdiction.example.json config/jurisdiction.json
```

Edit `config/jurisdiction.json` and set the `name` field to your jurisdiction name.
All other fields are optional.

**Step 2 — Place your documents in a directory:**

O.D.I.A. ingests PDF, JSON, XML, and TXT files. Create a directory and copy your
documents into it:

```bash
mkdir data/my_docs/
cp /path/to/your/documents/*.pdf data/my_docs/
```

**Step 3 — Run the audit:**

```bash
python scripts/run_audit.py --source data/my_docs/ --output reports/my_audit/
```

**Step 4 — Read the output:**

- `reports/my_audit/audit_report.md` — Full findings in Markdown
- `reports/my_audit/audit_report.json` — Machine-readable findings

Each finding includes: detector layer, severity (low/medium/high/critical),
a description of the anomaly, and structured evidence details.

---

## Run with Docker (One Command)

No Python or Node.js required.

```bash
docker build -t odia .
docker run -p 8080:8080 odia
```

Open `http://localhost:8080`.

To persist your documents and reports across container restarts:

```bash
docker run -p 8080:8080 -v odia-data:/data odia
```

To pass API keys for RAG features:

```bash
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=sk-... \
  odia
```

Or use the helper script:

```bash
bash scripts/docker_build.sh --run
```

For local development with live reload on both backend and frontend:

```bash
docker compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## Start the Web Dashboard

Start the API server:

```bash
uvicorn oraculus_di_auditor.interface.api:app --reload
```

Start the frontend (separate terminal):

```bash
cd frontend && npm install && npm run dev
```

Open `http://localhost:3000`.

The API is also available directly at `http://localhost:8000/docs` (Swagger UI).

---

## Advanced Features

| Feature | Command |
|---------|---------|
| Multi-jurisdiction comparison | `python scripts/run_multi_audit.py --config-dir config/ --output reports/` |
| Temporal contract evolution | `python scripts/run_temporal_analysis.py --source data/my_docs/ --output reports/` |
| CCOPS compliance assessment | `python scripts/run_compliance_check.py --source data/my_docs/ --output reports/` |
| Natural language query (RAG) | `python scripts/rag_query.py --query "What contracts exceeded their original scope?"` |
| Export formats | Add `--formats json,markdown,html` to any audit command |

Full documentation: [docs/](docs/)

---

## Detectors

O.D.I.A. runs 12 anomaly detectors across every document:

- **fiscal** — Dollar amounts without appropriation references; missing provenance
- **procurement** — Contract execution before governing-body authorization
- **scope** — Amendment-as-procurement; sole-source expansion beyond original scope
- **signature** — Blank or placeholder signature blocks
- **governance** — Surveillance capability deployed without policy documentation
- **surveillance** — Third-party surveillance outsourcing without safeguards
- **constitutional** — Broad delegation of authority without limiting standards
- **administrative** — Missing required fields; retroactive authorizations
- **cross_reference** — Conflicting federal and state legal citations
- **temporal** — Multi-year contract lineage patterns (scope creep, vendor lock-in)
- **compliance** — ACLU CCOPS oversight mandate coverage gaps
- **multi_jurisdiction** — Cross-jurisdiction vendor procurement patterns
