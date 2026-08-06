"""Controlled vocabulary of doctrinal authority citations for C.O.N.T.R.A.

Every Finding.doctrinal_anchor must be drawn from this module. Using
constants rather than free-form strings makes authority tracking auditable
at the code level and enables downstream reports (T.C.A.M.S., C.C.C.E.A.)
to aggregate findings by controlling authority.

Adding a new authority: add the constant here AND add a corresponding entry
to the Doctrinal Integration Memorandum authority map at the next version
increment (Framework Section 10, version discipline).

Source: C.O.N.T.R.A. Framework V1.0, Handoff Specification V1.0 Section 3.3
"""

# California Unconscionability Doctrine
ARMENDARIZ = (
    "Armendariz v. Foundation Health Psychcare Services, Inc. (2000) 24 Cal.4th 83"
)
OTO_KHO = "OTO, L.L.C. v. Kho (2019) 8 Cal.5th 111"
SANCHEZ_VALENCIA = "Sanchez v. Valencia Holding Co. (2015) 61 Cal.4th 899"
SONIC_CALABASAS = "Sonic-Calabasas A, Inc. v. Moreno (2013) 57 Cal.4th 1109"
ADOLPH_UBER = "Adolph v. Uber Technologies, Inc. (2023) 14 Cal.5th 1104"
GRAFTON_PARTNERS = "Grafton Partners L.P. v. Superior Court (2005) 36 Cal.4th 944"
DOUGLAS_USDC = "Douglas v. U.S. District Court (9th Cir. 2007) 495 F.3d 1062"

# Federal Arbitration Act Ceiling
CONCEPCION = "AT&T Mobility LLC v. Concepcion (2011) 563 U.S. 333"
ITALIAN_COLORS = "American Express Co. v. Italian Colors Restaurant (2013) 570 U.S. 228"
EPIC_SYSTEMS = "Epic Systems Corp. v. Lewis (2018) 584 U.S. 497"
VIKING_RIVER = "Viking River Cruises, Inc. v. Moriana (2022) 596 U.S. 639"
COINBASE_BIELSKI = "Coinbase, Inc. v. Bielski (2023) 599 U.S. 736"
HENRY_SCHEIN = "Henry Schein, Inc. v. Archer & White Sales, Inc. (2019) 586 U.S. 63"

# Empirical Arbitration Sources
CFPB_2015 = "CFPB Section 1028 Arbitration Study (March 2015)"
COLVIN_2011 = "Colvin, 8 J. Empirical Legal Studies 1 (2011)"

# California Privacy Statutes — CCPA/CPRA
CCPA_140 = "Cal. Civ. Code section 1798.140"
CCPA_100 = "Cal. Civ. Code section 1798.100"
CCPA_105 = "Cal. Civ. Code section 1798.105"
CCPA_106 = "Cal. Civ. Code section 1798.106"
CCPA_110 = "Cal. Civ. Code section 1798.110"
CCPA_120 = "Cal. Civ. Code section 1798.120"
CCPA_121 = "Cal. Civ. Code section 1798.121"
CCPA_130 = "Cal. Civ. Code section 1798.130"
CCPA_135 = "Cal. Civ. Code section 1798.135"
DELETE_ACT = "Cal. Civ. Code section 1798.99.80 et seq."

# California Arbitration Fee and Timing Statutes (SB 707)
CCP_1281_96 = "Cal. Code Civ. Proc. section 1281.96"
CCP_1281_97 = "Cal. Code Civ. Proc. section 1281.97"
CCP_1281_98 = "Cal. Code Civ. Proc. section 1281.98"

# California Statutes of Limitations
CCP_337 = "Cal. Code Civ. Proc. section 337"
CCP_338 = "Cal. Code Civ. Proc. section 338"

# CCPA Non-Waivability
CCPA_192 = "Cal. Civ. Code section 1798.192"

# California Silenced No More Act
CCP_1001 = "Cal. Code Civ. Proc. section 1001"

# California Punitive Damages
CIVCODE_3294 = "Cal. Civ. Code section 3294"

# FTC Enforcement — Dark Pattern / Consent Definition
RING_ORDER = (
    "United States v. Ring, LLC, No. 1:23-cv-01549 (D.D.C. entered June 16, 2023)"
)

# Academic Doctrinal Sources
YEUNG_2019 = "Council of Europe MSI-AUT DGI(2019)05 (Yeung, Rapporteur)"
EU_EXPERT_2019 = "EU Expert Group on Liability and New Technologies (2019)"
SCHERER_2016 = "Scherer, 29 Harv. J.L. & Tech. 353 (Spring 2016)"
JEUTNER_2021 = "Jeutner, 1(1) Morals & Machines 52 (2021)"
VILJOEN_2021 = "Viljoen, 131 Yale L.J. 573 (2021)"


# Lookup set — used to validate anchors at test time
ALL_ANCHORS: frozenset[str] = frozenset(
    {
        ARMENDARIZ,
        OTO_KHO,
        SANCHEZ_VALENCIA,
        SONIC_CALABASAS,
        ADOLPH_UBER,
        GRAFTON_PARTNERS,
        DOUGLAS_USDC,
        CONCEPCION,
        ITALIAN_COLORS,
        EPIC_SYSTEMS,
        VIKING_RIVER,
        COINBASE_BIELSKI,
        HENRY_SCHEIN,
        CFPB_2015,
        COLVIN_2011,
        CCPA_140,
        CCPA_100,
        CCPA_105,
        CCPA_106,
        CCPA_110,
        CCPA_120,
        CCPA_121,
        CCPA_130,
        CCPA_135,
        DELETE_ACT,
        CCP_1281_96,
        CCP_1281_97,
        CCP_1281_98,
        CCP_337,
        CCP_338,
        CCP_1001,
        CCPA_192,
        CIVCODE_3294,
        RING_ORDER,
        YEUNG_2019,
        EU_EXPERT_2019,
        SCHERER_2016,
        JEUTNER_2021,
        VILJOEN_2021,
    }
)
