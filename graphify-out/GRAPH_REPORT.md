# Graph Report - AI_Agent  (2026-07-07)

## Corpus Check
- 19 files · ~14,356 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 217 nodes · 445 edges · 20 communities (17 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

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

## God Nodes (most connected - your core abstractions)
1. `AgentEngine` - 28 edges
2. `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` - 28 edges
3. `StateStore` - 20 edges
4. `load_config()` - 15 edges
5. `TaskStep` - 15 edges
6. `AgentConfig` - 14 edges
7. `MCPClientRegistry` - 13 edges
8. `TestLifecycleManager` - 13 edges
9. `PlannerExecutorVerifier` - 12 edges
10. `_ScriptedLLM` - 12 edges

## Surprising Connections (you probably didn't know these)
- `_ScriptedLLM` --uses--> `AgentConfig`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `TaskStep`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `ToolRegistry`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `MCPClientRegistry`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `PlannerExecutorVerifier`  [INFERRED]
  tests/test_agent.py → agent.py

## Import Cycles
- None detected.

## Communities (20 total, 3 thin omitted)

### Community 0 - "StateStore"
Cohesion: 0.13
Nodes (5): main(), StateStore, ToolRegistry, _utc_now(), Any

### Community 1 - "test_agent.py"
Cohesion: 0.17
Nodes (31): AgentEngine, create_ui_app(), render_ui_html(), test(), Path, _ScriptedLLM, test_approval_lifecycle_roundtrip(), test_autonomous_job_queue_processes_enqueued_goal() (+23 more)

### Community 2 - "LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan"
Cohesion: 0.05
Nodes (40): 10) Data Model (SQLite), 11.1 Coding Mode, 11.2 Research Mode, 11.3 Analysis Mode, 11.4 Documentation Mode, 11) Task Modes (Coding, Research, Analysis, Docs), 12) Human Approval Workflow, 13) Failure Handling and Recovery (+32 more)

### Community 3 - "agent.py"
Cohesion: 0.16
Nodes (14): AgentConfig, BudgetConfig, _build_dataclass(), ensure_default_config(), LLMConfig, LLMProviderRouter, load_config(), MCPConfig (+6 more)

### Community 5 - "Path"
Cohesion: 0.19
Nodes (7): LocalLLMClient, PlannerExecutorVerifier, Path, TaskStep, TestLifecycleManager, TestRunReport, CompletedProcess

### Community 6 - "25) Skill Accumulation and New Skill Creation (Required)"
Cohesion: 0.22
Nodes (9): 25.1 What a Skill Is, 25.2 Skill Storage Model, 25.3 Learning Pipeline, 25.4 New Skill Creation Modes, 25.5 Skill Gating Rules (Critical), 25.6 Skill Selection at Runtime, 25.7 UI for Skill Lifecycle, 25.8 Anti-Corruption Rules (+1 more)

### Community 7 - "11) Task Modes (Coding, Research, Analysis, Docs)"
Cohesion: 0.17
Nodes (10): fetchStepsForRun(), PRE_LOADED_MODELS, refreshChat(), renderRunToChat(), renderSessionsSidebar(), runsCache, saveLLMSettings(), selectSession() (+2 more)

### Community 9 - "7) Tooling Policy (Do Not Skip)"
Cohesion: 0.40
Nodes (4): Test that main.py contains expected content, Test that the project structure is properly initialized, test_main_file_content(), test_project_structure_created()

## Knowledge Gaps
- **45 isolated node(s):** `PRE_LOADED_MODELS`, `runsCache`, `1) What You Are Building`, `2) Final Architecture (Recommended)`, `3.1 Option A: LM Studio Setup` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` connect `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` to `25) Skill Accumulation and New Skill Creation (Required)`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `StateStore` connect `StateStore` to `agent.py`, `_ScriptedLLM`, `Path`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `AgentEngine` connect `test_agent.py` to `StateStore`, `agent.py`, `_ScriptedLLM`, `Path`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **What connects `PRE_LOADED_MODELS`, `runsCache`, `Test that the project structure is properly initialized` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `StateStore` be split into smaller, more focused modules?**
  _Cohesion score 0.13227513227513227 - nodes in this community are weakly interconnected._
- **Should `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` be split into smaller, more focused modules?**
  _Cohesion score 0.04878048780487805 - nodes in this community are weakly interconnected._