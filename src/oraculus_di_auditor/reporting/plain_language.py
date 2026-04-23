"""Plain-language translator for ODIA anomaly findings.

Converts raw detector findings (technical dicts) into MAS-grade narrative
suitable for evidence packets, journalists, community organizers, and
council members.

Post-v2.7.2 rewrite (D1 from CLAUDE_CODE_HANDOFF_v2_7_3):

  * TRANSLATIONS now covers every finding ID the detectors actually
    emit — hyphen-separated, keyed to the canonical output of each
    detector in ``src/oraculus_di_auditor/analysis/*.py``. Legacy
    underscore-form subtypes (what callers constructed by hand before
    the detector rewrites) are retained as aliases so existing tests
    keep passing.

  * Each narrative is a ``str.format_map``-able template that
    interpolates the finding's ``details`` dict. Missing keys degrade
    to the un-interpolated template rather than raising. That lets the
    plain-language layer keep working even when a detector version
    skips a detail field.

  * ``translate_finding`` now also attaches a ``plain_evidence_echo``
    paragraph — a one-line rendering of the raw ``details`` dict — so
    the evidence packet can cite its own structured source inline the
    way a MAS report does.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Translation table
# Format: {detector_type: {subtype: {summary, impact, action}}}
#
# Subtype keys are PRIMARILY hyphen-form (matching what detectors emit),
# with underscore-form aliases retained for backward compat with callers
# that constructed subtypes by hand before the detector rewrites.
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    # -----------------------------------------------------------------------
    # procurement (layer) → procurement_timeline (translator key)
    # -----------------------------------------------------------------------
    "procurement_timeline": {
        # Canonical hyphen-form IDs from procurement_timeline.py
        "execution-precedes-authorization": {
            "summary": (
                "This contract was executed {days_early} day(s) before the "
                "council voted to authorize it."
            ),
            "impact": (
                "A binding financial commitment was made without the "
                "advance authorization required by California Gov Code "
                "§ 54202 and the jurisdiction's purchasing ordinance. "
                "Expenditures made prior to a valid appropriation can "
                "constitute a Gann-limit violation and expose the "
                "signatory to personal financial liability under Gov "
                "Code § 1090 in the sole-source case."
            ),
            "action": (
                "Obtain the execution and authorization documents, confirm "
                "the signature dates against the council minutes, and "
                "determine whether the contract should be ratified, "
                "voided, or referred to the grand jury."
            ),
        },
        "consent-calendar-placement": {
            "summary": (
                "A vendor contract was placed on the consent calendar "
                "(vendors: {vendors}), bypassing individual council "
                "discussion of the procurement."
            ),
            "impact": (
                "Consent-calendar placement of surveillance or "
                "sole-source contracts suppresses the public-deliberation "
                "requirement of the Brown Act (Gov Code § 54950 et seq.) "
                "and removes the opportunity for the community to "
                "examine the vendor before approval."
            ),
            "action": (
                "Request the consent-calendar item be pulled for "
                "individual discussion at the next meeting, and demand "
                "the staff report disclose the vendor's capabilities, "
                "cost, and comparable alternatives."
            ),
        },
        "sole-source-without-gov-code-citation": {
            "summary": (
                "Sole-source procurement was used without the California "
                "Gov Code § 10340 (or § 10300–10334) justification "
                "required for bypass of competitive bidding. Vendors "
                "referenced: {vendors}."
            ),
            "impact": (
                "Sole-source awards without a Gov Code citation are "
                "presumptively invalid and may trigger State Controller "
                "audit review. Recipients may be required to repay the "
                "award or re-procure under § 10344."
            ),
            "action": (
                "Request the Gov Code § 10340(b) written justification, "
                "the internal sole-source memo, and the department-head "
                "certification. If none exist, refer to the County "
                "Counsel or State Controller for compliance review."
            ),
        },
        "auto-renewal-clause": {
            "summary": (
                "Contract contains an auto-renewal clause — the contract "
                "with {vendors} renews without an affirmative council "
                "vote unless a non-renewal notice is served in advance."
            ),
            "impact": (
                "Auto-renewal clauses let multi-year surveillance or "
                "professional-services contracts persist indefinitely "
                "without recurring public scrutiny. Renewal-notice "
                "deadlines are easy to miss; the agency is then bound "
                "to another year of spending it may no longer want."
            ),
            "action": (
                "Calendar the non-renewal-notice deadline, request the "
                "renewal history for this vendor, and add a standing "
                "council review to the calendar 90 days before each "
                "auto-renewal fires."
            ),
        },
        # Legacy underscore-form aliases (kept for backward compat)
        "execution_before_authorization": {
            "summary": "This contract was signed before the City Council voted to approve it.",
            "impact": (
                "A binding financial commitment was made without proper "
                "authorization from elected officials."
            ),
            "action": (
                "Verify the authorization chain and determine whether the "
                "contract should be ratified or voided."
            ),
        },
        "rapid_execution": {
            "summary": (
                "This contract was signed very quickly after authorization — "
                "less than 7 days."
            ),
            "impact": (
                "The short turnaround may indicate the contract was "
                "predetermined before the public vote."
            ),
            "action": (
                "Review whether adequate public notice and deliberation "
                "preceded the authorization."
            ),
        },
        "procurement_before_authorization": {
            "summary": (
                "Procurement activity appears to have occurred before the "
                "governing body voted."
            ),
            "impact": (
                "Spending may have been initiated without the required "
                "legislative approval."
            ),
            "action": (
                "Trace the timeline of authorization against the procurement "
                "record."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # grant (layer: grant_compliance) → grant_compliance (translator key)
    # -----------------------------------------------------------------------
    "grant_compliance": {
        "jag-without-anti-supplanting": {
            "summary": (
                "This document references a Justice Assistance Grant "
                "(JAG / Edward Byrne Memorial) without the "
                "anti-supplanting certification required by {statute}."
            ),
            "impact": (
                "Federal law requires the recipient agency to certify "
                "that grant funds will not supplant local appropriations "
                "that would otherwise have been available for the same "
                "purposes. Absence of this certification is a grant-"
                "compliance violation under 2 C.F.R. § 200.303 and "
                "exposes the jurisdiction to OIG audit findings, "
                "repayment obligations, and possible debarment from "
                "future JAG awards."
            ),
            "action": (
                "Request the fully executed anti-supplanting "
                "certification from the JAG recipient agency. If not "
                "produced within 10 business days, refer to the DOJ "
                "Office of Justice Programs Office of Audit, Assessment, "
                "and Management for compliance review."
            ),
        },
        "jag-funded-surveillance": {
            "summary": (
                "A JAG grant is referenced alongside surveillance "
                "vendors {vendors} — JAG-funded technology purchases "
                "must be itemised and reported to the Bureau of Justice "
                "Assistance."
            ),
            "impact": (
                "BJA requires grant recipients to itemise technology "
                "and equipment purchases separately from personnel, and "
                "to report surveillance deployments against the JAG "
                "Program Assessment Rating Tool metrics. Bundling "
                "surveillance purchases into generic line items defeats "
                "federal oversight."
            ),
            "action": (
                "Request the JAG grant-application line-item budget and "
                "the quarterly Program Performance Report. Cross-"
                "reference the surveillance vendor invoices against the "
                "approved budget category."
            ),
        },
        "cops-without-itemisation": {
            "summary": (
                "A COPS Hiring Program grant is referenced without "
                "technology-cost itemisation — hiring and technology "
                "expenditures must be separated under the COPS grant "
                "rules."
            ),
            "impact": (
                "The COPS Office requires that grant-funded technology "
                "purchases be itemised separately from sworn-officer "
                "hiring so the grant's hiring-focus intent is preserved. "
                "Bundled cost reporting can constitute grant "
                "misallocation under 2 C.F.R. § 200.405."
            ),
            "action": (
                "Request the COPS grant application, the approved "
                "budget detail, and the quarterly financial reports. "
                "Verify technology line items are broken out and that "
                "total technology spend stays under the COPS-allowed "
                "technology cap."
            ),
        },
        "crim-intel-without-28-cfr-23": {
            "summary": (
                "Criminal-intelligence references appear in this "
                "document without a 28 CFR Part 23 compliance citation "
                "({statute})."
            ),
            "impact": (
                "28 CFR Part 23 imposes strict limits on how a federally "
                "funded criminal-intelligence system collects, stores, "
                "and shares information about identifiable persons. "
                "Operating an intelligence database without a 28 CFR "
                "Part 23 policy exposes the agency to DOJ audit "
                "findings, loss of federal funding, and civil "
                "liability under 42 U.S.C. § 1983."
            ),
            "action": (
                "Request the agency's 28 CFR Part 23 policy, the most "
                "recent audit, and the query-logging records. If no "
                "policy exists, demand adoption before continued "
                "operation of the intelligence system."
            ),
        },
    },
    # Alias table routes "grant" → "grant_compliance". Keeping legacy
    # grant entries here too so hand-constructed subtypes resolve.
    # -----------------------------------------------------------------------
    # signature (layer) → signature_chain (translator key)
    # -----------------------------------------------------------------------
    "signature_chain": {
        # Canonical hyphen-form IDs from signature_chain.py
        "unsigned-instrument": {
            "summary": (
                "A signature gap was detected in a {instrument_type} "
                "instrument (gap type: {signature_gap_type}, dollar "
                "amount: {dollar_amount})."
            ),
            "impact": (
                "Unsigned financial instruments are not legally binding "
                "and any action taken in reliance on them is voidable. "
                "An unsigned contract carrying a dollar amount may be "
                "treated as an unauthorized expenditure under Gov Code "
                "§ 1090 and trigger personal liability for the "
                "approving officer."
            ),
            "action": (
                "Obtain the fully executed original from the issuing "
                "office. If no signed original exists, refer to "
                "counsel for determination of whether the instrument "
                "is void and any expenditures must be clawed back."
            ),
        },
        "placeholder-tokens": {
            "summary": (
                "An unresolved signature placeholder token "
                "(`{token}`) was found at position {position} of this "
                "document."
            ),
            "impact": (
                "Placeholder tokens in a filed document indicate the "
                "record was released in draft form. Relying on a draft "
                "as if it were executed can constitute material "
                "misrepresentation and undermines the document's legal "
                "validity."
            ),
            "action": (
                "Request the final, executed version from the issuing "
                "office and refile the corrected document in the "
                "public record."
            ),
        },
        # Legacy underscore-form aliases
        "blank_signature": {
            "summary": "This document has a signature line that was never signed.",
            "impact": (
                "The document may not be legally binding without all "
                "required signatures."
            ),
            "action": (
                "Obtain fully executed copies of this document from the "
                "issuing office."
            ),
        },
        "pending_docusign": {
            "summary": (
                "This document shows a pending electronic signature that "
                "was never completed."
            ),
            "impact": (
                "The agreement may not have been finalized despite being "
                "treated as active."
            ),
            "action": (
                "Confirm whether a fully signed version exists in the "
                "official record."
            ),
        },
        "missing_signature": {
            "summary": "A required signature is absent from this document.",
            "impact": (
                "Without all required signatures, the document's legal "
                "validity is uncertain."
            ),
            "action": (
                "Request the fully executed version from the responsible "
                "department."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # governance (layer: governance_gap) → governance_gap (translator key)
    # -----------------------------------------------------------------------
    "governance_gap": {
        # Canonical hyphen-form IDs from governance_gap.py
        "capability-without-council-approval": {
            "summary": (
                "Surveillance capability (technologies: {technologies}, "
                "vendors: {vendors}) is referenced in this document "
                "without any council-approval or resolution language."
            ),
            "impact": (
                "Deploying surveillance without an enabling resolution "
                "violates the basic ACLU CCOPS oversight framework and, "
                "in California, exposes the agency to civil liability "
                "under SB 1186 / Civ Code § 1798.90 for unauthorized "
                "data collection. Without an authorizing vote, there is "
                "no public mandate for the technology's use."
            ),
            "action": (
                "Demand the governing body adopt a formal surveillance-"
                "use policy and authorizing resolution before continued "
                "operation of the capability, and request suspension of "
                "collection pending that approval."
            ),
        },
        "data-retention-gap": {
            "summary": (
                "Surveillance capability (technologies: {technologies}) "
                "is deployed without any data-retention policy "
                "reference."
            ),
            "impact": (
                "Absent a documented retention schedule, surveillance "
                "data can be held indefinitely or disposed of "
                "arbitrarily — both violate the California Public "
                "Records Act's retention-schedule requirement (Gov "
                "Code § 34090) and create 4th-Amendment liability "
                "under _Carpenter v. United States_, 138 S. Ct. 2206 "
                "(2018)."
            ),
            "action": (
                "Request the department's data-retention schedule, the "
                "Board-approved retention policy, and the most recent "
                "purge log. If none exist, demand adoption of a "
                "schedule bounded by the CPRA retention floor."
            ),
        },
        "lexipol-boilerplate": {
            "summary": (
                "Lexipol California State Master boilerplate language "
                "is referenced in this document — verify that "
                "vendor-specific provisions are actually present and "
                "customized."
            ),
            "impact": (
                "Lexipol boilerplate is generic and may not reflect "
                "the specific vendor contract or statutory obligations "
                "applicable to this jurisdiction. Using unmodified "
                "Lexipol language can create a false compliance "
                "signature where no real policy exists."
            ),
            "action": (
                "Request the full unabridged policy document, compare "
                "against the Lexipol master, and identify every "
                "provision that was customised (or wasn't) for this "
                "agency's actual operations."
            ),
        },
        "consent-calendar-placement": {
            "summary": (
                "A surveillance item (vendors: {vendors}) was placed on "
                "the consent calendar, bypassing individual council "
                "discussion."
            ),
            "impact": (
                "Consent-calendar placement of surveillance items is "
                "the single most common technique for evading the "
                "Brown Act's public-deliberation requirement. CCOPS "
                "Mandate 4 (public engagement) is effectively nullified."
            ),
            "action": (
                "Request the consent-calendar item be pulled for full "
                "individual discussion, with staff presentation and "
                "public comment, before any vote."
            ),
        },
        "sole-source-without-justification": {
            "summary": (
                "Sole-source procurement (vendors: {vendors}) was used "
                "without the California Gov Code § 10340 justification "
                "citation."
            ),
            "impact": (
                "Sole-source awards without a Gov Code citation are "
                "presumptively invalid. The award may be voided and "
                "the agency may face State Controller audit findings."
            ),
            "action": (
                "Obtain the Gov Code § 10340(b) written sole-source "
                "justification. If none exists, refer to County "
                "Counsel for a voidability determination."
            ),
        },
        "auto-renewal-clause": {
            "summary": (
                "An auto-renewal clause is present (vendors: "
                "{vendors}) — the contract renews without a council "
                "vote unless a non-renewal notice is served in advance."
            ),
            "impact": (
                "Auto-renewal lets multi-year surveillance contracts "
                "persist indefinitely without recurring public "
                "oversight. Missing the non-renewal-notice deadline "
                "binds the agency to another term it may no longer want."
            ),
            "action": (
                "Calendar the non-renewal-notice deadline 90 days in "
                "advance, and add the contract to a standing council "
                "review agenda before each auto-renewal date."
            ),
        },
        "transparency-portal-absence": {
            "summary": (
                "Surveillance capability (technologies: {technologies}) "
                "is referenced with no public transparency-portal or "
                "inventory mention."
            ),
            "impact": (
                "Absence of a public surveillance-technology inventory "
                "violates CCOPS Mandate 7 (transparency) and leaves "
                "residents with no way to discover what is being "
                "collected about them. This is the _Riley v. California_ "
                "134 S. Ct. 2473 (2014) concern applied to "
                "jurisdiction-wide deployments."
            ),
            "action": (
                "Demand publication of the full surveillance-technology "
                "inventory, following the ACLU CCOPS model ordinance, "
                "with annual updates and public notice of additions."
            ),
        },
        # Legacy underscore-form aliases
        "capability_without_governance": {
            "summary": (
                "A surveillance technology was deployed without required "
                "governance documentation."
            ),
            "impact": (
                "There is no written policy governing how this "
                "technology is used, who can access its data, or how "
                "long data is kept."
            ),
            "action": (
                "Request that the governing body adopt a surveillance "
                "use policy before continued operation."
            ),
        },
        "surveillance_without_policy": {
            "summary": (
                "Surveillance capability is in use without an "
                "accompanying oversight policy."
            ),
            "impact": (
                "Without a documented policy, there are no enforceable "
                "limits on how surveillance data is collected or used."
            ),
            "action": (
                "Demand adoption of a formal use policy before continued "
                "deployment of this technology."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # scope (layer) → scope_expansion (translator key)
    # -----------------------------------------------------------------------
    "scope_expansion": {
        # Canonical hyphen-form IDs from scope_expansion.py
        "significant-expansion": {
            "summary": (
                "This contract's total value expanded by "
                "{expansion_percentage}% — from {original_amount} to "
                "{expanded_amount} — through amendments rather than "
                "re-procurement."
            ),
            "impact": (
                "Amendment-as-procurement is the single most common "
                "technique for circumventing competitive bidding. A "
                "contract that doubles or triples in value without "
                "going back to bid may violate California Pub Contract "
                "Code § 20162 and expose the agency to bid-protest "
                "litigation from losing vendors."
            ),
            "action": (
                "Demand the cumulative amendment history, compare total "
                "against the competitive-bidding threshold, and refer "
                "to the District Attorney or Attorney General if the "
                "total exceeds the threshold without a new RFP."
            ),
        },
        "amendment-without-baseline": {
            "summary": (
                "An amendment instrument was found with no original "
                "authorization reference in the record."
            ),
            "impact": (
                "Without the baseline contract, the cumulative scope "
                "of the vendor relationship is unknowable. The agency "
                "cannot answer the basic question: `how much have we "
                "spent with this vendor in total?`"
            ),
            "action": (
                "Request the original baseline contract from the "
                "responsible department to establish a complete "
                "amendment history and total expenditure."
            ),
        },
        "sole-source-expansion": {
            "summary": (
                "Sole-source justification language is combined with "
                "an amendment instrument (matched: `{sole_source_match}`)."
            ),
            "impact": (
                "Using sole-source as the justification for an "
                "amendment to an already-executed contract is the "
                "classic vendor-lock-in pattern. Each amendment "
                "compounds the justification for the next, and the "
                "cumulative award never goes through competitive "
                "bidding."
            ),
            "action": (
                "Demand the full amendment history and cumulative "
                "award value, compare against the competitive-bidding "
                "threshold, and refer to the State Controller if "
                "cumulative expenditure exceeds the threshold."
            ),
        },
        # Legacy underscore-form aliases
        "amendment_exceeds_threshold": {
            "summary": (
                "This contract has been expanded far beyond its "
                "original approved scope through amendments."
            ),
            "impact": (
                "The total cost now significantly exceeds what was "
                "originally authorized, without a new competitive "
                "bidding process."
            ),
            "action": (
                "Review whether the expanded scope requires new "
                "authorization or competitive procurement."
            ),
        },
        "sole_source_expansion": {
            "summary": (
                "A sole-source contract has grown substantially beyond "
                "its original value through amendments."
            ),
            "impact": (
                "Large amendments to sole-source contracts can "
                "circumvent competitive procurement requirements."
            ),
            "action": (
                "Determine whether the total amended value requires "
                "re-procurement under competitive bidding rules."
            ),
        },
        "amendment_without_baseline": {
            "summary": (
                "This contract was amended but no original baseline "
                "contract was found to compare against."
            ),
            "impact": (
                "Without a baseline, it is impossible to determine "
                "how much the scope has grown."
            ),
            "action": (
                "Request the original contract from the responsible "
                "department to establish the baseline."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # surveillance (layer + translator key)
    # -----------------------------------------------------------------------
    "surveillance": {
        # Canonical hyphen-form IDs from surveillance.py
        "alpr-without-sb524-policy": {
            "summary": (
                "An ALPR (automated licence-plate reader) system is "
                "referenced in this document (evidence: {alpr_evidence}) "
                "without the California SB 524 AI-transparency policy "
                "citation ({statute}, effective {effective_date}). "
                "Document date: {document_date}."
            ),
            "impact": (
                "SB 524 requires every California public agency "
                "deploying AI-assisted surveillance systems — including "
                "ALPR — to adopt a written AI-transparency policy "
                "before deployment. Operating ALPR without the SB 524 "
                "policy is a direct statutory violation and exposes "
                "the jurisdiction to an Attorney-General injunction "
                "and civil penalties."
            ),
            "action": (
                "Suspend ALPR operation pending adoption of the SB 524 "
                "policy. Request the written policy, the vendor "
                "disclosure statement, and the most recent AI-impact "
                "assessment. If none exist, refer to the Attorney "
                "General for injunctive relief."
            ),
        },
        "alpr-privacy-act-gap": {
            "summary": (
                "ALPR deployment appears without a California Civil "
                "Code § 1798.90.5 usage-and-privacy policy citation "
                "({statute})."
            ),
            "impact": (
                "Civil Code § 1798.90.5–.55 (the California ALPR "
                "Privacy Act) requires every ALPR-operating agency to "
                "adopt a usage-and-privacy policy specifying access "
                "controls, retention, and permissible-use rules. "
                "Non-compliance exposes the jurisdiction to civil "
                "liability and statutory damages of $2,500 per "
                "violation under § 1798.90.54(b)."
            ),
            "action": (
                "Request the ALPR usage-and-privacy policy, the "
                "access-control log, and the data-sharing agreements "
                "with any other agencies. Demand public posting per "
                "§ 1798.90.55 if not already published."
            ),
        },
        "bwc-without-cjis-addendum": {
            "summary": (
                "A body-worn camera program is referenced (evidence: "
                "{bwc_evidence}) without the FBI CJIS Security Policy "
                "addendum or compliance reference ({statute})."
            ),
            "impact": (
                "BWC footage is classified as Criminal Justice "
                "Information (CJI) under the FBI CJIS Security Policy. "
                "Handling CJI without a CJIS Security Addendum exposes "
                "the agency to loss of access to CJIS systems, federal "
                "compliance violations, and downstream "
                "evidence-handling defects that can sustain § 1983 "
                "Fourth-Amendment claims."
            ),
            "action": (
                "Request the CJIS Security Addendum, the BWC retention "
                "schedule, and the evidence chain-of-custody procedure. "
                "Cross-reference against the agency's Lexipol Policy "
                "429 customisation. Audit the last 90 days of video "
                "access logs."
            ),
        },
        "ai-report-writing-without-policy": {
            "summary": (
                "AI-generated police report writing (Draft One or "
                "equivalent, evidence: {ai_evidence}) is referenced "
                "without the SB 524 AI-transparency policy citation "
                "({statute})."
            ),
            "impact": (
                "SB 524 explicitly names AI-assisted report writing as "
                "a category that must be governed by a written "
                "AI-transparency policy before deployment. Using "
                "AI-generated reports in criminal prosecutions without "
                "the policy creates _Brady v. Maryland_, 373 U.S. 83 "
                "(1963) disclosure obligations the prosecution may "
                "not be equipped to meet."
            ),
            "action": (
                "Suspend AI-report-writing pending policy adoption. "
                "Request the vendor's model-card disclosure, the "
                "training-data provenance, and the error-rate "
                "measurements. Refer to the District Attorney for "
                "Brady obligations on active prosecutions."
            ),
        },
        "drone-without-ab481-report": {
            "summary": (
                "A drone / UAS program is referenced (evidence: "
                "{drone_evidence}) without the AB 481 annual-report "
                "language ({statute})."
            ),
            "impact": (
                "AB 481 (Gov Code § 7070–7075) requires every "
                "California law-enforcement agency operating "
                "military-grade equipment — including drones — to "
                "publish an annual military-equipment report and "
                "obtain annual governing-body renewal. Operating "
                "without the annual report is a statutory violation."
            ),
            "action": (
                "Request the most recent AB 481 annual report and the "
                "governing-body renewal resolution. If missing, refer "
                "to the Attorney General under Gov Code § 7075(a)'s "
                "enforcement authority."
            ),
        },
        # Dynamic: surveillance:vendor-detected:* — subtype has a
        # nested colon. Add a catch-all under the literal subtype
        # "vendor-detected" so translate_finding's colon-split picks
        # it up via the partial-match branch.
        "vendor-detected": {
            "summary": (
                "A surveillance vendor was identified in the "
                "document text by name."
            ),
            "impact": (
                "Vendor identification establishes the footprint for "
                "deeper compliance review: every named vendor has "
                "associated statutory triggers (SB 524 for ALPR, AB "
                "481 for drones, CJIS for BWC, etc.) the reviewer "
                "should check."
            ),
            "action": (
                "Look up the vendor in the ODIA vendor database and "
                "confirm all statutory triggers for that vendor's "
                "product category are satisfied in the document."
            ),
        },
        "multilayer-architecture": {
            "summary": (
                "Multiple surveillance layers (ALPR + BWC + drone, or "
                "similar) are referenced in the same document."
            ),
            "impact": (
                "Multi-layer architectures concentrate surveillance "
                "capability and create aggregation risk: data from "
                "one layer can be cross-referenced against another in "
                "ways none of the enabling resolutions anticipated. "
                "This is the _Carpenter v. United States_, 138 S. Ct. "
                "2206 (2018) mosaic-theory concern applied at the "
                "jurisdiction level."
            ),
            "action": (
                "Demand a cross-layer data-sharing disclosure and a "
                "revised surveillance-use policy that governs "
                "cross-reference queries between layers."
            ),
        },
        "facial-recognition-reference": {
            "summary": (
                "Facial-recognition technology is referenced in this "
                "document."
            ),
            "impact": (
                "Facial recognition in law-enforcement use is "
                "specifically restricted in California (AB 1215, "
                "Pen Code § 832.19) and banned outright in several "
                "jurisdictions. Deployment without an explicit "
                "authorizing resolution and strict policy controls "
                "creates direct statutory exposure."
            ),
            "action": (
                "Request the authorizing resolution, the use policy, "
                "and the accuracy-testing documentation. If the "
                "jurisdiction operates under an AB 1215 ban, demand "
                "immediate suspension."
            ),
        },
        # Legacy underscore-form aliases
        "outsourcing_detected": {
            "summary": (
                "A third-party vendor is operating surveillance "
                "systems on behalf of the city."
            ),
            "impact": (
                "Outsourced surveillance may not be subject to the "
                "same oversight as city-operated systems."
            ),
            "action": (
                "Verify that vendor contracts include privacy "
                "safeguards and data handling requirements."
            ),
        },
        "third_party_data_sharing": {
            "summary": (
                "Surveillance data appears to be shared with a "
                "third-party contractor."
            ),
            "impact": (
                "Sharing data with vendors creates privacy risks and "
                "reduces accountability."
            ),
            "action": (
                "Review data-sharing agreements to confirm appropriate "
                "safeguards are in place."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # fiscal (layer + translator key)
    # -----------------------------------------------------------------------
    "fiscal": {
        # Canonical hyphen-form IDs from fiscal.py
        "missing-provenance-hash": {
            "summary": (
                "This document is missing a SHA-256 provenance hash — "
                "the integrity trail used to confirm the record has "
                "not been altered since release."
            ),
            "impact": (
                "Without a provenance hash, document authenticity "
                "cannot be cryptographically verified. Any subsequent "
                "claim that this file matches the original release is "
                "unprovable, which undermines the record's "
                "evidentiary value in adversarial proceedings."
            ),
            "action": (
                "Request a certified copy directly from the official "
                "records system (clerk's office, Legistar, etc.) and "
                "compute a fresh SHA-256 at intake to establish the "
                "chain of custody from this point forward."
            ),
        },
        "amount-without-appropriation": {
            "summary": (
                "This document references {amount_count} fiscal "
                "amount(s) (sample: {sample_amounts}) without a "
                "corresponding appropriation reference."
            ),
            "impact": (
                "Expenditures without a traceable appropriation may "
                "violate California Constitution Art. XVI § 6 "
                "(gift-of-public-funds prohibition) and the "
                "jurisdiction's purchasing ordinance. Each unbacked "
                "amount must be traced to a prior budget line."
            ),
            "action": (
                "Cross-reference each amount against the adopted "
                "budget to identify the appropriation source. Any "
                "amount that cannot be traced requires ratification "
                "or clawback under Gov Code § 37208."
            ),
        },
        # Legacy underscore-form aliases
        "amount_without_appropriation": {
            "summary": (
                "This document references spending that has no "
                "corresponding budget authorization."
            ),
            "impact": (
                "Public funds may have been spent without the required "
                "appropriation from the governing body."
            ),
            "action": (
                "Trace the appropriation chain to verify funds were "
                "properly authorized."
            ),
        },
        "missing_provenance_hash": {
            "summary": (
                "This financial document is missing a document integrity "
                "verification hash."
            ),
            "impact": (
                "Without a provenance hash, it is difficult to confirm "
                "the document has not been altered."
            ),
            "action": (
                "Request a certified copy directly from the official "
                "records system."
            ),
        },
        "unappropriated_spending": {
            "summary": (
                "Spending in this document appears to lack a "
                "corresponding budget line item."
            ),
            "impact": (
                "Funds spent outside of an approved budget may violate "
                "appropriation law."
            ),
            "action": (
                "Cross-reference with the adopted budget to identify "
                "the appropriation source."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # constitutional (layer + translator key)
    # -----------------------------------------------------------------------
    "constitutional": {
        "broad-delegation": {
            "summary": (
                "A broad delegation of authority was detected "
                "({delegation_count} match(es); sample: `{sample}`) "
                "without clear limiting standards."
            ),
            "impact": (
                "Delegations without an intelligible principle violate "
                "the non-delegation doctrine (_Mistretta v. United "
                "States_, 488 U.S. 361 (1989)) and risk judicial "
                "invalidation on separation-of-powers grounds. At the "
                "local level, unlimited delegations concentrate "
                "police power in an unelected staff member."
            ),
            "action": (
                "Recommend the governing body amend the delegation "
                "to include specific dollar limits, time limits, and "
                "scope constraints before any authority is exercised."
            ),
        },
        # Legacy underscore-form aliases
        "broad_delegation": {
            "summary": (
                "This resolution grants broad authority without clear "
                "limits on scope, time, or spending."
            ),
            "impact": (
                "Unlimited delegation of authority may violate "
                "separation of powers principles."
            ),
            "action": (
                "Recommend the governing body add specific dollar "
                "limits, time limits, and scope constraints."
            ),
        },
        "unlimited_authority": {
            "summary": (
                "An official was granted authority to act with no "
                "stated limits."
            ),
            "impact": (
                "Unconstrained delegations can lead to actions that "
                "were not contemplated by the governing body."
            ),
            "action": (
                "Request that the delegation be amended to include "
                "clear scope, duration, and spending limits."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # admin (layer: administrative) → administrative_integrity (translator key)
    # -----------------------------------------------------------------------
    "administrative_integrity": {
        # Canonical hyphen-form IDs from administrative_integrity.py
        "missing-final-action": {
            "summary": (
                "Document text indicates approval (signals: "
                "{approval_signals_found}) but the `final_action` field "
                "is blank (value: `{final_action_value}`)."
            ),
            "impact": (
                "A missing final-action record means there is no "
                "authoritative vote tally on a matter the record "
                "otherwise treats as approved. The Brown Act "
                "(Gov Code § 54953) requires a recorded vote — "
                "absence of that record is a direct statutory defect."
            ),
            "action": (
                "Request the complete legislative record — vote tally, "
                "final motion, and clerk's certification — from the "
                "city clerk's office. Compare against the approved "
                "minutes of the same meeting."
            ),
        },
        "blank-required-fields": {
            "summary": (
                "{field_count} required metadata field(s) are blank in "
                "this official document: {blank_fields}."
            ),
            "impact": (
                "Blank required fields indicate either a clerical "
                "defect (fixable) or deliberate omission (not "
                "fixable without explanation). Incomplete official "
                "records undermine chain-of-custody and may void the "
                "document's recorded-instrument status."
            ),
            "action": (
                "Request a corrected record from the responsible "
                "department. If a corrected version cannot be "
                "produced, demand the clerk's explanation for the "
                "omission."
            ),
        },
        "retroactive-authorization": {
            "summary": (
                "Retroactive or back-dated authorization language was "
                "detected in this document (matched: `{matched_phrase}` "
                "at position {position})."
            ),
            "impact": (
                "Retroactive authorization is the formal admission "
                "that an action was taken without advance approval. "
                "Depending on context, it may constitute a Gov Code "
                "§ 1090 conflict-of-interest violation, an "
                "appropriation-law violation, or a Brown Act violation "
                "under Gov Code § 54960.1."
            ),
            "action": (
                "Investigate whether the original action complied "
                "with procurement, authorization, and Brown Act rules. "
                "Refer to the District Attorney if the retroactive "
                "language ratifies a prohibited action."
            ),
        },
        "potential-misfiling": {
            "summary": (
                "Misfiling or document-placement error indicators "
                "were found in this record: {misfiling_indicators}."
            ),
            "impact": (
                "Misfiling indicators suggest the document was "
                "placed in the wrong agenda section, docket, or "
                "records classification. Misfiled records are easy "
                "to miss during due-diligence review and may indicate "
                "an attempt to suppress public scrutiny."
            ),
            "action": (
                "Request re-classification and re-filing in the "
                "correct section, and audit the clerk's filing "
                "procedure for systemic placement errors."
            ),
        },
        # Legacy underscore-form aliases
        "missing_final_action": {
            "summary": (
                "This legislative record is missing its final action "
                "or vote record."
            ),
            "impact": (
                "Without a recorded vote, it's unclear whether this "
                "item was properly approved."
            ),
            "action": (
                "Request the complete legislative record including "
                "the final action from the clerk's office."
            ),
        },
        "retroactive_authorization": {
            "summary": (
                "This document authorizes or ratifies an action that "
                "already took place."
            ),
            "impact": (
                "Retroactive authorizations suggest the action was "
                "taken without proper advance approval."
            ),
            "action": (
                "Investigate whether the original action complied "
                "with procurement or authorization rules."
            ),
        },
        "blank_required_field": {
            "summary": (
                "A required field in this official document was left "
                "blank."
            ),
            "impact": (
                "Incomplete official records undermine accountability "
                "and may indicate documentation errors."
            ),
            "action": (
                "Request a corrected record from the responsible "
                "department."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # cross_reference (layer + translator key)
    # -----------------------------------------------------------------------
    "cross_reference": {
        "jurisdiction_boundary": {
            "summary": (
                "This document references both federal and state law "
                "in a way that suggests jurisdictional confusion."
            ),
            "impact": (
                "Mixing federal and state authority without clarity "
                "can create enforcement gaps."
            ),
            "action": (
                "Refer to legal counsel for clarification of "
                "applicable jurisdiction."
            ),
        },
        "conflicting_citations": {
            "summary": (
                "This document cites federal and state statutes that "
                "may conflict with each other."
            ),
            "impact": (
                "Conflicting legal citations can make the document's "
                "requirements ambiguous or unenforceable."
            ),
            "action": (
                "Have an attorney review which legal authority governs "
                "and clarify the document accordingly."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # temporal_pattern (layer + translator key)
    # -----------------------------------------------------------------------
    "temporal_pattern": {
        "contract_evolution": {
            "summary": (
                "This contract has evolved significantly over time "
                "through a series of amendments."
            ),
            "impact": (
                "Incremental amendments can allow a contract to grow "
                "far beyond its original intent without proper review."
            ),
            "action": (
                "Review the full amendment history and determine "
                "whether re-procurement is warranted."
            ),
        },
        "vendor_lock_in": {
            "summary": (
                "This vendor has held a contract for an unusually "
                "long period with repeated renewals."
            ),
            "impact": (
                "Long-term vendor relationships without re-competition "
                "may limit cost savings and introduce bias."
            ),
            "action": (
                "Evaluate whether the contract should go through a "
                "new competitive bidding process."
            ),
        },
    },
    # -----------------------------------------------------------------------
    # ingestion (new in v2.7.3 — fail-loud extraction finding from D3)
    # -----------------------------------------------------------------------
    "ingestion": {
        "extraction-failure": {
            "summary": (
                "Text extraction from this file returned less than the "
                "minimum expected length ({extracted_chars} chars from "
                "a {file_bytes}-byte {file_format} file). Detectors "
                "had almost nothing to work with."
            ),
            "impact": (
                "Silent extraction failures are the most dangerous "
                "class of pipeline defect: the audit report looks "
                "complete but the underlying detectors never saw the "
                "document's actual text. Every absent finding is a "
                "false negative."
            ),
            "action": (
                "Re-ingest the file with OCR forced on, or obtain a "
                "machine-readable version from the issuing office. "
                "Until resolved, treat this document as unanalysed."
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def translate_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Add plain-language fields to a finding dict.

    Adds these keys to the returned copy:
      - ``plain_summary``       — one-sentence MAS-style restatement.
      - ``plain_impact``        — the legal / governance consequence.
      - ``plain_action``        — the recommended next step.
      - ``plain_evidence_echo`` — short verbatim recap of the structured
        ``details`` dict so the plain-language narrative always cites
        its own raw source (matches how MAS reports anchor paragraphs
        to evidence inline).

    Original finding dict is not mutated.
    """
    result = dict(finding)

    finding_id: str = finding.get("id", "") or ""
    layer: str = finding.get("layer", "") or ""
    details: dict[str, Any] = finding.get("details", {}) or {}

    if ":" in finding_id:
        parts = finding_id.split(":", 1)
        detector_type = parts[0].strip()
        subtype = parts[1].strip()
    else:
        detector_type = layer or finding_id
        subtype = ""

    detector_key = _normalize_detector_key(detector_type)
    detector_map = TRANSLATIONS.get(detector_key, {})
    translation = _resolve_subtype(detector_map, subtype)

    if translation:
        result["plain_summary"] = _format_safe(translation["summary"], details)
        result["plain_impact"] = _format_safe(translation["impact"], details)
        result["plain_action"] = _format_safe(translation["action"], details)
    else:
        severity = finding.get("severity", "unknown")
        result["plain_summary"] = (
            f"An anomaly was detected by the {detector_type} detector "
            f"with {severity} severity."
        )
        result["plain_impact"] = (
            "This finding requires professional review to assess its "
            "significance."
        )
        result["plain_action"] = (
            "Consult the full technical finding details and consider "
            "engaging qualified counsel."
        )

    result["plain_evidence_echo"] = _evidence_echo(details)
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
    "grant": "grant_compliance",
    "grants": "grant_compliance",
    "cross_reference": "cross_reference",
    "temporal": "temporal_pattern",
    "contract_evolution": "temporal_pattern",
}


