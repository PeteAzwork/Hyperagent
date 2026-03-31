from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CandidateResult:
    candidate_id: str
    quality: float
    cost_usd: float
    latency_ms: int
    regressions: int
    risk: float
    novelty: float
    safe: bool
    smoke_passed: bool


@dataclass
class GenerationRecord:
    gen_id: str
    parent_gen_id: str | None
    benchmark_version: str
    created_at: str = field(default_factory=now_iso)
    candidates: list[CandidateResult] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        base = asdict(self)
        base["candidates"] = [asdict(c) for c in self.candidates]
        return base

    def write(self, archive_dir: Path) -> Path:
        archive_dir.mkdir(parents=True, exist_ok=True)
        out = archive_dir / f"{self.gen_id}.json"
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out
