from __future__ import annotations

from dataclasses import dataclass

from .models import CandidateResult


@dataclass
class PromotionThresholds:
    min_quality: float = 0.80
    max_regressions: int = 0
    max_cost_usd: float = 15.0
    max_latency_ms: int = 5000
    max_risk: float = 0.20


def eligible(candidate: CandidateResult, t: PromotionThresholds) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if candidate.quality < t.min_quality:
        reasons.append("quality below threshold")
    if candidate.regressions > t.max_regressions:
        reasons.append("regressions above threshold")
    if candidate.cost_usd > t.max_cost_usd:
        reasons.append("cost above threshold")
    if candidate.latency_ms > t.max_latency_ms:
        reasons.append("latency above threshold")
    if candidate.risk > t.max_risk:
        reasons.append("risk above threshold")
    if not candidate.safe or not candidate.smoke_passed:
        reasons.append("failed safety or smoke gating")
    return len(reasons) == 0, reasons
