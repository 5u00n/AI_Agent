from pathlib import Path
import os
import sys

import pytest

from agent import (
    AgentConfig,
    AgentEngine,
    MCPClientRegistry,
    PlannerExecutorVerifier,
    ToolRegistry,
    TaskStep,
    TestLifecycleManager,
    create_ui_app,
    load_config,
    render_ui_html,
)


def _write_config(path: Path) -> Path:
    path.write_text(
        """
llm:
  provider: lmstudio
  base_url_lmstudio: http://127.0.0.1:1234/v1
  base_url_ollama: http://127.0.0.1:11434
  api_key_lmstudio: lm-studio
  api_key_ollama: ollama
  model_planner: planner-model
  model_executor: executor-model
  model_verifier: verifier-model
  transport: openai_compatible
budgets:
  max_steps: 5
  max_runtime_minutes: 10
  max_tool_calls: 20
safety:
  require_approval_for:
    - install
  blocked_commands:
    - sudo
  allowed_paths:
    - .
test_policy:
  enforce_task_test_gate: true
  auto_generate_tests: true
  verify_and_autocorrect_tests: true
  run_tests_before_completion: true
  delete_tests_after_task: true
  keep_tests_when_user_requests: true
  test_location_strategy: tests_temp
  max_test_fix_attempts: 2
  test_runner_by_mode:
    coding: pytest
ui:
  enabled: true
  host: 127.0.0.1
  port: 8000
  auth_mode: none
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def test_load_config_supports_provider_switch(tmp_path: Path) -> None:
    config_file = _write_config(tmp_path / "config.yaml")
    cfg = load_config(config_file)

    assert cfg.llm.provider == "lmstudio"
    assert cfg.llm.get_base_url() == "http://127.0.0.1:1234/v1"

    cfg.llm.provider = "ollama"
    assert cfg.llm.get_base_url() == "http://127.0.0.1:11434"


def test_test_lifecycle_deletes_generated_tests_by_default(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    manager = TestLifecycleManager(cfg, root_dir=tmp_path)

    step = TaskStep(step_id="s1", title="Add feature", mode="coding")
    report = manager.generate_verify_run_cleanup(step=step, keep_tests=False)

    assert report.passed is True
    assert report.generated_path is not None
    assert report.generated_path.exists() is False


def test_test_lifecycle_keeps_tests_when_requested(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    manager = TestLifecycleManager(cfg, root_dir=tmp_path)

    step = TaskStep(step_id="s2", title="Keep test", mode="coding")
    report = manager.generate_verify_run_cleanup(step=step, keep_tests=True)

    assert report.passed is True
    assert report.generated_path is not None
    assert report.generated_path.exists() is True


def test_engine_blocks_completion_if_test_gate_fails(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    step = TaskStep(step_id="s3", title="Broken", mode="coding")

    def bad_runner(*_args, **_kwargs):
        raise RuntimeError("simulated test failure")

    engine.test_manager._run_test_file = bad_runner  # type: ignore[attr-defined]

    result = engine.complete_step(step, keep_tests=False)
    assert result.status == "blocked"
    assert "test gate" in result.message.lower()


def test_tool_registry_enforces_allowlist_and_blocks_forbidden_command(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    cfg.safety.blocked_commands = ["rm -rf /", "sudo"]
    registry = ToolRegistry(cfg, root_dir=tmp_path)

    ok = registry.call("write_file", {"path": "note.txt", "content": "hello"})
    assert ok["ok"] is True

    denied = registry.call("run_shell", {"command": "sudo ls"})
    assert denied["ok"] is False
    assert "blocked" in denied["error"].lower()


def test_tool_registry_creates_pending_approval_for_sensitive_run_shell(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    cfg.safety.require_approval_for = ["run_shell"]
    engine = AgentEngine(cfg, root_dir=tmp_path)

    result = engine.tools.call("run_shell", {"command": "echo hello"}, run_id="run-1")

    assert result["ok"] is False
    assert result["requires_approval"] is True
    assert result["status"] == "pending_approval"
    assert result["approval_id"]

    pending = engine.store.list_approvals(status="pending")
    assert any(a["approval_id"] == result["approval_id"] for a in pending)


def test_tool_registry_executes_run_shell_when_not_requiring_approval(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    cfg.safety.require_approval_for = []
    engine = AgentEngine(cfg, root_dir=tmp_path)

    result = engine.tools.call("run_shell", {"command": "echo hello"})

    assert result["ok"] is True
    assert result["returncode"] == 0


def test_tool_registry_executes_run_shell_after_approval(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    cfg.safety.require_approval_for = ["run_shell"]
    engine = AgentEngine(cfg, root_dir=tmp_path)

    approval_id = engine.store.create_approval_request(
        action="run_shell",
        reason="Approve shell",
        payload_json='{"command":"echo ok"}',
        run_id="run-2",
    )
    engine.store.decide_approval(approval_id=approval_id, decision="approved", reviewer="user")

    result = engine.tools.call(
        "run_shell",
        {"command": "echo ok", "approval_id": approval_id},
        run_id="run-2",
    )
    assert result["ok"] is True
    assert result["returncode"] == 0


def test_tool_registry_rejects_run_shell_after_rejection(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    cfg.safety.require_approval_for = ["run_shell"]
    engine = AgentEngine(cfg, root_dir=tmp_path)

    approval_id = engine.store.create_approval_request(
        action="run_shell",
        reason="Reject shell",
        payload_json='{"command":"echo denied"}',
        run_id="run-3",
    )
    engine.store.decide_approval(approval_id=approval_id, decision="rejected", reviewer="user")

    result = engine.tools.call(
        "run_shell",
        {"command": "echo denied", "approval_id": approval_id},
        run_id="run-3",
    )
    assert result["ok"] is False
    assert result["status"] == "rejected_approval"


def test_planner_executor_verifier_loop_completes_with_stub_llm(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("Create hello.txt")

    assert result["status"] == "done"
    assert (tmp_path / "hello.txt").exists()


def test_mcp_registry_registers_server_and_reports_stub_call() -> None:
    mcp = MCPClientRegistry()
    mcp.register("filesystem", {"transport": "stdio", "command": "mcp-fs"})

    names = mcp.list_servers()
    assert "filesystem" in names

    result = mcp.call("filesystem", "read_file", {"path": "x"})
    assert result["ok"] is False
    assert "no such file or directory" in result["error"].lower() or "not found" in result["error"].lower()


def test_ui_root_page_exists(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    app = create_ui_app(engine)

    root_routes = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/" in root_routes


def test_render_ui_html_contains_run_builder_and_settings(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    html = render_ui_html(cfg)

    assert "AI Agent Chat" in html
    assert "Settings" in html
    assert "Test Policy" in html
    assert "mode" in html
    assert "goal" in html


def test_render_ui_html_reflects_default_provider_and_port(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    html = render_ui_html(cfg)

    assert 'value="lmstudio"' in html
    


def test_engine_persists_run_history_and_step_rows(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    out = engine.run_goal("Create history.txt", mode="coding", keep_tests=False)
    run_id = out["run_id"]

    runs = engine.store.list_runs(limit=10)
    assert any(r["run_id"] == run_id for r in runs)

    steps = engine.store.list_steps(run_id)
    assert len(steps) >= 1
    assert steps[0]["run_id"] == run_id


def test_ui_exposes_run_history_and_steps_endpoints(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    app = create_ui_app(engine)

    paths = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/runs" in paths
    assert "/runs/{run_id}/steps" in paths


def test_approval_lifecycle_roundtrip(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    approval_id = engine.store.create_approval_request(
        action="run_shell",
        reason="Needs user approval",
        payload_json='{"command":"echo hi"}',
        run_id=None,
    )

    pending = engine.store.list_approvals(status="pending")
    assert any(a["approval_id"] == approval_id for a in pending)

    engine.store.decide_approval(approval_id=approval_id, decision="approved", reviewer="user")
    approved = engine.store.list_approvals(status="approved")
    assert any(a["approval_id"] == approval_id for a in approved)


def test_ui_exposes_approval_endpoints(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    app = create_ui_app(engine)

    paths = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/approvals" in paths
    assert "/approvals/request" in paths
    assert "/approvals/{approval_id}/decision" in paths


class _ScriptedLLM:
    def __init__(self, responses):
        self.responses = list(responses)

    def complete_json(self, *_args, **_kwargs):
        if not self.responses:
            raise RuntimeError("no more scripted llm responses")
        return self.responses.pop(0)


def test_orchestrator_uses_llm_json_contracts(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    engine.llm_client = _ScriptedLLM(
        [
            {
                "steps": [
                    {"step_id": "step_1", "title": "Create llm_output.txt", "mode": "coding"},
                ]
            },
            {
                "action": "tool_call",
                "tool_name": "write_file",
                "tool_input": {"path": "llm_output.txt", "content": "hello from llm"},
            },
            {"ok": True, "reason": "tool result valid"},
        ]
    )

    result = engine.orchestrator.run("Create llm_output.txt")
    assert result["status"] == "done"
    assert (tmp_path / "llm_output.txt").exists()


def test_orchestrator_blocks_on_invalid_planner_contract(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    engine.llm_client = _ScriptedLLM([{"not_steps": []}])

    result = engine.orchestrator.run("Create invalid.txt")
    assert result["status"] == "blocked"
    assert "planner" in result["reason"].lower()


def test_task_aware_test_generation_for_create_file_step(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    manager = TestLifecycleManager(cfg, root_dir=tmp_path)
    step = TaskStep(
        step_id="s100",
        title="Create artifact.txt",
        mode="coding",
        expectations={"path": "artifact.txt", "content_contains": "created by agent"},
    )

    test_path = manager._generate_test_file(step)  # noqa: SLF001
    generated = test_path.read_text(encoding="utf-8")

    assert "artifact.txt" in generated
    assert "created by agent" in generated


def test_autonomous_job_queue_processes_enqueued_goal(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    job_id = engine.store.enqueue_job(goal="Create queued.txt", mode="coding", keep_tests=False)
    run_info = engine.process_next_job()

    assert run_info is not None
    assert run_info["result"]["status"] == "done"
    assert (tmp_path / "queued.txt").exists()

    job = engine.store.get_job(job_id)
    assert job is not None
    assert job["status"] == "done"


def test_mcp_registry_stdio_execution(tmp_path: Path) -> None:
    server_path = tmp_path / "fake_mcp_server.py"
    server_path.write_text(
        """
import json
import sys


def read_message():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def write_message(obj):
    sys.stdout.write(json.dumps(obj) + '\\n')
    sys.stdout.flush()


while True:
    try:
        req = read_message()
        if req is None:
            break
    except Exception:
        break
        
    method = req.get('method')
    if method == 'initialize':
        write_message({'jsonrpc': '2.0', 'id': req['id'], 'result': {'capabilities': {}, 'protocolVersion': '2024-11-05', 'serverInfo': {'name': 'fake', 'version': '1.0'}}})
    elif method == 'notifications/initialized':
        pass
    elif method == 'tools/call':
        params = req.get('params', {})
        write_message({
            'jsonrpc': '2.0', 
            'id': req['id'], 
            'result': {
                'content': [{'type': 'text', 'text': json.dumps({'echo': params})}],
                'isError': False
            }
        })
    elif method == 'tools/list':
        write_message({'jsonrpc': '2.0', 'id': req['id'], 'result': {'tools': [{'name': 'echoTool', 'description': 'echo', 'inputSchema': {'type': 'object', 'properties': {}}}]}})
    else:
        write_message({'jsonrpc': '2.0', 'id': req.get('id'), 'result': {'content': [], 'isError': False}})
""".strip()
        + "\n",
        encoding="utf-8",
    )

    mcp = MCPClientRegistry()
    mcp.register(
        "local",
        {"transport": "stdio", "command": sys.executable, "args": [str(server_path)]},
    )
    out = mcp.call("local", "echoTool", {"hello": "world"})

    assert out["ok"] is True
    assert "echoTool" in str(out)
