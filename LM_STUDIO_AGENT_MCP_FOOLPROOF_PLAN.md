# LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan

This document is a complete runbook for building a robust local AI agent setup using either LM Studio or Ollama as the LLM API provider, with optional MCP tool calling and a local UI for coding, research, analysis, and documentation workflows.

Use this as your single source of truth.

---

## 1) What You Are Building

You are building a local-first agent system with:

- A provider switch so you can choose LM Studio or Ollama per run.
- A Python agent runtime that can:
  - plan multi-step work,
  - execute safe tools,
  - optionally call MCP tools,
  - validate outputs,
  - store memory and logs.
- A local UI to start runs, approve risky actions, inspect logs, and review artifacts.
- Safety controls so you can leave it running with confidence.

Target outcomes:

- Coding tasks: implement, refactor, test, and summarize changes.
- Research tasks: gather, compare, and synthesize information.
- Analysis tasks: inspect data/text/code and produce structured insights.
- Documentation tasks: generate, update, and maintain docs with traceable sources.

---

## 2) Final Architecture (Recommended)

Use a 4-layer architecture:

1. Model Provider Layer (LM Studio or Ollama)

- LM Studio option: `http://127.0.0.1:1234/v1`.
- Ollama option: native API on `http://127.0.0.1:11434` (or OpenAI-compatible endpoint if you enable/use it).
- One main model (reasoning/planning).
- Optional secondary fast model for verification or summarization.

2. Agent Layer (Python)

- Planner: converts goal into a step plan.
- Executor: runs one safe step at a time.
- Verifier: checks if step/output meets criteria.
- Recovery: retries/replans when failures occur.

3. Tool Layer

- Native tools (filesystem, shell, git, search, fetch).
- MCP tools (if you attach MCP servers).
- Uniform tool wrapper for logging, policy checks, and timeout handling.

4. UI Layer (Local Web App)

- Run creation screen with mode selection.
- Live step timeline and tool-call logs.
- Human approval queue for sensitive actions.
- Artifacts viewer for outputs and summaries.

Persistence:

- SQLite DB for runs, steps, tool calls, errors, artifacts.
- File-based artifacts folder for outputs (`artifacts/`).

---

## 3) LLM Provider Setup (LM Studio or Ollama)

### 3.1 Option A: LM Studio Setup

1. Install LM Studio desktop app.
2. Download at least one instruction model.
3. Open LM Studio and load model into memory.

Model suggestions for local agent work:

- Balanced general/coding:
  - qwen2.5-coder 7B equivalent GGUF in LM Studio
  - llama-3.1-8b-instruct equivalent GGUF
- Heavier reasoning (if hardware allows):
  - 14B+ instruct model

Enable local server:

In LM Studio:

1. Go to Developer or API server section.
2. Enable OpenAI-compatible local server.
3. Confirm host/port (default usually `127.0.0.1:1234`).
4. Confirm endpoint root is `/v1`.

Health test:

```bash
curl http://127.0.0.1:1234/v1/models
```

Expected: JSON list of available loaded models.

### 3.2 Option B: Ollama Setup

1. Install Ollama.
2. Pull at least one model.

Example:

```bash
ollama pull qwen2.5-coder:7b
```

3. Ensure Ollama service is running on `127.0.0.1:11434`.

Health tests:

```bash
curl http://127.0.0.1:11434/api/tags
```

Expected: JSON list of available local models.

If using OpenAI-compatible mode, also validate your `/v1/models` endpoint.

### 3.3 Provider Switch Contract (Required)

Your agent config must support a provider selector:

- `provider`: `lmstudio` or `ollama`
- `base_url`: endpoint for chosen provider
- `model_planner`
- `model_executor`
- `model_verifier`

Rule: the planner/executor/verifier must never care which provider is selected. Only the model client adapter handles this.

### 3.4 Runtime Tuning Defaults

Set conservative defaults first:

- temperature: `0.1` to `0.3` for reliability
- top_p: `0.9`
- max_tokens: start `1024`, increase only if needed
- context window: as large as model/hardware reliably supports

For deterministic plans and tool schemas, keep temperature low.

---

## 4) Python Project Setup

Create these files/folders:

