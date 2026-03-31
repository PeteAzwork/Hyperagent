from __future__ import annotations

from pathlib import Path
import json

MANIFEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SubagentManifest",
    "type": "object",
    "required": [
        "name",
        "version",
        "description",
        "tool_tier",
        "entrypoint",
    ],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
        "description": {"type": "string"},
        "tool_tier": {
            "type": "string",
            "enum": ["observer", "analyst", "editor", "executor"],
        },
        "entrypoint": {"type": "string"},
        "allowed_tools": {"type": "array", "items": {"type": "string"}},
        "disallowed_tools": {"type": "array", "items": {"type": "string"}},
        "metadata": {"type": "object"},
    },
    "additionalProperties": True,
}

REQUIRED_PACKAGE_PATHS = [
    ".claude/agents/example-agent/subagent.md",
    "examples",
    "rubrics",
    "hooks",
    "helpers",
    "memory_seed.md",
    "manifest.json",
]


def validate_package(package_root: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for rel in REQUIRED_PACKAGE_PATHS:
        if not (package_root / rel).exists():
            errors.append(f"Missing required path: {rel}")

    manifest_path = package_root / "manifest.json"
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid manifest.json: {exc}")
            return False, errors

        for required_key in MANIFEST_SCHEMA["required"]:
            if required_key not in payload:
                errors.append(f"manifest.json missing key: {required_key}")

        tier = payload.get("tool_tier")
        allowed = MANIFEST_SCHEMA["properties"]["tool_tier"]["enum"]
        if tier is not None and tier not in allowed:
            errors.append(f"Invalid tool_tier '{tier}', expected one of {allowed}")

    return len(errors) == 0, errors
