---
type: community
members: 9
---

# .run

**Members:** 9 nodes

## Members
- [[._execute()]] - code - agent/orchestrator.py
- [[._plan()]] - code - agent/orchestrator.py
- [[._verify()]] - code - agent/orchestrator.py
- [[.run()]] - code - agent/orchestrator.py
- [[Any_4]] - code
- [[Ask the LLM if the execution result successfully fulfilled the step.          Re]] - rationale - agent/orchestrator.py
- [[Ask the LLM to break down the goal into a list of TaskSteps.          Includes a]] - rationale - agent/orchestrator.py
- [[Ask the LLM what tool to call for this step, then call it.          Returns]] - rationale - agent/orchestrator.py
- [[Execute the full plan-execute-verify loop for a given goal.          Args]] - rationale - agent/orchestrator.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/run
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_test_agent.py]]
- 3 edges to [[_COMMUNITY_Path]]

## Top bridge nodes
- [[._execute()]] - degree 5, connects to 2 communities
- [[._verify()]] - degree 5, connects to 2 communities
- [[._plan()]] - degree 4, connects to 2 communities
- [[.run()]] - degree 6, connects to 1 community