# Architecture Design Document

## Hyperagent system for improving a Claude Code subagent

## 1. Purpose

Design a **hyperagent architecture** that can iteratively improve a Claude Code subagent while keeping the system safe, testable, auditable, and deployable in a real engineering environment.

The design is inspired by the HyperAgents paper’s central idea: combine a **task agent** with a **meta agent**, and let the system improve not only task behavior but also parts of its own improvement strategy over time. In the paper’s framing, the key leap is that the meta-level improvement mechanism is itself editable. ([arXiv][3])

## 2. Scope

This design covers:

* improving one or more Claude Code subagents defined in `.claude/agents/`
* running candidate generations in isolated environments
* evaluating candidate agents on benchmark tasks and replay traces
* archiving lineage, scores, patches, and safety receipts
* promoting, rolling back, and transferring learned improvement patterns

This design does **not** assume we are modifying Claude Code internals. The mutable artifact is the **subagent package and its approved support surface**, not Anthropic’s core runtime.

## 3. Design goals

1. **Safe self-improvement**
   Improvements must happen inside strict trust boundaries.

2. **Fresh-session evaluation**
   Because subagents are loaded at session start, every candidate must be evaluated in a newly spawned Claude Code process. ([Claude API Docs][2])

3. **Open-ended search, not a single linear chain**
   Keep multiple candidate lineages and retain “stepping stones,” similar to HyperAgents’ archive-and-parent-selection pattern. The HyperAgents repo persists archive state and selects parents from prior generations rather than only refining the latest version. ([GitHub][4])

4. **Strong separation of control plane and mutable plane**
   Unlike the research repo’s broad “modify any part of the codebase” posture, production design must keep policy, evaluation, secrets, and promotion logic outside the mutable surface. The repo’s own warning about executing untrusted model-generated code is the clearest reason to enforce that separation. ([GitHub][1])

5. **Transferable meta-improvements**
   The long-term objective is not only to improve one subagent, but to learn reusable improvement recipes, telemetry structures, and evaluation patterns that can seed future subagents, which aligns with the paper’s metacognitive framing. ([arXiv][3])

---

## 4. High-level architecture

I would implement the system as **three planes**:

### A. Immutable control plane

This is the part that is **not self-modified** during normal runs.

Components:

* Orchestrator
* Policy engine
* Benchmark registry
* Evaluation harness
* Archive store
* Promotion controller
* Rollback controller
* Secrets broker
* Audit/trace store

This plane owns trust, permissions, release, and evidence.

### B. Semi-mutable meta plane

This is where the “hyper” behavior lives.

Components:

* Improvement planner
* Candidate editor
* Failure analyzer
* Parent selector
* Memory distiller
* Optional meta-strategy recipes

This plane may evolve, but only within bounded files and usually with stricter review than task-plane changes.

**Implementation note:** The meta plane components should run as direct Claude API calls (via the Agent SDK) rather than as Claude Code subagents. This avoids the session-loading constraint that applies to subagents, gives full control over system prompts and tool sets per invocation, and keeps the meta plane decoupled from the artifact format it is trying to improve. If a meta component needs file access or shell execution, provide those as explicit SDK tools scoped to the candidate workspace — do not give the meta plane access to the control plane's own files or the production subagent directory.

### C. Mutable task plane

This is the Claude Code subagent being improved.

Components:

* target subagent Markdown definition
* prompt fragments/examples
* agent-local hooks
* agent-local helper scripts
* agent-local retrieval config
* agent-local benchmark hints
* agent-local memory seed

This is the surface the hyperagent is primarily trying to improve.

---

## 5. Core design principle

The system should treat a Claude Code subagent as a **versioned software artifact**, not as a magical hidden prompt.

That means each candidate version has:

* a clear parent
* a reproducible diff
* a benchmark result set
* a safety receipt
* a cost/latency profile
* a promotion decision
* a rollback path

This mirrors the useful part of the HyperAgents repo: patches, lineage, parent selection, archive persistence, and evaluation outputs are first-class artifacts rather than incidental logs. ([GitHub][5])

---

## 6. Why the control loop must live outside the subagent

This is the most important Claude Code-specific design decision.

Because subagents are loaded at session start and cannot spawn other subagents, a self-improvement loop cannot reliably be implemented as “the subagent improves itself from inside its own running session.” Instead:

1. the control plane creates a candidate workspace
2. a meta-improver edits the candidate subagent files
3. the evaluator spawns a **fresh Claude Code session/process**
4. that fresh session loads the candidate subagent definition
5. the benchmark runs
6. results are recorded and ranked ([Claude API Docs][2])

