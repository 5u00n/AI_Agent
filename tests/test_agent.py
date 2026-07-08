from pathlib import Path
import os
import sys
import sqlite3

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


def test_write_birds_and_animals_html_page(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("write a beautiful html page about birds and animals")

    assert result["status"] == "done"
    assert (tmp_path / "birds_animals.html").exists()
    content = (tmp_path / "birds_animals.html").read_text(encoding="utf-8")
    assert "Birds and Animals" in content


def test_workspace_tools(tmp_path: Path, monkeypatch) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    # 1. Test set_working_directory
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    
    remembered_path = []
    def mock_save(path):
        remembered_path.append(path)
    def mock_get():
        return remembered_path[-1] if remembered_path else None

    monkeypatch.setattr("agent.save_remembered_working_dir", mock_save)
    monkeypatch.setattr("agent.get_remembered_working_dir", mock_get)

    res = engine.tools.call("set_working_directory", {"path": str(subdir)})
    assert res["ok"] is True
    assert mock_get() == subdir
    assert engine.tools.root_dir == subdir

    # 2. Test create_file_or_folder inside working directory
    res2 = engine.tools.call("create_file_or_folder", {"path": "test.txt", "is_folder": False, "content": "hello workspace"})
    assert res2["ok"] is True
    assert (subdir / "test.txt").exists()
    assert (subdir / "test.txt").read_text() == "hello workspace"

    # 3. Test create_file_or_folder with folders
    res3 = engine.tools.call("create_file_or_folder", {"path": "nested_dir", "is_folder": True})
    assert res3["ok"] is True
    assert (subdir / "nested_dir").is_dir()

    # 4. Test when no working directory is selected and it falls back to cwd
    monkeypatch.setattr("agent.get_remembered_working_dir", lambda: None)
    res4 = engine.tools.call("create_file_or_folder", {"path": "fallback.txt", "is_folder": False, "content": "hello fallback"})
    assert res4["ok"] is True
    assert (Path.cwd() / "fallback.txt").exists()
    
    # Cleanup fallback file
    if (Path.cwd() / "fallback.txt").exists():
        (Path.cwd() / "fallback.txt").unlink()


def test_research_goal(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("Research deep learning history")

    assert result["status"] == "done"
    assert (tmp_path / "deep_learning_research.txt").exists()
    content = (tmp_path / "deep_learning_research.txt").read_text(encoding="utf-8")
    assert "McCulloch-Pitts" in content


def test_write_content_goal(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("Write a blog post about artificial intelligence in education")

    assert result["status"] == "done"
    assert (tmp_path / "ai_education_blog.md").exists()
    content = (tmp_path / "ai_education_blog.md").read_text(encoding="utf-8")
    assert "personalizing learning" in content


def test_additional_native_tools(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    # 1. Test copy_file
    src = tmp_path / "source.txt"
    src.write_text("hello copy", encoding="utf-8")
    res = engine.tools.call("copy_file", {"src": "source.txt", "dest": "dest.txt"})
    assert res["ok"] is True
    assert (tmp_path / "dest.txt").exists()
    assert (tmp_path / "dest.txt").read_text(encoding="utf-8") == "hello copy"

    # 2. Test edit_file
    res2 = engine.tools.call("edit_file", {"path": "dest.txt", "content": "updated hello"})
    assert res2["ok"] is True
    assert (tmp_path / "dest.txt").read_text(encoding="utf-8") == "updated hello"

    # 3. Test rename_file
    res3 = engine.tools.call("rename_file", {"src": "dest.txt", "dest": "renamed.txt"})
    assert res3["ok"] is True
    assert not (tmp_path / "dest.txt").exists()
    assert (tmp_path / "renamed.txt").exists()
    assert (tmp_path / "renamed.txt").read_text(encoding="utf-8") == "updated hello"

    # 4. Test view_page
    res4 = engine.tools.call("view_page", {"path": "renamed.txt"})
    assert res4["ok"] is True
    assert "http://127.0.0.1:8000/workspace/renamed.txt" in res4["url"]


def test_delete_run(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    
    run_id = engine.store.create_run("delete test run")
    engine.store.add_message(run_id, "user", "delete test run")
    
    # Verify it exists
    runs = engine.store.list_runs()
    assert any(r["run_id"] == run_id for r in runs)
    
    # Delete it
    engine.store.delete_run(run_id)
    
    # Verify it is gone
    runs_after = engine.store.list_runs()
    assert not any(r["run_id"] == run_id for r in runs_after)


def test_fox_rabbit_story(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("write a story of a fox and rabbit")

    assert result["status"] == "done"
    assert (tmp_path / "fox_rabbit_story.txt").exists()
    content = (tmp_path / "fox_rabbit_story.txt").read_text(encoding="utf-8")
    assert "fox" in content and "rabbit" in content


def test_hello_chat(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'openai_compatible'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("hi, how are you")

    assert result["status"] == "done"
    assert "doing well" in result["reason"]


def test_research_mammal(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("research on largest mammal")

    assert result["status"] == "done"
    assert (tmp_path / "mammal_research.txt").exists()
    content = (tmp_path / "mammal_research.txt").read_text(encoding="utf-8")
    assert "blue whale" in content


def test_birds_slider_page(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("make beautiful web page for most beautiful birds in the world , make the website with slider")

    assert result["status"] == "done"
    assert (tmp_path / "birds_slider.html").exists()
    content = (tmp_path / "birds_slider.html").read_text(encoding="utf-8")
    assert "Most Beautiful Birds" in content and "slider" in content


def test_stop_run(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    run_id = engine.store.create_run("cancelled task", status="running")
    engine.store.set_run_status(run_id, "stopped")

    result = loop.run("cancelled task", run_id=run_id)
    assert result["status"] == "blocked"
    assert "stopped" in result["reason"].lower()


def test_update_run_goal(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    
    run_id = engine.store.create_run("old goal")
    engine.store.add_message(run_id, "user", "old goal")
    
    with sqlite3.connect(engine.store.db_path) as conn:
        conn.execute("UPDATE runs SET goal = ? WHERE run_id = ?", ("new goal", run_id))
        conn.execute("UPDATE messages SET content = ? WHERE run_id = ?", ("new goal", run_id))
    
    runs = engine.store.list_runs()
    assert any(r["run_id"] == run_id and r["goal"] == "new goal" for r in runs)


def test_dynamic_tool_registration(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    tools_dir = tmp_path / "custom_tools"
    tools_dir.mkdir(exist_ok=True)
    tool_code = """
def run(args: dict) -> dict:
    n = int(args.get("n", 0))
    return {"ok": True, "result": n * 10}
"""
    (tools_dir / "multiply_ten.py").write_text(tool_code, encoding="utf-8")

    assert engine.tools.get_custom_tool_names() == ["multiply_ten"]

    res = engine.tools.call("multiply_ten", {"n": 8})
    assert res["ok"] is True
    assert res["result"] == 80


def test_skills_listing(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)

    skills_dir = tmp_path / ".agents" / "skills" / "translator"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_md = """---
name: Spanish Translator
description: Expert Spanish translator
---
# Instructions
Always translate inputs to Spanish.
"""
    (skills_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    skills = []
    skills_root = tmp_path / ".agents" / "skills"
    if skills_root.exists():
        for p in skills_root.iterdir():
            if p.is_dir() and (p / "SKILL.md").exists():
                content = (p / "SKILL.md").read_text(encoding="utf-8")
                name = p.name
                desc = ""
                for line in content.splitlines():
                    if line.strip().startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.strip().startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                skills.append({"name": name, "description": desc, "folder": p.name})

    assert len(skills) == 1
    assert skills[0]["name"] == "Spanish Translator"
    assert skills[0]["description"] == "Expert Spanish translator"
    assert skills[0]["folder"] == "translator"


def test_llm_connection_failure(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'openai_compatible'
    cfg.llm.base_url_lmstudio = 'http://127.0.0.1:19999/v1'
    cfg.llm.base_url_ollama = 'http://127.0.0.1:19999'
    
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)
    
    import pytest
    with pytest.raises(RuntimeError) as exc_info:
        loop.run("test task")
        
    assert "Connection to LM Studio/LLM failed" in str(exc_info.value)
