# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/store.py — SQLite State Persistence Layer                          ║
# ║                                                                            ║
# ║  The StateStore class owns ALL database interactions. Every run, step,     ║
# ║  test report, approval, message, and background job is stored here.        ║
# ║                                                                            ║
# ║  Tables:                                                                   ║
# ║    • runs       — high-level goals and their status                       ║
# ║    • steps      — individual steps within a run                            ║
# ║    • task_tests — generated test files and their pass/fail results         ║
# ║    • approvals  — human approval requests for risky actions                ║
# ║    • jobs       — autonomous background job queue                          ║
# ║    • messages   — chat history for the UI (user ↔ agent messages)         ║
# ║                                                                            ║
# ║  DEBUG TIP: You can inspect the database directly with:                    ║
# ║      sqlite3 state/agent.db ".tables"                                     ║
# ║      sqlite3 state/agent.db "SELECT * FROM runs"                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.models import TaskStep, TestRunReport
from agent.utils import _utc_now


# ─────────────────────────────────────────────────────────────────────────────
# STATE STORE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class StateStore:
	"""SQLite-backed persistence for ALL agent state.

	Every public method opens its own connection and commits immediately.
	This is intentionally simple — no ORM, no connection pooling.
	Easy to debug, easy to inspect with sqlite3 CLI.
	"""

	def __init__(self, db_path: Path) -> None:
		self.db_path = db_path
		self.db_path.parent.mkdir(parents=True, exist_ok=True)
		self._init()

	# ─────────────────────────────────────────────────────────────────────
	# TABLE CREATION
	# ─────────────────────────────────────────────────────────────────────

	def _init(self) -> None:
		"""Create all tables if they don't exist yet."""
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS runs (
					run_id TEXT PRIMARY KEY,
					goal TEXT NOT NULL,
					status TEXT NOT NULL,
					created_at TEXT NOT NULL,
					updated_at TEXT NOT NULL
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS steps (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					run_id TEXT NOT NULL,
					step_id TEXT NOT NULL,
					title TEXT NOT NULL,
					mode TEXT NOT NULL,
					status TEXT NOT NULL,
					message TEXT NOT NULL,
					created_at TEXT NOT NULL
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS task_tests (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					run_id TEXT,
					step_id TEXT NOT NULL,
					path TEXT,
					status TEXT NOT NULL,
					message TEXT NOT NULL,
					generated_at TEXT NOT NULL,
					deleted_at TEXT
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS approvals (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					approval_id TEXT UNIQUE NOT NULL,
					run_id TEXT,
					action TEXT NOT NULL,
					reason TEXT NOT NULL,
					payload_json TEXT,
					status TEXT NOT NULL,
					reviewer TEXT,
					reviewed_at TEXT,
					created_at TEXT NOT NULL
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS jobs (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					job_id TEXT UNIQUE NOT NULL,
					goal TEXT NOT NULL,
					mode TEXT NOT NULL,
					keep_tests INTEGER NOT NULL,
					status TEXT NOT NULL,
					result_json TEXT,
					error TEXT,
					created_at TEXT NOT NULL,
					updated_at TEXT NOT NULL
				)
				"""
			)
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS messages (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					run_id TEXT NOT NULL,
					role TEXT NOT NULL,
					content TEXT NOT NULL,
					created_at TEXT NOT NULL
				)
				"""
			)

	# ─────────────────────────────────────────────────────────────────────
	# RUNS — create, status, list, delete
	# ─────────────────────────────────────────────────────────────────────

	def create_run(self, goal: str, run_id: Optional[str] = None, status: str = "running") -> str:
		"""Create a new run (or re-activate a stopped one)."""
		if not run_id:
			run_id = str(uuid.uuid4())
		now = _utc_now()
		with sqlite3.connect(self.db_path) as conn:
			row = conn.execute("SELECT status FROM runs WHERE run_id = ?", (run_id,)).fetchone()
			if row and row[0] in ("stopped", "cancelled"):
				# Re-activate a previously stopped run
				conn.execute(
					"UPDATE runs SET goal = ?, updated_at = ? WHERE run_id = ?",
					(goal, now, run_id),
				)
			else:
				conn.execute(
					"INSERT OR REPLACE INTO runs(run_id, goal, status, created_at, updated_at) VALUES(?,?,?,?,?)",
					(run_id, goal, status, now, now),
				)
		return run_id

	def set_run_status(self, run_id: str, status: str) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
				(status, _utc_now(), run_id),
			)

	def get_run_status(self, run_id: str) -> Optional[str]:
		with sqlite3.connect(self.db_path) as conn:
			row = conn.execute(
				"SELECT status FROM runs WHERE run_id = ? LIMIT 1",
				(run_id,),
			).fetchone()
			if not row:
				return None
			return str(row[0])

	def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
		with sqlite3.connect(self.db_path) as conn:
			rows = conn.execute(
				"SELECT run_id, goal, status, created_at, updated_at FROM runs ORDER BY created_at DESC LIMIT ?",
				(limit,),
			).fetchall()
			return [
				{
					"run_id": str(row[0]),
					"goal": str(row[1]),
					"status": str(row[2]),
					"created_at": str(row[3]),
					"updated_at": str(row[4]),
				}
				for row in rows
			]

	def delete_run(self, run_id: str) -> None:
		"""Delete a run and ALL associated data (steps, tests, approvals, messages)."""
		with sqlite3.connect(self.db_path) as conn:
			conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
			conn.execute("DELETE FROM steps WHERE run_id = ?", (run_id,))
			conn.execute("DELETE FROM task_tests WHERE run_id = ?", (run_id,))
			conn.execute("DELETE FROM approvals WHERE run_id = ?", (run_id,))
			conn.execute("DELETE FROM jobs WHERE job_id = ?", (run_id,))
			conn.execute("DELETE FROM messages WHERE run_id = ?", (run_id,))

	# ─────────────────────────────────────────────────────────────────────
	# MESSAGES — chat history for the UI
	# ─────────────────────────────────────────────────────────────────────

	def add_message(self, run_id: str, role: str, content: str) -> None:
		now = _utc_now()
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO messages(run_id, role, content, created_at) VALUES(?,?,?,?)",
				(run_id, role, content, now),
			)

	def list_messages(self, run_id: str) -> List[Dict[str, Any]]:
		with sqlite3.connect(self.db_path) as conn:
			conn.row_factory = sqlite3.Row
			rows = conn.execute(
				"SELECT id, run_id, role, content, created_at FROM messages WHERE run_id = ? ORDER BY id ASC",
				(run_id,),
			).fetchall()
			return [dict(r) for r in rows]

	def delete_message(self, message_id: int) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))

	# ─────────────────────────────────────────────────────────────────────
	# STEPS — per-step tracking within a run
	# ─────────────────────────────────────────────────────────────────────

	def add_step(self, run_id: str, step: TaskStep, status: str, message: str) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO steps(run_id, step_id, title, mode, status, message, created_at) VALUES(?,?,?,?,?,?,?)",
				(run_id, step.step_id, step.title, step.mode, status, message, _utc_now()),
			)

	def list_steps(self, run_id: str) -> List[Dict[str, Any]]:
		with sqlite3.connect(self.db_path) as conn:
			rows = conn.execute(
				"SELECT run_id, step_id, title, mode, status, message, created_at FROM steps WHERE run_id = ? ORDER BY id ASC",
				(run_id,),
			).fetchall()
			return [
				{
					"run_id": str(row[0]),
					"step_id": str(row[1]),
					"title": str(row[2]),
					"mode": str(row[3]),
					"status": str(row[4]),
					"message": str(row[5]),
					"created_at": str(row[6]),
				}
				for row in rows
			]

	# ─────────────────────────────────────────────────────────────────────
	# TEST REPORTS — generated test lifecycle tracking
	# ─────────────────────────────────────────────────────────────────────

	def add_test_report(self, run_id: Optional[str], step_id: str, report: TestRunReport) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO task_tests(run_id, step_id, path, status, message, generated_at, deleted_at) VALUES(?,?,?,?,?,?,?)",
				(
					run_id,
					step_id,
					str(report.generated_path) if report.generated_path else None,
					"passed" if report.passed else "failed",
					report.message,
					_utc_now(),
					_utc_now() if report.generated_path and not report.generated_path.exists() else None,
				),
			)

	def latest_test_path_for_run(self, run_id: str) -> Optional[str]:
		with sqlite3.connect(self.db_path) as conn:
			row = conn.execute(
				"SELECT path FROM task_tests WHERE run_id = ? ORDER BY id DESC LIMIT 1",
				(run_id,),
			).fetchone()
			if not row:
				return None
			return str(row[0]) if row[0] else None

	# ─────────────────────────────────────────────────────────────────────
	# APPROVALS — human approval workflow
	# ─────────────────────────────────────────────────────────────────────

	def create_approval_request(self, action: str, reason: str, payload_json: str, run_id: Optional[str]) -> str:
		approval_id = str(uuid.uuid4())
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO approvals(approval_id, run_id, action, reason, payload_json, status, reviewer, reviewed_at, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
				(approval_id, run_id, action, reason, payload_json, "pending", None, None, _utc_now()),
			)
		return approval_id

	def list_approvals(self, status: str = "pending", limit: int = 50) -> List[Dict[str, Any]]:
		with sqlite3.connect(self.db_path) as conn:
			rows = conn.execute(
				"SELECT approval_id, run_id, action, reason, payload_json, status, reviewer, reviewed_at, created_at FROM approvals WHERE status = ? ORDER BY created_at DESC LIMIT ?",
				(status, limit),
			).fetchall()
			return [
				{
					"approval_id": str(row[0]),
					"run_id": str(row[1]) if row[1] else None,
					"action": str(row[2]),
					"reason": str(row[3]),
					"payload_json": str(row[4]) if row[4] else None,
					"status": str(row[5]),
					"reviewer": str(row[6]) if row[6] else None,
					"reviewed_at": str(row[7]) if row[7] else None,
					"created_at": str(row[8]),
				}
				for row in rows
			]

	def decide_approval(self, approval_id: str, decision: str, reviewer: str) -> bool:
		if decision not in {"approved", "rejected"}:
			raise ValueError("decision must be 'approved' or 'rejected'")
		with sqlite3.connect(self.db_path) as conn:
			cur = conn.execute(
				"UPDATE approvals SET status = ?, reviewer = ?, reviewed_at = ? WHERE approval_id = ?",
				(decision, reviewer, _utc_now(), approval_id),
			)
			return cur.rowcount > 0

	def get_approval_status(self, approval_id: str) -> Optional[str]:
		with sqlite3.connect(self.db_path) as conn:
			row = conn.execute(
				"SELECT status FROM approvals WHERE approval_id = ? LIMIT 1",
				(approval_id,),
			).fetchone()
			if not row:
				return None
			return str(row[0])

	# ─────────────────────────────────────────────────────────────────────
	# JOB QUEUE — autonomous background processing
	# ─────────────────────────────────────────────────────────────────────

	def enqueue_job(self, goal: str, mode: str, keep_tests: bool, run_id: Optional[str] = None) -> str:
		"""Add a goal to the background job queue."""
		job_id = run_id if run_id else str(uuid.uuid4())
		now = _utc_now()
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT OR REPLACE INTO jobs(job_id, goal, mode, keep_tests, status, result_json, error, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
				(job_id, goal, mode, 1 if keep_tests else 0, "queued", None, None, now, now),
			)
			conn.execute(
				"INSERT OR REPLACE INTO runs(run_id, goal, status, created_at, updated_at) VALUES(?,?,?,?,?)",
				(job_id, goal, "queued", now, now),
			)
		self.add_message(job_id, "user", goal)
		return job_id

	def claim_next_job(self) -> Optional[Dict[str, Any]]:
		"""Atomically claim the oldest queued job for processing."""
		with sqlite3.connect(self.db_path) as conn:
			row = conn.execute(
				"SELECT job_id, goal, mode, keep_tests FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1"
			).fetchone()
			if not row:
				return None
			job_id = str(row[0])
			conn.execute(
				"UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
				("running", _utc_now(), job_id),
			)
			return {
				"job_id": job_id,
				"goal": str(row[1]),
				"mode": str(row[2]),
				"keep_tests": bool(row[3]),
			}

	def finish_job(self, job_id: str, status: str, result_json: Optional[str] = None, error: Optional[str] = None) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"UPDATE jobs SET status = ?, result_json = ?, error = ?, updated_at = ? WHERE job_id = ?",
				(status, result_json, error, _utc_now(), job_id),
			)

	def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
		with sqlite3.connect(self.db_path) as conn:
			row = conn.execute(
				"SELECT job_id, goal, mode, keep_tests, status, result_json, error, created_at, updated_at FROM jobs WHERE job_id = ? LIMIT 1",
				(job_id,),
			).fetchone()
			if not row:
				return None
			return {
				"job_id": str(row[0]),
				"goal": str(row[1]),
				"mode": str(row[2]),
				"keep_tests": bool(row[3]),
				"status": str(row[4]),
				"result_json": str(row[5]) if row[5] else None,
				"error": str(row[6]) if row[6] else None,
				"created_at": str(row[7]),
				"updated_at": str(row[8]),
			}

	def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
		with sqlite3.connect(self.db_path) as conn:
			rows = conn.execute(
				"SELECT job_id, goal, mode, keep_tests, status, result_json, error, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?",
				(limit,),
			).fetchall()
			return [
				{
					"job_id": str(row[0]),
					"goal": str(row[1]),
					"mode": str(row[2]),
					"keep_tests": bool(row[3]),
					"status": str(row[4]),
					"result_json": str(row[5]) if row[5] else None,
					"error": str(row[6]) if row[6] else None,
					"created_at": str(row[7]),
					"updated_at": str(row[8]),
				}
				for row in rows
			]
