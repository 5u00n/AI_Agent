---
source_file: "agent/engine.py"
type: "code"
community: "test_agent.py"
location: "L50"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/test_agentpy
---

# AgentEngine

## Connections
- [[.__init__()]] - `method` [EXTRACTED]
- [[.call_mcp_tool()]] - `method` [EXTRACTED]
- [[.complete_step()]] - `method` [EXTRACTED]
- [[.process_next_job()]] - `method` [EXTRACTED]
- [[.run_goal()]] - `method` [EXTRACTED]
- [[AgentConfig]] - `uses` [INFERRED]
- [[LLMProviderRouter]] - `uses` [INFERRED]
- [[LocalLLMClient]] - `uses` [INFERRED]
- [[MCPClientRegistry]] - `uses` [INFERRED]
- [[PlannerExecutorVerifier]] - `uses` [INFERRED]
- [[StateStore]] - `uses` [INFERRED]
- [[StepCompletion]] - `uses` [INFERRED]
- [[TaskStep]] - `uses` [INFERRED]
- [[TestLifecycleManager]] - `uses` [INFERRED]
- [[The top-level orchestrator that wires together all agent subsystems.      Create]] - `rationale_for` [EXTRACTED]
- [[ToolRegistry]] - `uses` [INFERRED]
- [[__init__.py]] - `imports` [EXTRACTED]
- [[api.py]] - `imports` [EXTRACTED]
- [[cli.py]] - `imports` [EXTRACTED]
- [[create_ui_app()]] - `references` [EXTRACTED]
- [[engine.py]] - `contains` [EXTRACTED]
- [[llm_client.py]] - `imports` [EXTRACTED]
- [[main()]] - `calls` [EXTRACTED]
- [[orchestrator.py]] - `imports` [EXTRACTED]
- [[run_inner_test.py]] - `imports` [EXTRACTED]
- [[test()]] - `calls` [EXTRACTED]
- [[test_additional_native_tools()]] - `calls` [EXTRACTED]
- [[test_agent.py]] - `imports` [EXTRACTED]
- [[test_approval_lifecycle_roundtrip()]] - `calls` [EXTRACTED]
- [[test_autonomous_job_queue_processes_enqueued_goal()]] - `calls` [EXTRACTED]
- [[test_birds_slider_page()]] - `calls` [EXTRACTED]
- [[test_delete_run()]] - `calls` [EXTRACTED]
- [[test_dynamic_tool_registration()]] - `calls` [EXTRACTED]
- [[test_engine_blocks_completion_if_test_gate_fails()]] - `calls` [EXTRACTED]
- [[test_engine_persists_run_history_and_step_rows()]] - `calls` [EXTRACTED]
- [[test_fox_rabbit_story()]] - `calls` [EXTRACTED]
- [[test_hello_chat()]] - `calls` [EXTRACTED]
- [[test_llm_connection_failure()]] - `calls` [EXTRACTED]
- [[test_orchestrator_blocks_on_invalid_planner_contract()]] - `calls` [EXTRACTED]
- [[test_orchestrator_uses_llm_json_contracts()]] - `calls` [EXTRACTED]
- [[test_planner_executor_verifier_loop_completes_with_stub_llm()]] - `calls` [EXTRACTED]
- [[test_research_goal()]] - `calls` [EXTRACTED]
- [[test_research_mammal()]] - `calls` [EXTRACTED]
- [[test_skills_listing()]] - `calls` [EXTRACTED]
- [[test_stop_run()]] - `calls` [EXTRACTED]
- [[test_tool_registry_creates_pending_approval_for_sensitive_run_shell()]] - `calls` [EXTRACTED]
- [[test_tool_registry_executes_run_shell_after_approval()]] - `calls` [EXTRACTED]
- [[test_tool_registry_executes_run_shell_when_not_requiring_approval()]] - `calls` [EXTRACTED]
- [[test_tool_registry_rejects_run_shell_after_rejection()]] - `calls` [EXTRACTED]
- [[test_ui.py]] - `imports` [EXTRACTED]
- [[test_ui_endpoints()]] - `calls` [EXTRACTED]
- [[test_ui_exposes_approval_endpoints()]] - `calls` [EXTRACTED]
- [[test_ui_exposes_run_history_and_steps_endpoints()]] - `calls` [EXTRACTED]
- [[test_ui_root_page_exists()]] - `calls` [EXTRACTED]
- [[test_update_run_goal()]] - `calls` [EXTRACTED]
- [[test_workspace_tools()]] - `calls` [EXTRACTED]
- [[test_write_birds_and_animals_html_page()]] - `calls` [EXTRACTED]
- [[test_write_content_goal()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/test_agentpy