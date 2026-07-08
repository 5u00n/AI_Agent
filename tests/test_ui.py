import json
from pathlib import Path
from fastapi.testclient import TestClient

from agent import AgentConfig, AgentEngine, create_ui_app

def test_ui_endpoints(tmp_path: Path) -> None:
    # Setup engine
    cfg = AgentConfig.default(root_dir=tmp_path)
    engine = AgentEngine(cfg, root_dir=tmp_path)
    
    # Setup FastAPI app
    app = create_ui_app(engine)
    client = TestClient(app)

    # 1. Test Root Page (HTML)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI Agent Chat" in response.text

    # 2. Test Settings Endpoint
    response = client.get("/settings")
    assert response.status_code == 200
    settings = response.json()
    assert settings["ui"]["port"] == 8000
    assert settings["llm"]["provider"] == "lmstudio"

    # 3. Test Test Policy Update Endpoint
    response = client.put(
        "/settings/test-policy",
        json={"auto_generate_tests": False}
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert engine.cfg.test_policy.auto_generate_tests is False

    # 4. Test Runs List
    response = client.get("/runs")
    assert response.status_code == 200
    assert "runs" in response.json()

    # 5. Test Approvals List
    response = client.get("/approvals")
    assert response.status_code == 200
    assert "approvals" in response.json()

    # 6. Test Models Endpoint (might return empty if no server running, but should return 200)
    response = client.get("/models?provider=lmstudio")
    assert response.status_code == 200
    assert "models" in response.json()
    assert response.json()["provider"] == "lmstudio"

    # 7. Test LLM Settings Update Endpoint
    response = client.put(
        "/settings/llm",
        json={"provider": "ollama", "max_tokens": 2048}
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert engine.cfg.llm.provider == "ollama"
    assert engine.cfg.llm.max_tokens == 2048

    # 8. Test Messages Endpoint
    run_id = engine.store.create_run("test messages goal")
    engine.store.add_message(run_id, "user", "hello message")
    engine.store.add_message(run_id, "agent", "hello back")
    response = client.get(f"/runs/{run_id}/messages")
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["content"] == "hello message"
    assert messages[1]["content"] == "hello back"

    # 9. Test Delete Run Endpoint
    response = client.delete(f"/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["ok"] is True

    # Confirm it is deleted
    response2 = client.get(f"/runs/{run_id}/messages")
    assert response2.status_code == 200
    assert len(response2.json()["messages"]) == 0

    # 10. Test Custom Tools API Endpoints
    response = client.get("/custom-tools")
    assert response.status_code == 200
    assert "tools" in response.json()

    # Create a custom tool via API
    response = client.post(
        "/custom-tools",
        json={
            "name": "add_numbers",
            "description": "Adds two numbers",
            "code": "def run(args: dict):\n    return {'result': int(args['a']) + int(args['b'])}"
        }
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    # Confirm it is in the list
    response = client.get("/custom-tools")
    assert "add_numbers" in response.json()["tools"]

    # 11. Test Skills API Endpoints
    response = client.get("/skills")
    assert response.status_code == 200
    assert "skills" in response.json()

    # Create a skill via API
    response = client.post(
        "/skills",
        json={
            "name": "math_solver",
            "description": "Expert in solving math",
            "instructions": "# Math Solver Skill\nSolve mathematical equations."
        }
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    # Confirm it is in the list
    response = client.get("/skills")
    assert any(s["name"] == "math_solver" for s in response.json()["skills"])
