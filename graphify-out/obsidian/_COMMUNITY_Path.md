---
type: community
members: 28
---

# Path

**Members:** 28 nodes

## Members
- [[.__init__()_6]] - code - agent/test_lifecycle.py
- [[._generate_test_file()]] - code - agent/test_lifecycle.py
- [[._run_test_file()]] - code - agent/test_lifecycle.py
- [[._test_dir()]] - code - agent/test_lifecycle.py
- [[._verify_and_autocorrect()]] - code - agent/test_lifecycle.py
- [[.complete_step()]] - code - agent/engine.py
- [[.generate_verify_run_cleanup()]] - code - agent/test_lifecycle.py
- [[Captures the result of generating, running, and optionally fixing tests.  	Field]] - rationale - agent/models.py
- [[CompletedProcess]] - code
- [[Execute the test file using pytest or plain python, per config.]] - rationale - agent/test_lifecycle.py
- [[Final verdict for a step after the test gate has run.  	Fields 		status]] - rationale - agent/models.py
- [[Generate a pytest file that verifies the step's output.          If an LLM clien]] - rationale - agent/test_lifecycle.py
- [[Manages the full lifecycle of auto-generated tests for each step.      Handles]] - rationale - agent/test_lifecycle.py
- [[Path_4]] - code
- [[Represents a single step in the planner's multi-step plan.  	Fields 		step_id]] - rationale - agent/models.py
- [[Return (and create) the directory where test files are written.]] - rationale - agent/test_lifecycle.py
- [[Run the complete test lifecycle for one step.          Args             step]] - rationale - agent/test_lifecycle.py
- [[Run the test lifecycle for a completed step and return the verdict.          Arg]] - rationale - agent/engine.py
- [[StepCompletion]] - code - agent/models.py
- [[TaskStep]] - code - agent/models.py
- [[TestLifecycleManager]] - code - agent/test_lifecycle.py
- [[TestRunReport]] - code - agent/models.py
- [[Validate the test file and attempt to fix it if broken.          If an LLM is av]] - rationale - agent/test_lifecycle.py
- [[engine.py]] - code - agent/engine.py
- [[models.py]] - code - agent/models.py
- [[orchestrator.py]] - code - agent/orchestrator.py
- [[store.py]] - code - agent/store.py
- [[test_lifecycle.py]] - code - agent/test_lifecycle.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Path
SORT file.name ASC
```

## Connections to other communities
- 20 edges to [[_COMMUNITY_agent.py]]
- 18 edges to [[_COMMUNITY_test_agent.py]]
- 7 edges to [[_COMMUNITY_StateStore]]
- 4 edges to [[_COMMUNITY_Story Elements]]
- 3 edges to [[_COMMUNITY_.run]]
- 2 edges to [[_COMMUNITY__ScriptedLLM]]
- 1 edge to [[_COMMUNITY_Fox Character]]
- 1 edge to [[_COMMUNITY_.run_goal]]

## Top bridge nodes
- [[engine.py]] - degree 22, connects to 6 communities
- [[TaskStep]] - degree 24, connects to 5 communities
- [[TestLifecycleManager]] - degree 19, connects to 3 communities
- [[TestRunReport]] - degree 9, connects to 2 communities
- [[store.py]] - degree 9, connects to 2 communities