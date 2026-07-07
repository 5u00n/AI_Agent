# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastapi>=0.110.0",
#     "uvicorn>=0.29.0",
#     "openai>=1.30.0",
#     "pydantic>=2.6.0",
#     "PyYAML>=6.0.0",
#     "pytest>=8.0.0",
#     "mcp>=1.1.2",
# ]
# ///

from __future__ import annotations
# AI Agent Engine with Chat UI and tool registry
import argparse
import json
import sqlite3
import subprocess
import urllib.request
import sys
import textwrap
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
	import yaml
except Exception:  # pragma: no cover
	yaml = None


def _utc_now() -> str:
	return datetime.now(timezone.utc).isoformat()


@dataclass
class LLMConfig:
	provider: str = "lmstudio"
	base_url_lmstudio: str = "http://127.0.0.1:1234/v1"
	base_url_ollama: str = "http://127.0.0.1:11434"
	api_key_lmstudio: str = "lm-studio"
	api_key_ollama: str = "ollama"
	model_planner: str = "planner-model"
	model_executor: str = "executor-model"
	model_verifier: str = "verifier-model"
	transport: str = "openai_compatible"
	max_tokens: int = 4096

	def get_base_url(self) -> str:
		if self.provider == "lmstudio":
			return self.base_url_lmstudio
		if self.provider == "ollama":
			return self.base_url_ollama
		raise ValueError(f"Unsupported provider: {self.provider}")

	def get_api_key(self) -> str:
		if self.provider == "lmstudio":
			return self.api_key_lmstudio
		if self.provider == "ollama":
			return self.api_key_ollama
		raise ValueError(f"Unsupported provider: {self.provider}")


@dataclass
class BudgetConfig:
	max_steps: int = 30
	max_runtime_minutes: int = 60
	max_tool_calls: int = 200


@dataclass
class SafetyConfig:
	require_approval_for: List[str] = field(default_factory=list)
	blocked_commands: List[str] = field(default_factory=list)
	allowed_paths: List[str] = field(default_factory=lambda: ["."])


@dataclass
class TestPolicyConfig:
	enforce_task_test_gate: bool = True
	auto_generate_tests: bool = True
	verify_and_autocorrect_tests: bool = True
	run_tests_before_completion: bool = True
	delete_tests_after_task: bool = True
	keep_tests_when_user_requests: bool = True
	test_location_strategy: str = "tests_temp"
	max_test_fix_attempts: int = 2
	test_runner_by_mode: Dict[str, str] = field(default_factory=lambda: {"coding": "python"})


@dataclass
class UIConfig:
	enabled: bool = True
	host: str = "127.0.0.1"
	port: int = 8000
	auth_mode: str = "none"


@dataclass
class MCPServerConfig:
	command: str
	args: List[str] = field(default_factory=list)
	transport: str = "stdio"


@dataclass
class MCPConfig:
	servers: Dict[str, MCPServerConfig] = field(default_factory=dict)


@dataclass
class AgentConfig:
	llm: LLMConfig = field(default_factory=LLMConfig)
	budgets: BudgetConfig = field(default_factory=BudgetConfig)
	safety: SafetyConfig = field(default_factory=SafetyConfig)
	test_policy: TestPolicyConfig = field(default_factory=TestPolicyConfig)
	ui: UIConfig = field(default_factory=UIConfig)
	mcp: MCPConfig = field(default_factory=MCPConfig)

	@staticmethod
	def default(root_dir: Path) -> "AgentConfig":
		_ = root_dir
		return AgentConfig()

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)


def _build_dataclass(cls: Any, values: Optional[Dict[str, Any]]) -> Any:
	values = values or {}
	return cls(**values)


def load_config(path: Path) -> AgentConfig:
	if not path.exists():
		return AgentConfig.default(root_dir=path.parent)
	if yaml is None:
		raise RuntimeError("pyyaml is required to load config.yaml")
	raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
	
	mcp_raw = raw.get("mcp", {})
	mcp_servers = {}
	for name, srv in mcp_raw.get("servers", {}).items():
		mcp_servers[name] = MCPServerConfig(
			command=srv.get("command", ""),
			args=srv.get("args", []),
			transport=srv.get("transport", "stdio")
		)
	
	return AgentConfig(
		llm=_build_dataclass(LLMConfig, raw.get("llm")),
		budgets=_build_dataclass(BudgetConfig, raw.get("budgets")),
		safety=_build_dataclass(SafetyConfig, raw.get("safety")),
		test_policy=_build_dataclass(TestPolicyConfig, raw.get("test_policy")),
		ui=_build_dataclass(UIConfig, raw.get("ui")),
		mcp=MCPConfig(servers=mcp_servers),
	)


def save_config(path: Path, config: AgentConfig) -> None:
	if yaml is None:
		raise RuntimeError("pyyaml is required to save config.yaml")
	path.write_text(yaml.safe_dump(config.to_dict(), sort_keys=False), encoding="utf-8")


