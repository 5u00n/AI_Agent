# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/mcp_client.py — MCP (Model Context Protocol) Client Registry       ║
# ║                                                                            ║
# ║  Connects to external MCP servers over stdio and lets the agent call       ║
# ║  tools that live in those servers.                                         ║
# ║                                                                            ║
# ║  Architecture:                                                             ║
# ║    • One background asyncio event loop runs per process (in a daemon       ║
# ║      thread) — all MCP calls are sent to this loop via                     ║
# ║      asyncio.run_coroutine_threadsafe().                                   ║
# ║    • Sessions are lazily initialized on first call to each server.         ║
# ║    • Only "stdio" transport is currently supported.                        ║
# ║                                                                            ║
# ║  DEBUG TIP: If MCP tools silently fail, check:                            ║
# ║    1. The MCP server binary is in PATH (e.g. "npx")                       ║
# ║    2. The server starts cleanly when run manually                          ║
# ║    3. The mcp package is installed: pip install mcp>=1.0.0                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# MCP CLIENT REGISTRY CLASS
# ─────────────────────────────────────────────────────────────────────────────

class MCPClientRegistry:
    """Manages connections to one or more MCP servers.

    Usage:
        registry = MCPClientRegistry()
        registry.register("my_server", {"command": "npx", "args": ["-y", "@some/server"], "transport": "stdio"})
        result = registry.call("my_server", "tool_name", {"param": "value"})
    """

    def __init__(self) -> None:
        # Registered server configs: name → {command, args, transport}
        self._servers: Dict[str, Dict[str, Any]] = {}
        # Active MCP sessions: name → ClientSession object
        self._sessions: Dict[str, Any] = {}
        # Shared asyncio event loop running in a background daemon thread
        self._loop: Optional[Any] = None
        self._thread: Optional[Any] = None
        # AsyncExitStack manages the lifecycle of all open sessions
        self._stack: Optional[Any] = None

    # ─────────────────────────────────────────────────────────────────────
    # SERVER REGISTRATION
    # ─────────────────────────────────────────────────────────────────────

    def register(self, name: str, config: Dict[str, Any]) -> None:
        """Register an MCP server definition. Does NOT connect immediately."""
        self._servers[name] = dict(config)

    def list_servers(self) -> List[str]:
        """Return names of all registered MCP servers."""
        return sorted(self._servers.keys())

    # ─────────────────────────────────────────────────────────────────────
    # SESSION INITIALIZATION (lazy, on first call)
    # ─────────────────────────────────────────────────────────────────────

    def _init_server_sync(self, name: str) -> None:
        """Initialize a stdio MCP session synchronously (blocks until connected).

        Called lazily on first use of a server. Subsequent calls are no-ops.
        """
        if name in self._sessions:
            return  # already connected

        # Import MCP library — raises RuntimeError if not installed
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise RuntimeError("mcp package is not installed. Please pip install mcp>=1.0.0") from exc

        # Start the background asyncio loop (once, shared across all servers)
        if self._loop is None:
            import asyncio
            import threading
            from contextlib import AsyncExitStack
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
            self._thread.start()
            self._stack = AsyncExitStack()

        server = self._servers[name]
        transport_type = str(server.get("transport", "")).strip().lower()
        if transport_type != "stdio":
            raise ValueError(f"MCP transport '{transport_type}' not implemented. Only 'stdio' is supported.")

        command = str(server.get("command", ""))
        args = [str(a) for a in server.get("args", [])]

        async def _connect():
            """Async coroutine: spawn server process and open a session."""
            server_params = StdioServerParameters(command=command, args=args)
            transport = await self._stack.enter_async_context(stdio_client(server_params))
            read, write = transport
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            return session

        import asyncio
        future = asyncio.run_coroutine_threadsafe(_connect(), self._loop)
        self._sessions[name] = future.result(timeout=10.0)

    # ─────────────────────────────────────────────────────────────────────
    # TOOL CALL
    # ─────────────────────────────────────────────────────────────────────

    def call(self, server_name: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a registered MCP server.

        Args:
            server_name: Name of the registered server.
            method:      Tool name (as reported by the server's tools list).
            params:      Dict of input parameters.

        Returns:
            {"ok": True, ...} on success, {"ok": False, "error": ...} on failure.
        """
        if server_name not in self._servers:
            return {"ok": False, "error": f"MCP server not found: {server_name}"}

        try:
            self._init_server_sync(server_name)
            session = self._sessions[server_name]

            import asyncio

            async def _do_call():
                result = await session.call_tool(method, arguments=params)
                if hasattr(result, "model_dump"):
                    return result.model_dump()
                return {"result": str(result)}

            future = asyncio.run_coroutine_threadsafe(_do_call(), self._loop)
            call_result = future.result(timeout=30.0)
            return {"ok": True, **call_result}

        except Exception as exc:
            return {"ok": False, "error": str(exc), "server": server_name}

    # ─────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────────────────────────────────────

    def __del__(self) -> None:
        """Gracefully close all open MCP sessions when the registry is garbage-collected."""
        if self._loop and self._stack:
            try:
                import asyncio
                future = asyncio.run_coroutine_threadsafe(self._stack.aclose(), self._loop)
                future.result(timeout=5.0)
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass
