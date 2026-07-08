from pathlib import Path
import sqlite3
import pytest
from agent import AgentConfig, AgentEngine, PlannerExecutorVerifier, TaskStep

def test_planner_executor_verifier_loop_completes_with_stub_llm(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'stub'
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)

    result = loop.run("Create hello.txt")

    assert result["status"] == "done"
    assert (tmp_path / "hello.txt").exists()


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


def test_llm_connection_failure(tmp_path: Path) -> None:
    cfg = AgentConfig.default(root_dir=tmp_path)
    cfg.llm.transport = 'openai_compatible'
    cfg.llm.base_url_lmstudio = 'http://127.0.0.1:19999/v1'
    cfg.llm.base_url_ollama = 'http://127.0.0.1:19999'
    
    engine = AgentEngine(cfg, root_dir=tmp_path)
    loop = PlannerExecutorVerifier(engine)
    
    with pytest.raises(RuntimeError) as exc_info:
        loop.run("test task")
        
    assert "Connection to LM Studio/LLM failed" in str(exc_info.value)
