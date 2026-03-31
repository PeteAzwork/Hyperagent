# Hyper-Agent Experiment — Comprehensive Implementation TODO

This TODO is derived from `Building Agents/hyperagent-design.md` and turns the architecture into an executable build plan.

## 0) Project setup and governance

- [ ] Define project charter (scope, goals, non-goals, success metrics).
- [ ] Identify owners for control plane, meta plane, task plane, evals, and operations.
- [ ] Select implementation stack (Python vs TypeScript for orchestrator + SDK integration).
- [ ] Create repository/module layout for:
  - [ ] `control-plane/`
  - [ ] `meta-plane/`
  - [ ] `task-plane/`
  - [ ] `benchmarks/`
  - [ ] `archive/`
  - [ ] `ops/`
- [ ] Establish coding conventions and ADR template for architectural decisions.
- [ ] Define release stages: dev → canary → staging → production.
- [ ] Create initial risk register and mitigation owners.

---

## 1) Control plane (immutable) foundation

### 1.1 Orchestrator
- [ ] Implement orchestrator service skeleton with durable job state.
- [ ] Add generation scheduler (manual + cron-based runs).
- [ ] Add stage-based lifecycle engine (Stages 0–11).
- [ ] Add retry/backoff policy and per-stage timeout controls.
- [ ] Add checkpointing for restart/resume across failures.

### 1.2 Policy engine
- [ ] Implement central policy schema (YAML/JSON + typed models).
- [ ] Define hard gates for:
  - [ ] forbidden edits
  - [ ] tool escalation
  - [ ] permission escalation
  - [ ] invalid/missing safety receipts
- [ ] Implement policy evaluation API used by static gate and promotion controller.

### 1.3 Benchmark registry
- [ ] Implement benchmark catalog with versioning (`bench_v###`).
- [ ] Register benchmark categories:
  - [ ] task success
  - [ ] behavioral quality
  - [ ] safety
  - [ ] efficiency
  - [ ] transfer
- [ ] Add benchmark split support: train/evolution, probe, holdout, adversarial.
- [ ] Add sealed holdout access controls.

### 1.4 Promotion / rollback controllers
- [ ] Implement promotion state machine (eligible → canary → staging → prod).
- [ ] Implement promotion preconditions (score, safety, cost, latency thresholds).
- [ ] Implement rollback API (`rollback --to <gen_id>`).
- [ ] Implement quarantine workflow for failed promoted generations.

### 1.5 Secrets + trust boundaries
- [ ] Implement secrets broker integration (read-only, no candidate exposure).
- [ ] Ensure no production secrets are injected into candidate environments.
- [ ] Enforce network/egress restrictions for candidate execution contexts.

---

## 2) Task plane (mutable subagent artifact)

### 2.1 Subagent package structure
- [ ] Create canonical package layout:
  - [ ] `.claude/agents/<name>/subagent.md`
  - [ ] `examples/`
  - [ ] `rubrics/`
  - [ ] `hooks/`
  - [ ] `helpers/`
  - [ ] `memory_seed.md`
  - [ ] `manifest.json`
- [ ] Define `manifest.json` schema including tool tier + metadata.
- [ ] Implement package validation command.

### 2.2 Mutation surface tiers
- [ ] Encode mutation tiers in policy:
  - [ ] Tier 0 immutable
  - [ ] Tier 1 semi-mutable
  - [ ] Tier 2 freely mutable in sandbox
- [ ] Add path allowlist/denylist enforcement for candidate edits.
- [ ] Add immutable file tamper detection.

### 2.3 Tool permission tiering
- [ ] Define tier-to-tools mapping (Observer/Analyst/Editor/Executor).
- [ ] Implement frontmatter injection of `allowedTools`/`disallowedTools` by orchestrator.
- [ ] Add static diff check to block unauthorized tool set expansion.
- [ ] Add manual-approval exception path for approved escalations.

---

## 3) Meta plane (semi-mutable improvement system)

### 3.1 Meta components
- [ ] Implement Improvement Planner.
- [ ] Implement Candidate Editor.
- [ ] Implement Failure Analyzer.
- [ ] Implement Parent Selector.
- [ ] Implement Memory Distiller.
- [ ] Implement optional recipe engine for reusable strategies.

### 3.2 SDK tool boundaries
- [ ] Expose only scoped tools to meta calls (candidate workspace only).
- [ ] Prevent access to control-plane files and production subagent dirs.
- [ ] Implement tool audit logging per meta invocation.

### 3.3 Structured candidate manifest
- [ ] Define candidate proposal schema containing:
  - [ ] hypothesis
  - [ ] expected improvements
  - [ ] intended files
  - [ ] rollback notes
- [ ] Enforce schema validation before edit stage.

---

## 4) Candidate workspace and execution isolation

- [ ] Implement workspace manager supporting:
  - [ ] git worktrees
  - [ ] shallow clone fallback
  - [ ] temp-dir mode
  - [ ] container mode
