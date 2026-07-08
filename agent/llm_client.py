# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/llm_client.py — LLM Provider Interface                             ║
# ║                                                                            ║
# ║  Handles all communication with the local LLM server (LM Studio/Ollama).  ║
# ║                                                                            ║
# ║  Two classes:                                                              ║
# ║    LLMProviderRouter  — simple metadata helper (which provider is active?) ║
# ║    LocalLLMClient     — the actual LLM caller                              ║
# ║                                                                            ║
# ║  Two transports:                                                           ║
# ║    "openai_compatible" — sends real HTTP requests to LM Studio/Ollama      ║
# ║    "stub"              — returns hardcoded mock responses (for tests only) ║
# ║                                                                            ║
# ║  IMPORTANT: The _fallback() method is ONLY used when transport = "stub".  ║
# ║  It pattern-matches keywords and returns scripted responses — do NOT use   ║
# ║  this as a real intelligence path.  To use the real LLM, start LM Studio  ║
# ║  and set transport = "openai_compatible" in config.yaml.                   ║
# ║                                                                            ║
# ║  DEBUG TIP: If you get connection errors, check:                           ║
# ║    1. LM Studio is running with a model loaded                            ║
# ║    2. The local server is enabled in LM Studio Developer tab               ║
# ║    3. config.yaml → llm → base_url_lmstudio matches the port              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# =============================================================================
# 🛠️ HOW TO MAKE THE APP BETTER: EXTENDING LLM CAPABILITIES
# =============================================================================
# 1. ADDING NEW LLM PROVIDERS:
#    If you want to use OpenAI, Anthropic, or Gemini APIs instead of just local
#    LM Studio/Ollama, add the API call logic inside `complete_json()` below.
# 2. PROMPT ENGINEERING:
#    To change how the agent thinks, modify the `system_prompt` strings inside
#    `complete_json()`. You can instruct it to be more cautious, format output
#    differently, or prioritize specific tools.
# 3. DEBUGGING LLM OUTPUT:
#    The code below now prints all LLM inputs and outputs to the server console
#    so you can see exactly what the AI is thinking!

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import json
from typing import TYPE_CHECKING, Any, Dict

from agent.config import LLMConfig

if TYPE_CHECKING:
    # Avoid circular import: AgentEngine imports LocalLLMClient, not the other way
    from agent.engine import AgentEngine


# ─────────────────────────────────────────────────────────────────────────────
# LLM PROVIDER ROUTER
# Lightweight metadata helper — tells callers which provider is currently active.
# ─────────────────────────────────────────────────────────────────────────────

class LLMProviderRouter:
    """Reports which LLM provider and endpoint is currently configured."""

    def __init__(self, cfg: LLMConfig) -> None:
        self.cfg = cfg

    def metadata(self) -> Dict[str, str]:
        return {
            "provider": self.cfg.provider,
            "base_url": self.cfg.get_base_url(),
            "transport": self.cfg.transport,
        }


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL LLM CLIENT
# Main class for sending prompts to the LLM and parsing JSON responses.
# ─────────────────────────────────────────────────────────────────────────────

