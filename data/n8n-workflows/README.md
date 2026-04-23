# n8n Workflow Bundle

Reference workflows for the O.D.I.A. v2.7.1 automation surface. Eight
workflows cover the Tier 1 → Tier 2 → Tier 3 pipeline described in
`docs/ENHANCEMENT_PLAN_v2_7_1.docx` §3.2.

**All workflows ship inactive.** Activate per-jurisdiction only after
reviewing the Code node's jurisdiction config and verifying the
backend webhook token matches n8n's stored credential.

## Bundle contents

| ID | Name | Fires on | Calls |
|---|---|---|---|
| WF-001 | CivicPlus Scraper → Tier 1 Ingest | CRON (configurable) | `POST /api/v1/webhook/ingest-and-analyze` |
| WF-003 | Severity Router | Finding produced by WF-001 | Routes to WF-004 / WF-005 / WF-011 |
| WF-004 | CRITICAL Finding → Gmail Alert | WF-003 routing | Gmail API |
| WF-005 | CPRA Deadline Watcher | CRON 06:00 daily | `GET /api/v1/cpra/deadlines-within/{window}` (C3) |
| WF-008 | Post-Batch MAS Generation | WF-001 batch completion | `POST /api/v1/reports/mas-generate` |
| WF-010 | RAIA Cross-Jurisdictional Synthesis | Manual / monthly | `POST /api/v1/webhook/synthesize` |
| WF-011 | USASpending.gov JAG Cross-Verification | Finding with `details.statute == "JAG"` | USASpending.gov API |
| WF-014 | Provenance Chain Export | Manual | `GET /api/v1/export/provenance-chain` |

Some workflows depend on endpoints that are not yet implemented (C3
CPRA watcher, C4 field verification, C6 Obsidian export). Importing the
bundle is safe regardless — workflows that hit missing endpoints fail
at execution, not at import.

## Importing

### Via the n8n UI (recommended for first import)

1. Open n8n at http://localhost:5678 and sign in with the basic-auth
   credentials from `.env`.
2. Click **Workflows** in the left rail → click **...** (more) in the
   top-right → **Import from File**.
3. Select `data/n8n-workflows/bundle.json` from this repo.
4. n8n will import all eight workflows into the current workspace.
   They will appear inactive in the workflows list.
5. For each workflow you intend to activate:
   - Open the workflow in the editor.
   - Locate the **Jurisdiction Config** Code node near the start.
   - Edit the `jurisdictionId` and any portal-URL / contact fields
     for your target jurisdiction.
   - Verify the **HTTP Request** credential references the correct
     ODIA webhook token (see *Credentials* below).
   - Toggle **Active** at the top of the editor.

### Via the n8n CLI (scripted imports)

```bash
# Inside the n8n container
docker exec -it odia-n8n n8n import:workflow \
    --input=/home/node/workflows/bundle.json
```

CLI import places the workflows in the default workspace of the
authenticated user. Activation still happens via the UI because the
CLI does not expose an activation flag.

## Credentials

The bundle does NOT include any secrets — n8n's credential export is
intentionally gitignored (see `.gitignore` at repo root + the
`credentials/` directory below once you export any). Before activating
any workflow you must create, in the n8n UI, at minimum:

- **ODIA Webhook Token** (HTTP Header Auth): header name
  `X-ODIA-Webhook-Token`, value from `.env`'s `ODIA_WEBHOOK_TOKEN`.
- **Gmail OAuth2** (for WF-004): standard n8n Gmail credential flow.
- **Google Drive OAuth2** (for WF-008, WF-010): standard flow; grant
  access to the folder whose ID you set as `ODIA_DRIVE_MAS_FOLDER`.

## First-jurisdiction activation (per handoff A10)

Low-volume jurisdictions are the right starting point — fewer
documents per day means any wiring bug surfaces with a small blast
radius. Good candidates from the current deployment footprint:

- Woodlake (~2 docs/week)
- Farmersville (~3 docs/week)
- Lindsay (~5 docs/week)

Activation log should be maintained at
`docs/automation/activation-log.md` with jurisdiction name,
activation date, and first-run finding count.
