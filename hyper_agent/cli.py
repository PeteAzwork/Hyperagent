from __future__ import annotations

from pathlib import Path
import argparse

from .budget import BudgetAccountant, BudgetCaps
from .dashboard import write_cost, write_funnel, write_timeline
from .evaluator import SmokeTask, run_fresh_session
from .manifest import validate_package
from .models import CandidateResult, GenerationRecord
from .promotion import PromotionThresholds, eligible
from .rollback import RollbackController, RollbackState
from .selection import pareto_frontier, safe_filter


ROOT = Path(__file__).resolve().parent.parent


def run_demo() -> None:
    package_root = ROOT / "subagent_package"
    ok, errors = validate_package(package_root)
    print(f"package_valid={ok}")
    if errors:
        for e in errors:
            print(f" - {e}")

    task = SmokeTask(task_id="smoke-001", prompt="noop")
    run_fresh_session(task, ROOT / "archive" / "smoke")

    candidates = [
        CandidateResult("cand-a", 0.85, 4.2, 1200, 0, 0.10, 0.2, True, True),
        CandidateResult("cand-b", 0.90, 8.3, 2400, 1, 0.15, 0.6, True, True),
        CandidateResult("cand-c", 0.81, 2.3, 900, 0, 0.09, 0.1, True, True),
    ]

    safe = safe_filter(candidates)
    frontier = pareto_frontier(safe)

    gen = GenerationRecord(
        gen_id="gen-001",
        parent_gen_id=None,
        benchmark_version="bench_v001",
        candidates=frontier,
        notes="demo generation",
    )
    gen_path = gen.write(ROOT / "archive" / "generations")
    print(f"wrote generation {gen_path}")

    accountant = BudgetAccountant(BudgetCaps(per_candidate_usd=10.0, per_run_usd=20.0))
    per_candidate_totals = {c.candidate_id: 0.0 for c in frontier}
    for c in frontier:
        ok_budget, reason = accountant.charge_candidate(c.candidate_id, c.cost_usd, per_candidate_totals[c.candidate_id])
        per_candidate_totals[c.candidate_id] += c.cost_usd
        print(f"budget {c.candidate_id}: {ok_budget} ({reason})")

    threshold = PromotionThresholds()
    for c in frontier:
        ok_promo, reasons = eligible(c, threshold)
        print(f"promotion {c.candidate_id}: {ok_promo} reasons={reasons}")

    rollback = RollbackController(RollbackState(current_gen_id="gen-001", previous_gen_id="gen-000"))
    rollback.quarantine("gen-001")
    rollback.rollback("gen-000")

    write_timeline([gen], ROOT / "dashboards" / "timeline.csv")
    write_funnel([gen], ROOT / "dashboards" / "funnel.csv")
    write_cost([gen], ROOT / "dashboards" / "cost.csv")
    print("dashboards written")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hyper-agent scaffold CLI")
    parser.add_argument("command", choices=["demo", "validate-package"])
    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "validate-package":
        ok, errors = validate_package(ROOT / "subagent_package")
        print(f"package_valid={ok}")
        if errors:
            for e in errors:
                print(e)


if __name__ == "__main__":
    main()