class LocalLLMClient:
    """Sends structured JSON prompts to the local LLM server and parses responses.

    The client is given a "role" (planner / executor / verifier) and a payload.
    It builds a role-specific system prompt, calls the LLM, and returns a parsed dict.

    If transport == "stub", all calls are intercepted by _fallback() instead.
    """

    def __init__(self, cfg: LLMConfig) -> None:
        self.cfg = cfg
        # Back-reference to AgentEngine — set after engine is constructed.
        # Used to enumerate MCP servers and custom tools in executor prompts.
        self.engine: "AgentEngine | None" = None

    # ─────────────────────────────────────────────────────────────────────
    # STUB / FALLBACK RESPONSES
    # Only active when transport = "stub" (development / unit-test mode).
    # ─────────────────────────────────────────────────────────────────────

    def _fallback(self, role: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return scripted mock responses for testing WITHOUT a real LLM server.

        ⚠️  WARNING: This is NOT real intelligence. It keyword-matches the goal
        text and returns pre-written answers. Do NOT rely on this in production.
        Set transport = "openai_compatible" to use a real model.
        """
        # ── PLANNER fallback: return a single-step plan ─────────────────
        if role == "planner":
            goal = str(payload.get("goal", "")).strip() or "Implement task"
            expectations: Dict[str, Any] = {}
            goal_parts = goal.split()

            # Try to detect .txt filename in the goal
            for token in goal_parts:
                if token.endswith(".txt"):
                    expectations["path"] = token
                    expectations["content_contains"] = "created by agent"
                    break

            if "html" in goal.lower() or "birds" in goal.lower():
                if "slider" in goal.lower():
                    expectations["path"] = "birds_slider.html"
                    expectations["content_contains"] = "Most Beautiful Birds"
                else:
                    expectations["path"] = "birds_animals.html"
                    expectations["content_contains"] = "Birds and Animals"
            elif "research" in goal.lower() or "deep learning" in goal.lower() or "mammal" in goal.lower():
                if "mammal" in goal.lower():
                    expectations["path"] = "mammal_research.txt"
                    expectations["content_contains"] = "blue whale"
                else:
                    expectations["path"] = "deep_learning_research.txt"
                    expectations["content_contains"] = "McCulloch-Pitts"
            elif "story" in goal.lower() or "fox" in goal.lower() or "rabbit" in goal.lower():
                expectations["path"] = "fox_rabbit_story.txt"
                expectations["content_contains"] = "sly fox"
            elif "hi" in goal.lower() or "how are you" in goal.lower():
                expectations = {}
            elif "blog" in goal.lower() or "education" in goal.lower() or "write" in goal.lower():
                expectations["path"] = "ai_education_blog.md"
                expectations["content_contains"] = "personalizing learning"

            return {
                "steps": [
                    {"step_id": "step_1", "title": goal, "mode": "coding", "expectations": expectations}
                ]
            }

        # ── EXECUTOR fallback: return a scripted tool call ──────────────
        if role == "executor":
            step = payload.get("step", {})
            title = str(step.get("title", "")).lower()

            if "create" in title and ".txt" in title:
                parts = str(step.get("title", "")).split()
                target = next((p for p in parts if p.endswith(".txt")), "output.txt")
                return {
                    "action": "tool_call",
                    "tool_name": "create_file_or_folder",
                    "tool_input": {"path": target, "content": "created by agent\n"},
                }
            if "html" in title or "birds" in title:
                if "slider" in title:
                    return {
                        "action": "tool_call",
                        "tool_name": "create_file_or_folder",
                        "tool_input": {
                            "path": "birds_slider.html",
                            "content": "<html><head><title>Most Beautiful Birds</title></head><body><h1>Most Beautiful Birds in the World</h1><div class='slider'>Slider Component</div></body></html>",
                        },
                    }
                else:
                    return {
                        "action": "tool_call",
                        "tool_name": "create_file_or_folder",
                        "tool_input": {
                            "path": "birds_animals.html",
                            "content": "<html><head><title>Birds and Animals</title></head><body><h1>Birds and Animals</h1></body></html>",
                        },
                    }
            if "research" in title or "deep learning" in title or "mammal" in title:
                if "mammal" in title:
                    return {
                        "action": "tool_call",
                        "tool_name": "create_file_or_folder",
                        "tool_input": {
                            "path": "mammal_research.txt",
                            "content": "Largest Mammal Research:\nThe blue whale (Balaenoptera musculus) is the largest mammal ever known to have lived on Earth.",
                        },
                    }
                else:
                    return {
                        "action": "tool_call",
                        "tool_name": "create_file_or_folder",
                        "tool_input": {
                            "path": "deep_learning_research.txt",
                            "content": "Deep Learning Research:\n1. 1943: McCulloch-Pitts neuron\n2. 1957: Perceptron\n",
                        },
                    }
            if "story" in title or "fox" in title or "rabbit" in title:
                return {
                    "action": "tool_call",
                    "tool_name": "create_file_or_folder",
                    "tool_input": {
                        "path": "fox_rabbit_story.txt",
                        "content": "Once upon a time, a sly fox and a quick rabbit lived in a forest together...",
                    },
                }
            if "hi" in title or "how are you" in title:
                return {"action": "final_answer", "final_answer": "Hello! I am doing well, thank you for asking."}
            if "blog" in title or "education" in title or "write" in title:
                return {
                    "action": "tool_call",
                    "tool_name": "create_file_or_folder",
                    "tool_input": {
                        "path": "ai_education_blog.md",
                        "content": "# AI in Education\nArtificial intelligence is transforming education by personalizing learning...\n",
                    },
                }
            return {"action": "final_answer", "final_answer": "no-op"}

        # ── VERIFIER fallback: trust the execution result's ok flag ─────
        if role == "verifier":
            result = payload.get("execution_result", {})
            return {"ok": bool(result.get("ok")), "reason": "fallback verifier decision"}

        return {}

    # ─────────────────────────────────────────────────────────────────────
    # REAL LLM CALL
    # Sends prompt to LM Studio / Ollama via OpenAI-compatible API.
    # ─────────────────────────────────────────────────────────────────────

    def complete_json(self, role: str, payload: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Send a role-specific prompt to the LLM and return the parsed JSON response.

        Args:
            role:    "planner" | "executor" | "verifier"
            payload: The context dict to send to the LLM
            model:   Model name (from config.yaml llm.model_planner/executor/verifier)

        Returns:
            Parsed dict from the LLM's JSON response.

        Raises:
            RuntimeError: If transport is unsupported, openai library missing,
                          or the LLM server is unreachable.
        """
        # Route to stub if transport is "stub" (tests / dev mode)
        if self.cfg.transport == "stub":
            return self._fallback(role, payload)

        if self.cfg.transport != "openai_compatible":
            raise RuntimeError(
                f"Unsupported transport '{self.cfg.transport}'. "
                "Only 'stub' and 'openai_compatible' are supported."
            )

        # ── Import OpenAI client (requires pip install openai) ──────────
        try:
            from openai import OpenAI
        except Exception as e:
            raise RuntimeError(
                "Failed to import 'openai' library. "
                "Please run 'pip install openai' to support real model server calls."
            ) from e

        # ── Build the structured prompt message ─────────────────────────
        prompt = {
            "role": role,
            "payload": payload,
            "must_return_json_object": True,
        }

        # ── Build role-specific system prompt ───────────────────────────
        system_prompt = "Return strictly valid JSON object only."

        if role == "planner":
            system_prompt += (
                " You must return a JSON object with a 'steps' array. Each step must have"
                " 'step_id', 'title', 'mode', and 'expectations' (with 'path' or 'content_contains')."
                " If 'session_history' is provided in the payload, these steps have already been successfully"
                " completed in this session. You should plan only the new, subsequent steps needed to achieve"
                " the new goal. Start the step_id numbering sequentially from the next number after the last"
                " completed step in the history."
            )

        elif role == "executor":
            # Dynamically enumerate available MCP tools to include in prompt
            mcp_tools_desc = []
            if self.engine is not None:
                for server_name in self.engine.mcp.list_servers():
                    try:
                        self.engine.mcp._init_server_sync(server_name)
                        session = self.engine.mcp._sessions[server_name]
                        import asyncio
                        future = asyncio.run_coroutine_threadsafe(session.list_tools(), self.engine.mcp._loop)
                        tools_list = future.result(timeout=2.0)
                        for t in tools_list.tools:
                            props = t.inputSchema.get("properties", {}) if hasattr(t, "inputSchema") and t.inputSchema else {}
                            args_str = ", ".join(f"{k}: {v.get('type')}" for k, v in props.items())
                            mcp_tools_desc.append(f"'{t.name}'({args_str}) from '{server_name}': {t.description}")
                    except Exception:
                        pass

            mcp_desc_str = ""
            if mcp_tools_desc:
                mcp_desc_str = " Available MCP tools: " + ", ".join(mcp_tools_desc) + "."

            # Also enumerate custom Python tools
            custom_tools = []
            if self.engine is not None:
                custom_tools = self.engine.tools.get_custom_tool_names()
            custom_desc_str = ""
            if custom_tools:
                custom_desc_str = " Available custom tools: " + ", ".join(f"'{n}'(args)" for n in custom_tools) + "."

            system_prompt += (
                " You must return a JSON object with 'action' (either 'tool_call' or 'final_answer')."
                " If calling a tool, specify 'tool_name' and 'tool_input'. Available native tools: "
                " 'write_file'(path, content), 'read_file'(path), 'create_new_file'(path, content), "
                " 'file_glob_search'(pattern), 'view_diff'(), 'ls'(path), 'fetch_url_content'(url), "
                " 'edit_existing_file'(path, old_string, new_string), 'grep_search'(query, path), 'run_shell'(command), "
                " 'set_working_directory'(path), 'create_file_or_folder'(path, is_folder, content), "
                " 'copy_file'(src, dest), 'edit_file'(path, content), 'rename_file'(src, dest), 'view_page'(path)."
                f"{mcp_desc_str}{custom_desc_str}"
                " If no workspace tool operation is needed (e.g. greeting, answering a question, or concluding), "
                " set 'action' to 'final_answer' and set 'final_answer' to your text response."
            )

        elif role == "verifier":
            task = payload.get("task")
            if task == "generate_pytest":
                system_prompt += " You must return a JSON object with 'test_code' containing python pytest code to verify the step requirements."
            elif task == "autocorrect_pytest":
                system_prompt += " You must return a JSON object with 'fixed_test_code' containing corrected python pytest code to fix the failure."
            else:
                system_prompt += (
                    " You must evaluate if the 'execution_result' successfully fulfilled the 'step' requirements."
                    " Carefully inspect 'execution_result' (including any 'file_content' written or modified)."
                    " Be constructive and practical: if the code is functional, correctly implements the requested logic,"
                    " and achieves the step's goal, mark it as ok: true."
                    " Do not reject the result for minor formatting differences or choice of loops (e.g., using while instead of for) "
                    " as long as the functionality is correct and satisfies the step requirements."
                    " Return a JSON object with 'ok' (boolean) and 'reason' (string)."
                )

        print(f"\n[{role.upper()}] >>> SENDING PROMPT TO {model}:")
        print(json.dumps(prompt, indent=2))

        # ── Fire the actual HTTP request ────────────────────────────────
        try:
            client = OpenAI(
                base_url=self.cfg.get_base_url(),
                api_key=self.cfg.get_api_key(),
                timeout=60.0,
            )
            resp = client.chat.completions.create(
                model=model,
                temperature=0.1,
                max_tokens=self.cfg.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            )
        except Exception as e:
            raise RuntimeError(
                f"Connection to LM Studio/LLM failed: {str(e)}.\n"
                f"Please ensure your LM Studio or local LLM server is running and listening at: {self.cfg.get_base_url()}\n"
                "If you want to run mock tests without a real LLM server, change the transport setting to 'stub' in settings or config."
            ) from e

        text = (resp.choices[0].message.content or "{}").strip()

        # Strip markdown code fences if the model wrapped its JSON response
        if text.startswith("```"):
            first_nl = text.find("\n")
            if first_nl != -1:
                text = text[first_nl + 1:]
            if text.endswith("```"):
                text = text[:-3]
        text = text.strip()
        
        print(f"\n[{role.upper()}] <<< LLM RESPONSE RAW:")
        print(text)

        try:
            parsed = json.loads(text, strict=False)
            print(f"\n[{role.upper()}] <<< LLM PARSED JSON:")
            print(json.dumps(parsed, indent=2))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON (Decode Error: {e}). Raw response:\n{text}") from e

        # Should never reach here — parse succeeded but wasn't a dict
        return {}
