# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/orchestrator.py — Planner → Executor → Verifier Loop               ║
# ║                                                                            ║
# ║  The heart of the agent. Implements the foolproof 3-phase control loop:   ║
# ║                                                                            ║
# ║    1. PLAN   — Ask LLM to break the goal into typed steps                 ║
# ║    2. EXECUTE — Ask LLM which tool to call for this step                  ║
# ║    3. VERIFY — Ask LLM if the result satisfies the step requirements      ║
# ║    4. Retry up to max_attempts if verification fails                       ║
# ║    5. Run test gate after each successful step (via AgentEngine)           ║
# ║                                                                            ║
# ║  Step statuses: "running" → "done" | "blocked"                            ║
# ║  Run statuses:  "running" → "done" | "blocked"                            ║
# ║                                                                            ║
# ║  DEBUG TIP: Watch the SQLite `steps` table to trace what the agent did:   ║
# ║      sqlite3 state/agent.db "SELECT * FROM steps ORDER BY id DESC"        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# 
# =============================================================================
# 🛠️ HOW TO MAKE THE APP BETTER: CHANGING AGENT LOGIC
# =============================================================================
# This file is the "brain" of the agent. It dictates the Plan -> Execute -> Verify loop.
# 
# 1. ADDING A NEW THINKING PHASE:
#    Right now the loop is _plan(), then _execute(), then _verify(). If you want 
#    the agent to do a "reflection" step before verifying, you can create a `_reflect()` 
#    method and call it inside the `run()` loop below.
# 
# 2. CHANGING HOW THE AGENT HANDLES ERRORS:
#    Scroll down to the `run()` method. You'll see `max_attempts = 3`. You can 
#    increase this, or change the logic so it sends the error to a completely 
#    different LLM model for debugging.
# 
# 3. INTERCEPTING LLM PAYLOADS:
#    Inside `_plan`, `_execute`, or `_verify`, you can modify the `payload` dict 
#    before it gets sent to `self.engine.llm_client.complete_json`. For example, 
#    you could inject additional context like "Current time: X" or "Rules from file Y".

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from agent.models import TaskStep

if TYPE_CHECKING:
    # Avoid circular import — engine imports orchestrator, not vice versa
    from agent.engine import AgentEngine


# ─────────────────────────────────────────────────────────────────────────────
# PLANNER-EXECUTOR-VERIFIER CLASS
# ─────────────────────────────────────────────────────────────────────────────

