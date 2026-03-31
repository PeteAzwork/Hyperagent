from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RollbackState:
    current_gen_id: str
    previous_gen_id: str | None
    quarantined: set[str] = field(default_factory=set)


class RollbackController:
    def __init__(self, state: RollbackState) -> None:
        self.state = state

    def quarantine(self, gen_id: str) -> None:
        self.state.quarantined.add(gen_id)

    def rollback(self, to_gen_id: str) -> None:
        self.state.previous_gen_id = self.state.current_gen_id
        self.state.current_gen_id = to_gen_id
