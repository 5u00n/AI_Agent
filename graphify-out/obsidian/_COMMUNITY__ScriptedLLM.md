---
type: community
members: 17
---

# _ScriptedLLM

**Members:** 17 nodes

## Members
- [[.__del__()]] - code - agent/mcp_client.py
- [[.__init__()_3]] - code - agent/mcp_client.py
- [[._init_server_sync()]] - code - agent/mcp_client.py
- [[.call()]] - code - agent/mcp_client.py
- [[.list_servers()]] - code - agent/mcp_client.py
- [[.register()]] - code - agent/mcp_client.py
- [[Any_3]] - code
- [[Call a tool on a registered MCP server.          Args             server_name]] - rationale - agent/mcp_client.py
- [[Gracefully close all open MCP sessions when the registry is garbage-collected.]] - rationale - agent/mcp_client.py
- [[Initialize a stdio MCP session synchronously (blocks until connected).]] - rationale - agent/mcp_client.py
- [[MCPClientRegistry]] - code - agent/mcp_client.py
- [[Manages connections to one or more MCP servers.      Usage         registry = M]] - rationale - agent/mcp_client.py
- [[Register an MCP server definition. Does NOT connect immediately.]] - rationale - agent/mcp_client.py
- [[Return names of all registered MCP servers.]] - rationale - agent/mcp_client.py
- [[mcp_client.py]] - code - agent/mcp_client.py
- [[scratch.py]] - code - scratch.py
- [[test_mcp_registry_registers_server_and_reports_stub_call()]] - code - tests/test_agent.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/_ScriptedLLM
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_test_agent.py]]
- 3 edges to [[_COMMUNITY_agent.py]]
- 2 edges to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_Story Elements]]

## Top bridge nodes
- [[MCPClientRegistry]] - degree 16, connects to 4 communities
- [[mcp_client.py]] - degree 3, connects to 2 communities
- [[scratch.py]] - degree 2, connects to 1 community
- [[test_mcp_registry_registers_server_and_reports_stub_call()]] - degree 2, connects to 1 community