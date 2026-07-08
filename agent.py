# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastapi>=0.110.0",
#     "uvicorn>=0.29.0",
#     "openai>=1.30.0",
#     "pydantic>=2.6.0",
#     "PyYAML>=6.0.0",
#     "pytest>=8.0.0",
#     "mcp>=1.1.2",
# ]
# ///
#
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent.py — Backwards-Compatible Entry Point Shim                         ║
# ║                                                                            ║
# ║  This file is intentionally kept minimal. All real code has moved into    ║
# ║  the agent/ package. See:                                                  ║
# ║                                                                            ║
# ║    agent/cli.py         — main() and argument parsing                     ║
# ║    agent/engine.py      — AgentEngine (composition root)                  ║
# ║    agent/config.py      — AgentConfig and all settings                    ║
# ║    agent/store.py       — StateStore (SQLite persistence)                 ║
# ║    agent/llm_client.py  — LocalLLMClient (talks to LM Studio/Ollama)     ║
# ║    agent/tools.py       — ToolRegistry (file ops, shell, web)             ║
# ║    agent/mcp_client.py  — MCPClientRegistry                               ║
# ║    agent/orchestrator.py — PlannerExecutorVerifier loop                   ║
# ║    agent/test_lifecycle.py — TestLifecycleManager                         ║
# ║    agent/ui.py          — render_ui_html() (the HTML frontend)            ║
# ║    agent/api.py         — create_ui_app() (FastAPI routes)                ║
# ║    agent/models.py      — TaskStep, TestRunReport, StepCompletion         ║
# ║    agent/utils.py       — _utc_now, workspace helpers                     ║
# ║                                                                            ║
# ║  Usage (unchanged from before):                                            ║
# ║    python agent.py --ui                    → start web UI                 ║
# ║    python agent.py --goal "Write a file"   → run in CLI mode              ║
# ║    uv run agent.py --ui                    → via uv script runner         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# 
# 💡 EXTENSION POINT:
# This is just the entry point. To add core agent loop features, see `agent/orchestrator.py`.
# To add tools, see `agent/tools.py`.
# See EXTENSION_GUIDE.md for details.

# All public symbols are re-exported from agent/__init__.py, so existing code
# like `from agent import AgentConfig, AgentEngine` continues to work.
from agent.cli import main

if __name__ == "__main__":
    raise SystemExit(main())