# Hyper-Agent Experiment (Execution Scaffold)

This directory now contains an executable scaffold for the **10 suggested first execution tasks** from `implementation-todo.md`.

## What is implemented

1. Canonical subagent package + manifest schema.
2. Candidate workspace isolation primitives.
3. Static gate with tier/path/tool escalation checks.
4. Fresh-session smoke evaluator.
5. `GenerationRecord` + archive writer.
6. Parent selector (safe filter + Pareto frontier).
7. Budget accounting + per-candidate/per-run caps.
8. Promotion eligibility rules (no deployment).
9. Rollback primitives + quarantine state.
10. Minimal dashboards (timeline, funnel, cost).

## Quickstart

```bash
cd /workspace/docs/hyper-agent-experiment
python3 -m hyper_agent.cli demo
```

Artifacts are written under `archive/` and `dashboards/`.