- [ ] Ensure each candidate has isolated filesystem root.
- [ ] Ensure each benchmark task runs in fresh Claude Code process.
- [ ] Add automatic workspace cleanup + retention policy for debug failures.
- [ ] Add deterministic environment setup (pin dependencies, model config, fixtures).

---

## 5) Static gate / critic (fast pre-eval rejection)

- [ ] Validate subagent frontmatter and markdown schema.
- [ ] Validate hook config syntax and runtime constraints.
- [ ] Lint/compile helper scripts.
- [ ] Enforce forbidden file/permission/tool changes.
- [ ] Run secret leakage detectors on diffs and generated logs.
- [ ] Emit machine-readable gate report with blocking reasons.

---

## 6) Evaluation harness and scoring

### 6.1 Fresh-session evaluator
- [ ] Build evaluation runner that spawns new Claude Code process per task.
- [ ] Add smoke eval mode (5–20 tasks, short timeout).
- [ ] Add full eval mode (train + holdout + adversarial + replay + safety probes).
- [ ] Persist stdout/stderr, receipts, traces, artifacts per task.

### 6.2 Replay evaluation
- [ ] Build replay importer for historical traces/tickets.
- [ ] Implement replay comparator for quality/risk/tool-usage deltas.

### 6.3 Scoring
- [ ] Implement hard-gate failures before scoring.
- [ ] Implement multi-objective ranking (quality, cost, latency, reliability, novelty).
- [ ] Compute regression counts vs promoted baseline.
- [ ] Compute variance/determinism metrics across repeated runs.

### 6.4 Benchmark integrity
- [ ] Implement sealed holdout mechanism (meta sees only pass/fail gate).
- [ ] Implement holdout rotation every N generations.
- [ ] Implement cross-version score comparison flags.
- [ ] Implement contamination audits for suspicious holdout jumps.

---

## 7) Hooks, telemetry, and safety receipts

- [ ] Implement hook handlers for:
  - [ ] PreToolUse
  - [ ] PostToolUse
  - [ ] PermissionRequest
  - [ ] SubagentStart/SubagentStop
  - [ ] TaskCreated/TaskCompleted
- [ ] Add path-policy enforcement in hooks.
- [ ] Add forbidden-shell-pattern enforcement.
- [ ] Add secret redaction pipeline for logs/traces.
- [ ] Add benchmark-task correlation IDs to all events.
- [ ] Produce signed safety receipt per task and bundle per candidate.

---

## 8) Archive, lineage, and audit systems

### 8.1 GenerationRecord storage
- [ ] Implement `GenerationRecord` schema from design doc.
- [ ] Store lineage pointers (`gen_id`, `parent_gen_id`, promoted baseline).
- [ ] Store score blocks + score deltas + benchmark version.
- [ ] Store cost profile and artifact references.

### 8.2 Storage architecture
- [ ] Implement relational metadata store for records and queries.
- [ ] Implement object storage for traces/diffs/receipts.
- [ ] Implement append-only audit log (separate from archive store).
- [ ] Add lineage graph materialization job.

### 8.3 Query + retention
- [ ] Add archive API for generation lookup and reconstruction.
- [ ] Add retention + compaction strategy with legal/audit constraints.
- [ ] Add quarantine bundle handling and root-cause linkage.

---

## 9) Parent selection and search strategy

- [ ] Implement safe-only candidate filtering.
- [ ] Implement Pareto frontier computation across:
  - [ ] task quality
  - [ ] regressions
  - [ ] cost
  - [ ] latency
  - [ ] risk
  - [ ] novelty
- [ ] Implement frontier sampling with exploit/explore ratio.
- [ ] Add support for multi-parent generation batches (3–5 default).
- [ ] Add adaptive strategy update hooks from distillation outputs.

---

## 10) Budget and circuit-breaker governance

### 10.1 Budget enforcement
- [ ] Implement hierarchical limits:
  - [ ] per-task
  - [ ] per-candidate
  - [ ] per-generation
  - [ ] per-run
- [ ] Implement graceful termination and partial-result archival on limit hit.

### 10.2 Circuit breakers
- [ ] Halt on run-level USD overage.
- [ ] Halt on consecutive smoke-fail generations.
- [ ] Halt on persistent diminishing returns trend.
- [ ] Halt on extreme outlier candidate spend.
- [ ] Emit alerts with breaker cause and recovery instructions.

### 10.3 Cost observability
- [ ] Track cost-per-generation and cost-per-promotion.
- [ ] Track cost-per-improvement-point.
- [ ] Feed cost signals into parent selector tie-break logic.

---

## 11) Concurrency and reliability engineering

- [ ] Implement candidate-level parallelism with semaphore controls.
- [ ] Implement task-level concurrency per candidate.
- [ ] Enforce environment-specific process ceilings (local/CI/scheduled).
- [ ] Ensure failure isolation (task failure ≠ candidate abort unless fatal).
- [ ] Add orchestrator idempotency keys for safe replays/retries.

---

## 12) Observability, dashboards, and alerts