That outer-loop structure is also consistent with the HyperAgents repo, where the main orchestration logic sits outside the task and meta wrappers in `generate_loop.py`. ([GitHub][5])

---

## 7. Reference component model

### 7.1 Orchestrator

Responsible for:

* generation budgeting
* parent selection
* candidate workspace creation
* invoking proposal, critique, evaluation, archive, and promotion stages
* handling retries and rollbacks

Recommended implementation:

* Python or TypeScript
* If tightly integrating with Claude Code, prefer TypeScript where Agent SDK usage is first-class
* Back it with a queue and durable storage

### 7.2 Candidate Workspace Manager

Creates isolated candidate environments using:

* git worktrees or shallow clones
* ephemeral temp dirs
* containerized execution

Each candidate workspace contains:

* project source
* `.claude/agents/` target files
* isolated `CLAUDE.md`
* isolated hook definitions
* benchmark fixtures
* no production secrets

The HyperAgents repo uses copied repositories, diff application, and Docker-based execution to evaluate generated variants; that basic shape is worth preserving. ([GitHub][4])

### 7.3 Meta-Improver

A separate agent process that:

* inspects prior archive records
* reads failure clusters
* proposes a hypothesis
* edits only the allowed mutation surface
* writes a structured candidate manifest

This is the equivalent of the repo’s meta agent, but with a far tighter boundary than “modify any part of the codebase.” In the public repo, the meta agent is intentionally broad and tool-rich; that is useful for research but not acceptable as a production default. ([GitHub][1])

### 7.4 Critic / Static Gate

Runs before full evaluation.

Checks:

* frontmatter validity
* prompt parseability
* hook syntax
* helper script lint/compile
* forbidden file edits
* forbidden permission changes
* forbidden tool-set expansion
* secret leakage patterns
* unsupported path accesses

This stage is fast and should reject most bad candidates before expensive evaluation.

### 7.5 Benchmark Evaluator

Runs the candidate against:

* training/evolution tasks
* smoke tests
* holdout tasks
* adversarial safety tests
* replayed historical traces

Each evaluation task spawns a **fresh Claude Code process** so the candidate subagent is loaded cleanly. Use the SDK or process launcher for this. ([Claude API Docs][6])

### 7.6 Telemetry / Hook Collector

Claude Code hooks are ideal for turning agent behavior into structured telemetry.

Use:

* **PreToolUse** to validate intent and record predicted risk
* **PostToolUse** to record actual tool effect
* **PermissionRequest** to detect attempted escalation
* **SubagentStart / SubagentStop** to bracket traces
* **TaskCreated / TaskCompleted** to align benchmark units with traces ([Claude API Docs][7])

This telemetry becomes a major source of signal for future self-improvement.

### 7.7 Archive Store

Inspired directly by the HyperAgents archive pattern.

Store for each generation:

* generation id
* parent generation id
* parent lineage
* candidate patch/diff
* files touched
* evaluation scores by suite
* safety receipts
* cost/latency
* benchmark traces
* failure summaries
* human approval outcome
* release status

The HyperAgents repo persists archive entries to `archive.jsonl`; that is a good baseline, though I would back it with a DB plus object storage in production. ([GitHub][4])

### 7.8 Parent Selector

Chooses the next parent candidate for open-ended search.

Recommended strategy:

* hard-gate unsafe candidates out
* compute Pareto frontier over:

  * task quality
  * regression count
  * cost
  * latency
  * risk
  * novelty
* sample among frontier candidates with an exploit/explore ratio

This keeps the paper’s “stepping stone” behavior while avoiding blind hill-climbing.

The HyperAgents code already has parent selection and optional selection-via-agent mechanisms, which is strong evidence that parent choice is a major part of the architecture, not a footnote. ([GitHub][5])

### 7.9 Promotion Controller

Moves a candidate to:

* canary
* staging
* production

Only after:

* passing holdout thresholds
* passing safety checks
* staying within cost and latency budgets
* optional human approval

### 7.10 Rollback Controller

Must support:

* instant revert to previous promoted generation
* archive-based reconstitution of any historical candidate
* quarantine of bad candidates
* root-cause linkage to patch and trace evidence

**Example failure scenario — promoted candidate causes production regression:**

