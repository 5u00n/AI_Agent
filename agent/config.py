# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/config.py — Configuration Dataclasses & YAML Loader                ║
# ║                                                                            ║
# ║  Single source of truth for every tunable knob in the agent system.        ║
# ║  All settings live in config.yaml and are loaded into typed dataclasses.   ║
# ║                                                                            ║
# ║  Sections:                                                                 ║
# ║    1. LLM provider settings (model names, endpoints, transport)            ║
# ║    2. Budget limits (max steps, runtime, tool calls)                       ║
# ║    3. Safety policy (approval gates, blocked commands)                     ║
# ║    4. Test policy (auto-generate, auto-correct, cleanup)                   ║
# ║    5. UI server settings                                                   ║
# ║    6. MCP server definitions                                               ║
# ║    7. Top-level AgentConfig that holds everything                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
	import yaml
except Exception:  # pragma: no cover
	yaml = None


# ─────────────────────────────────────────────────────────────────────────────
# 1. LLM PROVIDER CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LLMConfig:
	"""Settings for connecting to LM Studio or Ollama."""
	provider: str = "lmstudio"
	base_url_lmstudio: str = "http://127.0.0.1:1234/v1"
	base_url_ollama: str = "http://127.0.0.1:11434"
	api_key_lmstudio: str = "lm-studio"
	api_key_ollama: str = "ollama"
	model_planner: str = "planner-model"
	model_executor: str = "executor-model"
	model_verifier: str = "verifier-model"
	transport: str = "openai_compatible"   # "openai_compatible" | "stub"
	max_tokens: int = 4096

	def get_base_url(self) -> str:
		if self.provider == "lmstudio":
			return self.base_url_lmstudio
		if self.provider == "ollama":
			return self.base_url_ollama
		raise ValueError(f"Unsupported provider: {self.provider}")

	def get_api_key(self) -> str:
		if self.provider == "lmstudio":
			return self.api_key_lmstudio
		if self.provider == "ollama":
			return self.api_key_ollama
		raise ValueError(f"Unsupported provider: {self.provider}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. BUDGET LIMITS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BudgetConfig:
	"""Hard caps to prevent runaway agent loops."""
	max_steps: int = 30
	max_runtime_minutes: int = 60
	max_tool_calls: int = 200


# ─────────────────────────────────────────────────────────────────────────────
# 3. SAFETY POLICY
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SafetyConfig:
	"""Actions that need human approval and commands that are blocked."""
	require_approval_for: List[str] = field(default_factory=list)
	blocked_commands: List[str] = field(default_factory=list)
	allowed_paths: List[str] = field(default_factory=lambda: ["."])


# ─────────────────────────────────────────────────────────────────────────────
# 4. TEST POLICY (per-task test gate)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestPolicyConfig:
	"""Controls the mandatory test lifecycle for every completed step."""
	enforce_task_test_gate: bool = True
	auto_generate_tests: bool = True
	verify_and_autocorrect_tests: bool = True
	run_tests_before_completion: bool = True
	delete_tests_after_task: bool = True
	keep_tests_when_user_requests: bool = True
	test_location_strategy: str = "tests_temp"  # "tests_temp" | "adjacent_temp"
	max_test_fix_attempts: int = 2
	test_runner_by_mode: Dict[str, str] = field(default_factory=lambda: {"coding": "python"})


# ─────────────────────────────────────────────────────────────────────────────
# 5. UI SERVER SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UIConfig:
	enabled: bool = True
	host: str = "127.0.0.1"
	port: int = 8000
	auth_mode: str = "none"


# ─────────────────────────────────────────────────────────────────────────────
# 6. MCP SERVER DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MCPServerConfig:
	"""One registered MCP server (stdio transport by default)."""
	command: str
	args: List[str] = field(default_factory=list)
	transport: str = "stdio"


@dataclass
class MCPConfig:
	"""Collection of all MCP server registrations."""
	servers: Dict[str, MCPServerConfig] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# 7. TOP-LEVEL AGENT CONFIG  (composition root for all settings)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
	"""Master config that aggregates all sub-configs."""
	llm: LLMConfig = field(default_factory=LLMConfig)
	budgets: BudgetConfig = field(default_factory=BudgetConfig)
	safety: SafetyConfig = field(default_factory=SafetyConfig)
	test_policy: TestPolicyConfig = field(default_factory=TestPolicyConfig)
	ui: UIConfig = field(default_factory=UIConfig)
	mcp: MCPConfig = field(default_factory=MCPConfig)

	@staticmethod
	def default(root_dir: Path) -> "AgentConfig":
		_ = root_dir
		return AgentConfig()

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG LOADING / SAVING (YAML)
# ─────────────────────────────────────────────────────────────────────────────

def _build_dataclass(cls: Any, values: Optional[Dict[str, Any]]) -> Any:
	"""Safely instantiate a dataclass from a (possibly None) dict of values."""
	values = values or {}
	return cls(**values)


def load_config(path: Path) -> AgentConfig:
	"""Load agent config from a YAML file. Returns defaults if file missing."""
	if not path.exists():
		return AgentConfig.default(root_dir=path.parent)
	if yaml is None:
		raise RuntimeError("pyyaml is required to load config.yaml")
	raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

	# Parse MCP servers (nested dict of name → {command, args, transport})
	mcp_raw = raw.get("mcp", {})
	mcp_servers = {}
	for name, srv in mcp_raw.get("servers", {}).items():
		mcp_servers[name] = MCPServerConfig(
			command=srv.get("command", ""),
			args=srv.get("args", []),
			transport=srv.get("transport", "stdio")
		)

	return AgentConfig(
		llm=_build_dataclass(LLMConfig, raw.get("llm")),
		budgets=_build_dataclass(BudgetConfig, raw.get("budgets")),
		safety=_build_dataclass(SafetyConfig, raw.get("safety")),
		test_policy=_build_dataclass(TestPolicyConfig, raw.get("test_policy")),
		ui=_build_dataclass(UIConfig, raw.get("ui")),
		mcp=MCPConfig(servers=mcp_servers),
	)


def save_config(path: Path, config: AgentConfig) -> None:
	"""Persist agent config to a YAML file."""
	if yaml is None:
		raise RuntimeError("pyyaml is required to save config.yaml")
	path.write_text(yaml.safe_dump(config.to_dict(), sort_keys=False), encoding="utf-8")
