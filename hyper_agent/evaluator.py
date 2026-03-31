from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
import sys
import time


@dataclass
class SmokeTask:
    task_id: str
    prompt: str


def run_fresh_session(task: SmokeTask, artifact_dir: Path, timeout_sec: int = 10) -> dict:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()
    proc = subprocess.run(
        [sys.executable, "-c", "print('fresh-session-ok')"],
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    elapsed = int((time.time() - start) * 1000)

    result = {
        "task_id": task.task_id,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "latency_ms": elapsed,
    }
    (artifact_dir / f"{task.task_id}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result