1. **Detection (T+0):** Production telemetry shows the PR reviewer subagent's comment quality score has dropped 40% since the latest promotion (`gen_000143`). The observability layer fires an alert.
2. **Triage (T+2 min):** An operator (or automated threshold) triggers `rollback --to gen_000127` (the previous promoted generation).
3. **Revert (T+3 min):** The rollback controller swaps the active subagent package back to `gen_000127`, clears any cached memory seeds from the bad generation, and marks `gen_000143` as quarantined in the archive.
4. **Evidence preservation (T+3 min):** The bad candidate's full record — patch, traces, hook receipts, production telemetry during the incident window — is tagged as a quarantine bundle. Nothing is deleted.
5. **Root cause (T+1 hr):** The failure analyzer inspects the quarantine bundle and identifies that `gen_000143` removed a rubric fragment that governed test-coverage comments, causing the quality regression. This finding is written to the failure taxonomy for future meta-improvement.
6. **Prevention:** The distillation step adds a new regression test derived from the incident to the holdout benchmark suite.

---

## 8. Mutable surface definition

To make this safe, define **mutation tiers**.

### Tier 0: immutable

Never editable by the agent during routine self-improvement.

* policy engine
* evaluator truth logic
* promotion logic
* secrets broker
* archive writer
* release credentials
* organization-wide hook policy
* network egress policy

### Tier 1: semi-mutable

Editable only in dedicated meta-improvement runs and usually with human review.

* mutation grammar
* search strategy weights
* benchmark sampling rules
* critique prompt
* failure clustering heuristics
* summary distillation rules

### Tier 2: freely mutable inside the sandbox

Editable by the candidate generator.

* target subagent prompt
* examples and rubrics
* subagent-local hooks
* helper scripts
* retrieval heuristics
* task decomposition heuristics
* output formatting rules
* local memory seeds

This is the productionized version of the paper’s “editable task plus editable meta logic” idea: you keep the essence, but you do **not** let the system rewrite its own guardrails.

---

## 9. Claude Code-specific design choices

### 9.1 Use subagents as artifacts

Store each target subagent in a package-like layout:

```text
.claude/
  agents/
    reviewer/
      subagent.md
      examples/
      rubrics/
      hooks/
      helpers/
      memory_seed.md
      manifest.json
```

Even though Claude Code loads subagents from Markdown definitions, treating the subagent as a package makes benchmarking and diffing much easier. The official docs establish the subagent definition format; the packaging around it is my recommended implementation pattern. ([Claude API Docs][2])

### 9.2 Evaluate in fresh sessions

Because subagents are loaded at session start, candidate evaluation must use new processes. This is non-negotiable. Use the SDK’s Claude Code process spawning support to make every benchmark hermetic. ([Claude API Docs][2])

### 9.3 Lock tool permissions by policy

Claude Code supports per-subagent tool allowlists or denylists. Use that to create capability tiers and stop the improvement loop from silently expanding its own powers. ([Claude API Docs][2])

Recommended tiers:

* Observer: read/search only
* Analyst: read/search/bash
* Editor: add write/edit
* Executor: only in isolated sandboxes and only for benchmark tasks
* Never auto-promote a candidate that required broader tools than its parent without explicit review

**Enforcement mechanism:**

1. **Baseline declaration:** Each subagent's `manifest.json` declares its tool tier. The orchestrator writes the corresponding `allowedTools` list into the candidate's subagent frontmatter before evaluation.
2. **Runtime enforcement:** Claude Code's native per-subagent `allowedTools` / `disallowedTools` frontmatter fields enforce the tier at session load time. The candidate cannot override these because the frontmatter is written by the orchestrator, not the candidate editor.
3. **Escalation detection:** The static gate (Section 7.4) compares the candidate's frontmatter against its parent's. Any addition to `allowedTools` or removal from `disallowedTools` is flagged as a tool-set escalation and blocks promotion unless an explicit human approval is recorded.
4. **Hook-level backup:** A `PreToolUse` hook in the evaluation sandbox independently validates every tool call against the declared tier. If a tool call arrives that shouldn't be possible under the tier, it is rejected and logged as a safety anomaly.

### 9.4 Use hooks as both sensors and brakes

Hooks should do more than log. They should also enforce local policy.

Examples:

* reject edits outside allowed paths
* reject shell commands matching forbidden patterns
* redact secrets from logs
* stamp each tool action with benchmark task id
* produce a signed safety receipt for archive storage

Claude Code’s documented hook lifecycle makes this feasible. ([Claude API Docs][7])

### 9.5 Isolate memory during evaluation

Claude Code sessions start fresh, but persistent knowledge can come from `CLAUDE.md` and auto memory, including subagent-specific auto memory. That is useful in production, but it can contaminate evaluation. Use isolated memory roots per candidate and per benchmark suite, and only promote distilled memories after review. ([Claude API Docs][8])

---

## 10. Generation lifecycle

### Stage 0: baseline capture

* snapshot current promoted subagent
* record existing metrics
* export known good traces
* tag as `gen_initial`

