"""Plain-language translator for ODIA anomaly findings.

Converts raw detector findings (technical dicts) into 8th-grade-reading-level
explanations suitable for non-technical audiences such as journalists,
community organizers, and city council members.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Translation table
# Format: {detector_type: {subtype: {summary, impact, action}}}
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "procurement_timeline": {
        "execution_before_authorization": {
            "summary": "This contract was signed before the City Council voted to approve it.",
            "impact": "A binding financial commitment was made without proper authorization from elected officials.",
            "action": "Verify the authorization chain and determine whether the contract should be ratified or voided.",
        },
        "rapid_execution": {
            "summary": "This contract was signed very quickly after authorization — less than 7 days.",
            "impact": "The short turnaround may indicate the contract was predetermined before the public vote.",
            "action": "Review whether adequate public notice and deliberation preceded the authorization.",
        },
        "procurement_before_authorization": {
            "summary": "Procurement activity appears to have occurred before the governing body voted.",
            "impact": "Spending may have been initiated without the required legislative approval.",
            "action": "Trace the timeline of authorization against the procurement record.",
        },
    },
    "signature_chain": {
        "blank_signature": {
            "summary": "This document has a signature line that was never signed.",
            "impact": "The document may not be legally binding without all required signatures.",
            "action": "Obtain fully executed copies of this document from the issuing office.",
        },
        "pending_docusign": {
            "summary": "This document shows a pending electronic signature that was never completed.",
            "impact": "The agreement may not have been finalized despite being treated as active.",
            "action": "Confirm whether a fully signed version exists in the official record.",
        },
        "missing_signature": {
            "summary": "A required signature is absent from this document.",
            "impact": "Without all required signatures, the document's legal validity is uncertain.",
            "action": "Request the fully executed version from the responsible department.",
        },
    },
    "governance_gap": {
        "capability_without_governance": {
            "summary": "A surveillance technology was deployed without required governance documentation.",
            "impact": "There is no written policy governing how this technology is used, who can access its data, or how long data is kept.",
            "action": "Request that the governing body adopt a surveillance use policy before continued operation.",
        },
        "surveillance_without_policy": {
            "summary": "Surveillance capability is in use without an accompanying oversight policy.",
            "impact": "Without a documented policy, there are no enforceable limits on how surveillance data is collected or used.",
            "action": "Demand adoption of a formal use policy before continued deployment of this technology.",
        },
    },
    "scope_expansion": {
        "amendment_exceeds_threshold": {
            "summary": "This contract has been expanded far beyond its original approved scope through amendments.",
            "impact": "The total cost now significantly exceeds what was originally authorized, without a new competitive bidding process.",
            "action": "Review whether the expanded scope requires new authorization or competitive procurement.",
        },
        "sole_source_expansion": {
            "summary": "A sole-source contract has grown substantially beyond its original value through amendments.",
            "impact": "Large amendments to sole-source contracts can circumvent competitive procurement requirements.",
            "action": "Determine whether the total amended value requires re-procurement under competitive bidding rules.",
        },
        "amendment_without_baseline": {
            "summary": "This contract was amended but no original baseline contract was found to compare against.",
            "impact": "Without a baseline, it is impossible to determine how much the scope has grown.",
            "action": "Request the original contract from the responsible department to establish the baseline.",
        },
    },
    "surveillance": {
        "outsourcing_detected": {
            "summary": "A third-party vendor is operating surveillance systems on behalf of the city.",
            "impact": "Outsourced surveillance may not be subject to the same oversight as city-operated systems.",
            "action": "Verify that vendor contracts include privacy safeguards and data handling requirements.",
        },
        "third_party_data_sharing": {
            "summary": "Surveillance data appears to be shared with a third-party contractor.",
            "impact": "Sharing data with vendors creates privacy risks and reduces accountability.",
            "action": "Review data-sharing agreements to confirm appropriate safeguards are in place.",
        },
    },
    "fiscal": {
        "amount_without_appropriation": {
            "summary": "This document references spending that has no corresponding budget authorization.",
            "impact": "Public funds may have been spent without the required appropriation from the governing body.",
            "action": "Trace the appropriation chain to verify funds were properly authorized.",
        },
        "missing_provenance_hash": {
            "summary": "This financial document is missing a document integrity verification hash.",
            "impact": "Without a provenance hash, it is difficult to confirm the document has not been altered.",
            "action": "Request a certified copy directly from the official records system.",
        },
        "unappropriated_spending": {
            "summary": "Spending in this document appears to lack a corresponding budget line item.",
            "impact": "Funds spent outside of an approved budget may violate appropriation law.",
            "action": "Cross-reference with the adopted budget to identify the appropriation source.",
        },
    },
    "constitutional": {
        "broad_delegation": {
            "summary": "This resolution grants broad authority without clear limits on scope, time, or spending.",
            "impact": "Unlimited delegation of authority may violate separation of powers principles.",
            "action": "Recommend the governing body add specific dollar limits, time limits, and scope constraints.",
        },
        "unlimited_authority": {
            "summary": "An official was granted authority to act with no stated limits.",
            "impact": "Unconstrained delegations can lead to actions that were not contemplated by the governing body.",
            "action": "Request that the delegation be amended to include clear scope, duration, and spending limits.",
        },
    },
    "administrative_integrity": {
        "missing_final_action": {
            "summary": "This legislative record is missing its final action or vote record.",
            "impact": "Without a recorded vote, it's unclear whether this item was properly approved.",
            "action": "Request the complete legislative record including the final action from the clerk's office.",
        },
        "retroactive_authorization": {
            "summary": "This document authorizes or ratifies an action that already took place.",
            "impact": "Retroactive authorizations suggest the action was taken without proper advance approval.",
            "action": "Investigate whether the original action complied with procurement or authorization rules.",
        },
        "blank_required_field": {
            "summary": "A required field in this official document was left blank.",
            "impact": "Incomplete official records undermine accountability and may indicate documentation errors.",
            "action": "Request a corrected record from the responsible department.",
        },
    },
    "cross_reference": {
        "jurisdiction_boundary": {
            "summary": "This document references both federal and state law in a way that suggests jurisdictional confusion.",
            "impact": "Mixing federal and state authority without clarity can create enforcement gaps.",
            "action": "Refer to legal counsel for clarification of applicable jurisdiction.",
        },
        "conflicting_citations": {
            "summary": "This document cites federal and state statutes that may conflict with each other.",
            "impact": "Conflicting legal citations can make the document's requirements ambiguous or unenforceable.",
            "action": "Have an attorney review which legal authority governs and clarify the document accordingly.",
        },
    },
    "temporal_pattern": {
        "contract_evolution": {
            "summary": "This contract has evolved significantly over time through a series of amendments.",
            "impact": "Incremental amendments can allow a contract to grow far beyond its original intent without proper review.",
            "action": "Review the full amendment history and determine whether re-procurement is warranted.",
        },
        "vendor_lock_in": {
            "summary": "This vendor has held a contract for an unusually long period with repeated renewals.",
            "impact": "Long-term vendor relationships without re-competition may limit cost savings and introduce bias.",
            "action": "Evaluate whether the contract should go through a new competitive bidding process.",
        },
    },
}

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def translate_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Add plain-language fields to a finding dict.

    Adds three keys to the returned copy:
      - plain_summary: one sentence at ~8th grade reading level
      - plain_impact:  one sentence explaining why it matters
      - plain_action:  one sentence recommending what to do

    The original finding dict is not mutated.
    """
    result = dict(finding)

    # Extract detector type and subtype from the finding id or layer
    finding_id: str = finding.get("id", "") or ""
    layer: str = finding.get("layer", "") or ""

    if ":" in finding_id:
        parts = finding_id.split(":", 1)
        detector_type = parts[0].strip()
        subtype = parts[1].strip()
    else:
        detector_type = layer or finding_id
        subtype = ""

    # Normalize detector type key (handle aliases)
    detector_key = _normalize_detector_key(detector_type)

    # Look up translation
    detector_map = TRANSLATIONS.get(detector_key, {})
    translation = detector_map.get(subtype, {})

    if not translation:
        # Try a partial subtype match (e.g. "execution_before_authorization" → "execution_before")
        for key, val in detector_map.items():
            if subtype.startswith(key) or key.startswith(subtype):
                translation = val
                break

    if translation:
        result["plain_summary"] = translation["summary"]
        result["plain_impact"] = translation["impact"]
        result["plain_action"] = translation["action"]
    else:
        # Generic fallback
        severity = finding.get("severity", "unknown")
        result["plain_summary"] = (
            f"An anomaly was detected by the {detector_type} detector with {severity} severity."
        )
        result["plain_impact"] = (
            "This finding requires professional review to assess its significance."
        )
        result["plain_action"] = (
            "Consult the full technical finding details and consider engaging qualified counsel."
        )

    return result


def translate_report(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply translate_finding to every finding in a list. Returns new list."""
    return [translate_finding(f) for f in findings]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DETECTOR_KEY_ALIASES: dict[str, str] = {
    "procurement": "procurement_timeline",
    "procurement_violation": "procurement_timeline",
    "signature": "signature_chain",
    "governance": "governance_gap",
    "scope": "scope_expansion",
    "admin": "administrative_integrity",
    "administrative": "administrative_integrity",
    "cross_reference": "cross_reference",
    "temporal": "temporal_pattern",
    "contract_evolution": "temporal_pattern",
}


def _normalize_detector_key(key: str) -> str:
    return _DETECTOR_KEY_ALIASES.get(key, key)
