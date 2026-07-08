# Graph Report - AI_Agent  (2026-07-08)

## Corpus Check
- 34 files · ~26,806 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 353 nodes · 699 edges · 29 communities (27 shown, 2 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc1d2405`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_StateStore|StateStore]]
- [[_COMMUNITY_test_agent.py|test_agent.py]]
- [[_COMMUNITY_LM Studio or Ollama + Local Agent + MCP + UI Foolproof Implementation Plan|LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan]]
- [[_COMMUNITY_agent.py|agent.py]]
- [[_COMMUNITY__ScriptedLLM|_ScriptedLLM]]
- [[_COMMUNITY_Path|Path]]
- [[_COMMUNITY_25) Skill Accumulation and New Skill Creation (Required)|25) Skill Accumulation and New Skill Creation (Required)]]
- [[_COMMUNITY_11) Task Modes (Coding, Research, Analysis, Docs)|11) Task Modes (Coding, Research, Analysis, Docs)]]
- [[_COMMUNITY_3) LLM Provider Setup (LM Studio or Ollama)|3) LLM Provider Setup (LM Studio or Ollama)]]
- [[_COMMUNITY_7) Tooling Policy (Do Not Skip)|7) Tooling Policy (Do Not Skip)]]
- [[_COMMUNITY_8) MCP Integration Paths|8) MCP Integration Paths]]
- [[_COMMUNITY_test_1_initialize_conversation.py|test_1_initialize_conversation.py]]
- [[_COMMUNITY_Character Profiles|Character Profiles]]
- [[_COMMUNITY_11) Task Modes (Coding, Research, Analysis, Docs)|11) Task Modes (Coding, Research, Analysis, Docs)]]
- [[_COMMUNITY_3) LLM Provider Setup (LM Studio or Ollama)|3) LLM Provider Setup (LM Studio or Ollama)]]
- [[_COMMUNITY_Story Elements|Story Elements]]
- [[_COMMUNITY_7) Tooling Policy (Do Not Skip)|7) Tooling Policy (Do Not Skip)]]
- [[_COMMUNITY_Fox Character|Fox Character]]
- [[_COMMUNITY_8) MCP Integration Paths|8) MCP Integration Paths]]
- [[_COMMUNITY_.run|.run]]
- [[_COMMUNITY_.run_goal|.run_goal]]

## God Nodes (most connected - your core abstractions)
1. `AgentEngine` - 58 edges
2. `StateStore` - 31 edges
3. `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` - 28 edges
4. `PlannerExecutorVerifier` - 25 edges
5. `TaskStep` - 24 edges
6. `AgentConfig` - 23 edges
7. `Section-by-Section Breakdown` - 20 edges
8. `TestLifecycleManager` - 19 edges
9. `load_config()` - 18 edges
10. `create_ui_app()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `test_ui_exposes_approval_endpoints()` --calls--> `create_ui_app()`  [EXTRACTED]
  tests/test_agent.py → agent/api.py
- `test_ui_exposes_run_history_and_steps_endpoints()` --calls--> `create_ui_app()`  [EXTRACTED]
  tests/test_agent.py → agent/api.py
- `test_ui_root_page_exists()` --calls--> `create_ui_app()`  [EXTRACTED]
  tests/test_agent.py → agent/api.py
- `test_load_config_supports_provider_switch()` --calls--> `load_config()`  [EXTRACTED]
  tests/test_agent.py → agent/config.py
- `test_ui_endpoints()` --calls--> `AgentEngine`  [EXTRACTED]
  tests/test_ui.py → agent/engine.py

## Import Cycles
- None detected.

## Communities (29 total, 2 thin omitted)

### Community 0 - "StateStore"
Cohesion: 0.09
Nodes (11): Any, Path, Create a new run (or re-activate a stopped one)., Delete a run and ALL associated data (steps, tests, approvals, messages)., Add a goal to the background job queue., Atomically claim the oldest queued job for processing., SQLite-backed persistence for ALL agent state.  	Every public method opens its o, Create all tables if they don't exist yet. (+3 more)

### Community 1 - "test_agent.py"
Cohesion: 0.13
Nodes (45): AgentEngine, The top-level orchestrator that wires together all agent subsystems.      Create, PlannerExecutorVerifier, Implements the three-phase agent loop (plan → execute → verify).      Receives a, test(), Path, _ScriptedLLM, test_additional_native_tools() (+37 more)

### Community 2 - "LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan"
Cohesion: 0.08
Nodes (23): 10) Data Model (SQLite), 12) Human Approval Workflow, 13) Failure Handling and Recovery, 14) Performance and Stability Tuning, 15) Security Baseline, 16) End-to-End Validation Checklist, 17) 7-Day Implementation Plan, 18) Minimal API Example (Provider-Selectable Client) (+15 more)

