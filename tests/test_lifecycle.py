from pathlib import Path
from agent import AgentConfig, TaskStep, TestLifecycleManager, AgentEngine

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
