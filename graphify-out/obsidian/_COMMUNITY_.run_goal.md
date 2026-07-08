---
type: community
members: 7
---

# .run_goal

**Members:** 7 nodes

## Members
- [[.call_mcp_tool()]] - code - agent/engine.py
- [[.process_next_job()]] - code - agent/engine.py
- [[.run_goal()]] - code - agent/engine.py
- [[Any_1]] - code
- [[Claim and execute one queued job from the database.          Called in a tight l]] - rationale - agent/engine.py
- [[Find which MCP server exposes tool_name and call it.          Tries each registe]] - rationale - agent/engine.py
- [[Run a full goal through the plan-execute-verify loop.          Args]] - rationale - agent/engine.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/run_goal
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_test_agent.py]]
- 1 edge to [[_COMMUNITY_Path]]

## Top bridge nodes
- [[.run_goal()]] - degree 5, connects to 2 communities
- [[.process_next_job()]] - degree 4, connects to 1 community
- [[.call_mcp_tool()]] - degree 3, connects to 1 community