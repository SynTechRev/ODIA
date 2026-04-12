# Python → TypeScript Porting Guide

This document describes the methodology used to port ODIA's Python analysis
detectors to TypeScript for the mobile application.

## Porting Methodology

### 1. Function-by-Function Translation

Each Python detector file maps 1:1 to a TypeScript file:

| Python Source | TypeScript Port |
|---------------|-----------------|
| `analysis/fiscal.py` | `lib/analysis/detectors/fiscal.ts` |
| `analysis/constitutional.py` | `lib/analysis/detectors/constitutional.ts` |
| `analysis/surveillance.py` | `lib/analysis/detectors/surveillance.ts` |
| `analysis/procurement_timeline.py` | `lib/analysis/detectors/procurementTimeline.ts` |
| `analysis/governance_gap.py` | `lib/analysis/detectors/governanceGap.ts` |
| `analysis/signature_chain.py` | `lib/analysis/detectors/signatureChain.ts` |
| `analysis/administrative_integrity.py` | `lib/analysis/detectors/administrativeIntegrity.ts` |
| `analysis/scope_expansion.py` | `lib/analysis/detectors/scopeExpansion.ts` |
| `analysis/cross_reference.py` | `lib/analysis/detectors/crossReference.ts` |
| `analysis/text_utils.py` | `lib/analysis/textUtils.ts` |
| `analysis/scalar_core.py` | `lib/analysis/scalarCore.ts` |
| `analysis/audit_engine.py` | `lib/analysis/auditEngine.ts` |
| `analysis/pipeline.py` | `lib/analysis/pipeline.ts` |

### 2. Naming Conventions

| Python | TypeScript |
|--------|------------|
| `snake_case` functions | `camelCase` functions |
| `UPPER_SNAKE_CASE` constants | `UPPER_SNAKE_CASE` constants |
| `_private_function` | non-exported function |
| `dict[str, Any]` | `Record<string, unknown>` or typed interface |
| `list[dict]` | `Anomaly[]` |
| `str | None` | `string \| null` |

### 3. Regex Translation

Python `re` patterns translate directly to JavaScript RegExp:

```python
# Python
PATTERN = re.compile(r"\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+", re.IGNORECASE)
matches = PATTERN.findall(text)
```

```typescript
// TypeScript
const PATTERN = /\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+/gi;
const matches = text.match(PATTERN) || [];
```

**Key differences:**
- Python `re.IGNORECASE` → JavaScript `i` flag
- Python `re.findall()` → JavaScript `String.match()` (with `g` flag)
- Python `re.search()` → JavaScript `RegExp.exec()` or `RegExp.test()`
- JavaScript global regex (`g` flag) requires `lastIndex` reset between uses

### 4. Type System Mapping

```python
# Python
def detect_fiscal_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
```

```typescript
// TypeScript (with strong typing)
function detectFiscalAnomalies(doc: NormalizedDocument): Anomaly[]
```

All anomalies use the `Anomaly` interface:
```typescript
interface Anomaly {
  id: string;
  issue: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  layer: string;
  details: Record<string, unknown>;
}
```

### 5. Date Handling

```python
# Python
from datetime import date
date.fromisoformat(value.strip())
(auth_date - exec_date).days
```

```typescript
// TypeScript
const date = new Date(value.trim() + 'T00:00:00Z');
Math.round((authDate.getTime() - execDate.getTime()) / (1000 * 60 * 60 * 24));
```

**Key difference:** JavaScript `Date` constructor needs explicit UTC handling
to avoid timezone-related inconsistencies with Python's `date.fromisoformat()`.

### 6. Truthiness and Null Checks

```python
# Python
if not isinstance(doc, dict):
    return []
if not prov.get("hash"):
    ...
```

```typescript
// TypeScript
if (!doc || typeof doc !== 'object') {
  return [];
}
if (!prov?.hash) {
  ...
}
```

Python's `isinstance(x, dict)` → TypeScript's `typeof x === 'object'` plus null check.

### 7. List Comprehensions

```python
# Python
found = [kw for kw in KEYWORDS if kw in text_lower]
```

```typescript
// TypeScript
const found = KEYWORDS.filter((kw) => textLower.includes(kw));
```

## Verification Approach

### Output Comparison

For each detector, unit tests verify:
1. **Identical anomaly IDs** — Same `id` string (e.g., `"fiscal:missing-provenance-hash"`)
2. **Identical severity levels** — Same severity classification
3. **Identical layer names** — Same layer string
4. **Same detection logic** — Same conditions trigger/suppress findings
5. **Same details structure** — Same keys and value types in details

### Test-Driven Porting

1. Read the Python detector carefully
2. Write TypeScript tests based on expected Python behavior
3. Implement the TypeScript detector
4. Verify tests pass
5. Cross-check with Python tests in `tests/` directory

## Known Deviations

| Area | Python | TypeScript | Justification |
|------|--------|------------|---------------|
| Hash function | `hash(text) % 10**8` | `hashCode(text)` | Python's `hash()` is not deterministic across runs; both generate stable IDs |
| DateTime | `datetime.now(UTC)` | `new Date()` | Both produce ISO 8601 timestamps; JS uses local TZ in `.toISOString()` which outputs UTC |
| Type checking | `isinstance(doc, dict)` | `typeof doc === 'object'` | JavaScript has no `dict` type; object check is equivalent |
| Regex global state | Stateless | Requires `lastIndex` reset | JavaScript regex with `g` flag maintains state; must reset between uses |

## Adding New Detectors

To add a new detector:

1. Create `lib/analysis/detectors/newDetector.ts`
2. Implement the detector as a pure function
3. Add exports to `lib/analysis/detectors/index.ts` and `lib/analysis/index.ts`
4. Create `__tests__/detectors/newDetector.test.ts`
5. If integrated into the pipeline, update `auditEngine.ts` or `pipeline.ts`