- `agent.py` (main runner)
- `config.yaml` (all settings)
- `prompts/` (planner/executor/verifier prompts)
- `tools/` (native tool implementations)
- `mcp_clients/` (MCP connection adapters)
- `artifacts/` (outputs)
- `state/agent.db` (SQLite)
- `logs/` (structured logs)

Recommended packages:

```bash
pip install openai pydantic pyyaml tenacity python-dotenv rich sqlalchemy
```

If using MCP in Python:

```bash
pip install mcp
```

Note: exact MCP package APIs evolve. Pin versions once working:

```bash
pip freeze > requirements-lock.txt
```

---

## 5) Configuration Strategy (Critical)

Keep all knobs in `config.yaml`.

Suggested sections:

- `llm`:
  - `provider`: `lmstudio` or `ollama`
  - `base_url_lmstudio`: `http://127.0.0.1:1234/v1`
  - `base_url_ollama`: `http://127.0.0.1:11434`
  - `api_key_lmstudio`: `lm-studio` (placeholder value is usually accepted)
  - `api_key_ollama`: `ollama` (placeholder for OpenAI-compatible usage)
  - `model_planner`
  - `model_executor`
  - `model_verifier`
  - `transport`: `openai_compatible` or `ollama_native`
- `budgets`:
  - `max_steps`
  - `max_runtime_minutes`
  - `max_tool_calls`
- `safety`:
  - `require_approval_for`
  - `blocked_commands`
  - `allowed_paths`
- `test_policy`:
  - `enforce_task_test_gate`: true/false
  - `auto_generate_tests`: true/false
  - `verify_and_autocorrect_tests`: true/false
  - `run_tests_before_completion`: true/false
  - `delete_tests_after_task`: true/false (default true)
  - `keep_tests_when_user_requests`: true/false (default true)
  - `test_location_strategy`: `adjacent_temp` or `tests_temp`
  - `max_test_fix_attempts`
  - `test_runner_by_mode` (pytest, unit test, integration test, custom)
- `mcp`:
  - server definitions and transport (`stdio`, `http`, etc)
- `logging`:
  - log level
  - redact secrets true/false
- `ui`:
  - `enabled`
  - `host`
  - `port`
  - `auth_mode` (local-only token or none)

Why this matters:

- You can tune behavior without editing code.
- Easier rollback and reproducibility.

---

## 6) Agent Loop Design (Foolproof)

Use this exact control loop:

1. Receive goal.
2. Planner returns JSON plan with:
   - assumptions,
   - step list,
   - success criteria,
   - stop conditions.
3. Execute one step only.
4. Log everything.
5. For each completed task step, enforce test gate:

- create test code for the task,
- verify test quality and correctness,
- auto-correct tests until valid or retry limit reached,
- execute tests and require pass status,
- delete generated tests after pass unless user requested keep.

6. Verifier decides one of:
   - `continue`,
   - `retry_step`,
   - `replan`,
   - `ask_user`,
   - `done`.
7. Enforce hard budgets each loop.
8. On crash/restart, resume from DB state.

Mandatory guardrails:

- Never execute free-form shell text from model directly.
- Translate model intent -> validated tool schema.
- Reject tool call if policy denies it.
- Require approval for risky operations.

---

## 7) Tooling Policy (Do Not Skip)

### 7.1 Allowlist First

Allow only known commands/tools, for example:

- read files
- write files under workspace
- run tests
- run linters
- git status/log/diff

Block by default:

- deletion outside workspace
- privilege escalation (`sudo`)
- unrestricted network exfiltration
- destructive git operations

### 7.2 Timeouts and Retries

Each tool call must have:

- timeout (e.g. 30-120s)
- max retries (e.g. 2)
- structured error codes

Test lifecycle policy:

- test generation and test execution are mandatory before marking task success.
- if tests fail, implementation and/or tests are corrected, then re-run.
- completion is blocked until tests pass or run is explicitly marked blocked/failed.
- generated test files are removed automatically after successful verification unless user chose to keep them.

### 7.3 Audit Trail

Store for every call:

- timestamp
- tool name
- inputs
- result summary
- full stderr/stdout (if safe)

This is required for trust when running unattended.

---

## 8) MCP Integration Paths

There are 2 practical patterns.

### Pattern A: Your Agent as MCP Client (Recommended)

- Selected provider (LM Studio or Ollama) is only the model API.
- Your Python agent connects to MCP servers.
- Model decides which tool to invoke.
- Agent executes MCP call and returns result to model.

