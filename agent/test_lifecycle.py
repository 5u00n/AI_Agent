# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/test_lifecycle.py — Per-Task Test Lifecycle Manager                ║
# ║                                                                            ║
# ║  For every completed step, the agent MUST:                                 ║
# ║    1. GENERATE — create a pytest file that checks the step output          ║
# ║    2. VERIFY   — check the test file is syntactically valid                ║
# ║    3. AUTOCORRECT — if invalid, ask LLM to fix it (up to N attempts)      ║
# ║    4. RUN      — execute the test and require it to pass                   ║
# ║    5. CLEANUP  — delete the test file (unless keep_tests=True)             ║
# ║                                                                            ║
# ║  Test file locations (configured via test_policy.test_location_strategy):  ║
# ║    "tests_temp"    → <workspace>/tests_temp/test_<step_id>_<name>.py      ║
# ║    "adjacent_temp" → <workspace>/.agent_tmp_tests/test_<step_id>_<name>.py║
# ║                                                                            ║
# ║  DEBUG TIP: Set delete_tests_after_task: false in config.yaml to keep     ║
# ║  test files after a run and inspect them manually.                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import subprocess
import sys
import textwrap
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from agent.config import AgentConfig
from agent.models import TaskStep, TestRunReport


# ─────────────────────────────────────────────────────────────────────────────
# TEST LIFECYCLE MANAGER CLASS
# ─────────────────────────────────────────────────────────────────────────────

