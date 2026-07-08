# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/api.py — FastAPI REST Routes                                       ║
# ║                                                                            ║
# ║  Defines all HTTP endpoints for the agent's local web UI and API.         ║
# ║                                                                            ║
# ║  Route groups:                                                             ║
# ║    GET  /                           → serve the HTML UI                   ║
# ║    GET  /settings                   → current config as JSON              ║
# ║    PUT  /settings/llm               → update LLM settings                 ║
# ║    PUT  /settings/test-policy       → update test policy flags             ║
# ║    GET  /models                     → list models from provider            ║
# ║    POST /models/auto-detect         → detect provider + assign models      ║
# ║    GET/POST/DELETE /settings/mcp    → MCP server management               ║
# ║    GET/DELETE /runs                 → run history                          ║
# ║    GET /runs/{id}/steps             → step timeline                        ║
# ║    GET /runs/{id}/messages          → chat history                         ║
# ║    POST /runs/{id}/stop             → stop a running job                   ║
# ║    PUT /runs/{id}/goal              → rename a run                         ║
# ║    GET/POST /custom-tools           → custom tool management               ║
# ║    GET/POST /skills                 → skill management                     ║
# ║    GET/POST /approvals              → approval workflow                    ║
# ║    POST /approvals/{id}/decision    → approve or reject                    ║
# ║    POST /run                        → submit a new goal (enqueues job)     ║
# ║                                                                            ║
# ║  DEBUG TIP: FastAPI auto-generates interactive API docs at:               ║
# ║      http://127.0.0.1:8000/docs                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# 
# =============================================================================
# 🛠️ HOW TO MAKE THE APP BETTER: EXTENDING THE BACKEND API
# =============================================================================
# This file contains all the REST API endpoints the frontend uses to talk to the
# agent backend.
#
# 1. ADDING NEW DATA ENDPOINTS:
#    Scroll down inside the `create_ui_app` function. You can add new routes like:
#    @app.get("/my-new-data")
#    def get_my_data():
#        # fetch data from engine.store (database)
#        return {"ok": True, "data": ...}
#
# 2. TRIGGERING NEW AGENT ACTIONS:
#    If you want a button in the UI to make the agent do something specific, add a 
#    POST route here, use the `payload` parameter to get data from the UI, and 
#    then interact with `engine` (e.g. `engine.store.enqueue_job(...)`).
#
# 3. INTERACTING WITH THE DATABASE:
#    You have full access to `engine.store` here, which wraps SQLite. See `agent/store.py`
#    for the available methods, or add your own database queries there and call them here.

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import json
import sqlite3
from dataclasses import asdict
from typing import Any, Dict

from agent.config import MCPServerConfig, save_config
from agent.engine import AgentEngine
from agent.ui import render_ui_html
from agent.utils import _utc_now