This echoes the HyperAgents repo’s initial-generation setup pattern. ([GitHub][5])

### Stage 1: parent selection

Choose parent from archive using:

* safe-only candidates
* recent improvement trend
* domain/task cluster
* novelty balance
* cost budget

### Stage 2: candidate creation

* create worktree/container
* materialize parent subagent package
* inject benchmark set and isolated memory
* generate candidate id and manifest stub

### Stage 3: proposal

The meta-improver receives:

* parent manifest
* prior diff summary
* failure clusters
* top regressions
* budget remaining
* mutation rules

It produces:

* hypothesis
* expected improvement dimensions
* files it intends to modify
* rollback notes

### Stage 4: edit

The editor applies changes to allowed files only.

In the HyperAgents repo, tool use is intentionally broad and includes Bash plus a rich editor abstraction. For this design, keep that shape but wrap it in a stronger path and policy fence. ([GitHub][9])

### Stage 5: static validation

Reject candidate if:

* malformed frontmatter
* invalid hook config
* forbidden file touched
* tool-set escalation
* permission escalation
* unsupported model selection
* policy receipt missing

### Stage 6: smoke evaluation

Run a small benchmark slice:

* 5 to 20 tasks
* short timeout
* high-signal failure categories

Purpose:

* eliminate obviously broken candidates quickly

### Stage 7: full evaluation

Run:

* training/evolution set
* holdout set
* adversarial set
* replay tasks from real logs
* safety probe tasks

Each task uses a fresh Claude Code process. Persist trace bundles, hook receipts, stdout/stderr, patch diffs, and benchmark outputs.

### Stage 8: scoring

Compute:

* primary task score
* holdout score
* regression count
* token/cost profile
* wall-clock latency
* tool action risk score
* diff blast radius
* determinism/variance
* novelty score

### Stage 9: archive write

Store:

* full candidate record
* all receipts
* all scores
* lineage pointers
* critique summary
* promotion eligibility

### Stage 10: promotion

Promote only when:

* holdout score exceeds threshold
* no severe safety violations
* cost is within budget
* regression count below threshold
* optional human review passes

### Stage 11: distillation

Extract reusable learnings:

* improved rubric patterns
* better hook checks
* better benchmark generators
* better mutation recipes
* failure taxonomies

This is where the system becomes genuinely “hyper”: not just better subagent behavior, but better future self-improvement.

---

## 11. Evaluation architecture

A hyperagent without evaluation is just an automated prompt tweaker. The evaluator is the real source of progress.

### 11.1 Benchmark categories

Use at least five categories.

1. **Task success benchmarks**
   Real tasks the subagent is supposed to solve.

2. **Behavioral quality benchmarks**
   Clarity, adherence to format, minimal-change behavior, avoidance of overreach.

3. **Safety benchmarks**
   Attempts to exceed scope, use forbidden tools, access bad paths, or make destructive edits.

4. **Efficiency benchmarks**
   Token usage, wall-clock time, tool calls per task.

5. **Transfer benchmarks**
   New repos, new issue shapes, slightly shifted requirements.

### 11.2 Dataset split

Use:

* evolution/train split
* probe split
* holdout split
* adversarial split

Do not promote on train-only gains.

### 11.2.1 Benchmark integrity and contamination prevention

Over time, the meta-improver sees failure clusters, improvement patterns, and scoring trends that can indirectly leak signal about holdout tasks. Without active countermeasures, the system will overfit to its own evaluation infrastructure.

**Mitigations:**

* **Sealed holdout sets.** Maintain at least one holdout set that the meta-improver never sees — not even as aggregate pass/fail counts. Only the evaluator and the promotion controller access sealed holdout results. The meta-improver receives a single "holdout gate passed/failed" boolean, with no task-level detail.
* **Periodic holdout rotation.** Every N generations (recommended: every 20–50), retire the current holdout set into the training pool and promote a fresh set from a reserved task bank. Log each rotation as an archive event so lineage analysis can account for benchmark-regime changes.
* **Benchmark versioning.** Tag each benchmark set with a version identifier. Store the benchmark version alongside every `GenerationRecord` score. When comparing candidates across benchmark versions, flag the comparison as cross-version and weight it accordingly in parent selection.
* **Synthetic holdout generation.** Periodically use a separate LLM call (outside the meta plane) to generate novel benchmark tasks from real production traces. These synthetic tasks supplement the holdout rotation and reduce the risk of a fixed task bank becoming stale.
* **Contamination audits.** On a scheduled basis, check whether recent candidates show suspiciously high scores on newly introduced holdout tasks (which they should never have seen). A candidate that scores significantly above the baseline on fresh holdout tasks without a clear hypothesis for why warrants investigation.