def _normalize_detector_key(key: str) -> str:
    return _DETECTOR_KEY_ALIASES.get(key, key)


def _resolve_subtype(
    detector_map: dict[str, dict[str, str]],
    subtype: str,
) -> dict[str, str]:
    """Try exact / hyphen↔underscore / nested-colon / prefix matches."""
    if not detector_map:
        return {}

    # 1. Exact match.
    if subtype in detector_map:
        return detector_map[subtype]

    # 2. Hyphen ↔ underscore normalisation — detectors emit hyphens,
    #    legacy callers used underscores; accept either.
    dashed = subtype.replace("_", "-")
    if dashed in detector_map:
        return detector_map[dashed]
    scored = subtype.replace("-", "_")
    if scored in detector_map:
        return detector_map[scored]

    # 3. Nested-colon subtypes (e.g. ``vendor-detected:flock-safety``)
    #    — match the prefix before the nested colon.
    if ":" in subtype:
        head = subtype.split(":", 1)[0]
        if head in detector_map:
            return detector_map[head]
        head_dashed = head.replace("_", "-")
        if head_dashed in detector_map:
            return detector_map[head_dashed]

    # 4. Prefix fallback — preserves the pre-v2.7.3 partial-match behaviour.
    for key, val in detector_map.items():
        if subtype and (subtype.startswith(key) or key.startswith(subtype)):
            return val

    return {}


