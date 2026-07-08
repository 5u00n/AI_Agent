from pathlib import Path
import pytest
from agent import AgentConfig, AgentEngine, ToolRegistry

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

    # 4. Test when no working directory is selected and it falls back to self.root_dir (which was set to subdir)
    monkeypatch.setattr("agent.get_remembered_working_dir", lambda: None)
    res4 = engine.tools.call("create_file_or_folder", {"path": "fallback.txt", "is_folder": False, "content": "hello fallback"})
    assert res4["ok"] is True
    assert (subdir / "fallback.txt").exists()
    
    # Cleanup fallback file
    if (subdir / "fallback.txt").exists():
        (subdir / "fallback.txt").unlink()


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