### 11.3 Replay-based evaluation

A valuable enterprise technique is to replay historical agent transcripts or ticket flows and ask:

* did the new subagent solve the task better?
* with fewer tool calls?
* with fewer risky actions?
* with more accurate reasoning?

This is usually better than synthetic-only evaluation.

### 11.4 Scoring model

Use hard gates first:

* no forbidden edits
* no critical safety failures
* no invalid outputs

Then rank survivors with a multi-objective score:

* quality
* cost
* latency
* reliability
* novelty

Do not use a single scalar too early.

---

## 12. Archive and lineage model

Recommended `GenerationRecord`:

```json
{
  "gen_id": "gen_000143",
  "parent_gen_id": "gen_000127",
  "promoted_baseline_id": "gen_000098",
  "target_subagent": "reviewer",
  "mutation_tier": "tier2",
  "hypothesis": "Add explicit rubric and tighten bash usage rules",
  "files_touched": [
    ".claude/agents/reviewer/subagent.md",
    ".claude/agents/reviewer/hooks/post_tool_use.py"
  ],
  "scores": {
    "train": 0.82,
    "holdout": 0.79,
    "safety": 0.99,
    "cost": 0.71,
    "latency": 0.68,
    "novelty": 0.43
  },
  "scores_vs_promoted": {
    "train_delta": "+0.04",
    "holdout_delta": "+0.02",
    "safety_delta": "0.00",
    "cost_delta": "-0.03",
    "latency_delta": "-0.05"
  },
  "benchmark_version": "bench_v012",
  "regressions": 2,
  "cost_incurred": {
    "input_tokens": 284000,
    "output_tokens": 47000,
    "estimated_usd": 1.42
  },
  "policy_receipt": "receipt_...",
  "trace_bundle": "bundle_...",
  "promotion_status": "staging_candidate"
}
```

The HyperAgents repo’s `archive.jsonl` approach is a good conceptual seed, but production should use:

* relational metadata store
* object store for traces and diffs
* queryable dashboards
* lineage graph view ([GitHub][4])

---

## 13. Meta-improvement strategy

This is where I would deliberately adapt the paper rather than copy the repo literally.

### 13.1 What the meta plane may improve

Allow it to improve:

* mutation recipes
* failure clustering prompts
* summary templates
* benchmark selection heuristics
* exploitation vs exploration weights
* candidate critique patterns

### 13.2 What it may not improve automatically

Do not let it auto-modify:

* secrets access
* egress/network policy
* promotion rules
* path restrictions
* benchmark truth labels
* archive integrity logic

### 13.3 Meta-memory

Maintain three memory layers:

**Ephemeral run memory**
Per candidate, per evaluation run.

**Lineage memory**
Cross-generation summaries:

* what failed repeatedly
* what improved repeatedly
* recurring unsafe patterns
* useful prompt motifs

**Approved portable memory**
Distilled, reviewed recipes reusable across other subagents.

This is the cleanest practical interpretation of the paper’s metacognitive self-modification idea.

---

## 14. Safety model

The public HyperAgents repo warns that it executes untrusted model-generated code. For a Claude Code hyperagent, safety must be an architectural primitive, not a README footnote. ([GitHub][10])

### 14.1 Trust boundaries

* No production secrets in candidate sandboxes
* No production repo writes during evaluation
* No uncontrolled network egress
* No direct promotion from candidate runtime
* No candidate writes to policy or archive authority

### 14.2 Tool restrictions

Use per-subagent allowlists/denylists from Claude Code, and reject any candidate that broadens its own tools unless explicitly approved. ([Claude API Docs][2])

### 14.3 Path restrictions

Allowed writes only under:

* target subagent package
* candidate-local helper dir
* candidate-local hooks dir
* benchmark output dir

Everything else is denied.

### 14.4 Command restrictions

Deny by policy:

* destructive shell patterns
* package installation outside sandbox
* credential helpers
* git push
* SSH
* socket tunnels
* hidden background daemons unless allowed for a benchmark

### 14.5 Release restrictions

Promotion should be done by a non-LLM service using signed artifacts and explicit approvals.

---

## 15. Cost model and budget governance

A hyperagent loop that spawns fresh Claude Code sessions per candidate per benchmark task can consume API budget rapidly. Cost governance must be an architectural concern, not an afterthought.

### 15.1 Budget hierarchy

Define budgets at four levels:

| Level | Scope | Example limit |
|-------|-------|---------------|
| **Per-task** | Single benchmark task evaluation | 50k input tokens, 10k output tokens |
| **Per-candidate** | All tasks for one candidate (smoke + full) | 500k input tokens, 100k output tokens |
| **Per-generation** | All candidates in one generation batch | 5M input tokens, 1M output tokens |
| **Per-run** | Entire orchestrator invocation | 50M input tokens, 10M output tokens, $50 USD |

The orchestrator enforces these limits. When a limit is reached, the current scope is terminated gracefully — partial results are archived, and the generation continues with remaining candidates (for per-candidate limits) or halts entirely (for per-run limits).

### 15.2 Circuit breakers

Implement automatic halts when:

* cumulative spend for a run exceeds its USD ceiling
* three consecutive generations produce no candidate that passes the smoke evaluation
* cost-per-improvement-point trends upward for five consecutive generations (diminishing returns)
* a single candidate consumes more than 2x the median candidate cost without completing evaluation

When a circuit breaker fires, the orchestrator archives the current state, logs the trigger reason, and sends an alert. The run can be resumed manually after investigation.

### 15.3 Cost tracking

Every `GenerationRecord` includes a `cost_incurred` block (see Section 12). The archive store aggregates these into:

* cost per generation over time
* cost per promotion (total spend between consecutive promotions)
* cost per score-point improvement
* cumulative spend per target subagent

These metrics feed into both the parent selector (prefer cheaper lineages when quality is equal) and the observability dashboards (Section 17).

---

## 16. Concurrency and parallelism model

The generation lifecycle (Section 10) is described sequentially for clarity, but a production system must support parallelism to make open-ended search practical.

### 16.1 Candidate-level parallelism

Each generation may produce multiple candidates from different parents. These candidates are independent after Stage 2 (workspace creation) and can proceed through Stages 3–9 in parallel.

Recommended defaults:

* **Candidates per generation:** 3–5 (configurable)
* **Max concurrent evaluations:** bounded by available compute and API rate limits, not by the orchestrator
* **Evaluation isolation:** each candidate runs in its own worktree/container with no shared mutable state

### 16.2 Task-level parallelism within evaluation

Within a single candidate's evaluation (Stages 6–7), individual benchmark tasks are independent and can run concurrently. Each task spawns its own Claude Code process, so parallelism is limited by:

* available CPU/memory for concurrent Claude Code processes
* API rate limits (requests per minute, tokens per minute)
* the per-candidate budget ceiling (Section 15.1)

Recommended: run up to 5 benchmark tasks concurrently per candidate, with a semaphore to stay within API rate limits.

### 16.3 Failure handling in parallel batches

* **Task failure:** A single benchmark task failure does not abort the candidate's evaluation. Record the failure, continue with remaining tasks, and include the failure in scoring.
* **Candidate failure:** If a candidate fails static validation (Stage 5) or is rejected at smoke evaluation (Stage 6), release its resources immediately. Do not block other candidates in the same generation.
* **Orchestrator failure:** The orchestrator should checkpoint its state after each stage transition. On restart, it can resume from the last completed stage for each in-progress candidate rather than re-running the entire generation.

### 16.4 Resource ceiling

Define a maximum resource envelope per environment:

| Environment | Max concurrent candidates | Max concurrent tasks per candidate | Max total Claude Code processes |
|-------------|--------------------------|------------------------------------|---------------------------------|
| Local developer | 1 | 2 | 3 |
| CI benchmark | 3 | 5 | 15 |
| Scheduled improvement | 5 | 5 | 25 |

These limits are enforced by the orchestrator's semaphore pool, not by individual candidates.

---

## 17. Observability and alerting

When the hyperagent runs in scheduled self-improvement mode, operators need visibility into system health without reading raw archive records.

### 17.1 Dashboards

Maintain at minimum:

* **Generation timeline:** score trends (train, holdout, safety) over generations, with promotion events marked
* **Cost burn-down:** cumulative spend per run and per generation, against budget ceilings
* **Candidate funnel:** how many candidates are generated, pass static validation, pass smoke, pass full evaluation, and reach promotion eligibility — per generation
* **Lineage graph:** visual tree of parent-child relationships with score annotations, highlighting the promoted lineage and any quarantined branches
* **Safety trend:** count of safety violations per generation, broken down by category (tool escalation, path violation, forbidden command, secret leak)

### 17.2 Alerts

Fire alerts on:

| Condition | Severity | Action |
|-----------|----------|--------|
| Circuit breaker triggered | High | Halt run, notify operator |
| Safety violation in promoted candidate | Critical | Auto-rollback, notify operator |
| No promotion for N generations (default: 10) | Medium | Notify operator — may indicate stale benchmarks or exhausted search space |
| Holdout score declining across generations | Medium | Notify operator — possible benchmark contamination or overfitting |
| Cost per generation exceeding 2x rolling average | Medium | Notify operator |
| Archive store growth exceeding retention policy | Low | Trigger archive compaction |