Use when you want full orchestration control.

### Pattern B: Another host runtime handles MCP; your code uses API only

- A host (or framework) handles MCP plumbing.
- Your custom logic sends prompts and receives final outputs.

Use when you want simpler orchestration but less control.

For coding/research/analysis/docs, Pattern A is better.

---

## 9) Prompt Design for Reliability

Create separate system prompts:

- planner prompt
- executor prompt
- verifier prompt

Rules to include:

- Always respond as strict JSON matching schema.
- Never invent tool names.
- Prefer small, reversible actions.
- Cite evidence for conclusions.

For documentation tasks, require output structure:

- objective
- source evidence
- draft text
- open questions

For research tasks, require confidence fields:

- claim
- evidence
- confidence (0-1)
- uncertainty notes

---

## 10) Data Model (SQLite)

Create tables:

- `runs`
  - run_id, goal, start_time, end_time, status
- `plans`
  - run_id, plan_version, plan_json
- `steps`
  - step_id, run_id, step_index, description, status
- `tool_calls`
  - call_id, step_id, tool, input_json, output_json, latency_ms
- `events`
  - event_id, run_id, type, payload_json, timestamp
- `task_tests`
  - test_id, run_id, step_id, path, generated_at, verified_at, executed_at, status, deleted_at, keep_reason

Why this matters:

- resume capability
- debugging failures
- performance tuning
- compliance/auditing

---

## 11) Task Modes (Coding, Research, Analysis, Docs)

Define explicit run modes in config and prompts.

### 11.1 Coding Mode

- default tools: file edit, test, lint, git diff
- success: generated tests pass, lint clean, summary generated
- extras: change risk notes and rollback suggestion

### 11.2 Research Mode

- default tools: web fetch/search (if enabled), notes synthesis
- success: claims mapped to sources/confidence and validation tests/check scripts pass
- extras: contradictory evidence section

### 11.3 Analysis Mode

- default tools: parse files/data, metrics scripts
- success: reproducible results, validation checks pass, and assumptions documented
- extras: sensitivity checks

### 11.4 Documentation Mode

- default tools: repository read, doc write/update
- success: docs updated with examples/known limitations and doc-validation checks pass
- extras: changelog section

---

## 12) Human Approval Workflow

Require approval before:

- package install
- deleting/moving many files
- pushing code
- running long background jobs
- external network POST/PUT calls

Implementation:

- Agent sets action status to `pending_approval`.
- Writes approval request artifact.
- Waits for user approval token/input.
- Continues only when approved.

---

## 13) Failure Handling and Recovery

Classify failures:

- `model_output_invalid`
- `tool_timeout`
- `tool_permission_denied`
- `resource_exhausted`
- `dependency_missing`

Recovery policy:

1. Retry once with same step and narrower prompt.
2. If fails, replan remaining tasks.
3. If still blocked, ask user with exact blocker.
4. Persist checkpoint before exit.

---

## 14) Performance and Stability Tuning

- Keep prompts short and structured.
- Summarize old context every 3-5 steps.
- Do not keep full transcript in each call.
- Cap tool output size (truncate + store full artifact).
- Use separate model for verification if main model is expensive.

Hardware notes:

- If responses are slow or unstable, use smaller quantization/model.
- Prefer consistent throughput over largest model.

---

## 15) Security Baseline

- Bind LM Studio and Ollama servers to localhost only.
- Never store real secrets in prompts/logs.
- Redact tokens from tool outputs before logging.
- Restrict agent file access to workspace root.
- Keep a blocked command list and enforce it in code.
- Bind UI to localhost or protect it with a local token.

Minimal blocked examples:

- `rm -rf /`
- `sudo *`
- `chmod -R 777 /`
- `git reset --hard`
- unrestricted curl uploads with sensitive files

---

## 16) End-to-End Validation Checklist

Run these in order:

1. Chosen provider server up and model listed (LM Studio or Ollama).
2. Agent can complete simple dry-run plan with no tools.
3. Agent can execute safe read-only tool.
4. Agent can write artifact in `artifacts/`.
5. Approval gate blocks risky action correctly.
6. Resume works after forced process restart.
7. Mode-specific tasks work for all 4 modes.
8. UI can create a run, display live progress, and show approvals.
9. For every completed task, tests are generated, corrected if needed, executed, and passed.
10. Generated tests are auto-deleted on success unless keep option is explicitly enabled.
11. Error paths log clear diagnostics.

