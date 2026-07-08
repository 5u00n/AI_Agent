# Graph Report - AI_Agent  (2026-07-08)

## Corpus Check
- 24 files · ~18,406 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 260 nodes · 543 edges · 27 communities (24 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.5)
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

## God Nodes (most connected - your core abstractions)
1. `AgentEngine` - 40 edges
2. `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` - 28 edges
3. `StateStore` - 24 edges
4. `PlannerExecutorVerifier` - 20 edges
5. `load_config()` - 15 edges
6. `TaskStep` - 15 edges
7. `AgentConfig` - 14 edges
8. `MCPClientRegistry` - 13 edges
9. `TestLifecycleManager` - 13 edges
10. `_ScriptedLLM` - 12 edges

## Surprising Connections (you probably didn't know these)
- `_ScriptedLLM` --uses--> `TaskStep`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `MCPClientRegistry`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `PlannerExecutorVerifier`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `AgentEngine`  [INFERRED]
  tests/test_agent.py → agent.py
- `_ScriptedLLM` --uses--> `AgentConfig`  [INFERRED]
  tests/test_agent.py → agent.py

## Import Cycles
- None detected.

## Communities (27 total, 3 thin omitted)

### Community 0 - "StateStore"
Cohesion: 0.15
Nodes (5): main(), StateStore, TaskStep, _utc_now(), Any

### Community 1 - "test_agent.py"
Cohesion: 0.14
Nodes (43): AgentEngine, create_ui_app(), PlannerExecutorVerifier, render_ui_html(), test(), Path, test_additional_native_tools(), test_approval_lifecycle_roundtrip() (+35 more)

### Community 2 - "LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan"
Cohesion: 0.08
Nodes (23): 10) Data Model (SQLite), 12) Human Approval Workflow, 13) Failure Handling and Recovery, 14) Performance and Stability Tuning, 15) Security Baseline, 16) End-to-End Validation Checklist, 17) 7-Day Implementation Plan, 18) Minimal API Example (Provider-Selectable Client) (+15 more)

### Community 3 - "agent.py"
Cohesion: 0.11
Nodes (20): AgentConfig, BudgetConfig, _build_dataclass(), ensure_default_config(), get_remembered_working_dir(), load_config(), MCPConfig, MCPServerConfig (+12 more)

### Community 4 - "_ScriptedLLM"
Cohesion: 0.15
Nodes (5): LLMConfig, LLMProviderRouter, LocalLLMClient, MCPClientRegistry, test_mcp_registry_registers_server_and_reports_stub_call()

### Community 5 - "Path"
Cohesion: 0.29
Nodes (6): Chapter 1: The Discovery, Chapter 2: Into the Unknown, Chapter 3: The Challenge, Chapter 4: The Resolution, Epilogue, The Enchanted Forest Adventure

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
Cohesion: 0.29
Nodes (6): Creative Story Outline, Genre, Main Characters, Plot Points, Setting, Themes

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
Cohesion: 0.40
Nodes (4): Characters, Plot, Setting, Story Elements

### Community 24 - "7) Tooling Policy (Do Not Skip)"
Cohesion: 0.50
Nodes (4): 7.1 Allowlist First, 7.2 Timeouts and Retries, 7.3 Audit Trail, 7) Tooling Policy (Do Not Skip)

### Community 26 - "8) MCP Integration Paths"
Cohesion: 0.67
Nodes (3): 8) MCP Integration Paths, Pattern A: Your Agent as MCP Client (Recommended), Pattern B: Another host runtime handles MCP; your code uses API only

## Knowledge Gaps
- **62 isolated node(s):** `PRE_LOADED_MODELS`, `runsCache`, `1) What You Are Building`, `2) Final Architecture (Recommended)`, `3.1 Option A: LM Studio Setup` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentEngine` connect `test_agent.py` to `StateStore`, `agent.py`, `_ScriptedLLM`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `StateStore` connect `StateStore` to `agent.py`, `_ScriptedLLM`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` connect `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` to `25) Skill Accumulation and New Skill Creation (Required)`, `11) Task Modes (Coding, Research, Analysis, Docs)`, `3) LLM Provider Setup (LM Studio or Ollama)`, `7) Tooling Policy (Do Not Skip)`, `8) MCP Integration Paths`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **What connects `PRE_LOADED_MODELS`, `runsCache`, `Test that the project structure is properly initialized` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `StateStore` be split into smaller, more focused modules?**
  _Cohesion score 0.14623655913978495 - nodes in this community are weakly interconnected._
- **Should `test_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14361702127659576 - nodes in this community are weakly interconnected._
- **Should `LM Studio or Ollama + Local Agent + MCP + UI: Foolproof Implementation Plan` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._