class _SafeFormatDict(dict):
    """dict subclass that returns `{missing-key}` literal for absent keys.

    Used with ``str.format_map`` so a narrative template that references
    a detail field the detector didn't emit still renders readably
    instead of raising ``KeyError``. Values are also coerced to ``str``
    so nested lists / dicts render cleanly.
    """

    def __missing__(self, key: str) -> str:
        return "not recorded"


def _format_safe(template: str, details: dict[str, Any]) -> str:
    """Apply ``template.format_map(details)``, degrading gracefully.

    Non-trivial cases:
      * Missing keys → the ``_SafeFormatDict`` returns ``"not recorded"``.
      * ``None`` values → rendered as the literal ``"none"`` so the
        narrative doesn't say ``document_date: None``.
      * ``list`` values → joined with ``", "`` when short enough.
      * Everything else → ``str(value)``.
    """
    if not template:
        return ""
    rendered_details: dict[str, Any] = {}
    for k, v in details.items():
        if v is None:
            rendered_details[k] = "none"
        elif isinstance(v, list):
            rendered_details[k] = ", ".join(str(x) for x in v) or "none"
        else:
            rendered_details[k] = str(v)
    try:
        return template.format_map(_SafeFormatDict(rendered_details))
    except (IndexError, ValueError):
        # ``format_map`` can still raise on malformed templates — bail
        # to the un-interpolated version rather than losing the text.
        return template


def _evidence_echo(details: dict[str, Any]) -> str:
    """Render a one-line recap of the raw details dict.

    Order-preserving (Python dict order) so the echo is deterministic
    from a given detector-run. Caps each value at 80 chars to keep the
    rendered packet readable.
    """
    if not details:
        return "Evidence anchors: (no structured details recorded)"
    parts: list[str] = []
    for key, value in details.items():
        if isinstance(value, list):
            rendered = ", ".join(str(v) for v in value) or "none"
        elif value is None:
            rendered = "none"
        else:
            rendered = str(value)
        if len(rendered) > 80:
            rendered = rendered[:77] + "..."
        parts.append(f"{key}={rendered}")
    return "Evidence anchors: " + "; ".join(parts)