### 17.3 Audit log

All orchestrator decisions — parent selection, candidate creation, gate pass/fail, promotion, rollback — are written to an append-only audit log separate from the archive store. This log is not accessible to any agent component and serves as the ground truth for post-incident review.

---

## 18. Human-in-the-loop workflow

"Optional human approval" appears in multiple sections (7.9, 10, 13.2). This section defines the concrete workflow.

### 18.1 Approval triggers

Human review is required when:

* a candidate is the first to reach promotion eligibility for a new target subagent (initial trust establishment)
* a candidate modifies Tier 1 (semi-mutable) files
* a candidate's tool tier is broader than its parent's
* a candidate's cost profile exceeds 1.5x the current promoted candidate
* the promotion controller is configured for mandatory review (recommended for production environments)

### 18.2 Review artifact

When human approval is required, the promotion controller generates a **review bundle** containing:

* the candidate's `GenerationRecord`
* a human-readable diff between the candidate and the current promoted version
* a summary of score changes across all benchmark categories
* the candidate's hypothesis and the meta-improver's rationale
* any safety anomalies flagged during evaluation
* a link to the full trace bundle for deep inspection

### 18.3 Review channels

The review bundle can be delivered through:

* **Pull request:** The promotion controller opens a PR in the target repository containing the candidate's subagent package changes. Standard code review applies. Merge = approval, close = rejection.
* **Dashboard approval:** A dedicated UI in the observability dashboard presents the review bundle with approve/reject buttons.
* **Chat notification:** A Slack or Teams message with a summary and approve/reject action buttons, suitable for low-ceremony environments.

The chosen channel is configured per target subagent in the orchestrator config. Multiple channels can be active simultaneously (e.g., PR for Tier 1 changes, dashboard for Tier 2 changes).

### 18.4 Timeout and escalation

If no human response is received within a configurable window (default: 24 hours), the promotion controller:

1. Marks the candidate as "approval_timeout" in the archive
2. Sends an escalation notification
3. Does **not** auto-promote — silence is denial

---

## 19. Deployment model

### Environment types

* local developer mode
* CI benchmark mode
* scheduled self-improvement mode
* staging
* production

### Recommended rollout path

1. **Offline evolution**
   Improve using benchmark corpora only.

2. **Replay-only shadow mode**
   Compare candidate to production on historical tasks.

3. **Canary mode**
   Small subset of real tasks.

4. **Champion/challenger mode**
   Candidate runs alongside production; production remains authoritative.

5. **Promotion**
   After thresholds and approval.

### Rollback

Rollback must be one command:

* switch to prior promoted generation
* invalidate bad candidate
* preserve evidence bundle for review

---

## 20. Suggested repository structure

```text
hyperagent/
  control/
    orchestrator/
    evaluator/
    scorer/
    parent_selector/
    promotion/
    rollback/
    policy/
    archive/
  benchmarks/
    reviewer/
      train/
      holdout/
      adversarial/
      replay/
  candidates/
    gen_000001/
      worktree/
      patch.diff
      traces/
      receipts/
      results.json
  distill/
    recipes/
    failure_taxonomy/
    portable_memory/
  .claude/
    agents/
      reviewer/
        subagent.md
        hooks/
        helpers/
        memory_seed.md
        manifest.json
  CLAUDE.md
```

This keeps Claude-native artifacts close to the project while preserving an external control plane.

---

## 21. Example operating pattern for one target subagent

Assume the target is a **PR reviewer** subagent.

The hyperagent might learn to improve:

* how it scopes changed files
* when it uses Bash versus read/search tools
* how it structures review comments
* when it abstains
* how it cross-checks tests
* how it references style rules from `CLAUDE.md`

Claude Code’s persistent project memory and subagent-local memory make this especially useful, but those memories must be versioned and isolated during evaluation to avoid silent contamination. ([Claude API Docs][8])

A likely improvement sequence is:

1. prompt-only evolution
2. add rubric fragments
3. add hook-based telemetry
4. add helper scripts
5. distill learned reviewer heuristics into portable recipes
6. use those recipes to seed a test-writer or refactor-planner subagent

That last step is the closest production analogue to the paper’s transfer story.

---

## 22. How this differs from the research repo

This design keeps the **spirit** of HyperAgents but changes the control architecture.

### Kept from HyperAgents

* archive and lineage
* parent selection
* patch-based generations
* isolated evaluation
* open-ended search over candidates
* meta-level improvement as a first-class concern ([GitHub][5])

