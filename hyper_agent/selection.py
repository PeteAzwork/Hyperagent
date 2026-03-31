from __future__ import annotations

from .models import CandidateResult


def dominates(a: CandidateResult, b: CandidateResult) -> bool:
    better_or_equal = (
        a.quality >= b.quality
        and a.regressions <= b.regressions
        and a.cost_usd <= b.cost_usd
        and a.latency_ms <= b.latency_ms
        and a.risk <= b.risk
    )
    strictly_better = (
        a.quality > b.quality
        or a.regressions < b.regressions
        or a.cost_usd < b.cost_usd
        or a.latency_ms < b.latency_ms
        or a.risk < b.risk
    )
    return better_or_equal and strictly_better


def safe_filter(candidates: list[CandidateResult]) -> list[CandidateResult]:
    return [c for c in candidates if c.safe and c.smoke_passed]


def pareto_frontier(candidates: list[CandidateResult]) -> list[CandidateResult]:
    frontier: list[CandidateResult] = []
    for c in candidates:
        if any(dominates(other, c) for other in candidates if other is not c):
            continue
        frontier.append(c)
    return frontier
