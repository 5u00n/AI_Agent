import sys
from pathlib import Path
from agent import MCPClientRegistry

def test_mcp_registry_registers_server_and_reports_stub_call() -> None:
    mcp = MCPClientRegistry()
    mcp.register("filesystem", {"transport": "stdio", "command": "mcp-fs"})

    names = mcp.list_servers()
    assert "filesystem" in names

    result = mcp.call("filesystem", "read_file", {"path": "x"})
    assert result["ok"] is False
    assert "no such file or directory" in result["error"].lower() or "not found" in result["error"].lower()


def test_mcp_registry_stdio_execution(tmp_path: Path) -> None:
    server_path = tmp_path / "fake_mcp_server.py"
    server_path.write_text(
        """
import json
import sys


def read_message():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def write_message(obj):
    sys.stdout.write(json.dumps(obj) + '\\n')
    sys.stdout.flush()


while True:
    try:
        req = read_message()
        if req is None:
            break
    except Exception:
        break
        
    method = req.get('method')
    if method == 'initialize':
        write_message({'jsonrpc': '2.0', 'id': req['id'], 'result': {'capabilities': {}, 'protocolVersion': '2024-11-05', 'serverInfo': {'name': 'fake', 'version': '1.0'}}})
    elif method == 'notifications/initialized':
        pass
    elif method == 'tools/call':
        params = req.get('params', {})
        write_message({
            'jsonrpc': '2.0', 
            'id': req['id'], 
            'result': {
                'content': [{'type': 'text', 'text': json.dumps({'echo': params})}],
                'isError': False
            }
        })
    elif method == 'tools/list':
        write_message({'jsonrpc': '2.0', 'id': req['id'], 'result': {'tools': [{'name': 'echoTool', 'description': 'echo', 'inputSchema': {'type': 'object', 'properties': {}}}]}})
    else:
        write_message({'jsonrpc': '2.0', 'id': req.get('id'), 'result': {'content': [], 'isError': False}})
""".strip()
        + "\n",
        encoding="utf-8",
    )

    mcp = MCPClientRegistry()
    mcp.register(
        "local",
        {"transport": "stdio", "command": sys.executable, "args": [str(server_path)]},
    )
    out = mcp.call("local", "echoTool", {"hello": "world"})

    assert out["ok"] is True
    assert "echoTool" in str(out)
