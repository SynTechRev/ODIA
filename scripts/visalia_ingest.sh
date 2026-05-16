#!/usr/bin/env bash
# =============================================================================
# visalia_ingest.sh — autonomous Visalia ingest via Ubuntu shell
# =============================================================================
# Bypasses n8n entirely. Why: n8n's hardened image strips out shell-execution
# node types AND lacks curl/apk for installing one. Since (a) wget downloads
# from Cloudflare-fronted CivicPlus work fine in Ubuntu and (b) curl POST to
# our local uvicorn works fine, the simplest path is to do the whole loop
# right here in shell.
#
# Pipeline:
#   1. curl the AgendaCenter search page (CIDs=all returns server-rendered HTML
#      with all 75-85 document links visible — no JS required)
#   2. grep + sed to extract /AgendaCenter/ViewFile/... hrefs
#   3. for each link: wget the PDF, then curl POST it to ODIA's webhook
#   4. tally success / failure counts at the end
#
# Throttled with 1-second sleep between downloads to be polite to CivicPlus.
#
# Usage:  bash scripts/visalia_ingest.sh
# =============================================================================

set -uo pipefail

JURISDICTION="visalia"
PORTAL="https://www.visalia.gov/AgendaCenter/Search/?term=&CIDs=all&startDate=&endDate=&dateRange=&dateSelector="
WEBHOOK="http://localhost:8000/api/v1/webhook/ingest-and-analyze"
TOKEN_FILE="/mnt/c/Users/yahua/AppData/Roaming/ODIA/webhook_token"
WORK_DIR="/tmp/visalia_pdfs"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# --- Pre-flight ---
[[ -r "$TOKEN_FILE" ]] || { echo "ERROR: Webhook token file not found at $TOKEN_FILE"; exit 1; }
TOKEN=$(<"$TOKEN_FILE")
[[ -n "$TOKEN" ]] || { echo "ERROR: Token file is empty"; exit 1; }
mkdir -p "$WORK_DIR"

echo "==== Visalia autonomous ingest ===="
echo "Token: ${TOKEN:0:8}..."
echo "Work dir: $WORK_DIR"
echo "Webhook: $WEBHOOK"
echo

# --- Step 1: fetch the search page ---
echo ">>> Fetching AgendaCenter search page..."
HTML=$(curl -sL -A "$UA" "$PORTAL")
HTML_BYTES=${#HTML}
echo "    Got $HTML_BYTES bytes of HTML"

# --- Step 2: extract /AgendaCenter/ViewFile/... links (dedup) ---
echo ">>> Extracting document links..."
mapfile -t LINKS < <(
    echo "$HTML" \
    | grep -oE 'href="/AgendaCenter/ViewFile/[^"]+"' \
    | sed -E 's|href="(/AgendaCenter/ViewFile/[^"]+)"|https://www.visalia.gov\1|' \
    | sort -u
)
TOTAL=${#LINKS[@]}
echo "    Found $TOTAL unique document links"
[[ $TOTAL -gt 0 ]] || { echo "ERROR: 0 links extracted — page structure may have changed"; exit 1; }

# --- Step 3: download + POST each ---
SUCCESS=0
FAILED=0
ALREADY_SEEN=0
i=0
for URL in "${LINKS[@]}"; do
    i=$((i + 1))
    # Build a stable filename from the URL tail (e.g. _05062026-821 → 05062026-821.pdf)
    DOC_TYPE=$(echo "$URL" | awk -F/ '{print $(NF-1)}' | tr A-Z a-z)
    DOC_ID=$(echo "$URL" | awk -F/ '{print $NF}' | sed 's/^_//')
    LOCAL="$WORK_DIR/${JURISDICTION}_${DOC_TYPE}_${DOC_ID}.pdf"

    printf "[%3d/%d] %-40s " "$i" "$TOTAL" "${DOC_TYPE}_${DOC_ID}"

    # Download
    if ! wget -q -O "$LOCAL" -U "$UA" "$URL"; then
        echo "DOWNLOAD_FAILED"
        FAILED=$((FAILED + 1))
        rm -f "$LOCAL"
        continue
    fi

    BYTES=$(stat -c%s "$LOCAL")
    if [[ $BYTES -lt 1000 ]]; then
        echo "TOO_SMALL ($BYTES bytes — likely a challenge page, not PDF)"
        FAILED=$((FAILED + 1))
        rm -f "$LOCAL"
        continue
    fi
    # Skip agenda packets > 20 MB on first pass — they're meeting bundles
    # with attached exhibits, and the small-byte versions of the same
    # meeting (the agenda-only PDFs) cover the same finding-text. Audit
    # latency on 100+ MB PDFs is 10-30 min each; not viable for a
    # first-light bulk run. Re-ingest these individually later if needed.
    if [[ $BYTES -gt 20971520 ]]; then  # 20 MB cap
        echo "TOO_LARGE_SKIPPED (${BYTES} bytes — agenda packet, deferred)"
        FAILED=$((FAILED + 1))
        # File kept on disk for later targeted ingest
        continue
    fi

    # POST to ODIA
    RESPONSE=$(curl -sS -X POST \
        -H "X-ODIA-Webhook-Token: $TOKEN" \
        -F "file=@$LOCAL;type=application/pdf" \
        -F "jurisdiction_id=$JURISDICTION" \
        "$WEBHOOK")

    # Quick check on response
    if echo "$RESPONSE" | grep -q '"already_seen":true'; then
        echo "ALREADY_SEEN ($BYTES bytes)"
        ALREADY_SEEN=$((ALREADY_SEEN + 1))
    elif echo "$RESPONSE" | grep -q '"status":"ok"'; then
        FINDINGS=$(echo "$RESPONSE" | grep -oE '"count":[0-9]+' | head -1 | grep -oE '[0-9]+')
        echo "OK ($BYTES bytes, $FINDINGS findings)"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "POST_FAILED: $(echo "$RESPONSE" | head -c 100)"
        FAILED=$((FAILED + 1))
    fi

    sleep 1   # be polite to CivicPlus
done

# --- Summary ---
echo
echo "==== Done ===="
echo "Success (new):    $SUCCESS"
echo "Already seen:     $ALREADY_SEEN"
echo "Failed:           $FAILED"
echo "Total processed:  $i / $TOTAL"
echo
echo "PDFs cached at:   $WORK_DIR"