### Deliberately changed

* no unrestricted “modify any part of the codebase”
* no mutable safety controller
* no mutable promotion logic
* no hidden benchmark contamination
* no live-session self-rewrite of the loaded subagent

This is the difference between a strong research prototype and an architecture you could defend in production review.

---

## 23. Implementation roadmap

### Phase 1: safe baseline

* one target subagent
* prompt-only mutations
* archive + benchmark + rollback
* fresh-session evaluation
* no meta-plane edits

### Phase 2: richer task-plane evolution

* hook evolution
* helper-script evolution
* multi-objective parent selection
* replay benchmarks
* canary rollout

### Phase 3: bounded meta-improvement

* mutable mutation recipes
* failure taxonomy distillation
* portable memory library
* cross-subagent transfer

### Phase 4: portfolio hyperagent

* improve multiple Claude Code subagents
* share meta-recipes across them
* benchmark transfer systematically

---

## 24. Relationship to the containerised agent runtime

The candidate workspace manager (Section 7.2) and the fresh-session evaluation model (Section 9.2) require isolated, reproducible execution environments. The containerised agent runtime described in `Building Agents/containerised-agent-design.md` provides a ready-made substrate for this:

* **Evaluation sandboxes as container instances.** Each candidate evaluation can run inside a dedicated container instance with its own workspace mount, session state, and tool configuration. The container's file-mount isolation (`/workspace` root enforcement, `.sessions/` exclusion) aligns directly with the hyperagent's path restriction requirements (Section 14.3).
* **Session-per-task mapping.** The containerised runtime's named session model maps naturally to benchmark tasks — each task gets a session, and the session's `history.jsonl` becomes the trace artifact for the archive.
* **Tool configuration via YAML.** The runtime's `config.yaml` tool configuration (allowed commands, MCP server connections, file access scope) can serve as the enforcement point for tool permission tiers (Section 9.3). The orchestrator generates a candidate-specific `config.yaml` that reflects the declared tool tier.
* **Build expiry as a safety net.** The runtime's 30-day build expiry mechanism ensures that long-running scheduled improvement loops do not silently drift away from the current codebase and dependency set.

For Phase 1 (Section 23), local developer mode can use direct Claude Code process spawning. For Phase 2 and beyond, the containerised runtime is the recommended execution backend for evaluation sandboxes.

---

## 25. Bottom line

The right way to build a **HyperAgent for a Claude Code subagent** is to place the recursive-improvement loop **outside** the subagent runtime and treat the subagent definition as a **versioned, benchmarked, promotable artifact**. The paper and repo provide the useful primitives: editable task/meta behavior, archive-based open-ended search, patch lineage, and isolated evaluation. Claude Code provides the practical substrate: subagent artifacts, tool controls, hooks, memory, and process spawning. The production architecture is the combination of those two ideas, with a hard control-plane boundary so the system can improve aggressively without being trusted blindly. ([arXiv][3])

I can turn this into a concrete repo skeleton next, including candidate manifests, archive schema, hook contracts, and an evaluator loop.

[1]: https://github.com/facebookresearch/HyperAgents/blob/main/meta_agent.py "Meta agent implementation — broad tool access and unrestricted codebase modification that this design constrains"
[2]: https://docs.anthropic.com/en/docs/claude-code/sub-agents "Claude Code subagent documentation — definition format, session loading, and tool allowlists"
[3]: https://arxiv.org/abs/2603.19461 "HyperAgents paper — core idea of editable task + editable meta-improvement strategy"
[4]: https://github.com/facebookresearch/HyperAgents/blob/main/utils/gl_utils.py "Archive and generation utilities — archive persistence, diff application, and Docker-based evaluation"
[5]: https://github.com/facebookresearch/HyperAgents/blob/main/generate_loop.py "Main orchestration loop — parent selection, generation management, and archive writes"
[6]: https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-typescript "Claude Code TypeScript SDK — process spawning for hermetic benchmark evaluation"
[7]: https://docs.anthropic.com/en/docs/claude-code/hooks "Claude Code hooks — PreToolUse, PostToolUse, and other lifecycle events for telemetry and policy enforcement"
[8]: https://docs.anthropic.com/en/docs/claude-code/memory "Claude Code memory — project memory, subagent-local memory, and isolation considerations"
[9]: https://github.com/facebookresearch/HyperAgents/blob/main/agent/tools/bash.py "Bash tool implementation — broad shell access pattern that this design wraps in policy fences"
[10]: https://github.com/facebookresearch/Hyperagents "HyperAgents repository root — includes safety warnings about executing untrusted model-generated code"
