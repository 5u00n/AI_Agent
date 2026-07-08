---
type: community
members: 32
---

# StateStore

**Members:** 32 nodes

## Members
- [[.__init__()_5]] - code - agent/store.py
- [[.add_message()]] - code - agent/store.py
- [[.add_step()]] - code - agent/store.py
- [[.add_test_report()]] - code - agent/store.py
- [[.claim_next_job()]] - code - agent/store.py
- [[.create_approval_request()]] - code - agent/store.py
- [[.create_run()]] - code - agent/store.py
- [[.decide_approval()]] - code - agent/store.py
- [[.delete_run()]] - code - agent/store.py
- [[.enqueue_job()]] - code - agent/store.py
- [[.finish_job()]] - code - agent/store.py
- [[.get_approval_status()]] - code - agent/store.py
- [[.get_job()]] - code - agent/store.py
- [[.get_run_status()]] - code - agent/store.py
- [[.latest_test_path_for_run()]] - code - agent/store.py
- [[.list_approvals()]] - code - agent/store.py
- [[.list_jobs()]] - code - agent/store.py
- [[.list_messages()]] - code - agent/store.py
- [[.list_runs()]] - code - agent/store.py
- [[.list_steps()]] - code - agent/store.py
- [[.set_run_status()]] - code - agent/store.py
- [[Add a goal to the background job queue.]] - rationale - agent/store.py
- [[Any_5]] - code
- [[Atomically claim the oldest queued job for processing.]] - rationale - agent/store.py
- [[Create a new run (or re-activate a stopped one).]] - rationale - agent/store.py
- [[Create all tables if they don't exist yet.]] - rationale - agent/store.py
- [[Delete a run and ALL associated data (steps, tests, approvals, messages).]] - rationale - agent/store.py
- [[Path_3]] - code
- [[Return the current UTC time as an ISO-8601 string.  	Used everywhere a timestamp]] - rationale - agent/utils.py
- [[SQLite-backed persistence for ALL agent state.  	Every public method opens its o]] - rationale - agent/store.py
- [[StateStore]] - code - agent/store.py
- [[_utc_now()]] - code - agent/utils.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/StateStore
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Path]]
- 6 edges to [[_COMMUNITY_agent.py]]
- 1 edge to [[_COMMUNITY_test_agent.py]]
- 1 edge to [[_COMMUNITY_Story Elements]]
- 1 edge to [[_COMMUNITY_Fox Character]]

## Top bridge nodes
- [[StateStore]] - degree 31, connects to 5 communities
- [[_utc_now()]] - degree 16, connects to 2 communities
- [[.add_step()]] - degree 3, connects to 1 community
- [[.add_test_report()]] - degree 3, connects to 1 community