### Community 3 - "agent.py"
Cohesion: 0.10
Nodes (37): create_ui_app(), Create and configure the FastAPI application.      All routes are defined inside, ensure_default_config(), main(), Path, Load config if it exists, or create a default config.yaml and return it., Parse CLI args, create the engine, and run in the appropriate mode.      Returns, AgentConfig (+29 more)

### Community 4 - "_ScriptedLLM"
Cohesion: 0.13
Nodes (9): MCPClientRegistry, Any, Call a tool on a registered MCP server.          Args:             server_name:, Gracefully close all open MCP sessions when the registry is garbage-collected., Manages connections to one or more MCP servers.      Usage:         registry = M, Register an MCP server definition. Does NOT connect immediately., Return names of all registered MCP servers., Initialize a stdio MCP session synchronously (blocks until connected). (+1 more)

### Community 5 - "Path"
Cohesion: 0.14
Nodes (16): Run the test lifecycle for a completed step and return the verdict.          Arg, Represents a single step in the planner's multi-step plan.  	Fields: 		step_id:, Captures the result of generating, running, and optionally fixing tests.  	Field, Final verdict for a step after the test gate has run.  	Fields: 		status:, StepCompletion, TaskStep, TestRunReport, Path (+8 more)

### Community 6 - "25) Skill Accumulation and New Skill Creation (Required)"
Cohesion: 0.22
Nodes (9): 25.1 What a Skill Is, 25.2 Skill Storage Model, 25.3 Learning Pipeline, 25.4 New Skill Creation Modes, 25.5 Skill Gating Rules (Critical), 25.6 Skill Selection at Runtime, 25.7 UI for Skill Lifecycle, 25.8 Anti-Corruption Rules (+1 more)

### Community 7 - "11) Task Modes (Coding, Research, Analysis, Docs)"
Cohesion: 0.17
Nodes (10): fetchStepsForRun(), PRE_LOADED_MODELS, refreshChat(), renderRunToChat(), renderSessionsSidebar(), runsCache, saveLLMSettings(), selectSession() (+2 more)

### Community 9 - "7) Tooling Policy (Do Not Skip)"
Cohesion: 0.40
Nodes (4): Test that main.py contains expected content, Test that the project structure is properly initialized, test_main_file_content(), test_project_structure_created()

### Community 14 - "test_1_initialize_conversation.py"
Cohesion: 0.07
Nodes (26): ✅ §10 — Data Model (SQLite), 🟡 §11 — Task Modes, ✅ §12 — Human Approval Workflow, 🟡 §13 — Failure Handling and Recovery, 🟡 §14 — Performance Tuning, ✅ §15 — Security Baseline, 🟡 §16 — End-to-End Validation Checklist, ✅ §18 — Minimal API Example (+18 more)

### Community 20 - "Character Profiles"
Cohesion: 0.40
Nodes (4): Character 1: Alex Chen, Character 2: Maya Rodriguez, Character 3: Dr. James Peterson, Character Profiles