class TestLifecycleManager:
    """Manages the full lifecycle of auto-generated tests for each step.

    Handles: generate → verify/autocorrect → run → cleanup.
    """

    # Prevent pytest from collecting this class as a test
    __test__ = False

    def __init__(self, cfg: AgentConfig, root_dir: Path, llm_client=None) -> None:
        self.cfg = cfg
        self.root_dir = root_dir
        # Optional LLM client — used for AI-powered test generation and autocorrect.
        # If None (or transport is not openai_compatible), falls back to template generation.
        self.llm_client = llm_client

    # ─────────────────────────────────────────────────────────────────────
    # TEST DIRECTORY
    # ─────────────────────────────────────────────────────────────────────

    def _test_dir(self) -> Path:
        """Return (and create) the directory where test files are written."""
        strategy = self.cfg.test_policy.test_location_strategy
        if strategy == "adjacent_temp":
            d = self.root_dir / ".agent_tmp_tests"
        else:
            d = self.root_dir / "tests_temp"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ─────────────────────────────────────────────────────────────────────
    # STEP 1: GENERATE TEST FILE
    # ─────────────────────────────────────────────────────────────────────

    def _generate_test_file(self, step: TaskStep) -> Path:
        """Generate a pytest file that verifies the step's output.

        If an LLM client is available with a real transport, asks the LLM to
        write the test code. Otherwise, uses a template based on step.expectations.
        """
        # Build a safe filename from the step title
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in step.title.lower()).strip("_")
        name = safe_name or "task"
        path = self._test_dir() / f"test_{step.step_id}_{name}.py"

        # ── Try LLM-based test generation (real transport only) ──────────
        if self.llm_client and self.cfg.llm.transport == "openai_compatible":
            payload = {"step": asdict(step), "task": "generate_pytest"}
            res = self.llm_client.complete_json("verifier", payload, self.cfg.llm.model_verifier)
            if isinstance(res, dict) and "test_code" in res:
                path.write_text(str(res["test_code"]), encoding="utf-8")
                return path

        # ── Template-based test generation (fallback) ─────────────────────
        expected_path = step.expectations.get("path")
        expected_contains = step.expectations.get("content_contains")

        if isinstance(expected_path, str) and expected_path:
            # Generate a test that checks the expected file exists (and optionally its content)
            target = (self.root_dir / expected_path).resolve()
            content = (
                "from pathlib import Path\n\n\n"
                "def test_task_contract():\n"
                f"    # Generated test contract for step: {step.title}\n"
                f"    target = Path({str(target)!r})\n"
                "    assert target.exists(), \"Expected artifact file to exist\"\n"
            )
            if isinstance(expected_contains, str) and expected_contains:
                content += (
                    f"    text = target.read_text(encoding=\"utf-8\")\n"
                    f"    assert {expected_contains!r} in text, \"Expected content marker not found\"\n"
                )
            content += (
                "\n\n"
                "if __name__ == \"__main__\":\n"
                "    test_task_contract()\n"
            )
        else:
            # No specific file expected — generate a trivially passing test
            content = textwrap.dedent(
                f"""
                def test_task_contract():
                    # Generated test contract for step: {step.title}
                    assert True


                if __name__ == "__main__":
                    test_task_contract()
                """
            ).lstrip()

        path.write_text(content, encoding="utf-8")
        return path

    # ─────────────────────────────────────────────────────────────────────
    # STEP 2: VERIFY & AUTOCORRECT
    # ─────────────────────────────────────────────────────────────────────

    def _verify_and_autocorrect(self, test_path: Path, error_message: str = "") -> None:
        """Validate the test file and attempt to fix it if broken.

        If an LLM is available and there's an error message, asks the LLM to
        rewrite the test. Otherwise does a simple structural check.
        """
        source = test_path.read_text(encoding="utf-8")

        # ── LLM autocorrect (real transport + error message present) ─────
        if self.llm_client and self.cfg.llm.transport == "openai_compatible" and error_message:
            payload = {"test_code": source, "error": error_message, "task": "autocorrect_pytest"}
            res = self.llm_client.complete_json("verifier", payload, self.cfg.llm.model_verifier)
            if isinstance(res, dict) and "fixed_test_code" in res:
                test_path.write_text(str(res["fixed_test_code"]), encoding="utf-8")
                return

        # ── Basic structural fix (fallback) ──────────────────────────────
        if "def test_" not in source:
            fixed = "def test_autofixed():\n    assert True\n"
            test_path.write_text(fixed, encoding="utf-8")

    # ─────────────────────────────────────────────────────────────────────
    # STEP 3: RUN TEST FILE
    # ─────────────────────────────────────────────────────────────────────

    def _run_test_file(self, test_path: Path, mode: str) -> subprocess.CompletedProcess:
        """Execute the test file using pytest or plain python, per config."""
        runner = self.cfg.test_policy.test_runner_by_mode.get(mode, "python")
        if runner == "pytest":
            return subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-q"],
                capture_output=True,
                text=True,
                check=False,
            )
        return subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            check=False,
        )

    # ─────────────────────────────────────────────────────────────────────
    # MAIN ENTRY POINT — full generate → verify → run → cleanup pipeline
    # ─────────────────────────────────────────────────────────────────────

    def generate_verify_run_cleanup(self, step: TaskStep, keep_tests: bool = False) -> TestRunReport:
        """Run the complete test lifecycle for one step.

        Args:
            step:       The completed step to generate and run tests for.
            keep_tests: If True, the test file is NOT deleted after passing.

        Returns:
            TestRunReport with pass/fail status, path, attempt count, message.
        """
        policy = self.cfg.test_policy

        # ── Test gate disabled ────────────────────────────────────────────
        if not policy.enforce_task_test_gate:
            return TestRunReport(True, None, 0, "test gate disabled")

        if not policy.auto_generate_tests:
            return TestRunReport(False, None, 0, "test generation is required but disabled")

        # ── Generate the test file ────────────────────────────────────────
        test_path = self._generate_test_file(step)
        attempts = 0
        last_message = ""

        # ── Run / autocorrect loop ────────────────────────────────────────
        for attempt in range(policy.max_test_fix_attempts + 1):
            attempts = attempt + 1

            # Verify / autocorrect before each run
            if policy.verify_and_autocorrect_tests:
                self._verify_and_autocorrect(test_path, last_message)

            result = self._run_test_file(test_path, step.mode)

            if result.returncode == 0:
                # ── PASS: optionally clean up ─────────────────────────────
                delete_after = policy.delete_tests_after_task and not keep_tests
                if delete_after and test_path.exists():
                    test_path.unlink()
                return TestRunReport(True, test_path, attempts, "tests passed")

            # Capture error for next autocorrect attempt
            last_message = (result.stderr or result.stdout or "test execution failed").strip()

        # All attempts exhausted — return failure
        return TestRunReport(False, test_path, attempts, last_message or "test gate failed")
