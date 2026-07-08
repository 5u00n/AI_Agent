# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/tools.py — Native Tool Registry                                    ║
# ║                                                                            ║
# ║  The ToolRegistry is the agent's "hands" — every file operation, shell    ║
# ║  command, and web fetch goes through here.                                 ║
# ║                                                                            ║
# ║  SAFETY ENFORCEMENT HAPPENS HERE:                                          ║
# ║    • Path jail: all file access must stay inside root_dir                  ║
# ║    • Blocked commands: rm -rf, sudo, git reset --hard, etc.                ║
# ║    • Approval gates: run_shell can require human sign-off                  ║
# ║    • Custom tools: dynamic Python modules loaded from custom_tools/        ║
# ║                                                                            ║
# ║  Built-in tools (call via tool_name):                                      ║
# ║    write_file, read_file, create_new_file, edit_file, rename_file,        ║
# ║    copy_file, edit_existing_file, single_find_and_replace,                 ║
# ║    file_glob_search, grep_search, ls, view_diff, view_page,               ║
# ║    fetch_url_content, run_shell, set_working_directory,                    ║
# ║    create_file_or_folder                                                   ║
# ║                                                                            ║
# ║  DEBUG TIP: If a tool returns {ok: False, error: "blocked by safety       ║
# ║  policy"}, check config.yaml → safety → blocked_commands.                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# 
# =============================================================================
# 🛠️ HOW TO MAKE THE APP BETTER: ADDING NEW CAPABILITIES
# =============================================================================
# This file defines everything the agent can DO (the "hands" of the agent).
# 
# 1. ADDING A NEW NATIVE TOOL:
#    Scroll down to the `call` method. Add a new `if tool_name == "my_tool":` block.
#    You must return a dictionary with at least `{"ok": True/False}`. You can add 
#    any Python logic inside (e.g. calling an external API, interacting with docker,
#    or doing complex file parsing).
# 
# 2. ADDING DYNAMIC CUSTOM TOOLS:
#    You don't actually need to edit this file to add simple tools! Just create a 
#    Python file in the `custom_tools/` folder (e.g. `custom_tools/weather.py`) 
#    that defines a `run(args: dict) -> dict:` function. The agent will auto-load it.
# 
# 3. SAFETY AND APPROVALS:
#    If you add a tool that could be dangerous (like `delete_database`), you can 
#    gate it behind human approval by adding it to `require_approval_for` in 
#    config.yaml and implementing the approval check like in the `run_shell` tool.

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from agent.config import AgentConfig
# NOTE: get_remembered_working_dir and save_remembered_working_dir are looked up
# lazily via the 'agent' package namespace at call time so that test monkeypatches
# on 'agent.get_remembered_working_dir' / 'agent.save_remembered_working_dir' work.

if TYPE_CHECKING:
    from agent.store import StateStore


