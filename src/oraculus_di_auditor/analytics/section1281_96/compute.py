"""Statistical computation functions for the CCP § 1281.96 arbitration pipeline.

All functions are pure (no DB access, no side effects).  Feed NormalizedCase
lists from the retrieval pipeline or from DB rows mapped through NormalizedCase.

Functions:
    wilson_ci                           -- Wilson score confidence interval
    prevailing_rate_stratified          -- consumer win rate by rep + tier
    arbitrator_repeat_player_concentration
    corporate_repeat_player_concentration
    contra_corpus_entity_slice          -- slice cases for CONTRA corpus entities
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from .normalize import NormalizedCase

# ---------------------------------------------------------------------------
# Wilson confidence interval
# ---------------------------------------------------------------------------


def wilson_ci(n: int, N: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion.

    Arguments:
        n  -- number of successes
        N  -- total number of trials
        z  -- z-score (default 1.96 = two-tailed 95% CI)

    Returns:
        (lower, upper) as floats clamped to [0.0, 1.0].
        Returns (0.0, 0.0) when N == 0.

    Formula avoids scipy; the derivation is the standard Wilson (1927) result.
    Reference: Wilson, E.B. (1927). "Probable inference, the law of succession,
    and statistical inference." J. Amer. Stat. Assoc. 22(158): 209-212.
    """
    if N == 0:
        return 0.0, 0.0
    p = n / N
    z2_over_N = z**2 / N
    center = (p + z2_over_N / 2.0) / (1.0 + z2_over_N)
    spread = (
        z * math.sqrt(p * (1.0 - p) / N + z2_over_N / (4.0 * N)) / (1.0 + z2_over_N)
    )
    return max(0.0, center - spread), min(1.0, center + spread)


# ---------------------------------------------------------------------------
# Stratified prevailing rate
# ---------------------------------------------------------------------------


def prevailing_rate_stratified(cases: list[NormalizedCase]) -> dict:
    """Consumer prevailing rate stratified by representation status and claim tier.

    Denominates exclusively on disposition_type == "AWARD_AFTER_HEARING".
    Settlements, withdrawals, and dismissals are excluded from the denominator
    because the consumer choice to settle is not an arbitrator-determined outcome.

    Returns a nested dict:
        {
          consumer_represented_value -> {
            claim_amount_tier_value -> {
              "n_cases": int,
              "n_consumer_wins": int,
              "rate": float,           -- n_consumer_wins / n_cases
              "ci_lower": float,       -- Wilson 95% CI lower
              "ci_upper": float,       -- Wilson 95% CI upper
            }
          }
        }

    Tier keys may be None (rendered as "UNKNOWN") for cases missing claim amounts.
    """
    award_cases = [c for c in cases if c.disposition_type == "AWARD_AFTER_HEARING"]

    cells: dict[tuple[str, str], list[NormalizedCase]] = defaultdict(list)
    for case in award_cases:
        key = (case.consumer_represented, case.claim_amount_tier or "UNKNOWN")
        cells[key].append(case)

    result: dict[str, dict] = {}
    for (rep, tier), cell_cases in sorted(cells.items()):
        n = len(cell_cases)
        wins = sum(1 for c in cell_cases if c.prevailing_party == "CONSUMER")
        lo, hi = wilson_ci(wins, n)
        result.setdefault(rep, {})[tier] = {
            "n_cases": n,
            "n_consumer_wins": wins,
            "rate": round(wins / n, 4) if n else 0.0,
            "ci_lower": round(lo, 4),
            "ci_upper": round(hi, 4),
        }

    return result


# ---------------------------------------------------------------------------
# Arbitrator repeat-player concentration
# ---------------------------------------------------------------------------