Only then allow unattended long runs.

---

## 17) 7-Day Implementation Plan

Day 1:

- Provider setup (LM Studio and/or Ollama) + health checks
- config system + basic logger

Day 2:

- planner JSON schema + parsing/validation
- step persistence in SQLite

Day 3:

- native tools with policy enforcement
- timeout/retry wrappers

Day 4:

- verifier + replan logic
- artifact writing

Day 5:

- MCP client integration for selected servers
- tool registry unification

Day 6:

- run modes (coding/research/analysis/docs)
- approval gate + pending queue
- mandatory test gate with auto-fix + execution loop

Day 7:

- UI screens (run form, timeline, approvals, artifacts)
- UI settings editor for test policy (including keep/delete behavior)
- stability test suite + docs + lock dependencies

---

## 18) Minimal API Example (Provider-Selectable Client)

```python
from openai import OpenAI


def build_client(provider: str) -> OpenAI:
    if provider == "lmstudio":
        return OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
    if provider == "ollama":
        # Use your Ollama OpenAI-compatible endpoint when enabled/available.
        return OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
    raise ValueError(f"Unsupported provider: {provider}")


client = build_client("lmstudio")

resp = client.chat.completions.create(
    model="your-loaded-model-name",
    temperature=0.2,
    messages=[
        {"role": "system", "content": "Respond with JSON only."},
        {"role": "user", "content": "Return {\"ok\":true}."},
    ],
)

print(resp.choices[0].message.content)
```

If you choose Ollama native API instead of OpenAI-compatible mode, implement a separate adapter for `/api/chat` and keep the same planner/executor/verifier interfaces.

---

## 19) Minimal Agent Prompt Contract

Use this contract for model responses:

```json
{
  "thought_summary": "short reasoning summary",
  "action": "tool_call|final_answer|replan|ask_user",
  "tool_name": "optional",
  "tool_input": {},
  "final_answer": "optional",
  "confidence": 0.0
}
```

Reject and reprompt if JSON parse fails.

---

## 20) Practical Defaults for Your Use Case

For coding + research + analysis + docs on a local machine:

- Provider: switchable (`lmstudio` or `ollama`)
- Main model: strong 7B/8B instruct/coder
- Temperature: `0.2`
- Max step budget per run: `30`
- Tool timeout: `60s`
- Retry limit: `2`
- Replan trigger: `2 consecutive step failures`
- Approval required for install/delete/network-write
- Test gate: enabled for all modes
- Delete generated tests after success: enabled by default

---

## 21) What To Build Next (Exact Order)

1. Replace `agent.py` with skeleton classes:
   - Config loader
   - Provider router (`lmstudio` or `ollama`)
   - LLM client adapters
   - Planner
   - Executor
   - Verifier
   - State store
2. Add `config.yaml`.
3. Add one safe tool (`read_file`) and one controlled tool (`run_test`).
4. Add strict JSON validator.
5. Add approval gate.
6. Add MCP server connector.
7. Add mode prompts for coding/research/analysis/docs.
8. Add local UI (run creation, timeline, approvals, artifacts).
9. Add skill accumulation engine (capture, evaluate, promote, reuse).
10. Add per-task test lifecycle manager (generate, verify, correct, run, cleanup).

---

## 22) Common Mistakes To Avoid

- Letting model run arbitrary shell directly.
- No persistence (cannot resume after interruption).
- Giant prompts with no summarization.
- No schema validation on model output.
- Mixing planning and execution in one unreliable step.
- Running unattended without approval policy.
- Storing newly learned skills without validation gates.
- Marking tasks done without passing generated tests.

---

## 23) Done Definition

Your system is production-ready when all are true:

- Runs complete in each mode with reproducible outputs.
- Failures are recoverable and clearly logged.
- High-risk operations always require approval.
- State survives restart and resumes correctly.
- UI controls and monitoring are stable.
- Agent can accumulate validated skills and reuse them in later runs.
- Every completed task passed the test gate (generated, corrected, executed).
- Generated tests are deleted by default unless user explicitly asked to keep.
- You trust it to run without constant supervision.

---

## 24) Optional Enhancements

