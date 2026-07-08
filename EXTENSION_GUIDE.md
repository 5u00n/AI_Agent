# Extending the AI Agent

This guide explains where and how you can add your own features to the AI Agent framework.

## 1. Adding UI Features
**File:** `agent/ui.py`
- The entire frontend is contained in the `render_ui_html` function. 
- You can add new HTML elements (buttons, modals, views), modify the CSS `<style>` block, or add custom JavaScript logic in the `<script>` block.
- **Example:** You could add a new button in the sidebar to export chat history, and wire it up to a new JavaScript function that calls a backend API.

## 2. Adding Backend API Routes
**File:** `agent/api.py`
- All HTTP endpoints are defined inside the `create_ui_app` function using FastAPI.
- If your new UI feature needs to fetch data or trigger an action, add a new `@app.get(...)` or `@app.post(...)` route here.
- **Example:** Add a `@app.get("/export")` endpoint that queries the database (`engine.store`) and returns a CSV or JSON file of the current session.

## 3. Adding Built-in Tools for the Agent
**File:** `agent/tools.py`
- The `ToolRegistry` class handles everything the agent is allowed to "do" (file operations, shell commands, web fetching).
- To add a new core tool, add a new `if tool_name == "your_tool_name":` block inside the `call` method.
- Return a dictionary with at least `{"ok": True/False, ...}`.
- **Note:** You can also add tools without touching the core code by creating Python files in the `custom_tools/` folder. The agent automatically detects any `.py` file there as a dynamic tool that must define a `run(args: dict) -> dict` function.

## 4. Modifying the Agent's Core Loop
**File:** `agent/orchestrator.py`
- The `PlannerExecutorVerifier` class contains the core logic: `_plan` (break down goals), `_execute` (choose tools), and `_verify` (check results).
- If you want to change how the agent thinks, add a new phase (e.g., a "Reflection" phase), or modify how prompts are sent to the LLM, this is the file to edit.

## 5. Entry Point & CLI
**File:** `agent.py` and `agent/cli.py`
- If you want to add new command-line arguments (e.g., `--debug`, `--verbose`), modify the `argparse` setup in `agent/cli.py`.

## Summary Workflow for a New Feature
1. **Frontend:** Add the HTML/JS in `agent/ui.py`.
2. **Backend:** Add the supporting FastAPI route in `agent/api.py`.
3. **Agent Capability:** If the feature gives the agent a new capability, add it to `agent/tools.py` or as a file in the `custom_tools/` directory.
