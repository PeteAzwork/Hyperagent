# First Steps Progress (Execution Pass 1)

This file tracks implementation status for Section 19 of `implementation-todo.md`.

1. [x] Implement canonical subagent package + manifest schema.
2. [x] Implement candidate workspace isolation.
3. [x] Implement static gate with tier/path/tool escalation checks.
4. [x] Implement fresh-session smoke evaluator.
5. [x] Implement `GenerationRecord` + archive writer.
6. [x] Implement parent selector (safe filter + Pareto frontier).
7. [x] Implement budget accounting + per-candidate/per-run caps.
8. [x] Implement promotion eligibility rules (no deploy yet).
9. [x] Implement rollback primitives + quarantine state.
10. [x] Add minimal dashboards (timeline, funnel, cost).

## Notes

- Current implementation is a functional scaffold intended to unblock iteration.
- Next pass should wire these modules into a single orchestrator lifecycle and add tests.