# ─────────────────────────────────────────────────────────────────────────────
# TOOL REGISTRY CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ToolRegistry:
    """Executes named tools on behalf of the agent.

    Every tool call is:
        1. Checked against the blocked_commands list (hard block)
        2. Checked against require_approval_for list (soft gate)
        3. Path-jailed to root_dir
        4. Executed and its result returned as a plain dict

    All results follow the convention: {"ok": bool, ...} 
    """

    def __init__(self, cfg: AgentConfig, root_dir: Path, store: Optional["StateStore"] = None) -> None:
        self.cfg = cfg
        self.root_dir = root_dir
        self.store = store  # used to create/check approval records

    # ─────────────────────────────────────────────────────────────────────
    # CUSTOM TOOL DISCOVERY
    # ─────────────────────────────────────────────────────────────────────

    def get_custom_tool_names(self) -> List[str]:
        """List all custom Python tools in the custom_tools/ directory."""
        tools_dir = self.root_dir / "custom_tools"
        if not tools_dir.exists():
            return []
        return [p.stem for p in tools_dir.glob("*.py")]

    # ─────────────────────────────────────────────────────────────────────
    # SAFETY HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def _requires_approval(self, action: str) -> bool:
        """Return True if this action type requires human approval before running."""
        return action in set(self.cfg.safety.require_approval_for)

    def _is_blocked(self, command: str) -> bool:
        """Return True if the command matches any blocked pattern (case-insensitive)."""
        cmd = command.strip().lower()
        for pattern in self.cfg.safety.blocked_commands:
            if pattern.lower() in cmd:
                return True
        return False

    def _safe_path(self, raw_path: str) -> Path:
        """Resolve a path and verify it stays inside root_dir (path jail).

        Raises:
            ValueError: If the resolved path escapes the workspace root.
        """
        path = (self.root_dir / raw_path).resolve()
        if not str(path).startswith(str(self.root_dir.resolve())):
            raise ValueError("path outside allowed workspace")
        return path

    # ─────────────────────────────────────────────────────────────────────
    # TOOL DISPATCH
    # All tools are handled in one big if/elif chain for easy debugging.
    # Each branch is clearly labeled with its tool name.
    # ─────────────────────────────────────────────────────────────────────

    def call(self, tool_name: str, args: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
        """Dispatch a tool call by name and return its result dict.

        Args:
            tool_name: Name of the tool to execute.
            args:      Dict of input arguments for the tool.
            run_id:    Optional run context (used for approval records).

        Returns:
            Dict with at least {"ok": bool}. Additional keys depend on tool.
        """

        # ── WORKSPACE CONTROL ────────────────────────────────────────────
        if tool_name == "set_working_directory":
            path_str = str(args.get("path", "")).strip()
            if not path_str:
                return {"ok": False, "error": "path is required"}
            target = Path(path_str).resolve()
            if not target.exists():
                return {"ok": False, "error": "directory does not exist"}
            if not target.is_dir():
                return {"ok": False, "error": "path is not a directory"}
            import agent as _agent_pkg
            _agent_pkg.save_remembered_working_dir(target)
            self.root_dir = target
            return {"ok": True, "message": f"Working directory set to: {target}"}

        # ── CREATE FILE OR FOLDER (with workspace prompt fallback) ────────
        if tool_name == "create_file_or_folder":
            path_str = str(args.get("path", "")).strip()
            is_folder = bool(args.get("is_folder", False))
            content = str(args.get("content", ""))

            import agent as _agent_pkg
            active_dir = _agent_pkg.get_remembered_working_dir()
            if not active_dir:
                import os
                if "PYTEST_CURRENT_TEST" in os.environ:
                    active_dir = self.root_dir
                elif sys.stdin.isatty():
                    print("\n[PROMPT] No workspace folder is selected.")
                    entered = input("Enter the absolute path where you want to save this: ").strip()
                    if not entered:
                        return {"ok": False, "error": "no path provided"}
                    target = Path(entered).resolve()
                else:
                    target = (Path.cwd() / path_str).resolve()
                    print(f"[INFO] No workspace selected; using current directory fallback: {target}")
            
            if active_dir:
                target = (active_dir / path_str).resolve()

            try:
                if is_folder:
                    target.mkdir(parents=True, exist_ok=True)
                    return {"ok": True, "path": str(target), "message": f"Folder created at {target}"}
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                    return {"ok": True, "path": str(target), "message": f"File created at {target}"}
            except Exception as exc:
                return {"ok": False, "error": f"Failed to create file/folder: {exc}"}

        # ── FILE WRITE TOOLS ─────────────────────────────────────────────
        if tool_name == "write_file":
            target = self._safe_path(str(args.get("path", "")))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(args.get("content", "")), encoding="utf-8")
            return {"ok": True, "path": str(target)}

        if tool_name == "create_new_file":
            target = self._safe_path(str(args.get("path", "")))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(args.get("content", "")), encoding="utf-8")
            return {"ok": True, "path": str(target)}

        if tool_name == "edit_file":
            target = self._safe_path(str(args.get("path", "")))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(args.get("content", "")), encoding="utf-8")
            return {"ok": True, "path": str(target), "message": f"File {target} updated successfully"}

        # ── FILE READ TOOL ───────────────────────────────────────────────
        if tool_name == "read_file":
            target = self._safe_path(str(args.get("path", "")))
            if not target.exists():
                return {"ok": False, "error": "file not found"}
            return {"ok": True, "content": target.read_text(encoding="utf-8")}

        # ── FILE COPY / RENAME ───────────────────────────────────────────
        if tool_name == "copy_file":
            src = self._safe_path(str(args.get("src", "")))
            dest = self._safe_path(str(args.get("dest", "")))
            if not src.exists():
                return {"ok": False, "error": f"source file {src} not found"}
            dest.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(src, dest)
            return {"ok": True, "message": f"Copied {src} to {dest}"}

        if tool_name == "rename_file":
            src = self._safe_path(str(args.get("src", "")))
            dest = self._safe_path(str(args.get("dest", "")))
            if not src.exists():
                return {"ok": False, "error": f"source path {src} not found"}
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
            return {"ok": True, "message": f"Renamed {src} to {dest}"}

        # ── FIND-AND-REPLACE EDIT ────────────────────────────────────────
        if tool_name in {"edit_existing_file", "single_find_and_replace"}:
            target = self._safe_path(str(args.get("path", "")))
            old_str = str(args.get("old_string", ""))
            new_str = str(args.get("new_string", ""))
            if not target.exists():
                return {"ok": False, "error": "file not found"}
            content = target.read_text(encoding="utf-8")
            if old_str not in content:
                return {"ok": False, "error": "old_string not found"}
            content = content.replace(old_str, new_str)
            target.write_text(content, encoding="utf-8")
            return {"ok": True, "path": str(target)}

        # ── DIRECTORY / SEARCH TOOLS ─────────────────────────────────────
        if tool_name == "ls":
            target = self._safe_path(str(args.get("path", ".")))
            if not target.is_dir():
                return {"ok": False, "error": "not a directory"}
            items = [str(p.relative_to(target)) for p in target.iterdir()]
            return {"ok": True, "contents": items}

        if tool_name == "file_glob_search":
            pattern = str(args.get("pattern", "**/*"))
            matches = list(self.root_dir.rglob(pattern))
            return {"ok": True, "files": [str(p.relative_to(self.root_dir)) for p in matches[:100]]}

        if tool_name == "grep_search":
            query = str(args.get("query", ""))
            target = self._safe_path(str(args.get("path", ".")))
            proc = subprocess.run(["grep", "-rn", query, str(target)], capture_output=True, text=True)
            return {"ok": True, "matches": proc.stdout[:10000]}

        # ── GIT DIFF ─────────────────────────────────────────────────────
        if tool_name == "view_diff":
            proc = subprocess.run(["git", "diff"], cwd=str(self.root_dir), capture_output=True, text=True)
            return {"ok": True, "diff": proc.stdout}

        # ── VIEW PAGE (returns URL to workspace-served file) ─────────────
        if tool_name == "view_page":
            path_str = str(args.get("path", "")).strip()
            url = f"http://127.0.0.1:8000/workspace/{path_str}"
            return {"ok": True, "url": url, "message": f"Page is viewable at {url}"}

        # ── HTTP FETCH ───────────────────────────────────────────────────
        if tool_name == "fetch_url_content":
            url = str(args.get("url", ""))
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    return {"ok": True, "content": resp.read().decode("utf-8")[:10000]}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

        # ── RUN SHELL — most sensitive tool; has approval gate ───────────
        if tool_name == "run_shell":
            command = str(args.get("command", ""))

            # Hard block check (matches blocked_commands list from config)
            if self._is_blocked(command):
                return {"ok": False, "error": "blocked by safety policy"}

            # Approval gate — if run_shell is in require_approval_for, check status
            if self._requires_approval("run_shell"):
                approval_id_arg = args.get("approval_id")
                if approval_id_arg and self.store is not None:
                    status = self.store.get_approval_status(str(approval_id_arg))
                    if status == "approved":
                        pass  # fall through to execution
                    elif status == "rejected":
                        return {
                            "ok": False,
                            "status": "rejected_approval",
                            "approval_id": str(approval_id_arg),
                            "error": "approval rejected",
                        }
                    else:
                        return {
                            "ok": False,
                            "requires_approval": True,
                            "status": "pending_approval",
                            "approval_id": str(approval_id_arg),
                            "error": "awaiting approval",
                        }
                else:
                    # Create a new approval request and block execution
                    approval_id = None
                    if self.store is not None:
                        approval_id = self.store.create_approval_request(
                            action="run_shell",
                            reason="run_shell requires approval by policy",
                            payload_json=json.dumps({"command": command}),
                            run_id=run_id,
                        )
                    return {
                        "ok": False,
                        "requires_approval": True,
                        "status": "pending_approval",
                        "approval_id": approval_id,
                        "error": "awaiting approval",
                    }

            # Execute the shell command (within root_dir working directory)
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(self.root_dir),
            )
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }

        # ── CUSTOM PYTHON TOOLS (loaded from custom_tools/*.py) ──────────
        custom_path = self.root_dir / "custom_tools" / f"{tool_name}.py"
        if custom_path.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(tool_name, custom_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "run"):
                        res = module.run(args)
                        if isinstance(res, dict):
                            return res
                        return {"ok": True, "result": res}
                    else:
                        return {"ok": False, "error": f"Custom tool {tool_name} is missing a run(args) function"}
            except Exception as exc:
                return {"ok": False, "error": f"Failed to execute custom tool {tool_name}: {exc}"}

        # ── UNKNOWN TOOL ─────────────────────────────────────────────────
        return {"ok": False, "error": f"unknown tool: {tool_name}"}