- Add vector memory for long projects.
- Add benchmark harness for model comparisons.
- Add quality scoring rubric per mode.
- Add task templates for repeated workflows.
- Add multi-user local roles for approvals.

---

## 25) Skill Accumulation and New Skill Creation (Required)

You requested long-term skill growth. Implement this from the beginning.

### 25.1 What a Skill Is

A skill is a reusable execution pattern that includes:

- skill name
- trigger conditions
- required tools
- step template
- expected outputs
- safety limits
- success metrics

### 25.2 Skill Storage Model

Add tables:

- `skills`
  - skill_id, name, description, version, status, created_at
- `skill_versions`
  - skill_id, version, prompt_template, tool_contract_json, safety_policy_json
- `skill_usage`
  - run_id, skill_id, success, latency_ms, error_code
- `skill_candidates`
  - candidate_id, source_run_id, extracted_pattern_json, evaluation_score, status

Statuses:

- `candidate`
- `validated`
- `active`
- `retired`

### 25.3 Learning Pipeline

1. Capture successful runs and extract repeated step patterns.
2. Build candidate skill templates automatically.
3. Validate candidates on benchmark tasks.
4. Promote only if quality and safety thresholds pass.
5. Track drift and retire degraded skills.

### 25.4 New Skill Creation Modes

Support 3 modes:

1. Manual: user defines skill template and constraints.
2. Assisted: agent drafts skill, user approves.
3. Automatic: agent proposes and self-tests, final promotion still requires approval.

### 25.5 Skill Gating Rules (Critical)

Before a new skill becomes active, require:

- minimum success rate (for example 85 percent on validation set)
- zero safety policy violations
- bounded tool scope (no new unrestricted commands)
- human approval for production activation

### 25.6 Skill Selection at Runtime

At each new goal:

1. Retrieve top matching active skills by similarity to goal.
2. Prefer higher-confidence skill with better historical success.
3. Fall back to generic planner when confidence is low.
4. Log why a skill was selected or skipped.

### 25.7 UI for Skill Lifecycle

Add a Skills page with:

- Active skills list and versions
- Candidate skills queue
- Validation metrics and failure reasons
- Promote, rollback, retire controls

### 25.8 Anti-Corruption Rules

- Never overwrite an active skill directly; always create a new version.
- Keep immutable history of changes.
- Roll back automatically if post-promotion failures spike.
- Do not let model-generated skill definitions bypass policy checks.

---

## 26) UI Plan (Required)

Build a local UI from the start (not optional).

Recommended stack:

- Backend API: FastAPI
- Frontend: server-rendered templates or a lightweight SPA
- Realtime updates: WebSocket or periodic polling (2s interval)

Minimum screens:

1. Run Builder

- Goal input
- Mode selector (coding/research/analysis/docs)
- Provider selector (LM Studio or Ollama)
- Model selector (planner/executor/verifier)
- Budget and safety settings
- Test policy settings (mandatory test gate, retries, runner, delete-or-keep behavior)

2. Live Run Monitor

- Current step
- Step history and statuses
- Tool call logs with duration and outcomes
- Usage counters

3. Approval Center

- Pending risky actions
- Approve or reject with reason
- Full action context preview

4. Artifacts and Reports

- Generated files list
- Final summary
- Failure report with retry history

5. Skills Lifecycle

- Candidate skills
- Validation results
- Promote/retire/version controls

6. Settings

- Global defaults editor for provider, safety, MCP, and test policy
- Toggle: keep generated tests after completion (default off)
- Per-run override: keep tests for this run only
- Audit view: which tests were generated/executed/deleted for each task

UI hard requirements:

- Must survive page refresh and restore active run view from DB.
- Must show clear provider currently in use.
- Must prevent approvals from unauthenticated external clients (localhost-only or local token).

---

## 27) Immediate Next Action

Start with:

1. Implement provider selector and adapters (LM Studio and Ollama) first.
2. Implement minimal `agent.py` skeleton with strict JSON outputs.
3. Add basic local UI with run creation and live progress.
4. Add skill candidate capture from successful runs.
5. Run one coding-mode dry-run on each provider.
6. Implement mandatory test lifecycle manager and verify cleanup behavior.
7. Add MCP tool connector after native tools are stable.

This order gives the fastest path to a stable unattended local agent that improves over time.