### Community 21 - "11) Task Modes (Coding, Research, Analysis, Docs)"
Cohesion: 0.40
Nodes (5): 11.1 Coding Mode, 11.2 Research Mode, 11.3 Analysis Mode, 11.4 Documentation Mode, 11) Task Modes (Coding, Research, Analysis, Docs)

### Community 22 - "3) LLM Provider Setup (LM Studio or Ollama)"
Cohesion: 0.40
Nodes (5): 3.1 Option A: LM Studio Setup, 3.2 Option B: Ollama Setup, 3.3 Provider Switch Contract (Required), 3.4 Runtime Tuning Defaults, 3) LLM Provider Setup (LM Studio or Ollama)

### Community 23 - "Story Elements"
Cohesion: 0.15
Nodes (10): LLMConfig, Settings for connecting to LM Studio or Ollama., Path, LLMProviderRouter, LocalLLMClient, Any, Send a role-specific prompt to the LLM and return the parsed JSON response., Reports which LLM provider and endpoint is currently configured. (+2 more)

### Community 24 - "7) Tooling Policy (Do Not Skip)"
Cohesion: 0.50
Nodes (4): 7.1 Allowlist First, 7.2 Timeouts and Retries, 7.3 Audit Trail, 7) Tooling Policy (Do Not Skip)

### Community 25 - "Fox Character"
Cohesion: 0.18
Nodes (9): Any, Path, Dispatch a tool call by name and return its result dict.          Args:, Executes named tools on behalf of the agent.      Every tool call is:         1., List all custom Python tools in the custom_tools/ directory., Return True if this action type requires human approval before running., Return True if the command matches any blocked pattern (case-insensitive)., Resolve a path and verify it stays inside root_dir (path jail).          Raises: (+1 more)

### Community 26 - "8) MCP Integration Paths"
Cohesion: 0.67
Nodes (3): 8) MCP Integration Paths, Pattern A: Your Agent as MCP Client (Recommended), Pattern B: Another host runtime handles MCP; your code uses API only

### Community 27 - ".run"
Cohesion: 0.28
Nodes (5): Any, Ask the LLM what tool to call for this step, then call it.          Returns:, Ask the LLM if the execution result successfully fulfilled the step.          Re, Execute the full plan-execute-verify loop for a given goal.          Args:, Ask the LLM to break down the goal into a list of TaskSteps.          Includes a

### Community 28 - ".run_goal"
Cohesion: 0.33
Nodes (4): Any, Run a full goal through the plan-execute-verify loop.          Args:, Claim and execute one queued job from the database.          Called in a tight l, Find which MCP server exposes tool_name and call it.          Tries each registe

## Knowledge Gaps
- **72 isolated node(s):** `PRE_LOADED_MODELS`, `runsCache`, `1) What You Are Building`, `2) Final Architecture (Recommended)`, `3.1 Option A: LM Studio Setup` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentEngine` connect `test_agent.py` to `StateStore`, `agent.py`, `_ScriptedLLM`, `Path`, `Story Elements`, `Fox Character`, `.run_goal`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `StateStore` connect `StateStore` to `test_agent.py`, `agent.py`, `Path`, `Story Elements`, `Fox Character`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `MCPClientRegistry` connect `_ScriptedLLM` to `test_agent.py`, `agent.py`, `Path`, `Story Elements`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `AgentEngine` (e.g. with `AgentConfig` and `LLMProviderRouter`) actually correct?**
  _`AgentEngine` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `StateStore` (e.g. with `AgentEngine` and `TaskStep`) actually correct?**
  _`StateStore` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `PlannerExecutorVerifier` (e.g. with `AgentEngine` and `TaskStep`) actually correct?**
  _`PlannerExecutorVerifier` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Create and configure the FastAPI application.      All routes are defined inside`, `Load config if it exists, or create a default config.yaml and return it.`, `Parse CLI args, create the engine, and run in the appropriate mode.      Returns` to the rest of the system?**
  _132 weakly-connected nodes found - possible documentation gaps or missing edges._