def arbitrator_repeat_player_concentration(cases: list[NormalizedCase]) -> dict:
    """Arbitrator repeat-player effect: case-volume concentration by arbitrator.

    Computes what fraction of total arbitration case-volume is concentrated
    in the top 5%, 10%, and 25% of arbitrators by case count.  High
    concentration indicates a small pool of repeat arbitrators who develop
    ongoing relationships with the corporate repeat player.

    Returns:
        total_case_assignments: int   -- sum of all arbitrator-case pairings
        unique_arbitrators: int
        top_5pct_arbitrators: int     -- # arbitrators needed to reach 5% of volume
        top_5pct_case_share: float
        top_10pct_arbitrators: int
        top_10pct_case_share: float
        top_25pct_arbitrators: int
        top_25pct_case_share: float
        top_10_by_volume: list[dict]  -- name, case_count, share for top 10
    """
    counts: Counter[str] = Counter()
    for case in cases:
        for name in case.arbitrator_names:
            if name and name.strip():
                counts[name.strip()] += 1

    total = sum(counts.values())
    if total == 0:
        return {
            "total_case_assignments": 0,
            "unique_arbitrators": 0,
            "top_5pct_arbitrators": 0,
            "top_5pct_case_share": 0.0,
            "top_10pct_arbitrators": 0,
            "top_10pct_case_share": 0.0,
            "top_25pct_arbitrators": 0,
            "top_25pct_case_share": 0.0,
            "top_10_by_volume": [],
        }

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

    def _threshold(pct: float) -> tuple[int, float]:
        target = total * pct
        cumulative = 0
        for i, (_, n) in enumerate(ranked):
            cumulative += n
            if cumulative >= target:
                return i + 1, cumulative / total
        return len(ranked), 1.0

    t5_n, t5_share = _threshold(0.05)
    t10_n, t10_share = _threshold(0.10)
    t25_n, t25_share = _threshold(0.25)

    top10 = [
        {
            "name": name,
            "case_count": count,
            "share": round(count / total, 4),
        }
        for name, count in ranked[:10]
    ]

    return {
        "total_case_assignments": total,
        "unique_arbitrators": len(counts),
        "top_5pct_arbitrators": t5_n,
        "top_5pct_case_share": round(t5_share, 4),
        "top_10pct_arbitrators": t10_n,
        "top_10pct_case_share": round(t10_share, 4),
        "top_25pct_arbitrators": t25_n,
        "top_25pct_case_share": round(t25_share, 4),
        "top_10_by_volume": top10,
    }


# ---------------------------------------------------------------------------
# Corporate repeat-player concentration
# ---------------------------------------------------------------------------


def corporate_repeat_player_concentration(cases: list[NormalizedCase]) -> dict:
    """Non-consumer party (company) case-volume concentration and outcome data.

    Returns:
        total_cases: int
        unique_companies: int
        herfindahl_index: float  -- HHI on case-volume shares (0-10000)
        top_10_by_volume: list[dict] with keys:
            entity_key, name, case_count, share,
            award_cases, consumer_win_rate (None if no AWARD_AFTER_HEARING)
    """
    company_cases: dict[str, list[NormalizedCase]] = defaultdict(list)
    for case in cases:
        key = (
            case.non_consumer_party_entity_id
            or case.non_consumer_party_name
            or "UNKNOWN"
        )
        company_cases[key].append(case)

    total = len(cases)
    if total == 0:
        return {
            "total_cases": 0,
            "unique_companies": 0,
            "herfindahl_index": 0.0,
            "top_10_by_volume": [],
        }

    hhi = sum((len(v) / total * 100) ** 2 for v in company_cases.values())
    ranked = sorted(company_cases.items(), key=lambda kv: len(kv[1]), reverse=True)

    top10 = []
    for entity_key, co_cases in ranked[:10]:
        award_cases = [
            c for c in co_cases if c.disposition_type == "AWARD_AFTER_HEARING"
        ]
        consumer_wins = sum(1 for c in award_cases if c.prevailing_party == "CONSUMER")
        n_award = len(award_cases)
        win_rate = consumer_wins / n_award if n_award else None
        display_name = co_cases[0].non_consumer_party_name if co_cases else entity_key
        top10.append(
            {
                "entity_key": entity_key,
                "name": display_name,
                "case_count": len(co_cases),
                "share": round(len(co_cases) / total, 4),
                "award_cases": n_award,
                "consumer_win_rate": (
                    round(win_rate, 4) if win_rate is not None else None
                ),
            }
        )

    return {
        "total_cases": total,
        "unique_companies": len(company_cases),
        "herfindahl_index": round(hhi, 2),
        "top_10_by_volume": top10,
    }


# ---------------------------------------------------------------------------
# CONTRA corpus entity slice
# ---------------------------------------------------------------------------


def contra_corpus_entity_slice(
    cases: list[NormalizedCase],
    entity_ids: set[str],
) -> dict[str, list[NormalizedCase]]:
    """Return arbitration cases grouped by entity_id for CONTRA corpus entities.

    entity_ids -- set of entity_ids where CommercialEntity.in_contra_corpus == True.
    Cases where non_consumer_party_entity_id is None or not in entity_ids are excluded.

    This creates the empirical link between C.O.N.T.R.A. detector findings
    (contract terms scored by CASI) and arbitration outcome data for the same
    entity: high CASI + low consumer win rate = strong adhesion contract thesis.
    """
    result: dict[str, list[NormalizedCase]] = defaultdict(list)
    for case in cases:
        eid = case.non_consumer_party_entity_id
        if eid and eid in entity_ids:
            result[eid].append(case)
    return dict(result)