# ─────────────────────────────────────────────────────────────────────────────
# APP FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def create_ui_app(engine: AgentEngine):
    """Create and configure the FastAPI application.

    All routes are defined inside this function (closure) so they have access
    to the engine instance without globals.

    Returns:
        FastAPI app ready to pass to uvicorn.run().
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import HTMLResponse
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("fastapi is required for UI mode") from exc

    app = FastAPI(title="Local Agent UI API", version="1.0.0")

    # Serve workspace files statically at /workspace/<path>
    from fastapi.staticfiles import StaticFiles
    app.mount("/workspace", StaticFiles(directory=str(engine.root_dir)), name="workspace")

    # ─────────────────────────────────────────────────────────────────────
    # ROOT — serve the HTML UI
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/", response_class=HTMLResponse)
    def root_page():
        content = render_ui_html(engine.cfg)
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    # ─────────────────────────────────────────────────────────────────────
    # SETTINGS
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/settings")
    def get_settings() -> Dict[str, Any]:
        return engine.cfg.to_dict()

    @app.put("/settings/llm")
    def update_llm_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in payload.items():
            if not hasattr(engine.cfg.llm, key):
                raise HTTPException(status_code=400, detail=f"Unknown llm setting key: {key}")
            setattr(engine.cfg.llm, key, value)
        save_config(engine.root_dir / "config.yaml", engine.cfg)
        return {"ok": True, "llm": engine.cfg.llm.__dict__}

    @app.put("/settings/test-policy")
    def update_test_policy(payload: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in payload.items():
            if not hasattr(engine.cfg.test_policy, key):
                raise HTTPException(status_code=400, detail=f"Unknown test policy key: {key}")
            setattr(engine.cfg.test_policy, key, value)
        return {"ok": True, "test_policy": asdict(engine.cfg.test_policy)}

    # ─────────────────────────────────────────────────────────────────────
    # MODELS — list available models from LM Studio or Ollama
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/models")
    def list_models(provider: str = "") -> Dict[str, Any]:
        import httpx
        prov = provider or engine.cfg.llm.provider
        if prov == "lmstudio":
            url = engine.cfg.llm.base_url_lmstudio + "/models"
        else:
            url = engine.cfg.llm.base_url_ollama + "/api/tags"
        models = []
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if prov == "lmstudio":
                        models = [m.get("id") for m in data.get("data", [])]
                    else:
                        models = [m.get("name") for m in data.get("models", [])]
        except Exception:
            pass
        return {"provider": prov, "models": models}

    @app.post("/models/auto-detect")
    def auto_detect_and_allocate() -> Dict[str, Any]:
        """Auto-detect running provider and assign its first model to all roles."""
        import httpx
        lm_models = []
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(engine.cfg.llm.base_url_lmstudio + "/models")
                if resp.status_code == 200:
                    lm_models = [m.get("id") for m in resp.json().get("data", [])]
        except Exception:
            pass

        ollama_models = []
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(engine.cfg.llm.base_url_ollama + "/api/tags")
                if resp.status_code == 200:
                    ollama_models = [m.get("name") for m in resp.json().get("models", [])]
        except Exception:
            pass

        if lm_models:
            prov, models = "lmstudio", lm_models
        elif ollama_models:
            prov, models = "ollama", ollama_models
        else:
            raise HTTPException(status_code=400, detail="No running local model providers found (LM Studio or Ollama).")

        model_name = models[0]
        engine.cfg.llm.provider = prov
        engine.cfg.llm.model_planner = model_name
        engine.cfg.llm.model_executor = model_name
        engine.cfg.llm.model_verifier = model_name
        save_config(engine.root_dir / "config.yaml", engine.cfg)

        return {
            "ok": True,
            "provider": prov,
            "models": models,
            "allocated": {
                "planner": model_name,
                "executor": model_name,
                "verifier": model_name,
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # WORKSPACE FOLDER SELECTOR (macOS Native)
    # ─────────────────────────────────────────────────────────────────────

    @app.post("/workspace/select")
    def select_workspace_folder() -> Dict[str, Any]:
        """Trigger the macOS native folder picker via AppleScript."""
        import subprocess
        try:
            result = subprocess.run(
                ["osascript", "-e", 'POSIX path of (choose folder with prompt "Select Workspace Folder")'],
                capture_output=True,
                text=True,
                check=True
            )
            path = result.stdout.strip()
            if path:
                # Update the active tool registry root_dir directly so the backend remembers
                from pathlib import Path
                target = Path(path).resolve()
                import agent.utils as _utils
                _utils.save_remembered_working_dir(target)
                engine.tools.root_dir = target
                return {"ok": True, "path": path}
            return {"ok": False, "error": "Folder selection cancelled"}
        except subprocess.CalledProcessError:
            return {"ok": False, "error": "Folder selection cancelled"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    # MCP SERVER MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/settings/mcp")
    def list_mcp_servers() -> Dict[str, Any]:
        return {"servers": {k: asdict(v) for k, v in engine.cfg.mcp.servers.items()}}

    @app.post("/settings/mcp")
    def add_mcp_server(payload: Dict[str, Any]) -> Dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        command = str(payload.get("command", "")).strip()
        args_raw = payload.get("args", [])
        if isinstance(args_raw, str):
            args = [a.strip() for a in args_raw.split(",") if a.strip()]
        else:
            args = [str(a).strip() for a in args_raw if str(a).strip()]
        if not name or not command:
            raise HTTPException(status_code=400, detail="name and command are required")
        engine.cfg.mcp.servers[name] = MCPServerConfig(command=command, args=args)
        save_config(engine.root_dir / "config.yaml", engine.cfg)
        engine.mcp.register(name, {"command": command, "args": args, "transport": "stdio"})
        return {"ok": True, "servers": {k: asdict(v) for k, v in engine.cfg.mcp.servers.items()}}

    @app.delete("/settings/mcp/{name}")
    def remove_mcp_server(name: str) -> Dict[str, Any]:
        if name in engine.cfg.mcp.servers:
            del engine.cfg.mcp.servers[name]
            save_config(engine.root_dir / "config.yaml", engine.cfg)
        if name in engine.mcp._servers:
            del engine.mcp._servers[name]
        if name in engine.mcp._sessions:
            del engine.mcp._sessions[name]
        return {"ok": True, "servers": {k: asdict(v) for k, v in engine.cfg.mcp.servers.items()}}

    # ─────────────────────────────────────────────────────────────────────
    # RUN MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/runs")
    def list_runs(limit: int = 20) -> Dict[str, Any]:
        return {"runs": engine.store.list_runs(limit=limit)}

    @app.delete("/runs/{run_id}")
    def delete_run_endpoint(run_id: str) -> Dict[str, Any]:
        engine.store.delete_run(run_id)
        return {"ok": True}

    @app.get("/runs/{run_id}/steps")
    def list_steps(run_id: str) -> Dict[str, Any]:
        return {"run_id": run_id, "steps": engine.store.list_steps(run_id)}

    @app.get("/runs/{run_id}/messages")
    def get_run_messages(run_id: str) -> Dict[str, Any]:
        return {"messages": engine.store.list_messages(run_id)}

    @app.delete("/messages/{message_id}")
    def delete_message_endpoint(message_id: int) -> Dict[str, Any]:
        engine.store.delete_message(message_id)
        return {"ok": True}

    @app.post("/runs/{run_id}/stop")
    def stop_run_endpoint(run_id: str) -> Dict[str, Any]:
        engine.store.set_run_status(run_id, "stopped")
        # Also mark the job as failed if it exists
        with sqlite3.connect(engine.store.db_path) as conn:
            conn.execute(
                "UPDATE jobs SET status = 'failed', error = 'Stopped by user' WHERE job_id = ?",
                (run_id,),
            )
        return {"ok": True}

    @app.put("/runs/{run_id}/goal")
    def update_run_goal_endpoint(run_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        goal = str(payload.get("goal", "")).strip()
        if not goal:
            raise HTTPException(status_code=400, detail="goal is required")
        now = _utc_now()
        with sqlite3.connect(engine.store.db_path) as conn:
            conn.execute(
                "UPDATE runs SET goal = ?, updated_at = ? WHERE run_id = ?",
                (goal, now, run_id),
            )
            conn.execute(
                "UPDATE jobs SET goal = ?, updated_at = ? WHERE job_id = ?",
                (goal, now, run_id),
            )
            conn.execute(
                "UPDATE messages SET content = ? WHERE run_id = ? AND role = 'user' "
                "AND id = (SELECT id FROM messages WHERE run_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1)",
                (goal, run_id, run_id),
            )
        return {"ok": True}

    # ─────────────────────────────────────────────────────────────────────
    # CUSTOM TOOLS
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/custom-tools")
    def list_custom_tools() -> Dict[str, Any]:
        return {"tools": engine.tools.get_custom_tool_names()}

    @app.post("/custom-tools")
    def add_custom_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        description = str(payload.get("description", "")).strip()
        code = str(payload.get("code", "")).strip()
        if not name or not code:
            raise HTTPException(status_code=400, detail="name and code are required")
        tools_dir = engine.root_dir / "custom_tools"
        tools_dir.mkdir(exist_ok=True)
        tool_path = tools_dir / f"{name}.py"
        file_content = f'"""\n{description}\n"""\n\n{code}\n'
        tool_path.write_text(file_content, encoding="utf-8")
        return {"ok": True}

    # ─────────────────────────────────────────────────────────────────────
    # SKILLS MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/skills")
    def list_skills_endpoint() -> Dict[str, Any]:
        skills_dir = engine.root_dir / ".agents" / "skills"
        if not skills_dir.exists():
            return {"skills": []}
        skills = []
        for p in skills_dir.iterdir():
            if p.is_dir() and (p / "SKILL.md").exists():
                content = (p / "SKILL.md").read_text(encoding="utf-8")
                name = p.name
                desc = ""
                for line in content.splitlines():
                    if line.strip().startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip('"').strip("'")
                    elif line.strip().startswith("description:"):
                        desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                skills.append({"name": name, "description": desc, "folder": p.name})
        return {"skills": skills}

    @app.post("/skills")
    def add_skill_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        description = str(payload.get("description", "")).strip()
        instructions = str(payload.get("instructions", "")).strip()
        if not name or not instructions:
            raise HTTPException(status_code=400, detail="name and instructions are required")

        safe_folder = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
        if not safe_folder:
            safe_folder = "custom_skill"

        skills_dir = engine.root_dir / ".agents" / "skills"
        skill_folder = skills_dir / safe_folder
        skill_folder.mkdir(parents=True, exist_ok=True)

        skill_md = f"""---
