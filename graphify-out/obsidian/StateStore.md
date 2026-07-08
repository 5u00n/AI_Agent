---
source_file: "agent/store.py"
type: "code"
community: "StateStore"
location: "L38"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/StateStore
---

# StateStore

## Connections
- [[.__init__()]] - `calls` [EXTRACTED]
- [[.__init__()_5]] - `method` [EXTRACTED]
- [[.add_message()]] - `method` [EXTRACTED]
- [[.add_step()]] - `method` [EXTRACTED]
- [[.add_test_report()]] - `method` [EXTRACTED]
- [[.claim_next_job()]] - `method` [EXTRACTED]
- [[.create_approval_request()]] - `method` [EXTRACTED]
- [[.create_run()]] - `method` [EXTRACTED]
- [[.decide_approval()]] - `method` [EXTRACTED]
- [[.delete_run()]] - `method` [EXTRACTED]
- [[.enqueue_job()]] - `method` [EXTRACTED]
- [[.finish_job()]] - `method` [EXTRACTED]
- [[.get_approval_status()]] - `method` [EXTRACTED]
- [[.get_job()]] - `method` [EXTRACTED]
- [[.get_run_status()]] - `method` [EXTRACTED]
- [[.latest_test_path_for_run()]] - `method` [EXTRACTED]
- [[.list_approvals()]] - `method` [EXTRACTED]
- [[.list_jobs()]] - `method` [EXTRACTED]
- [[.list_messages()]] - `method` [EXTRACTED]
- [[.list_runs()]] - `method` [EXTRACTED]
- [[.list_steps()]] - `method` [EXTRACTED]
- [[.set_run_status()]] - `method` [EXTRACTED]
- [[AgentEngine]] - `uses` [INFERRED]
- [[SQLite-backed persistence for ALL agent state.  	Every public method opens its o]] - `rationale_for` [EXTRACTED]
- [[TaskStep]] - `uses` [INFERRED]
- [[TestRunReport]] - `uses` [INFERRED]
- [[ToolRegistry]] - `uses` [INFERRED]
- [[__init__.py]] - `imports` [EXTRACTED]
- [[engine.py]] - `imports` [EXTRACTED]
- [[store.py]] - `contains` [EXTRACTED]
- [[tools.py]] - `imports` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/StateStore