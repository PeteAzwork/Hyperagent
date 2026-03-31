from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile


@dataclass
class Workspace:
    candidate_id: str
    root: Path


class WorkspaceManager:
    def __init__(self, base_tmp: Path | None = None) -> None:
        self.base_tmp = base_tmp

    def create(self, candidate_id: str) -> Workspace:
        root = Path(
            tempfile.mkdtemp(prefix=f"candidate-{candidate_id}-", dir=self.base_tmp)
        )
        return Workspace(candidate_id=candidate_id, root=root)

    def cleanup(self, workspace: Workspace, retain: bool = False) -> None:
        if retain:
            return
        if workspace.root.exists():
            shutil.rmtree(workspace.root)
