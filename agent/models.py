# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/models.py — Core Data Models                                       ║
# ║                                                                            ║
# ║  Lightweight dataclasses that represent the fundamental units of work:     ║
# ║    • TaskStep    — one step in a multi-step plan                           ║
# ║    • TestRunReport — result of running generated tests for a step          ║
# ║    • StepCompletion — final verdict for a completed step                   ║
# ║                                                                            ║
# ║  These models are imported by almost every other module, so they live      ║
# ║  in their own file with ZERO heavy dependencies.                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# TASK STEP — one unit of work in a plan
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TaskStep:
	"""Represents a single step in the planner's multi-step plan.

	Fields:
		step_id:       Unique identifier (e.g. "step_1")
		title:         Human-readable description of what this step does
		mode:          Task mode — "coding" | "research" | "analysis" | "docs"
		expectations:  Dict of expected outputs (path, content_contains, etc.)
	"""
	step_id: str
	title: str
	mode: str
	expectations: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# TEST RUN REPORT — outcome of the test lifecycle for one step
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestRunReport:
	"""Captures the result of generating, running, and optionally fixing tests.

	Fields:
		passed:          True if all generated tests passed
		generated_path:  Path to the generated test file (may be deleted after)
		attempts:        How many generate→fix→run cycles were needed
		message:         Human-readable summary (e.g. "tests passed" or error)
	"""
	passed: bool
	generated_path: Optional[Path]
	attempts: int
	message: str


# ─────────────────────────────────────────────────────────────────────────────
# STEP COMPLETION — final status after test gate check
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepCompletion:
	"""Final verdict for a step after the test gate has run.

	Fields:
		status:       "done" or "blocked"
		message:      Explanation of what happened
		test_report:  Optional TestRunReport with detailed test outcome
	"""
	status: str
	message: str
	test_report: Optional[TestRunReport] = None