- [ ] Implement dashboards:
  - [ ] generation timeline
  - [ ] cost burn-down
  - [ ] candidate funnel
  - [ ] lineage graph
  - [ ] safety trend
- [ ] Implement alert rules for:
  - [ ] circuit-breaker triggers
  - [ ] promoted-candidate safety violation
  - [ ] no promotions for N generations
  - [ ] holdout decline trend
  - [ ] cost anomalies
  - [ ] archive growth/retention pressure

---

## 13) Human-in-the-loop promotion workflow

- [ ] Define mandatory review triggers (Tier 1 edits, tool escalation, high cost, initial trust).
- [ ] Implement review bundle generator including:
  - [ ] candidate record
  - [ ] human-readable diff
  - [ ] score changes
  - [ ] rationale/hypothesis
  - [ ] safety anomalies
  - [ ] trace links
- [ ] Integrate review channel(s): PR-based approval and/or internal approval UI.
- [ ] Require signed/recorded approval decision in audit log.

---

## 14) Meta-distillation and transfer learning

- [ ] Build distillation pipeline for reusable learnings:
  - [ ] rubric fragments
  - [ ] hook checks
  - [ ] benchmark templates
  - [ ] mutation recipes
  - [ ] failure taxonomy updates
- [ ] Separate ephemeral, lineage, and approved-portable memory stores.
- [ ] Add review process for promoting portable memory across subagents.
- [ ] Create starter recipe packs for onboarding new target subagents.

---

## 15) Security hardening and compliance

- [ ] Threat-model all three planes and trust boundaries.
- [ ] Add sandbox restrictions for commands, network, and filesystem.
- [ ] Block forbidden commands (`git push`, SSH, credential helpers, etc.).
- [ ] Sign promotion artifacts and verify at release time.
- [ ] Add incident response runbook for safety regressions.
- [ ] Add periodic security audit cadence and pen-test checklist.

---

## 16) Testing strategy (must-have before production)

### 16.1 Unit tests
- [ ] Policy engine rules and tier enforcement.
- [ ] Scoring and Pareto frontier logic.
- [ ] Budget accounting and breaker triggers.

### 16.2 Integration tests
- [ ] End-to-end generation lifecycle on toy benchmark.
- [ ] Fresh-session guarantee test (subagent reload behavior).
- [ ] Static gate rejection matrix.
- [ ] Archive write/read/reconstruct flow.

### 16.3 Chaos/failure tests
- [ ] Orchestrator crash and resume from checkpoint.
- [ ] Candidate workspace corruption handling.
- [ ] Evaluation task timeouts and partial scoring behavior.
- [ ] Rollback drill from simulated production regression.

### 16.4 Safety tests
- [ ] Tool escalation attempt blocked.
- [ ] Path escape attempt blocked.
- [ ] Secret exfiltration probe blocked.
- [ ] Forbidden command attempts detected and denied.

---

## 17) Delivery roadmap and milestones

### Milestone A — MVP loop (2–3 weeks)
- [ ] Single target subagent
- [ ] Stages 0–9 implemented
- [ ] Smoke + limited full eval
- [ ] Archive + basic parent selection

### Milestone B — Safe promotion loop (2–4 weeks)
- [ ] Promotion + rollback controllers
- [ ] Human approval workflow
- [ ] Cost budgets + circuit breakers
- [ ] Core dashboards and alerts

### Milestone C — Hyper behavior (3–5 weeks)
- [ ] Distillation pipeline
- [ ] Recipe transfer across second subagent
- [ ] Adaptive search strategy updates
- [ ] Holdout rotation + contamination audits

### Milestone D — Production readiness (ongoing)
- [ ] Security hardening completion
- [ ] Reliability targets (SLOs) met
- [ ] Runbook validation + incident exercises
- [ ] Governance signoff

---

## 18) Definition of done (global)

- [ ] Reproducible end-to-end run from baseline snapshot to promotion decision.
- [ ] No candidate can bypass policy gates or mutate Tier 0 artifacts.
- [ ] Every evaluation task runs in a fresh session and emits trace + safety receipt.
- [ ] Every generation has complete lineage, score, and cost records.
- [ ] Rollback can restore prior promoted generation in minutes.
- [ ] Human approval is enforced where required and audit-complete.
- [ ] Cost controls prevent runaway spend in unattended runs.
- [ ] Distilled learnings are versioned and reusable across subagents.

---

## 19) Suggested first execution order (next 10 tasks)

1. [ ] Implement canonical subagent package + manifest schema.
2. [ ] Implement candidate workspace isolation.
3. [ ] Implement static gate with tier/path/tool escalation checks.
4. [ ] Implement fresh-session smoke evaluator.
5. [ ] Implement `GenerationRecord` + archive writer.
6. [ ] Implement parent selector (safe filter + Pareto frontier).
7. [ ] Implement budget accounting + per-candidate/per-run caps.
8. [ ] Implement promotion eligibility rules (no deploy yet).
9. [ ] Implement rollback primitives + quarantine state.
10. [ ] Add minimal dashboards (timeline, funnel, cost).

