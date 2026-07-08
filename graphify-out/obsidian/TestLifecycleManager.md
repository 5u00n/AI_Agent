---
source_file: "agent/test_lifecycle.py"
type: "code"
community: "Path"
location: "L39"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Path
---

# TestLifecycleManager

## Connections
- [[.__init__()]] - `calls` [EXTRACTED]
- [[.__init__()_6]] - `method` [EXTRACTED]
- [[._generate_test_file()]] - `method` [EXTRACTED]
- [[._run_test_file()]] - `method` [EXTRACTED]
- [[._test_dir()]] - `method` [EXTRACTED]
- [[._verify_and_autocorrect()]] - `method` [EXTRACTED]
- [[.generate_verify_run_cleanup()]] - `method` [EXTRACTED]
- [[AgentConfig]] - `uses` [INFERRED]
- [[AgentEngine]] - `uses` [INFERRED]
- [[Manages the full lifecycle of auto-generated tests for each step.      Handles]] - `rationale_for` [EXTRACTED]
- [[TaskStep]] - `uses` [INFERRED]
- [[TestRunReport]] - `uses` [INFERRED]
- [[__init__.py]] - `imports` [EXTRACTED]
- [[engine.py]] - `imports` [EXTRACTED]
- [[test_agent.py]] - `imports` [EXTRACTED]
- [[test_lifecycle.py]] - `contains` [EXTRACTED]
- [[test_task_aware_test_generation_for_create_file_step()]] - `calls` [EXTRACTED]
- [[test_test_lifecycle_deletes_generated_tests_by_default()]] - `calls` [EXTRACTED]
- [[test_test_lifecycle_keeps_tests_when_requested()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Path