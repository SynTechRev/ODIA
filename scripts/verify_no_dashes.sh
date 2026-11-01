#!/bin/bash
# Verify zero em-dashes and zero en-dashes across all markdown and produced artifacts.
# Run before every commit on the learning/10-day-challenge branch.
# Usage: bash scripts/verify_no_dashes.sh [target_dir]
set -e

TARGET_DIR="${1:-.}"

EM_DASH=$'\xe2\x80\x94'
EN_DASH=$'\xe2\x80\x93'

em_count=$(grep -r --include="*.md" --include="*.py" --include="*.yaml" \
  --include="*.yml" --include="*.txt" --include="*.jsonl" \
  -c "$EM_DASH" "$TARGET_DIR" 2>/dev/null \
  | awk -F: '{s+=$2} END {print s+0}')

en_count=$(grep -r --include="*.md" --include="*.py" --include="*.yaml" \
  --include="*.yml" --include="*.txt" --include="*.jsonl" \
  -c "$EN_DASH" "$TARGET_DIR" 2>/dev/null \
  | awk -F: '{s+=$2} END {print s+0}')

echo "Em-dash count: $em_count"
echo "En-dash count: $en_count"

if [ "$em_count" -gt 0 ] || [ "$en_count" -gt 0 ]; then
  echo ""
  echo "FAIL: Non-zero dash count. Files containing dashes:"
  grep -r --include="*.md" --include="*.py" --include="*.yaml" \
    --include="*.yml" --include="*.txt" --include="*.jsonl" \
    -l "$EM_DASH" "$TARGET_DIR" 2>/dev/null && true
  grep -r --include="*.md" --include="*.py" --include="*.yaml" \
    --include="*.yml" --include="*.txt" --include="*.jsonl" \
    -l "$EN_DASH" "$TARGET_DIR" 2>/dev/null && true
  exit 1
fi
echo "PASS: Zero em-dashes and en-dashes verified."
