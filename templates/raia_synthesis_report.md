# R.A.I.A. Cross-Jurisdiction Synthesis Report

**Synthesis ID:** `{{ result.synthesis_id }}`
**Generated:** {{ result.generated_at }}
**Tier 3 recursive synthesis:** {% if result.include_tier3 %}included{% else %}not included{% endif %}

**Jurisdictions analysed:** {% if result.jurisdictions %}{{ result.jurisdictions | map(attribute='jurisdiction_id') | join(', ') }}{% else %}none{% endif %}{# v3.0: explicit newline below; trim_blocks would otherwise eat the line break before the next conditional #}

{% if result.missing_jurisdictions -%}
**Missing (no persisted data):** {{ result.missing_jurisdictions | join(', ') }}

{% endif -%}

---

## Executive Summary

Across {{ result.jurisdictions | length }} jurisdiction(s), R.A.I.A. observed
{{ result.jurisdictions | sum(attribute='document_count') }} document(s),
{{ result.jurisdictions | sum(attribute='analysis_count') }} analysis run(s),
and {{ result.jurisdictions | sum(attribute='total_anomalies') }} anomaly finding(s).
{{ result.patterns | length }} cross-jurisdiction pattern(s) surfaced at synthesis time.

---

## Per-Jurisdiction Summary

{% if result.jurisdictions -%}
| Jurisdiction | Documents | Analyses | Anomalies | Avg Score | Top Layer |
|--------------|-----------|----------|-----------|-----------|-----------|
{% for s in result.jurisdictions -%}
| {{ s.jurisdiction_id }} | {{ s.document_count }} | {{ s.analysis_count }} | {{ s.total_anomalies }} | {{ "%.3f" | format(s.scalar_score_avg) }} | {% if s.layer_counts %}{{ s.layer_counts.items() | sort(attribute=1, reverse=true) | first | first }}{% else %}—{% endif %} |
{% endfor %}
{%- else -%}
*No jurisdiction data loaded.*
{%- endif %}

### Severity breakdown

{% for s in result.jurisdictions -%}
- **{{ s.jurisdiction_id }}** — {% if s.severity_counts %}{% for sev, count in s.severity_counts.items() %}{{ sev }}: {{ count }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}
{% endfor %}

---

## Cross-Jurisdiction Patterns

{% if result.patterns -%}
{% for p in result.patterns %}
### {{ p.pattern_id }}

- **Type:** `{{ p.pattern_type }}`
- **Confidence:** {{ "%.2f" | format(p.confidence) }} ({{ p.jurisdictions_affected | length }} of {{ result.jurisdictions | length }} jurisdictions)
- **Jurisdictions:** {{ p.jurisdictions_affected | join(', ') }}
- **Description:** {{ p.description }}
{% if p.evidence %}

**Evidence:**
{% for key, value in p.evidence.items() %}
- `{{ key }}`: {{ value }}
{% endfor %}
{% endif %}
{% endfor %}
{%- else -%}
*No cross-jurisdiction patterns detected. At least two jurisdictions with persisted data are required.*
{%- endif %}

---

## Top Anomalies (per jurisdiction)

{% for s in result.jurisdictions -%}
### {{ s.jurisdiction_id }}

{% if s.top_anomalies -%}
{% for a in s.top_anomalies -%}
- **[{{ a.severity | upper }}]** `{{ a.anomaly_id }}` ({{ a.layer }}) — {{ a.issue }}
{% endfor %}
{%- else -%}
*No anomalies recorded.*
{%- endif %}

{% endfor %}

{% if result.include_tier3 and result.tier3_notes -%}
---

## Tier 3 Notes

{% for key, value in result.tier3_notes.items() -%}
- **{{ key }}:** {{ value }}
{% endfor %}
{%- endif %}