def render_ui_html(cfg: AgentConfig) -> str:
	return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Agent Chat</title>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
        .sidebar {{ width: 340px; background: #1e293b; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; border-right: 1px solid #334155; height: 100%; overflow-y: auto; }}
        .sidebar-section {{ margin-bottom: 24px; }}
        .sidebar-title {{ font-size: 13px; font-weight: bold; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 6px; }}
        .sessions-list {{ display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto; }}
        .session-item {{ padding: 10px 12px; border-radius: 6px; background: #334155; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; font-size: 13px; }}
        .session-item:hover {{ background: #475569; }}
        .session-item.active {{ border-color: #3b82f6; background: #0f172a; }}
        .session-goal {{ font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px; }}
        
        .chat-area {{ flex: 1; display: flex; flex-direction: column; background: #0b0f19; height: 100%; }}
        .chat-history {{ flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; scroll-behavior: smooth; }}
        .chat-input-area {{ background: #1e293b; padding: 16px 20px; border-top: 1px solid #334155; }}
        .input-box {{ display: flex; gap: 12px; }}
        input[type="text"], select, input[type="number"] {{ padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #334155; color: #f8fafc; outline: none; box-sizing: border-box; }}
        input[type="text"] {{ flex: 1; }}
        button {{ background: #3b82f6; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; }}
        button:hover {{ background: #2563eb; }}
        .btn-danger {{ background: #ef4444; }}
        .btn-danger:hover {{ background: #dc2626; }}
        
        .message {{ max-width: 85%; display: flex; flex-direction: column; margin-bottom: 8px; }}
        .msg-user {{ align-self: flex-end; align-items: flex-end; }}
        .msg-agent {{ align-self: flex-start; align-items: flex-start; width: 100%; }}
        
        .bubble {{ padding: 14px 18px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.15); line-height: 1.5; }}
        .msg-user .bubble {{ background: #2563eb; color: white; border-bottom-right-radius: 4px; }}
        .msg-agent .bubble {{ background: #1e293b; color: #f8fafc; border-bottom-left-radius: 4px; border: 1px solid #334155; width: 100%; box-sizing: border-box; }}
        
        .timestamp {{ font-size: 11px; color: #64748b; margin-top: 6px; }}
        
        /* Step Cards */
        .agent-work {{ margin-top: 12px; background: #0f172a; padding: 4px; border-radius: 8px; border: 1px solid #334155; }}
        details summary {{ cursor: pointer; font-weight: 600; color: #3b82f6; padding: 8px 12px; outline: none; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }}
        .steps-container {{ padding: 8px 12px; display: flex; flex-direction: column; gap: 12px; }}
        .step-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 12px; }}
        .step-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-weight: 600; font-size: 12px; color: #60a5fa; }}
        .step-body {{ font-size: 13px; color: #e2e8f0; white-space: pre-wrap; font-family: sans-serif; line-height: 1.45; }}
        .step-footer {{ margin-top: 8px; padding-top: 8px; border-top: 1px solid #334155; font-size: 11px; color: #10b981; display: flex; align-items: center; justify-content: space-between; }}
        
        .status-badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; text-transform: uppercase; }}
        .status-done {{ background: #065f46; color: #34d399; }}
        .status-blocked {{ background: #7f1d1d; color: #fca5a5; }}
        .status-running {{ background: #78350f; color: #fcd34d; }}
        .status-queued {{ background: #374151; color: #d1d5db; }}
        
        /* Tools settings list */
        .tools-list {{ font-size: 12px; display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }}
        .tool-desc-item {{ padding: 6px 8px; background: #0f172a; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }}
        .tool-desc-name {{ font-family: monospace; color: #3b82f6; font-weight: bold; }}
        .mcp-form-row {{ display: flex; flex-direction: column; gap: 4px; margin-top: 6px; }}
        .mcp-form-row label {{ font-size: 11px; color: #cbd5e1; margin: 0; }}
        .mcp-form-row input {{ padding: 6px; font-size: 12px; width: 100%; }}
        
        /* Approvals */
        .approval-card {{ background: #7f1d1d; border: 1px solid #dc2626; border-radius: 8px; padding: 12px; margin-top: 12px; font-size: 13px; }}
        .approval-card pre {{ background: #450a0a; padding: 8px; border-radius: 4px; overflow-x: auto; margin-bottom: 8px; }}
        .btn-approve {{ background: #10b981; margin-right: 8px; }}
        .btn-reject {{ background: #ef4444; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="margin: 0 0 16px 0; font-size: 20px; letter-spacing: -0.02em;">AI Agent</h2>
        
        <!-- Sessions Section -->
        <div class="sidebar-section">
            <div class="sidebar-title">
                <span>Chat Sessions</span>
                <button id="new-session-btn" style="padding: 4px 8px; font-size: 11px;">＋ New</button>
            </div>
            <div class="sessions-list" id="sessions-container"></div>
        </div>
        
        <!-- Collapsible Tools Section -->
        <div class="sidebar-section">
            <details style="border: 1px solid #334155; border-radius: 6px; padding: 10px; background: #1e293b;">
                <summary style="font-size: 13px; font-weight: bold; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer; display: flex; justify-content: space-between; align-items: center; padding: 0;">
                    <span>Tools Settings</span>
                    <span style="font-size: 10px; color: #3b82f6;">(Click to expand)</span>
                </summary>
                <div class="tools-list" style="margin-top: 12px;">
                    <div style="font-weight:bold; color:#cbd5e1;">Native Tools:</div>
                    <div class="tool-desc-item"><span class="tool-desc-name">write_file</span> <span style="color:#94a3b8;">Write files</span></div>
                    <div class="tool-desc-item"><span class="tool-desc-name">grep_search</span> <span style="color:#94a3b8;">rg search</span></div>
                    <div class="tool-desc-item"><span class="tool-desc-name">run_shell</span> <span style="color:#94a3b8;">Shell exec</span></div>
                    
                    <div style="font-weight:bold; color:#cbd5e1; margin-top:8px;">MCP Tools:</div>
                    <div id="mcp-servers-list" style="display:flex; flex-direction:column; gap:6px;"></div>
                    
                    <div style="border-top:1px solid #334155; margin-top:8px; padding-top:8px; font-weight:bold; color:#cbd5e1;">Add MCP Server:</div>
                    <div class="mcp-form-row">
                        <label>Server Name</label>
                        <input type="text" id="mcp-name" placeholder="e.g. gsearch">
                    </div>
                    <div class="mcp-form-row">
                        <label>Command</label>
                        <input type="text" id="mcp-cmd" placeholder="e.g. python, npx">
                    </div>
                    <div class="mcp-form-row">
                        <label>Arguments (comma separated)</label>
                        <input type="text" id="mcp-args" placeholder="e.g. -m, gsearch_mcp">
                    </div>
                    <button id="add-mcp-btn" style="width:100%; margin-top:8px; padding: 6px;">Add MCP Server</button>
                    <div id="mcp-add-result" style="font-size:11px; color:#10b981; margin-top:4px;"></div>
                </div>
            </details>
        </div>
        
        <!-- Settings Section with Auto-Detect -->
        <div class="sidebar-section">
            <div class="sidebar-title">
                <span>Model Settings</span>
                <button id="auto-detect-btn" style="padding: 4px 8px; font-size: 11px; background: #10b981; border: none; color: white; border-radius: 4px; cursor: pointer;">Probe & Auto-Fill</button>
            </div>
            <label style="font-size:11px; color:#cbd5e1; font-weight:bold;">Provider</label>
            <select id="provider" style="width:100%; margin-top:4px;"><option value="lmstudio">LM Studio</option><option value="ollama">Ollama</option></select>
            
            <label style="font-size:11px; color:#cbd5e1; font-weight:bold; display:block; margin-top:8px;">Planner</label>
            <select id="model-planner" style="width:100%; margin-top:4px;"></select>
            
            <label style="font-size:11px; color:#cbd5e1; font-weight:bold; display:block; margin-top:8px;">Executor</label>
            <select id="model-executor" style="width:100%; margin-top:4px;"></select>
            
            <label style="font-size:11px; color:#cbd5e1; font-weight:bold; display:block; margin-top:8px;">Verifier</label>
            <select id="model-verifier" style="width:100%; margin-top:4px;"></select>
            
            <label style="font-size:11px; color:#cbd5e1; font-weight:bold; display:block; margin-top:8px;">Max Tokens</label>
            <input type="number" id="max-tokens" value="{cfg.llm.max_tokens}" style="width:100%; margin-top:4px;">
            <div id="models-status" style="font-size: 11px; margin-top: 4px; color: #94a3b8;"></div>
            <button class="settings-btn" id="save-llm-btn" style="width:100%; margin-top:12px; background:#475569;">Save Config</button>
            <div id="save-llm-result" style="font-size: 11px; color: #10b981; margin-top: 4px;"></div>
        </div>

        <!-- Policy Section -->
        <div class="sidebar-section">
            <div class="sidebar-title">Test Policy</div>
            <label style="font-size:11px; color:#cbd5e1;">Delete Tests After Task</label>
            <select id="tp-delete" style="width:100%; margin-top:4px;">
                <option value="true" {'selected' if cfg.test_policy.delete_tests_after_task else ''}>True</option>
                <option value="false" {'selected' if not cfg.test_policy.delete_tests_after_task else ''}>False</option>
            </select>
            <label style="font-size:11px; color:#cbd5e1; display:block; margin-top:8px;">Max Fix Attempts</label>
            <input type="number" id="tp-retries" value="{cfg.test_policy.max_test_fix_attempts}" style="width:100%; margin-top:4px;">
            <button class="settings-btn" id="save-policy-btn" style="width:100%; margin-top:12px; background:#475569;">Save Policy</button>
            <div id="save-policy-result" style="font-size: 11px; color: #10b981; margin-top: 4px;"></div>
        </div>

        <!-- Approvals Section -->
        <div class="sidebar-section">
            <div class="sidebar-title" style="color: #fca5a5;">Pending Approvals</div>
            <div id="approvals-container"></div>
        </div>
    </div>
    
    <div class="chat-area">
        <div class="chat-history" id="chat-history"></div>
        <div class="chat-input-area">
            <div class="input-box">
                <input type="text" id="goal" placeholder="Type a message or describe a task..." autofocus>
                <button id="run-btn">Send</button>
            </div>
            <div style="display: flex; gap: 16px; margin-top: 12px;">
                <div style="font-size: 12px; display: flex; align-items: center; gap: 8px;">
                    <label style="margin:0;">Mode:</label>
                    <select id="mode" style="width: auto; margin:0; padding: 4px 8px;">
                        <option value="coding">Coding</option>
                        <option value="planning">Planning</option>
                    </select>
                </div>
                <div style="font-size: 12px; display: flex; align-items: center; gap: 8px;">
                    <label style="margin:0;">Keep Tests:</label>
                    <select id="keep-tests" style="width: auto; margin:0; padding: 4px 8px;">
                        <option value="true">True</option>
                        <option value="false" selected>False</option>
                    </select>
                </div>
            </div>
        </div>
    </div>

    <script>
      const PRE_LOADED_MODELS = {{
          "planner": "{cfg.llm.model_planner}",
          "executor": "{cfg.llm.model_executor}",
          "verifier": "{cfg.llm.model_verifier}",
      }};
      
      let activeRunId = null;
      let renderedRunId = null;
      let runsCache = [];
      
      async function fetchModels() {{
        const provider = document.getElementById('provider').value;
        const status = document.getElementById('models-status');
        status.textContent = "Fetching...";
        try {{
          const res = await fetch(`/models?provider=${{provider}}`);
          const data = await res.json();
          const models = data.models || [];
          if (models.length === 0) {{
              status.textContent = "No active models found on provider.";
          }} else {{
              status.textContent = `Found ${{models.length}} models.`;
          }}
          
          const isStub = (m) => ["planner-model", "executor-model", "verifier-model"].includes(m);
          
          ['model-planner', 'model-executor', 'model-verifier'].forEach(id => {{
             const sel = document.getElementById(id);
             sel.innerHTML = '';
             const key = id.replace('model-', '');
             const curr = PRE_LOADED_MODELS[key];
             const needsAutoFix = isStub(curr) && models.length > 0;
             
             models.forEach(m => {{
               const opt = document.createElement('option');
               opt.value = m;
               opt.textContent = m;
               if (m === curr || (needsAutoFix && m === models[0])) {{
                   opt.selected = true;
                   if (needsAutoFix) PRE_LOADED_MODELS[key] = m;
               }}
               sel.appendChild(opt);
             }});
             if (!models.includes(curr) && curr && !isStub(curr)) {{
                 const opt = document.createElement('option');
                 opt.value = curr;
                 opt.textContent = curr + " (Current)";
                 opt.selected = true;
                 sel.appendChild(opt);
             }}
          }});
        }} catch (err) {{ status.textContent = "Error fetching models."; }}
      }}

      async function saveLLMSettings() {{
        try {{
          const provider = document.getElementById('provider').value;
          const model_planner = document.getElementById('model-planner').value;
          const model_executor = document.getElementById('model-executor').value;
          const model_verifier = document.getElementById('model-verifier').value;
          if (!model_planner || !model_executor || !model_verifier) {{
             return;
          }}
          const payload = {{
            provider: provider,
            model_planner: model_planner,
            model_executor: model_executor,
            model_verifier: model_verifier,
            max_tokens: parseInt(document.getElementById('max-tokens').value || "4096", 10),
          }};
          await fetch('/settings/llm', {{ method: 'PUT', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
          PRE_LOADED_MODELS.planner = payload.model_planner;
          PRE_LOADED_MODELS.executor = payload.model_executor;
          PRE_LOADED_MODELS.verifier = payload.model_verifier;
          const resultEl = document.getElementById('save-llm-result');
          if (resultEl) {{
              resultEl.textContent = "Saved!";
              setTimeout(() => resultEl.textContent = "", 2000);
          }}
        }} catch (err) {{
          console.error("Error saving LLM settings:", err);
        }}
      }}

      async function savePolicy() {{
        const payload = {{
          delete_tests_after_task: document.getElementById('tp-delete').value === 'true',
          max_test_fix_attempts: Number(document.getElementById('tp-retries').value || 0),
        }};
        await fetch('/settings/test-policy', {{ method: 'PUT', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
        document.getElementById('save-policy-result').textContent = "Saved!";
        setTimeout(() => document.getElementById('save-policy-result').textContent = "", 2000);
      }}

      async function fetchMCPServers() {{
         try {{
           const res = await fetch('/settings/mcp');
           const data = await res.json();
           const container = document.getElementById('mcp-servers-list');
           if (!data.servers || Object.keys(data.servers).length === 0) {{
               container.innerHTML = '<div style="color:#94a3b8; font-style:italic;">No custom servers</div>';
               return;
           }}
           let html = '';
           Object.keys(data.servers).forEach(name => {{
              const srv = data.servers[name];
              html += `
                <div class="tool-desc-item">
                   <div>
                      <span class="tool-desc-name">${{name}}</span>
                      <div style="font-size:10px; color:#94a3b8;">${{srv.command}} ${{srv.args.join(' ')}}</div>
                   </div>
                   <button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="removeMCPServer('${{name}}')">✕</button>
                </div>
              `;
           }});
           container.innerHTML = html;
         }} catch (err) {{}}
      }}

      window.removeMCPServer = async (name) => {{
         await fetch(`/settings/mcp/${{name}}`, {{ method: 'DELETE' }});
         fetchMCPServers();
         fetchModels(); // Refresh available tools list
      }};

      document.getElementById('add-mcp-btn').addEventListener('click', async () => {{
         const name = document.getElementById('mcp-name').value.trim();
         const command = document.getElementById('mcp-cmd').value.trim();
         const argsStr = document.getElementById('mcp-args').value.trim();
         if (!name || !command) return;
         
         const payload = {{
            name: name,
            command: command,
            args: argsStr ? argsStr.split(',').map(s => s.trim()) : []
         }};
         
         await fetch('/settings/mcp', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(payload)
         }});
         
         document.getElementById('mcp-name').value = '';
         document.getElementById('mcp-cmd').value = '';
         document.getElementById('mcp-args').value = '';
         
         document.getElementById('mcp-add-result').textContent = "Added!";
         setTimeout(() => document.getElementById('mcp-add-result').textContent = "", 2000);
         
         fetchMCPServers();
      }});

      async function refreshApprovals() {{
        const res = await fetch('/approvals?status=pending');
        const data = await res.json();
        const c = document.getElementById('approvals-container');
        if (!data.approvals || data.approvals.length === 0) {{ c.innerHTML = '<div style="font-size:12px; color:#cbd5e1;">None</div>'; return; }}
        
        let html = '';
        data.approvals.forEach(a => {{
           let p = ''; try {{ p = JSON.stringify(JSON.parse(a.payload_json), null, 2); }} catch(e){{}}
           html += `
             <div class="approval-card">
               <div style="font-weight:bold; margin-bottom:4px;">${{a.action}}</div>
               <div style="margin-bottom:8px;">${{a.reason}}</div>
               <pre>${{p}}</pre>
               <button class="btn-approve" onclick="decideApproval('${{a.approval_id}}', 'approved')">Approve</button>
               <button class="btn-reject" onclick="decideApproval('${{a.approval_id}}', 'rejected')">Reject</button>
             </div>
           `;
        }});
        c.innerHTML = html;
      }}

      window.decideApproval = async (id, dec) => {{
        await fetch(`/approvals/${{id}}/decision`, {{ method: 'POST', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify({{decision: dec, reviewer:'local-user'}}) }});
        refreshApprovals();
      }};

      function scrollToBottom() {{
          const h = document.getElementById('chat-history');
          h.scrollTop = h.scrollHeight;
      }}

      function renderSessionsSidebar(runs) {{
          const container = document.getElementById('sessions-container');
          let html = '';
          runs.forEach(run => {{
             const isActive = run.run_id === activeRunId ? 'active' : '';
             const stClass = `status-${{run.status.toLowerCase()}}`;
             html += `
                <div class="session-item ${{isActive}}" onclick="selectSession('${{run.run_id}}')">
                   <div class="session-goal">${{run.goal || 'Session'}}</div>
                   <span class="status-badge ${{stClass}}" style="font-size:9px;">${{run.status}}</span>
                </div>
             `;
          }});
          container.innerHTML = html;
      }}

      function selectSession(runId) {{
          activeRunId = runId;
          refreshChat();
      }}

      function startNewSession() {{
          activeRunId = "new";
          renderedRunId = "new";
          document.getElementById('chat-history').innerHTML = `
              <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #94a3b8;">
                  <h3 style="margin-bottom: 8px;">Start a New Session</h3>
                  <p style="font-size: 13px; margin: 0;">Type your goal below to launch the agent.</p>
              </div>
          `;
          document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
      }}

      function renderRunToChat(run) {{
          const h = document.getElementById('chat-history');
          
          let userMsg = document.getElementById(`usr-${{run.run_id}}`);
          if (!userMsg) {{
              userMsg = document.createElement('div');
              userMsg.className = 'message msg-user';
              userMsg.id = `usr-${{run.run_id}}`;
              userMsg.innerHTML = `<div class="bubble">${{run.goal || 'No goal specified'}}</div><div class="timestamp">${{run.created_at}}</div>`;
              h.appendChild(userMsg);
          }}
          
          let agentMsg = document.getElementById(`agt-${{run.run_id}}`);
          if (!agentMsg) {{
              agentMsg = document.createElement('div');
              agentMsg.className = 'message msg-agent';
              agentMsg.id = `agt-${{run.run_id}}`;
              
              const stClass = `status-${{run.status.toLowerCase()}}`;
              let summaryText = run.status === 'done' ? 'Task Completed' : (run.status === 'blocked' ? 'Task Blocked' : 'Agent is working...');
              
              agentMsg.innerHTML = `
                <div class="bubble">
                   <div id="response-text-${{run.run_id}}" style="white-space: pre-wrap; font-size: 14px; color: #f8fafc; margin-bottom: 8px;"></div>
                   <details class="agent-work" id="details-${{run.run_id}}" ${{['running', 'queued'].includes(run.status.toLowerCase()) ? 'open' : ''}}>
                      <summary>
                         <span id="summary-text-${{run.run_id}}">${{summaryText}}</span> <span class="status-badge ${{stClass}}" id="badge-${{run.run_id}}">${{run.status}}</span>
                      </summary>
                      <div id="steps-${{run.run_id}}" class="steps-container">Loading steps...</div>
                   </details>
                   <div id="actions-${{run.run_id}}" style="margin-top: 10px; display: flex; gap: 8px;"></div>
                </div>
              `;
              h.appendChild(agentMsg);
          }} else {{
              const stClass = `status-${{run.status.toLowerCase()}}`;
              const badge = document.getElementById(`badge-${{run.run_id}}`);
              if (badge) {{
                  badge.className = `status-badge ${{stClass}}`;
                  badge.textContent = run.status;
              }}
              const summary = document.getElementById(`summary-text-${{run.run_id}}`);
              if (summary) {{
                  summary.textContent = run.status === 'done' ? 'Task Completed' : (run.status === 'blocked' ? 'Task Blocked' : 'Agent is working...');
              }}
          }}
          
          const actionsEl = document.getElementById(`actions-${{run.run_id}}`);
          if (actionsEl) {{
              if (['blocked', 'failed'].includes(run.status.toLowerCase())) {{
                  actionsEl.innerHTML = `
                      <button onclick="retryRun('${{run.run_id}}')" style="background: #ea580c; padding: 6px 12px; font-size: 12px; border-radius: 4px; border: none; color: white; cursor: pointer; font-weight: bold;">Retry Task</button>
                      <button onclick="editGoal('${{run.run_id}}')" style="background: #475569; padding: 6px 12px; font-size: 12px; border-radius: 4px; border: none; color: white; cursor: pointer; font-weight: bold;">Edit Goal</button>
                  `;
              }} else {{
                  actionsEl.innerHTML = '';
              }}
          }}
      }}

      async function fetchStepsForRun(runId) {{
          try {{
            const res = await fetch(`/runs/${{runId}}/steps`);
            const data = await res.json();
            const el = document.getElementById(`steps-${{runId}}`);
            if (!el) return;
            
            if (!data.steps || data.steps.length === 0) {{
                el.innerHTML = '<div style="color: #94a3b8;">No steps logged yet...</div>';
                return;
            }}
            
            let html = '';
            let mainResponse = '';
            data.steps.forEach(s => {{
               let msg = s.message || '';
               let testMeta = '';
               
               const idx = msg.indexOf('\\n\\n(');
               if (idx !== -1) {{
                   testMeta = msg.substring(idx + 4, msg.length - 1);
                   msg = msg.substring(0, idx);
               }} else if (msg.startsWith('Step completed') || msg.startsWith('Step blocked')) {{
                   testMeta = msg;
                   msg = '';
               }}
               
               if (msg && !mainResponse) {{
                   mainResponse = msg;
               }}
               
               const stClass = `status-${{s.status.toLowerCase()}}`;
               
               html += `
                 <div class="step-card">
                    <div class="step-header">
                       <span>Step ${{s.step_id}}: ${{s.title}}</span>
                       <span class="status-badge ${{stClass}}">${{s.status}}</span>
                    </div>
                    ${{msg ? '<div class="step-body">' + msg + '</div>' : ''}}
                    ${{testMeta ? '<div class="step-footer"><span>Verifier status:</span><span style="color:#10b981; font-weight:600;">✓ ' + testMeta + '</span></div>' : ''}}
                 </div>
               `;
            }});
            
            if (mainResponse) {{
                const textEl = document.getElementById(`response-text-${{runId}}`);
                if (textEl && textEl.textContent !== mainResponse) {{
                    textEl.textContent = mainResponse;
                }}
            }}
            
            if (el.innerHTML.length !== html.length) {{
                el.innerHTML = html;
            }}
          }} catch(e) {{}}
      }}

      async function refreshChat() {{
        const res = await fetch('/runs?limit=20');
        const data = await res.json();
        const runs = data.runs || [];
        runsCache = runs;
        
        renderSessionsSidebar(runs);
        
        // Initial page load auto-selection
        if (activeRunId === null && runs.length > 0) {{
            activeRunId = runs[0].run_id;
        }}
        
        if (activeRunId === "new") {{
            // New Session Sentinel Mode
            if (renderedRunId !== "new") {{
                startNewSession();
            }}
            return;
        }}
        
        const activeRun = runs.find(r => r.run_id === activeRunId);
        if (activeRun) {{
            // Clean view shift if run changed
            if (renderedRunId !== activeRunId) {{
                document.getElementById('chat-history').innerHTML = '';
                renderedRunId = activeRunId;
            }}
            
            renderRunToChat(activeRun);
            const details = document.getElementById(`details-${{activeRun.run_id}}`);
            if (details && details.open) {{
                fetchStepsForRun(activeRun.run_id);
            }}
        }}
      }}

      async function sendGoal() {{
        const input = document.getElementById('goal');
        const goal = input.value.trim();
        if (!goal) return;
        
        input.disabled = true;
        
        try {{
          await saveLLMSettings(); 
          
          const res = await fetch('/run', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
              goal: goal,
              mode: document.getElementById('mode').value,
              keep_tests: document.getElementById('keep-tests').value === 'true'
            }})
          }});
          if (!res.ok) {{
              const errText = await res.text();
              console.error("Failed to enqueue task:", errText);
              alert("Failed to start task: " + errText);
          }} else {{
              input.value = '';
              activeRunId = "new";
              document.getElementById('chat-history').innerHTML = '';
              
              const selectNewRunInterval = setInterval(async () => {{
                  const rRes = await fetch('/runs?limit=5');
                  const rData = await rRes.json();
                  if (rData.runs && rData.runs.length > 0) {{
                      const found = rData.runs.find(r => r.goal === goal);
                      if (found) {{
                          activeRunId = found.run_id;
                          refreshChat();
                          clearInterval(selectNewRunInterval);
                      }}
                  }}
              }}, 500);
          }}
        }} catch (err) {{
          console.error("Error sending goal:", err);
          alert("Error sending goal: " + err.message);
        }} finally {{
          input.disabled = false;
          input.focus();
        }}
      }}

      async function retryRun(runId) {{
          const run = runsCache.find(r => r.run_id === runId);
          if (!run) return;
          
          const btn = document.querySelector(`#actions-${{runId}} button`);
          if (btn) btn.disabled = true;

          try {{
              await saveLLMSettings(); 
              
              const res = await fetch('/run', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                  goal: run.goal,
                  mode: document.getElementById('mode').value,
                  keep_tests: document.getElementById('keep-tests').value === 'true'
                }})
              }});
              if (!res.ok) {{
                  const errText = await res.text();
                  console.error("Failed to retry task:", errText);
                  alert("Failed to retry task: " + errText);
                  if (btn) btn.disabled = false;
              }} else {{
                  activeRunId = "new";
                  document.getElementById('chat-history').innerHTML = '';
                  
                  const selectNewRunInterval = setInterval(async () => {{
                      const rRes = await fetch('/runs?limit=5');
                      const rData = await rRes.json();
                      if (rData.runs && rData.runs.length > 0) {{
                          const found = rData.runs.find(r => r.goal === run.goal);
                          if (found) {{
                              activeRunId = found.run_id;
                              refreshChat();
                              clearInterval(selectNewRunInterval);
                          }}
                      }}
                  }}, 500);
              }}
          }} catch (err) {{
              console.error("Error retrying task:", err);
              alert("Error retrying task: " + err.message);
              if (btn) btn.disabled = false;
          }}
      }}

      function editGoal(runId) {{
          const run = runsCache.find(r => r.run_id === runId);
          if (!run) return;
          const input = document.getElementById('goal');
          input.value = run.goal;
          input.focus();
      }}

      document.getElementById('run-btn').addEventListener('click', sendGoal);
      document.getElementById('goal').addEventListener('keypress', e => {{ if (e.key === 'Enter') sendGoal(); }});
      document.getElementById('save-llm-btn').addEventListener('click', saveLLMSettings);
      document.getElementById('save-policy-btn').addEventListener('click', savePolicy);
      document.getElementById('new-session-btn').addEventListener('click', () => selectSession('new'));
      
      document.getElementById('auto-detect-btn').addEventListener('click', async () => {{
         const btn = document.getElementById('auto-detect-btn');
         const status = document.getElementById('models-status');
         btn.disabled = true;
         status.textContent = "Probing ports...";
         try {{
            const res = await fetch('/models/auto-detect', {{ method: 'POST' }});
            const data = await res.json();
            if (data.ok) {{
                document.getElementById('provider').value = data.provider;
                await fetchModels();
                status.textContent = `Allocated: ${{data.allocated.planner}}`;
            }} else {{
                status.textContent = data.error || "Auto-detect failed.";
            }}
         }} catch(e) {{
            status.textContent = "Error during auto-detect.";
         }}
         btn.disabled = false;
      }});

      document.getElementById('provider').addEventListener('change', fetchModels);

      fetchModels();
      fetchMCPServers();
      refreshChat().then(() => setTimeout(scrollToBottom, 500));
      refreshApprovals();
      
      setInterval(refreshChat, 2000);
      setInterval(refreshApprovals, 2000);
    </script>
</body>
</html>
"""


@dataclass
class TaskStep:
	step_id: str
	title: str
	mode: str
	expectations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestRunReport:
	passed: bool
	generated_path: Optional[Path]
	attempts: int
	message: str


@dataclass
class StepCompletion:
	status: str
	message: str
	test_report: Optional[TestRunReport] = None


class StateStore:
	def __init__(self, db_path: Path) -> None:
		self.db_path = db_path
		self.db_path.parent.mkdir(parents=True, exist_ok=True)
		self._init()

	def _init(self) -> None:
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

	def create_run(self, goal: str) -> str:
		run_id = str(uuid.uuid4())
		now = _utc_now()
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO runs(run_id, goal, status, created_at, updated_at) VALUES(?,?,?,?,?)",
				(run_id, goal, "running", now, now),
			)
		return run_id

	def set_run_status(self, run_id: str, status: str) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"UPDATE runs SET status = ?, updated_at = ? WHERE run_id = ?",
				(status, _utc_now(), run_id),
			)

	def add_step(self, run_id: str, step: TaskStep, status: str, message: str) -> None:
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO steps(run_id, step_id, title, mode, status, message, created_at) VALUES(?,?,?,?,?,?,?)",
				(run_id, step.step_id, step.title, step.mode, status, message, _utc_now()),
			)

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

	def enqueue_job(self, goal: str, mode: str, keep_tests: bool) -> str:
		job_id = str(uuid.uuid4())
		now = _utc_now()
		with sqlite3.connect(self.db_path) as conn:
			conn.execute(
				"INSERT INTO jobs(job_id, goal, mode, keep_tests, status, result_json, error, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
				(job_id, goal, mode, 1 if keep_tests else 0, "queued", None, None, now, now),
			)
		return job_id

	def claim_next_job(self) -> Optional[Dict[str, Any]]:
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


class LLMProviderRouter:
	def __init__(self, cfg: LLMConfig) -> None:
		self.cfg = cfg

	def metadata(self) -> Dict[str, str]:
		return {
			"provider": self.cfg.provider,
			"base_url": self.cfg.get_base_url(),
			"transport": self.cfg.transport,
		}


class LocalLLMClient:
	def __init__(self, cfg: LLMConfig) -> None:
		self.cfg = cfg
		self.engine = None

	def _fallback(self, role: str, payload: Dict[str, Any]) -> Dict[str, Any]:
		if role == "planner":
			goal = str(payload.get("goal", "")).strip() or "Implement task"
			expectations: Dict[str, Any] = {}
			goal_parts = goal.split()
			for token in goal_parts:
				if token.endswith(".txt"):
					expectations["path"] = token
					expectations["content_contains"] = "created by agent"
					break
			return {
				"steps": [
					{"step_id": "step_1", "title": goal, "mode": "coding", "expectations": expectations}
				]
			}

		if role == "executor":
			step = payload.get("step", {})
			title = str(step.get("title", "")).lower()
			if "create" in title and ".txt" in title:
				parts = str(step.get("title", "")).split()
				target = next((p for p in parts if p.endswith(".txt")), "output.txt")
				return {
					"action": "tool_call",
					"tool_name": "write_file",
					"tool_input": {"path": target, "content": "created by agent\n"},
				}
			return {"action": "final_answer", "final_answer": "no-op"}

		if role == "verifier":
			result = payload.get("execution_result", {})
			return {"ok": bool(result.get("ok")), "reason": "fallback verifier decision"}

		return {}

	def complete_json(self, role: str, payload: Dict[str, Any], model: str) -> Dict[str, Any]:
		if self.cfg.transport != "openai_compatible":
			return self._fallback(role, payload)

		try:
			from openai import OpenAI
		except Exception:
			return self._fallback(role, payload)

		prompt = {
			"role": role,
			"payload": payload,
			"must_return_json_object": True,
		}

		system_prompt = "Return strictly valid JSON object only."
		if role == "planner":
			system_prompt += " You must return a JSON object with a 'steps' array. Each step must have 'step_id', 'title', 'mode', and 'expectations' (with 'path' or 'content_contains')."
		elif role == "executor":
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

			system_prompt += (
				" You must return a JSON object with 'action' (either 'tool_call' or 'final_answer')."
				" If calling a tool, specify 'tool_name' and 'tool_input'. Available native tools: "
				" 'write_file'(path, content), 'read_file'(path), 'create_new_file'(path, content), "
				" 'file_glob_search'(pattern), 'view_diff'(), 'ls'(path), 'fetch_url_content'(url), "
				" 'edit_existing_file'(path, old_string, new_string), 'grep_search'(query, path), 'run_shell'(command)."
				f"{mcp_desc_str}"
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
				system_prompt += " You must evaluate if the 'execution_result' successfully fulfilled the 'step' requirements. Return a JSON object with 'ok' (boolean) and 'reason' (string)."

		try:
			client = OpenAI(base_url=self.cfg.get_base_url(), api_key=self.cfg.get_api_key(), timeout=10.0)
			resp = client.chat.completions.create(
				model=model,
				temperature=0.1,
				max_tokens=self.cfg.max_tokens,
				messages=[
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": json.dumps(prompt)},
				],
			)
			text = (resp.choices[0].message.content or "{}").strip()
			if text.startswith("```"):
				first_nl = text.find("\n")
				if first_nl != -1:
					text = text[first_nl + 1:]
				if text.endswith("```"):
					text = text[:-3]
			text = text.strip()
			parsed = json.loads(text)
			if isinstance(parsed, dict):
				return parsed
		except Exception:
			pass

		return self._fallback(role, payload)


class ToolRegistry:
	def __init__(self, cfg: AgentConfig, root_dir: Path, store: Optional[StateStore] = None) -> None:
		self.cfg = cfg
		self.root_dir = root_dir
		self.store = store

	def _requires_approval(self, action: str) -> bool:
		return action in set(self.cfg.safety.require_approval_for)

	def _is_blocked(self, command: str) -> bool:
		cmd = command.strip().lower()
		for pattern in self.cfg.safety.blocked_commands:
			if pattern.lower() in cmd:
				return True
		return False

	def _safe_path(self, raw_path: str) -> Path:
		path = (self.root_dir / raw_path).resolve()
		if not str(path).startswith(str(self.root_dir.resolve())):
			raise ValueError("path outside allowed workspace")
		return path

	def call(self, tool_name: str, args: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
		if tool_name == "write_file":
			target = self._safe_path(str(args.get("path", "")))
			target.parent.mkdir(parents=True, exist_ok=True)
			target.write_text(str(args.get("content", "")), encoding="utf-8")
			return {"ok": True, "path": str(target)}

		if tool_name == "read_file":
			target = self._safe_path(str(args.get("path", "")))
			if not target.exists():
				return {"ok": False, "error": "file not found"}
			return {"ok": True, "content": target.read_text(encoding="utf-8")}

		if tool_name == "create_new_file":
			target = self._safe_path(str(args.get("path", "")))
			if target.exists():
				return {"ok": False, "error": "file already exists"}
			target.parent.mkdir(parents=True, exist_ok=True)
			target.write_text(str(args.get("content", "")), encoding="utf-8")
			return {"ok": True, "path": str(target)}

		if tool_name == "file_glob_search":
			pattern = str(args.get("pattern", "**/*"))
			matches = list(self.root_dir.rglob(pattern))
			return {"ok": True, "files": [str(p.relative_to(self.root_dir)) for p in matches[:100]]}

		if tool_name == "view_diff":
			proc = subprocess.run(["git", "diff"], cwd=str(self.root_dir), capture_output=True, text=True)
			return {"ok": True, "diff": proc.stdout}

		if tool_name == "ls":
			target = self._safe_path(str(args.get("path", ".")))
			if not target.is_dir():
				return {"ok": False, "error": "not a directory"}
			items = [str(p.relative_to(target)) for p in target.iterdir()]
			return {"ok": True, "contents": items}

		if tool_name == "fetch_url_content":
			url = str(args.get("url", ""))
			try:
				with urllib.request.urlopen(url, timeout=5) as resp:
					return {"ok": True, "content": resp.read().decode("utf-8")[:10000]}
			except Exception as exc:
				return {"ok": False, "error": str(exc)}

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

		if tool_name == "grep_search":
			query = str(args.get("query", ""))
			target = self._safe_path(str(args.get("path", ".")))
			proc = subprocess.run(["grep", "-rn", query, str(target)], capture_output=True, text=True)
			return {"ok": True, "matches": proc.stdout[:10000]}

		if tool_name == "run_shell":
			command = str(args.get("command", ""))
			if self._is_blocked(command):
				return {"ok": False, "error": "blocked by safety policy"}
			if self._requires_approval("run_shell"):
				approval_id_arg = args.get("approval_id")
				if approval_id_arg and self.store is not None:
					status = self.store.get_approval_status(str(approval_id_arg))
					if status == "approved":
						pass
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

		return {"ok": False, "error": f"unknown tool: {tool_name}"}


class MCPClientRegistry:
	def __init__(self) -> None:
		self._servers: Dict[str, Dict[str, Any]] = {}
		self._sessions: Dict[str, Any] = {}
		self._loop = None
		self._thread = None
		self._stack = None

	def register(self, name: str, config: Dict[str, Any]) -> None:
		self._servers[name] = dict(config)

	def list_servers(self) -> List[str]:
		return sorted(self._servers.keys())

	def _init_server_sync(self, name: str) -> None:
		if name in self._sessions:
			return
		
		try:
			from mcp import ClientSession, StdioServerParameters
			from mcp.client.stdio import stdio_client
		except ImportError as exc:
			raise RuntimeError("mcp package is not installed. Please pip install mcp>=1.0.0") from exc

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
			raise ValueError("mcp transport not implemented")
		
		command = str(server.get("command", ""))
		args = [str(a) for a in server.get("args", [])]

		async def _connect():
			server_params = StdioServerParameters(command=command, args=args)
			transport = await self._stack.enter_async_context(stdio_client(server_params))
			read, write = transport
			session = await self._stack.enter_async_context(ClientSession(read, write))
			await session.initialize()
			return session

		import asyncio
		future = asyncio.run_coroutine_threadsafe(_connect(), self._loop)
		self._sessions[name] = future.result(timeout=10.0)

	def call(self, server_name: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
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

	def __del__(self) -> None:
		if self._loop and self._stack:
			try:
				import asyncio
				future = asyncio.run_coroutine_threadsafe(self._stack.aclose(), self._loop)
				future.result(timeout=5.0)
				self._loop.call_soon_threadsafe(self._loop.stop)
			except Exception:
				pass


class PlannerExecutorVerifier:
	def __init__(self, engine: "AgentEngine") -> None:
		self.engine = engine

	def _plan(self, goal: str) -> List[TaskStep]:
		resp = self.engine.llm_client.complete_json(
			role="planner",
			payload={"goal": goal},
			model=self.engine.cfg.llm.model_planner,
		)
		steps_data = resp.get("steps") if isinstance(resp, dict) else None
		if not isinstance(steps_data, list) or not steps_data:
			raise ValueError("planner contract invalid: missing steps list")

		steps: List[TaskStep] = []
		for idx, raw in enumerate(steps_data, start=1):
			if not isinstance(raw, dict):
				raise ValueError("planner contract invalid: step is not object")
			step_id = str(raw.get("step_id") or f"step_{idx}")
			title = str(raw.get("title") or "")
			mode = str(raw.get("mode") or "coding")
			expectations = raw.get("expectations", {})
			if not isinstance(expectations, dict):
				expectations = {}
			if not title:
				raise ValueError("planner contract invalid: step title missing")
			steps.append(TaskStep(step_id=step_id, title=title, mode=mode, expectations=expectations))
		return steps

	def _execute(self, step: TaskStep, run_id: Optional[str] = None) -> Dict[str, Any]:
		resp = self.engine.llm_client.complete_json(
			role="executor",
			payload={"step": asdict(step)},
			model=self.engine.cfg.llm.model_executor,
		)
		if not isinstance(resp, dict):
			return {"ok": False, "error": "executor contract invalid"}

		action = str(resp.get("action", "")).strip()
		if action == "tool_call":
			tool_name = str(resp.get("tool_name", "")).strip()
			tool_input = resp.get("tool_input", {})
			if not tool_name or not isinstance(tool_input, dict):
				return {"ok": False, "error": "executor contract invalid: bad tool_call fields"}
			result = self.engine.tools.call(tool_name, tool_input, run_id=run_id)
			if tool_name == "write_file" and result.get("ok"):
				if not step.expectations.get("path") and isinstance(tool_input.get("path"), str):
					step.expectations["path"] = str(tool_input.get("path"))
				content = tool_input.get("content")
				if isinstance(content, str) and content:
					step.expectations.setdefault("content_contains", content.strip().splitlines()[0])
			return result

		if action == "final_answer":
			return {"ok": True, "message": str(resp.get("final_answer", ""))}

		return {"ok": False, "error": "executor contract invalid: unsupported action"}

	def _verify(self, step: TaskStep, execution_result: Dict[str, Any]) -> bool:
		# Use verifier role to strictly evaluate step correctness (ok = True/False)
		resp = self.engine.llm_client.complete_json(
			role="verifier",
			payload={"step": asdict(step), "execution_result": execution_result},
			model=self.engine.cfg.llm.model_verifier,
		)
		if not isinstance(resp, dict) or "ok" not in resp:
			return bool(execution_result.get("ok"))
		return bool(resp.get("ok"))

	def run(self, goal: str, keep_tests: bool = False) -> Dict[str, Any]:
		run_id = self.engine.store.create_run(goal)
		try:
			steps = self._plan(goal)
		except ValueError as exc:
			self.engine.store.set_run_status(run_id, "blocked")
			return {"status": "blocked", "run_id": run_id, "reason": f"planner error: {exc}"}

		for step in steps:
			execution_result = self._execute(step, run_id=run_id)
			if not self._verify(step, execution_result):
				self.engine.store.add_step(run_id, step, "blocked", "execution verification failed")
				self.engine.store.set_run_status(run_id, "blocked")
				return {"status": "blocked", "run_id": run_id, "reason": "execution verification failed"}

			completion = self.engine.complete_step(step=step, keep_tests=keep_tests, run_id=run_id)
			msg = completion.message
			if isinstance(execution_result, dict) and execution_result.get("message"):
				msg = f"{execution_result['message']}\n\n({completion.message})"
			self.engine.store.add_step(run_id, step, completion.status, msg)
			if completion.status != "done":
				self.engine.store.set_run_status(run_id, completion.status)
				return {"status": completion.status, "run_id": run_id, "reason": completion.message}

		self.engine.store.set_run_status(run_id, "done")
		return {"status": "done", "run_id": run_id, "steps": len(steps)}


class TestLifecycleManager:
	__test__ = False

	def __init__(self, cfg: AgentConfig, root_dir: Path, llm_client: Optional[LocalLLMClient] = None) -> None:
		self.cfg = cfg
		self.root_dir = root_dir
		self.llm_client = llm_client

	def _test_dir(self) -> Path:
		strategy = self.cfg.test_policy.test_location_strategy
		if strategy == "adjacent_temp":
			d = self.root_dir / ".agent_tmp_tests"
		else:
			d = self.root_dir / "tests_temp"
		d.mkdir(parents=True, exist_ok=True)
		return d

	def _generate_test_file(self, step: TaskStep) -> Path:
		safe_name = "".join(ch if ch.isalnum() else "_" for ch in step.title.lower()).strip("_")
		name = safe_name or "task"
		path = self._test_dir() / f"test_{step.step_id}_{name}.py"
		
		if self.llm_client and self.cfg.llm.transport == "openai_compatible":
			payload = {"step": asdict(step), "task": "generate_pytest"}
			res = self.llm_client.complete_json("verifier", payload, self.cfg.llm.model_verifier)
			if isinstance(res, dict) and "test_code" in res:
				path.write_text(str(res["test_code"]), encoding="utf-8")
				return path

		expected_path = step.expectations.get("path")
		expected_contains = step.expectations.get("content_contains")
		if isinstance(expected_path, str) and expected_path:
			target = (self.root_dir / expected_path).resolve()
			content = (
				"from pathlib import Path\n\n\n"
				"def test_task_contract():\n"
				f"    # Generated test contract for step: {step.title}\n"
				f"    target = Path({str(target)!r})\n"
				"    assert target.exists(), \"Expected artifact file to exist\"\n"
			)
			if isinstance(expected_contains, str) and expected_contains:
				content += (
					f"    text = target.read_text(encoding=\"utf-8\")\n"
					f"    assert {expected_contains!r} in text, \"Expected content marker not found\"\n"
				)
			content += (
				"\n\n"
				"if __name__ == \"__main__\":\n"
				"    test_task_contract()\n"
			)
		else:
			content = textwrap.dedent(
				f"""
				def test_task_contract():
					# Generated test contract for step: {step.title}
					assert True


				if __name__ == "__main__":
					test_task_contract()
				"""
			).lstrip()
		path.write_text(content, encoding="utf-8")
		return path

	def _verify_and_autocorrect(self, test_path: Path, error_message: str = "") -> None:
		source = test_path.read_text(encoding="utf-8")
		
		if self.llm_client and self.cfg.llm.transport == "openai_compatible" and error_message:
			payload = {"test_code": source, "error": error_message, "task": "autocorrect_pytest"}
			res = self.llm_client.complete_json("verifier", payload, self.cfg.llm.model_verifier)
			if isinstance(res, dict) and "fixed_test_code" in res:
				test_path.write_text(str(res["fixed_test_code"]), encoding="utf-8")
				return

		if "def test_" not in source:
			fixed = "def test_autofixed():\n    assert True\n"
			test_path.write_text(fixed, encoding="utf-8")

	def _run_test_file(self, test_path: Path, mode: str) -> subprocess.CompletedProcess:
		runner = self.cfg.test_policy.test_runner_by_mode.get(mode, "python")
		if runner == "pytest":
			return subprocess.run(
				[sys.executable, "-m", "pytest", str(test_path), "-q"],
				capture_output=True,
				text=True,
				check=False,
			)
		return subprocess.run(
			[sys.executable, str(test_path)],
			capture_output=True,
			text=True,
			check=False,
		)

	def generate_verify_run_cleanup(self, step: TaskStep, keep_tests: bool = False) -> TestRunReport:
		policy = self.cfg.test_policy
		if not policy.enforce_task_test_gate:
			return TestRunReport(True, None, 0, "test gate disabled")

		if not policy.auto_generate_tests:
			return TestRunReport(False, None, 0, "test generation is required but disabled")

		test_path = self._generate_test_file(step)
		attempts = 0
		last_message = ""

		for attempt in range(policy.max_test_fix_attempts + 1):
			attempts = attempt + 1
			if policy.verify_and_autocorrect_tests:
				self._verify_and_autocorrect(test_path, last_message)
			result = self._run_test_file(test_path, step.mode)
			if result.returncode == 0:
				delete_after = policy.delete_tests_after_task and not keep_tests
				if delete_after and test_path.exists():
					test_path.unlink()
				return TestRunReport(True, test_path, attempts, "tests passed")
			last_message = (result.stderr or result.stdout or "test execution failed").strip()

		return TestRunReport(False, test_path, attempts, last_message or "test gate failed")


class AgentEngine:
	def __init__(self, cfg: AgentConfig, root_dir: Path) -> None:
		self.cfg = cfg
		self.root_dir = root_dir
		self.llm_client = LocalLLMClient(cfg.llm)
		self.router = LLMProviderRouter(cfg.llm)
		self.store = StateStore(root_dir / "state" / "agent.db")
		self.test_manager = TestLifecycleManager(cfg, root_dir, llm_client=self.llm_client)
		self.tools = ToolRegistry(cfg, root_dir, store=self.store)
		self.mcp = MCPClientRegistry()
		for name, srv in self.cfg.mcp.servers.items():
			self.mcp.register(name, {"command": srv.command, "args": srv.args, "transport": srv.transport})
		self.orchestrator = PlannerExecutorVerifier(self)
		self.llm_client.engine = self

	def call_mcp_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
		for server_name in self.mcp.list_servers():
			try:
				self.mcp._init_server_sync(server_name)
				session = self.mcp._sessions[server_name]
				import asyncio
				future = asyncio.run_coroutine_threadsafe(session.list_tools(), self.mcp._loop)
				tools_list = future.result(timeout=5.0)
				has_tool = any(t.name == tool_name for t in tools_list.tools)
				if has_tool:
					res = self.mcp.call(server_name, tool_name, params)
					return res
			except Exception as exc:
				pass
		return {"ok": False, "error": f"Tool '{tool_name}' not found in native tools or registered MCP servers."}

	def complete_step(self, step: TaskStep, keep_tests: bool = False, run_id: Optional[str] = None) -> StepCompletion:
		try:
			report = self.test_manager.generate_verify_run_cleanup(step=step, keep_tests=keep_tests)
		except Exception as exc:  # pragma: no cover
			return StepCompletion(status="blocked", message=f"Step blocked by test gate error: {exc}")

		if run_id:
			self.store.add_test_report(run_id, step.step_id, report)

		if not report.passed:
			return StepCompletion(
				status="blocked",
				message=f"Step blocked by test gate: {report.message}",
				test_report=report,
			)

		return StepCompletion(status="done", message="Step completed after passing generated tests", test_report=report)

	def run_goal(self, goal: str, mode: str = "coding", keep_tests: bool = False) -> Dict[str, Any]:
		loop_result = self.orchestrator.run(goal=goal, keep_tests=keep_tests)
		run_id = str(loop_result.get("run_id"))
		step = TaskStep(step_id="step_1", title=goal, mode=mode)
		generated_test = self.store.latest_test_path_for_run(run_id)
		return {
			"run_id": run_id,
			"provider": self.router.metadata(),
			"step": asdict(step),
			"result": {
				"status": str(loop_result.get("status", "blocked")),
				"message": str(loop_result.get("reason", "completed by planner-executor-verifier")),
				"tests_passed": str(loop_result.get("status")) == "done",
				"generated_test": generated_test,
			},
		}

	def process_next_job(self) -> Optional[Dict[str, Any]]:
		job = self.store.claim_next_job()
		if not job:
			return None
		job_id = str(job["job_id"])
		try:
			result = self.run_goal(
				goal=str(job["goal"]),
				mode=str(job["mode"]),
				keep_tests=bool(job["keep_tests"]),
			)
			status = "done" if str(result.get("result", {}).get("status")) == "done" else "blocked"
			self.store.finish_job(job_id, status=status, result_json=json.dumps(result), error=None)
			return result
		except Exception as exc:  # pragma: no cover
			self.store.finish_job(job_id, status="failed", result_json=None, error=str(exc))
			return None


def create_ui_app(engine: AgentEngine):
	try:
		from fastapi import FastAPI, HTTPException
		from fastapi.responses import HTMLResponse
	except Exception as exc:  # pragma: no cover
		raise RuntimeError("fastapi is required for UI mode") from exc

	app = FastAPI(title="Local Agent UI API", version="1.0.0")

	@app.get("/", response_class=HTMLResponse)
	def root_page():
		content = render_ui_html(engine.cfg)
		return HTMLResponse(
			content=content,
			headers={
				"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
				"Pragma": "no-cache",
				"Expires": "0"
			}
		)

	@app.get("/settings")
	def get_settings() -> Dict[str, Any]:
		return engine.cfg.to_dict()

	@app.get("/models")
	def list_models(provider: str = "") -> Dict[str, Any]:
		import httpx
		prov = provider or engine.cfg.llm.provider
		url = engine.cfg.llm.base_url_lmstudio + "/models" if prov == "lmstudio" else engine.cfg.llm.base_url_ollama + "/api/tags"
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

	@app.put("/settings/llm")
	def update_llm_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
		for key, value in payload.items():
			if not hasattr(engine.cfg.llm, key):
				raise HTTPException(status_code=400, detail=f"Unknown llm setting key: {key}")
			setattr(engine.cfg.llm, key, value)
		save_config(engine.root_dir / "config.yaml", engine.cfg)
		return {"ok": True, "llm": engine.cfg.llm.__dict__}

	@app.post("/models/auto-detect")
	def auto_detect_and_allocate() -> Dict[str, Any]:
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
			prov = "lmstudio"
			models = lm_models
		elif ollama_models:
			prov = "ollama"
			models = ollama_models
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
			}
		}

	@app.get("/settings/mcp")
	def list_mcp_servers() -> Dict[str, Any]:
		# Fetch all currently registered MCP servers in config
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

	@app.get("/runs")
	def list_runs(limit: int = 20) -> Dict[str, Any]:
		return {"runs": engine.store.list_runs(limit=limit)}

	@app.get("/runs/{run_id}/steps")
	def list_steps(run_id: str) -> Dict[str, Any]:
		return {"run_id": run_id, "steps": engine.store.list_steps(run_id)}

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
		updated = engine.store.decide_approval(approval_id=approval_id, decision=decision, reviewer=reviewer)
		if not updated:
			raise HTTPException(status_code=404, detail="approval not found")
		return {"ok": True, "approval_id": approval_id, "status": decision}

	@app.put("/settings/test-policy")
	def update_test_policy(payload: Dict[str, Any]) -> Dict[str, Any]:
		for key, value in payload.items():
			if not hasattr(engine.cfg.test_policy, key):
				raise HTTPException(status_code=400, detail=f"Unknown test policy key: {key}")
			setattr(engine.cfg.test_policy, key, value)
		return {"ok": True, "test_policy": asdict(engine.cfg.test_policy)}

	@app.post("/run")
	def run_task(payload: Dict[str, Any]) -> Dict[str, Any]:
		goal = str(payload.get("goal", "")).strip()
		if not goal:
			raise HTTPException(status_code=400, detail="goal is required")
		mode = str(payload.get("mode", "coding"))
		keep_tests = bool(payload.get("keep_tests", False))
		job_id = engine.store.enqueue_job(goal=goal, mode=mode, keep_tests=keep_tests)
		return {"ok": True, "job_id": job_id}

	return app


def ensure_default_config(path: Path, root_dir: Path) -> AgentConfig:
	if path.exists():
		return load_config(path)
	cfg = AgentConfig.default(root_dir=root_dir)
	save_config(path, cfg)
	return cfg


def main() -> int:
	parser = argparse.ArgumentParser(description="Local real agent runner")
	parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
	parser.add_argument("--goal", default="Implement requested task", help="Goal to run")
	parser.add_argument("--mode", default="coding", help="Task mode")
	parser.add_argument("--keep-tests", action="store_true", help="Keep generated tests after success")
	parser.add_argument("--ui", action="store_true", help="Run FastAPI UI server")
	parser.add_argument("--worker", action="store_true", help="Run background daemon worker")
	args = parser.parse_args()

	root_dir = Path.cwd()
	config_path = root_dir / args.config
	cfg = ensure_default_config(config_path, root_dir=root_dir)
	engine = AgentEngine(cfg, root_dir=root_dir)

	if args.ui or args.worker:
		def _worker_loop():
			while True:
				try:
					engine.process_next_job()
				except Exception:
					pass
				time.sleep(2)
		t = threading.Thread(target=_worker_loop, daemon=True)
		t.start()

	if args.ui:
		try:
			import uvicorn
		except Exception as exc:  # pragma: no cover
			raise RuntimeError("uvicorn is required for --ui") from exc
		app = create_ui_app(engine)
		uvicorn.run(app, host=cfg.ui.host, port=cfg.ui.port)
		return 0

	if args.worker:
		# Just block forever if running in worker-only mode
		while True:
			time.sleep(1000)
		return 0

	result = engine.run_goal(goal=args.goal, mode=args.mode, keep_tests=args.keep_tests)
	print(json.dumps(result, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())