from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


TIER_POLICY = {
    "tier0": {
        "immutable_paths": ["control-plane/", "meta-plane/"],
        "max_tools": {"read", "glob"},
    },
    "tier1": {
        "immutable_paths": ["control-plane/"],
        "max_tools": {"read", "glob", "bash", "edit"},
    },
    "tier2": {
        "immutable_paths": [],
        "max_tools": {"read", "glob", "bash", "edit", "write", "exec"},
    },
}


@dataclass
class GateIssue:
    blocking: bool
    reason: str


def evaluate_diff(
    tier: str,
    changed_paths: list[str],
    requested_tools: list[str],
    baseline_tools: list[str],
) -> list[GateIssue]:
    issues: list[GateIssue] = []
    policy = TIER_POLICY[tier]

    for path in changed_paths:
        normalized = str(PurePosixPath(path))
        for imm in policy["immutable_paths"]:
            if normalized.startswith(imm):
                issues.append(
                    GateIssue(True, f"Forbidden edit '{normalized}' under immutable prefix '{imm}'")
                )

    req_tools = set(requested_tools)
    allowed = set(policy["max_tools"])
    expanded = req_tools - set(baseline_tools)
    disallowed = req_tools - allowed

    if expanded and disallowed:
        issues.append(
            GateIssue(True, f"Unauthorized tool expansion: {sorted(disallowed)}")
        )

    return issues
