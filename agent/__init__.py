# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/__init__.py — Public Package API                                   ║
# ║                                                                            ║
# ║  Re-exports all symbols that external code (tests, scripts) import from   ║
# ║  the "agent" package.                                                      ║
# ║                                                                            ║
# ║  This means all existing imports like:                                     ║
# ║      from agent import AgentEngine, AgentConfig, TaskStep, ...            ║
# ║  continue to work UNCHANGED after the refactoring.                        ║
# ║                                                                            ║
# ║  DO NOT add business logic here — this is a pure re-export file.          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG (dataclasses + YAML loader)
# ─────────────────────────────────────────────────────────────────────────────
from agent.config import (
    AgentConfig,
    BudgetConfig,
    LLMConfig,
    MCPConfig,
    MCPServerConfig,
    SafetyConfig,
    TestPolicyConfig,
    UIConfig,
    load_config,
    save_config,
)

# ─────────────────────────────────────────────────────────────────────────────
# CORE DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────
from agent.models import StepCompletion, TaskStep, TestRunReport

# ─────────────────────────────────────────────────────────────────────────────
# STATE STORE
# ─────────────────────────────────────────────────────────────────────────────
from agent.store import StateStore

# ─────────────────────────────────────────────────────────────────────────────
# LLM CLIENT
# ─────────────────────────────────────────────────────────────────────────────
from agent.llm_client import LLMProviderRouter, LocalLLMClient

# ─────────────────────────────────────────────────────────────────────────────
# TOOL REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
from agent.tools import ToolRegistry

# ─────────────────────────────────────────────────────────────────────────────
# MCP CLIENT REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
from agent.mcp_client import MCPClientRegistry

# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
from agent.orchestrator import PlannerExecutorVerifier

# ─────────────────────────────────────────────────────────────────────────────
# TEST LIFECYCLE MANAGER
# ─────────────────────────────────────────────────────────────────────────────
from agent.test_lifecycle import TestLifecycleManager

# ─────────────────────────────────────────────────────────────────────────────
# ENGINE (composition root)
# ─────────────────────────────────────────────────────────────────────────────
from agent.engine import AgentEngine

# ─────────────────────────────────────────────────────────────────────────────
# UI + API
# ─────────────────────────────────────────────────────────────────────────────
from agent.api import create_ui_app
from agent.ui import render_ui_html

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
from agent.cli import ensure_default_config, main

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
from agent.utils import (
    _utc_now,
    get_remembered_working_dir,
    save_remembered_working_dir,
)

__all__ = [
    # config
    "AgentConfig", "LLMConfig", "BudgetConfig", "SafetyConfig",
    "TestPolicyConfig", "UIConfig", "MCPConfig", "MCPServerConfig",
    "load_config", "save_config",
    # models
    "TaskStep", "TestRunReport", "StepCompletion",
    # store
    "StateStore",
    # llm
    "LLMProviderRouter", "LocalLLMClient",
    # tools
    "ToolRegistry",
    # mcp
    "MCPClientRegistry",
    # orchestrator
    "PlannerExecutorVerifier",
    # test lifecycle
    "TestLifecycleManager",
    # engine
    "AgentEngine",
    # api + ui
    "create_ui_app", "render_ui_html",
    # cli
    "main", "ensure_default_config",
    # utils
    "_utc_now", "get_remembered_working_dir", "save_remembered_working_dir",
]
