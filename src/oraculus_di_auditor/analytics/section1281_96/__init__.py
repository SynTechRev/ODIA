"""CCP § 1281.96 consumer arbitration data pipeline.

California Code of Civil Procedure § 1281.96 requires AAA, JAMS, and other
providers to publish quarterly consumer arbitration statistics.  This pipeline
retrieves, normalizes, and analyzes that data to produce empirically grounded
prevalence rates, repeat-player concentration scores, and CONTRA corpus slices.

Public surface:
    NormalizedCase          — canonical case dataclass (normalize.py)
    AAARetriever            — AAA quarterly scraper (retrieval_aaa.py)
    JAMSRetriever           — JAMS quarterly scraper (retrieval_jams.py)
    SmallerProviderRetriever — ADR Services / Judicate West / FedArb / NAM
    wilson_ci               — Wilson score confidence interval (compute.py)
    prevailing_rate_stratified
    arbitrator_repeat_player_concentration
    corporate_repeat_player_concentration
    contra_corpus_entity_slice
    build_summary_report    — python-docx report generator (report.py)
"""

from .compute import (
    arbitrator_repeat_player_concentration,
    contra_corpus_entity_slice,
    corporate_repeat_player_concentration,
    prevailing_rate_stratified,
    wilson_ci,
)
from .normalize import NormalizedCase
from .report import build_summary_report
from .retrieval_aaa import AAARetriever
from .retrieval_jams import JAMSRetriever
from .retrieval_smaller import SmallerProviderRetriever

__all__ = [
    "NormalizedCase",
    "AAARetriever",
    "JAMSRetriever",
    "SmallerProviderRetriever",
    "wilson_ci",
    "prevailing_rate_stratified",
    "arbitrator_repeat_player_concentration",
    "corporate_repeat_player_concentration",
    "contra_corpus_entity_slice",
    "build_summary_report",
]
