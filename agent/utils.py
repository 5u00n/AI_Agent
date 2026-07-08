# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/utils.py — Tiny Shared Helpers                                      ║
# ║                                                                            ║
# ║  Small utility functions used across the agent package:                    ║
# ║  • UTC timestamps                                                         ║
# ║  • Workspace directory memory (remembered working dir)                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# UTC TIMESTAMP HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _utc_now() -> str:
	"""Return the current UTC time as an ISO-8601 string.

	Used everywhere a timestamp is stored in the database or log.
	"""
	return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# WORKSPACE DIRECTORY MEMORY
# Persists the user's chosen working directory across agent restarts.
# Stored in a JSON settings file under the app data directory.
# ─────────────────────────────────────────────────────────────────────────────

_SETTINGS_FILE = Path("/Users/suren/.gemini/antigravity-ide/workspace_settings.json")


def get_remembered_working_dir() -> Optional[Path]:
	"""Load the previously saved working directory, or None if not set/deleted."""
	if _SETTINGS_FILE.exists():
		try:
			data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
			p = data.get("working_directory")
			if p:
				path_obj = Path(p)
				if path_obj.exists() and path_obj.is_dir():
					return path_obj
		except Exception:
			pass
	return None


def save_remembered_working_dir(path: Path) -> None:
	"""Persist the given path as the working directory for future sessions."""
	_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
	_SETTINGS_FILE.write_text(json.dumps({"working_directory": str(path.resolve())}), encoding="utf-8")
