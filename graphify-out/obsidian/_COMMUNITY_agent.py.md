---
type: community
members: 47
---

# agent.py

**Members:** 47 nodes

## Members
- [[NOTE get_remembered_working_dir and save_remembered_working_dir are looked up]] - rationale - agent/tools.py
- [[.to_dict()]] - code - agent/config.py
- [[Actions that need human approval and commands that are blocked.]] - rationale - agent/config.py
- [[AgentConfig]] - code - agent/config.py
- [[Any]] - code
- [[BudgetConfig]] - code - agent/config.py
- [[Collection of all MCP server registrations.]] - rationale - agent/config.py
- [[Controls the mandatory test lifecycle for every completed step.]] - rationale - agent/config.py
- [[Create and configure the FastAPI application.      All routes are defined inside]] - rationale - agent/api.py
- [[Hard caps to prevent runaway agent loops.]] - rationale - agent/config.py
- [[Load agent config from a YAML file. Returns defaults if file missing.]] - rationale - agent/config.py
- [[Load config if it exists, or create a default config.yaml and return it.]] - rationale - agent/cli.py
- [[Load the previously saved working directory, or None if not set.]] - rationale - agent/utils.py
- [[MCPConfig]] - code - agent/config.py
- [[MCPServerConfig]] - code - agent/config.py
- [[Master config that aggregates all sub-configs.]] - rationale - agent/config.py
- [[One registered MCP server (stdio transport by default).]] - rationale - agent/config.py
- [[Parse CLI args, create the engine, and run in the appropriate mode.      Returns]] - rationale - agent/cli.py
- [[Path]] - code
- [[Path_1]] - code
- [[Path_6]] - code
- [[Path_8]] - code
- [[Persist agent config to a YAML file.]] - rationale - agent/config.py
- [[Persist the given path as the working directory for future sessions.]] - rationale - agent/utils.py
- [[Safely instantiate a dataclass from a (possibly None) dict of values.]] - rationale - agent/config.py
- [[SafetyConfig]] - code - agent/config.py
- [[TestPolicyConfig]] - code - agent/config.py
- [[UIConfig]] - code - agent/config.py
- [[__init__.py]] - code - agent/__init__.py
- [[_build_dataclass()]] - code - agent/config.py
- [[agent.py]] - code - agent.py
- [[api.py]] - code - agent/api.py
- [[cli.py]] - code - agent/cli.py
- [[config.py]] - code - agent/config.py
- [[create_ui_app()]] - code - agent/api.py
- [[ensure_default_config()]] - code - agent/cli.py
- [[get_remembered_working_dir()]] - code - agent/utils.py
- [[load_config()]] - code - agent/config.py
- [[main()]] - code - agent/cli.py
- [[render_ui_html()]] - code - agent/ui.py
- [[save_config()]] - code - agent/config.py
- [[save_remembered_working_dir()]] - code - agent/utils.py
- [[test_ui.py]] - code - tests/test_ui.py
- [[test_ui_endpoints()]] - code - tests/test_ui.py
- [[tools.py]] - code - agent/tools.py
- [[ui.py]] - code - agent/ui.py
- [[utils.py]] - code - agent/utils.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/agentpy
SORT file.name ASC
```

## Connections to other communities
- 27 edges to [[_COMMUNITY_test_agent.py]]
- 20 edges to [[_COMMUNITY_Path]]
- 8 edges to [[_COMMUNITY_Story Elements]]
- 6 edges to [[_COMMUNITY_StateStore]]
- 4 edges to [[_COMMUNITY_Fox Character]]
- 3 edges to [[_COMMUNITY__ScriptedLLM]]

## Top bridge nodes
- [[__init__.py]] - degree 41, connects to 6 communities
- [[AgentConfig]] - degree 23, connects to 4 communities
- [[api.py]] - degree 11, connects to 3 communities
- [[tools.py]] - degree 8, connects to 3 communities
- [[config.py]] - degree 19, connects to 2 communities