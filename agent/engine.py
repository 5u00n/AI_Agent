# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/engine.py — AgentEngine (Composition Root)                         ║
# ║                                                                            ║
# ║  AgentEngine is the central object that owns and connects all subsystems:  ║
# ║                                                                            ║
# ║    ┌──────────────────────────────────────────────────────────────┐       ║
# ║    │                      AgentEngine                             │       ║
# ║    │                                                              │       ║
# ║    │  cfg ──► LLMConfig, BudgetConfig, SafetyConfig, etc.        │       ║
# ║    │  store ──► StateStore (SQLite)                              │       ║
# ║    │  llm_client ──► LocalLLMClient (calls LM Studio/Ollama)    │       ║
# ║    │  router ──► LLMProviderRouter (metadata)                    │       ║
# ║    │  tools ──► ToolRegistry (file ops, shell, web)              │       ║
# ║    │  mcp ──► MCPClientRegistry (external MCP servers)           │       ║
# ║    │  test_manager ──► TestLifecycleManager                      │       ║
# ║    │  orchestrator ──► PlannerExecutorVerifier (the loop)        │       ║
# ║    └──────────────────────────────────────────────────────────────┘       ║
# ║                                                                            ║
# ║  Public interface:                                                         ║
# ║    engine.run_goal(goal, mode, keep_tests)  — run a complete goal         ║
# ║    engine.complete_step(step, ...)          — run test gate for one step   ║
# ║    engine.call_mcp_tool(tool_name, params)  — call a tool on any MCP server║
# ║    engine.process_next_job()                — dequeue and run one job      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from agent.config import AgentConfig
from agent.llm_client import LLMProviderRouter, LocalLLMClient
from agent.mcp_client import MCPClientRegistry
from agent.models import StepCompletion, TaskStep
from agent.orchestrator import PlannerExecutorVerifier
from agent.store import StateStore
from agent.test_lifecycle import TestLifecycleManager
from agent.tools import ToolRegistry


# ─────────────────────────────────────────────────────────────────────────────
# AGENT ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class AgentEngine:
    """The top-level orchestrator that wires together all agent subsystems.

    Create one instance per process. Pass it to create_ui_app() for the web
    server, or call run_goal() directly for CLI mode.
    """

    def __init__(self, cfg: AgentConfig, root_dir: Path) -> None:
        self.cfg = cfg
        self.root_dir = root_dir

        # ── Core subsystems ──────────────────────────────────────────────
        self.store = StateStore(root_dir / "state" / "agent.db")
        self.llm_client = LocalLLMClient(cfg.llm)
        self.router = LLMProviderRouter(cfg.llm)
        self.tools = ToolRegistry(cfg, root_dir, store=self.store)
        self.mcp = MCPClientRegistry()
        self.test_manager = TestLifecycleManager(cfg, root_dir, llm_client=self.llm_client)
        self.orchestrator = PlannerExecutorVerifier(self)

        # Register MCP servers from config
        for name, srv in self.cfg.mcp.servers.items():
            self.mcp.register(name, {"command": srv.command, "args": srv.args, "transport": srv.transport})

        # Give the LLM client a back-reference so it can enumerate MCP tools and custom tools
        self.llm_client.engine = self

    # ─────────────────────────────────────────────────────────────────────
    # MCP TOOL DISPATCH
    # ─────────────────────────────────────────────────────────────────────

    def call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find which MCP server exposes tool_name and call it.

        Tries each registered server in order. Returns an error dict if none found.
        """
        for server_name in self.mcp.list_servers():
            try:
                self.mcp._init_server_sync(server_name)
                session = self.mcp._sessions[server_name]
                import asyncio
                future = asyncio.run_coroutine_threadsafe(session.list_tools(), self.mcp._loop)
                tools_list = future.result(timeout=5.0)
                has_tool = any(t.name == tool_name for t in tools_list.tools)
                if has_tool:
                    return self.mcp.call(server_name, tool_name, params)
            except Exception:
                pass
        return {"ok": False, "error": f"Tool '{tool_name}' not found in native tools or registered MCP servers."}

    # ─────────────────────────────────────────────────────────────────────
    # TEST GATE — called after each step execution
    # ─────────────────────────────────────────────────────────────────────

    def complete_step(self, step: TaskStep, keep_tests: bool = False, run_id: Optional[str] = None) -> StepCompletion:
        """Run the test lifecycle for a completed step and return the verdict.

        Args:
            step:       The step that was just executed.
            keep_tests: If True, keep generated test files after passing.
            run_id:     Optional run ID to store the test report in the database.

        Returns:
            StepCompletion with status "done" or "blocked".
        """
        try:
            report = self.test_manager.generate_verify_run_cleanup(step=step, keep_tests=keep_tests)
        except Exception as exc:  # pragma: no cover
            return StepCompletion(status="blocked", message=f"Step blocked by test gate error: {exc}")

        # Persist the test report to the database
        if run_id:
            self.store.add_test_report(run_id, step.step_id, report)

        if not report.passed:
            return StepCompletion(
                status="blocked",
                message=f"Step blocked by test gate: {report.message}",
                test_report=report,
            )

        return StepCompletion(
            status="done",
            message="Step completed after passing generated tests",
            test_report=report,
        )

    # ─────────────────────────────────────────────────────────────────────
    # GOAL EXECUTION — main public entry point
    # ─────────────────────────────────────────────────────────────────────

    def run_goal(
        self,
        goal: str,
        mode: str = "coding",
        keep_tests: bool = False,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a full goal through the plan-execute-verify loop.

        Args:
            goal:       Natural language task description.
            mode:       Task mode — "coding" | "research" | "analysis" | "docs".
            keep_tests: If True, generated test files are NOT deleted.
            run_id:     Optional existing run ID (for resuming or explicit IDs).

        Returns:
            Dict with run_id, provider metadata, step info, and result status.
        """
        loop_result = self.orchestrator.run(goal=goal, keep_tests=keep_tests, run_id=run_id)
        run_id = str(loop_result.get("run_id"))

        # Store the agent's final message in chat history for the UI
        msg = str(loop_result.get("reason", "completed by planner-executor-verifier"))
        self.store.add_message(run_id, "agent", msg)

        step = TaskStep(step_id="step_1", title=goal, mode=mode)
        generated_test = self.store.latest_test_path_for_run(run_id)

        return {
            "run_id": run_id,
            "provider": self.router.metadata(),
            "step": asdict(step),
            "result": {
                "status": str(loop_result.get("status", "blocked")),
                "message": msg,
                "tests_passed": str(loop_result.get("status")) == "done",
                "generated_test": generated_test,
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # BACKGROUND JOB PROCESSING — called by the worker thread
    # ─────────────────────────────────────────────────────────────────────

    def process_next_job(self) -> Optional[Dict[str, Any]]:
        """Claim and execute one queued job from the database.

        Called in a tight loop by the background worker thread. Returns None
        if no jobs are queued.
        """
        job = self.store.claim_next_job()
        if not job:
            return None

        job_id = str(job["job_id"])
        try:
            result = self.run_goal(
                goal=str(job["goal"]),
                mode=str(job["mode"]),
                keep_tests=bool(job["keep_tests"]),
                run_id=job_id,
            )
            status = "done" if str(result.get("result", {}).get("status")) == "done" else "blocked"
            self.store.finish_job(job_id, status=status, result_json=json.dumps(result), error=None)
            return result
        except Exception as exc:  # pragma: no cover
            self.store.finish_job(job_id, status="failed", result_json=None, error=str(exc))
            return None