class PlannerExecutorVerifier:
    """Implements the three-phase agent loop (plan → execute → verify).

    Receives an AgentEngine reference to access the LLM client, tool registry,
    state store, and test lifecycle manager — but does NOT own any of those.
    """

    def __init__(self, engine: "AgentEngine") -> None:
        self.engine = engine

    # ─────────────────────────────────────────────────────────────────────
    # PHASE 1: PLAN
    # ─────────────────────────────────────────────────────────────────────

    def _plan(self, goal: str, run_id: Optional[str] = None) -> List[TaskStep]:
        """Ask the LLM to break down the goal into a list of TaskSteps.

        Includes any previously completed steps as context so the planner
        can continue from where a prior session left off.

        Returns:
            List of TaskStep objects to execute in order.

        Raises:
            ValueError: If the LLM response doesn't match the expected schema.
        """
        history = []
        if run_id:
            prev_steps = self.engine.store.list_steps(run_id)
            for s in prev_steps:
                if s.get("status") == "done":
                    history.append({
                        "step_id": s.get("step_id"),
                        "title": s.get("title"),
                        "message": s.get("message"),
                    })

        payload: Dict[str, Any] = {"goal": goal}
        if history:
            payload["session_history"] = history

        resp = self.engine.llm_client.complete_json(
            role="planner",
            payload=payload,
            model=self.engine.cfg.llm.model_planner,
        )

        steps_data = resp.get("steps") if isinstance(resp, dict) else None
        if not isinstance(steps_data, list) or not steps_data:
            raise ValueError("planner contract invalid: missing steps list")

        steps: List[TaskStep] = []
        for idx, raw in enumerate(steps_data, start=1):
            if not isinstance(raw, dict):
                raise ValueError("planner contract invalid: step is not object")
            step_id = str(raw.get("step_id") or f"step_{idx}")
            title = str(raw.get("title") or "")
            mode = str(raw.get("mode") or "coding")
            expectations = raw.get("expectations", {})
            if not isinstance(expectations, dict):
                expectations = {}
            if not title:
                raise ValueError("planner contract invalid: step title missing")
            steps.append(TaskStep(step_id=step_id, title=title, mode=mode, expectations=expectations))

        return steps

    # ─────────────────────────────────────────────────────────────────────
    # PHASE 2: EXECUTE
    # ─────────────────────────────────────────────────────────────────────

    def _execute(
        self,
        step: TaskStep,
        goal: str,
        steps: List[TaskStep],
        last_error: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ask the LLM what tool to call for this step, then call it.

        Returns:
            The tool call result dict from ToolRegistry.call().
        """
        history = []
        if run_id:
            prev_steps = self.engine.store.list_steps(run_id)
            for s in prev_steps:
                if s.get("status") == "done":
                    history.append({
                        "step_id": s.get("step_id"),
                        "title": s.get("title"),
                        "message": s.get("message"),
                    })

        payload: Dict[str, Any] = {
            "goal": goal,
            "plan_steps": [asdict(s) for s in steps],
            "step": asdict(step),
        }
        if history:
            payload["session_history"] = history

        if last_error:
            # Give the LLM a hint: prefer write_file over edit_existing_file
            # when old_string matching is failing
            if "old_string" in last_error or "not found" in last_error or "mismatch" in last_error:
                last_error += (
                    "\nTIP: If edit_existing_file is failing because of old_string mismatch, "
                    "use write_file (or create_new_file) to write the complete updated content "
                    "of the file directly. This is much more reliable and avoids substring match issues."
                )
            payload["last_error"] = last_error

        try:
            resp = self.engine.llm_client.complete_json(
                role="executor",
                payload=payload,
                model=self.engine.cfg.llm.model_executor,
            )
        except ValueError as exc:
            return {"ok": False, "error": f"LLM returned invalid JSON for execution: {exc}"}

        if not isinstance(resp, dict):
            return {"ok": False, "error": "executor contract invalid"}

        action = str(resp.get("action", "")).strip()
        tool_name = str(resp.get("tool_name", "")).strip()
        tool_input = resp.get("tool_input", {})

        # ── Determine if this is a tool call ────────────────────────────
        # The LLM might use: action="tool_call", action=<tool_name>, or supply tool_name directly
        custom_tools = self.engine.tools.get_custom_tool_names()
        known_tools = {
            "write_file", "read_file", "create_new_file", "file_glob_search",
            "view_diff", "ls", "fetch_url_content", "edit_existing_file",
            "grep_search", "run_shell", "set_working_directory", "create_file_or_folder",
            "copy_file", "edit_file", "rename_file", "view_page",
            "single_find_and_replace",
        } | set(custom_tools)

        is_tool_call = False
        if action == "tool_call":
            is_tool_call = True
        elif tool_name and isinstance(tool_input, dict):
            is_tool_call = True
        elif action in known_tools:
            is_tool_call = True
            if not tool_name:
                tool_name = action

        if is_tool_call:
            if not tool_name or not isinstance(tool_input, dict):
                return {"ok": False, "error": "executor contract invalid: bad tool_call fields"}

            result = self.engine.tools.call(tool_name, tool_input, run_id=run_id)

            # Auto-populate step expectations from write_file results
            if tool_name == "write_file" and result.get("ok"):
                if not step.expectations.get("path") and isinstance(tool_input.get("path"), str):
                    step.expectations["path"] = str(tool_input.get("path"))
                content = tool_input.get("content")
                if isinstance(content, str) and content:
                    step.expectations.setdefault("content_contains", content.strip().splitlines()[0])

            # Attach file content to result for verifier context
            if result.get("ok"):
                path_val = result.get("path") or tool_input.get("path")
                if path_val:
                    try:
                        p = self.engine.tools._safe_path(str(path_val))
                        if p.exists() and p.is_file():
                            result["file_content"] = p.read_text(encoding="utf-8")[:10000]
                    except Exception:
                        pass

            return result

        # ── Final answer (no tool needed) ────────────────────────────────
        if action == "final_answer" or "final_answer" in resp:
            return {"ok": True, "message": str(resp.get("final_answer", ""))}

        return {"ok": False, "error": f"executor contract invalid: unsupported action: {action}"}

    # ─────────────────────────────────────────────────────────────────────
    # PHASE 3: VERIFY
    # ─────────────────────────────────────────────────────────────────────

    def _verify(
        self,
        step: TaskStep,
        execution_result: Dict[str, Any],
        goal: str,
        steps: List[TaskStep],
        run_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Ask the LLM if the execution result successfully fulfilled the step.

        Returns:
            (ok: bool, reason: str)
        """
        history = []
        if run_id:
            prev_steps = self.engine.store.list_steps(run_id)
            for s in prev_steps:
                if s.get("status") == "done":
                    history.append({
                        "step_id": s.get("step_id"),
                        "title": s.get("title"),
                        "message": s.get("message"),
                    })

        payload: Dict[str, Any] = {
            "goal": goal,
            "plan_steps": [asdict(s) for s in steps],
            "step": asdict(step),
            "execution_result": execution_result,
        }
        if history:
            payload["session_history"] = history

        try:
            resp = self.engine.llm_client.complete_json(
                role="verifier",
                payload=payload,
                model=self.engine.cfg.llm.model_verifier,
            )
        except ValueError as exc:
            return False, f"LLM returned invalid JSON for verification: {exc}"

        if not isinstance(resp, dict) or "ok" not in resp:
            # Fall back: trust the tool result's own ok flag
            ok = bool(execution_result.get("ok"))
            reason = "fallback decision" if ok else str(execution_result.get("error", "execution failed"))
            return ok, reason

        return bool(resp.get("ok")), str(resp.get("reason", ""))

    # ─────────────────────────────────────────────────────────────────────
    # MAIN LOOP — ties all three phases together
    # ─────────────────────────────────────────────────────────────────────

    def run(self, goal: str, keep_tests: bool = False, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the full plan-execute-verify loop for a given goal.

        Args:
            goal:       The natural language goal to accomplish.
            keep_tests: If True, generated test files are NOT deleted after passing.
            run_id:     Optional existing run ID to resume (or create new).

        Returns:
            Dict with "status" ("done" | "blocked"), "run_id", "steps", "reason".
        """
        # Create or re-activate the run record in the database
        if not run_id:
            run_id = self.engine.store.create_run(goal, status="running")
        else:
            self.engine.store.create_run(goal, run_id=run_id, status="running")

        # Early exit if already stopped by user
        if self.engine.store.get_run_status(run_id) == "stopped":
            return {"status": "blocked", "run_id": run_id, "reason": "Task stopped by user"}

        # ── PHASE 1: PLAN ────────────────────────────────────────────────
        try:
            steps = self._plan(goal, run_id=run_id)
        except ValueError as exc:
            self.engine.store.set_run_status(run_id, "blocked")
            return {"status": "blocked", "run_id": run_id, "reason": f"planner error: {exc}"}

        # ── PHASE 2+3: EXECUTE + VERIFY (per step) ───────────────────────
        last_msg = "completed by planner-executor-verifier"

        for step in steps:
            # Check for stop signal before each step
            if self.engine.store.get_run_status(run_id) == "stopped":
                return {"status": "blocked", "run_id": run_id, "reason": "Task stopped by user"}

            attempts = 0
            max_attempts = 3
            last_error: Optional[str] = None
            success = False
            execution_result: Dict[str, Any] = {}

            # Retry loop — up to max_attempts per step
            while attempts < max_attempts:
                if self.engine.store.get_run_status(run_id) == "stopped":
                    return {"status": "blocked", "run_id": run_id, "reason": "Task stopped by user"}

                attempts += 1
                execution_result = self._execute(step, goal, steps, last_error=last_error, run_id=run_id)
                verify_ok, verify_reason = self._verify(step, execution_result, goal, steps, run_id=run_id)

                if verify_ok:
                    success = True
                    break
                else:
                    last_error = f"Attempt {attempts} failed: {verify_reason}"
                    self.engine.store.add_step(
                        run_id,
                        step,
                        "running",
                        f"Step execution failed on attempt {attempts}: {verify_reason}. Retrying...",
                    )

            # If all retries exhausted, mark run as blocked
            if not success:
                self.engine.store.add_step(run_id, step, "blocked", f"execution verification failed: {last_error}")
                self.engine.store.set_run_status(run_id, "blocked")
                return {"status": "blocked", "run_id": run_id, "reason": f"execution verification failed: {last_error}"}

            # ── TEST GATE (after successful step execution) ───────────────
            completion = self.engine.complete_step(step=step, keep_tests=keep_tests, run_id=run_id)

            # Include the tool result's message alongside the test gate message
            msg = completion.message
            if isinstance(execution_result, dict) and execution_result.get("message"):
                msg = f"{execution_result['message']}\n\n({completion.message})"
            last_msg = msg

            self.engine.store.add_step(run_id, step, completion.status, msg)

            if completion.status != "done":
                self.engine.store.set_run_status(run_id, completion.status)
                return {"status": completion.status, "run_id": run_id, "reason": completion.message}

        # Final stop check after all steps
        if self.engine.store.get_run_status(run_id) == "stopped":
            return {"status": "blocked", "run_id": run_id, "reason": "Task stopped by user"}

        self.engine.store.set_run_status(run_id, "done")
        return {"status": "done", "run_id": run_id, "steps": len(steps), "reason": last_msg}