name: {name}
description: {description}
---

# Instructions
{instructions}
"""
        (skill_folder / "SKILL.md").write_text(skill_md, encoding="utf-8")
        return {"ok": True}

    # ─────────────────────────────────────────────────────────────────────
    # APPROVALS — human approval workflow
    # ─────────────────────────────────────────────────────────────────────

    @app.get("/approvals")
    def list_approvals(status: str = "pending", limit: int = 50) -> Dict[str, Any]:
        return {"approvals": engine.store.list_approvals(status=status, limit=limit)}

    @app.post("/approvals/request")
    def request_approval(payload: Dict[str, Any]) -> Dict[str, Any]:
        action = str(payload.get("action", "")).strip()
        reason = str(payload.get("reason", "")).strip()
        if not action or not reason:
            raise HTTPException(status_code=400, detail="action and reason are required")
        run_id = payload.get("run_id")
        payload_json = json.dumps(payload.get("payload", {}))
        approval_id = engine.store.create_approval_request(
            action=action,
            reason=reason,
            payload_json=payload_json,
            run_id=str(run_id) if run_id else None,
        )
        return {"ok": True, "approval_id": approval_id}

    @app.post("/approvals/{approval_id}/decision")
    def decide_approval(approval_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        decision = str(payload.get("decision", "")).strip().lower()
        reviewer = str(payload.get("reviewer", "local-user")).strip() or "local-user"
        if decision not in {"approved", "rejected"}:
            raise HTTPException(status_code=400, detail="decision must be approved or rejected")
        updated = engine.store.decide_approval(
            approval_id=approval_id,
            decision=decision,
            reviewer=reviewer,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="approval not found")
        return {"ok": True, "approval_id": approval_id, "status": decision}

    # ─────────────────────────────────────────────────────────────────────
    # SUBMIT GOAL — enqueue a new job
    # ─────────────────────────────────────────────────────────────────────

    @app.post("/run")
    def run_task(payload: Dict[str, Any]) -> Dict[str, Any]:
        goal = str(payload.get("goal", "")).strip()
        if not goal:
            raise HTTPException(status_code=400, detail="goal is required")
        mode = str(payload.get("mode", "coding"))
        keep_tests = bool(payload.get("keep_tests", False))
        run_id = payload.get("run_id")
        job_id = engine.store.enqueue_job(goal=goal, mode=mode, keep_tests=keep_tests, run_id=run_id)
        return {"ok": True, "job_id": job_id}

    return app
