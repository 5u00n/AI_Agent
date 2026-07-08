from pathlib import Path
from agent import load_config

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
