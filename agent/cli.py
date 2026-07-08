# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/cli.py — Command-Line Entry Point                                  ║
# ║                                                                            ║
# ║  Handles:                                                                  ║
# ║    • Argument parsing (--ui, --goal, --mode, --keep-tests, --worker)      ║
# ║    • Config loading and default generation                                 ║
# ║    • Starting the FastAPI/uvicorn server (--ui mode)                      ║
# ║    • Starting the background worker thread                                 ║
# ║    • Running a single goal in CLI mode (default)                           ║
# ║                                                                            ║
# ║  Usage examples:                                                           ║
# ║    python agent.py --ui                          # start web UI server     ║
# ║    python agent.py --goal "Write hello.py"       # run a goal via CLI     ║
# ║    python agent.py --goal "..." --keep-tests     # keep generated tests    ║
# ║    python agent.py --worker                      # background worker only  ║
# ║    uv run agent.py --ui                          # via uv (recommended)    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import json
import threading
import time
from pathlib import Path

from agent.config import AgentConfig, load_config, save_config
from agent.engine import AgentEngine
from agent.utils import get_remembered_working_dir


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG BOOTSTRAPPING
# ─────────────────────────────────────────────────────────────────────────────

def ensure_default_config(path: Path, root_dir: Path) -> AgentConfig:
    """Load config if it exists, or create a default config.yaml and return it."""
    if path.exists():
        return load_config(path)
    cfg = AgentConfig.default(root_dir=root_dir)
    save_config(path, cfg)
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    """Parse CLI args, create the engine, and run in the appropriate mode.

    Returns:
        Exit code (0 = success).
    """
    parser = argparse.ArgumentParser(description="Local real agent runner")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument("--goal", default="Implement requested task", help="Goal to run")
    parser.add_argument("--mode", default="coding", help="Task mode")
    parser.add_argument("--keep-tests", action="store_true", help="Keep generated tests after success")
    parser.add_argument("--ui", action="store_true", help="Run FastAPI UI server")
    parser.add_argument("--worker", action="store_true", help="Run background daemon worker")
    args = parser.parse_args()

    # ── Determine workspace root ─────────────────────────────────────────
    remembered = get_remembered_working_dir()
    root_dir = remembered if remembered else Path.cwd()
    config_path = root_dir / args.config

    # ── Load or create config and build the engine ───────────────────────
    cfg = ensure_default_config(config_path, root_dir=root_dir)
    engine = AgentEngine(cfg, root_dir=root_dir)

    # ── Background worker thread (runs jobs from the DB queue) ───────────
    if args.ui or args.worker:
        def _worker_loop():
            """Continuously dequeue and process jobs. Runs in a daemon thread."""
            while True:
                try:
                    engine.process_next_job()
                except Exception:
                    pass
                time.sleep(2)

        t = threading.Thread(target=_worker_loop, daemon=True)
        t.start()

    # ── UI mode: start FastAPI + uvicorn ─────────────────────────────────
    if args.ui:
        try:
            import uvicorn
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("uvicorn is required for --ui") from exc
        from agent.api import create_ui_app
        app = create_ui_app(engine)
        # Use 127.0.0.1 explicitly instead of localhost
        uvicorn.run(app, host=cfg.ui.host, port=cfg.ui.port, access_log=False)
        return 0

    # ── Worker-only mode: block forever (worker thread runs in background) ─
    if args.worker:
        while True:
            time.sleep(1000)
        return 0  # unreachable

    # ── CLI mode: run a single goal and print the result ─────────────────
    result = engine.run_goal(goal=args.goal, mode=args.mode, keep_tests=args.keep_tests)
    print(json.dumps(result, indent=2))
    return 0
