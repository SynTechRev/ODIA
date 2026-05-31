"""odia_legal.citations — multi-code legal citation parsing and normalization.

parse_citations(text) → list[Citation]   # all types
parse_usc(text)       → list[Citation]   # 34 U.S.C. § 10152
parse_cfr(text)       → list[Citation]   # 2 C.F.R. § 200.303
parse_cal_code(text)  → list[Citation]   # Gov. Code § 6254(f)
parse_cal_case(text)  → list[Citation]   # ACLU v. Superior Court (2011) 202 Cal.App.4th 55
"""

from odia_legal.citations.parser import (
    Citation,
    parse_cal_case,
    parse_cal_code,
    parse_cfr,
    parse_citations,
    parse_usc,
)

__all__ = [
    "Citation",
    "parse_citations",
    "parse_usc",
    "parse_cfr",
    "parse_cal_code",
    "parse_cal_case",
]
