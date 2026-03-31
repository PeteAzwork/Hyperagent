from __future__ import annotations

from pathlib import Path
import csv

from .models import GenerationRecord


def write_timeline(generations: list[GenerationRecord], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["gen_id", "created_at", "candidate_count"])
        for gen in generations:
            writer.writerow([gen.gen_id, gen.created_at, len(gen.candidates)])
    return output


def write_funnel(generations: list[GenerationRecord], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    total = sum(len(g.candidates) for g in generations)
    safe = sum(1 for g in generations for c in g.candidates if c.safe)
    smoke = sum(1 for g in generations for c in g.candidates if c.smoke_passed)
    promoted_eligible = sum(
        1
        for g in generations
        for c in g.candidates
        if c.safe and c.smoke_passed and c.regressions == 0
    )
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["stage", "count"])
        writer.writerow(["total", total])
        writer.writerow(["safe", safe])
        writer.writerow(["smoke_passed", smoke])
        writer.writerow(["eligible_proxy", promoted_eligible])
    return output


def write_cost(generations: list[GenerationRecord], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["gen_id", "candidate_id", "cost_usd"])
        for gen in generations:
            for c in gen.candidates:
                writer.writerow([gen.gen_id, c.candidate_id, f"{c.cost_usd:.4f}"])
    return output
