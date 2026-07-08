---
source_file: "agent/models.py"
type: "code"
community: "Path"
location: "L28"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Path
---

# TaskStep

## Connections
- [[._execute()]] - `references` [EXTRACTED]
- [[._generate_test_file()]] - `references` [EXTRACTED]
- [[._plan()]] - `references` [EXTRACTED]
- [[._verify()]] - `references` [EXTRACTED]
- [[.add_step()]] - `references` [EXTRACTED]
- [[.complete_step()]] - `references` [EXTRACTED]
- [[.generate_verify_run_cleanup()]] - `references` [EXTRACTED]
- [[.run_goal()]] - `calls` [EXTRACTED]
- [[AgentEngine]] - `uses` [INFERRED]
- [[PlannerExecutorVerifier]] - `uses` [INFERRED]
- [[Represents a single step in the planner's multi-step plan.  	Fields 		step_id]] - `rationale_for` [EXTRACTED]
- [[StateStore]] - `uses` [INFERRED]
- [[TestLifecycleManager]] - `uses` [INFERRED]
- [[__init__.py]] - `imports` [EXTRACTED]
- [[engine.py]] - `imports` [EXTRACTED]
- [[models.py]] - `contains` [EXTRACTED]
- [[orchestrator.py]] - `imports` [EXTRACTED]
- [[store.py]] - `imports` [EXTRACTED]
- [[test_agent.py]] - `imports` [EXTRACTED]
- [[test_engine_blocks_completion_if_test_gate_fails()]] - `calls` [EXTRACTED]
- [[test_lifecycle.py]] - `imports` [EXTRACTED]
- [[test_task_aware_test_generation_for_create_file_step()]] - `calls` [EXTRACTED]
- [[test_test_lifecycle_deletes_generated_tests_by_default()]] - `calls` [EXTRACTED]
- [[test_test_lifecycle_keeps_tests_when_requested()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Path