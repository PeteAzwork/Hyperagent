from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetCaps:
    per_candidate_usd: float
    per_run_usd: float


class BudgetAccountant:
    def __init__(self, caps: BudgetCaps) -> None:
        self.caps = caps
        self.run_spend = 0.0

    def charge_candidate(self, candidate_id: str, amount_usd: float, candidate_total: float) -> tuple[bool, str]:
        if candidate_total + amount_usd > self.caps.per_candidate_usd:
            return False, f"candidate cap exceeded for {candidate_id}"
        if self.run_spend + amount_usd > self.caps.per_run_usd:
            return False, "run cap exceeded"
        self.run_spend += amount_usd
        return True, "ok"
