# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  agent/ui.py — HTML/CSS/JS Template for the Chat UI                      ║
# ║                                                                            ║
# ║  Contains the entire frontend: one self-contained HTML page served by     ║
# ║  the FastAPI server at GET /. Includes all CSS and JavaScript inline.     ║
# ║                                                                            ║
# ║  To modify the UI:                                                         ║
# ║    • CSS: look for the <style> block inside the template string            ║
# ║    • JS:  look for the <script> block at the bottom of the template       ║
# ║    • HTML layout: the sidebar, chat-area, and modal divs                  ║
# ║                                                                            ║
# ║  DEBUG TIP: Open browser DevTools (F12) and check the Console tab         ║
# ║  for JavaScript errors. API calls are logged to the console as well.      ║
# ║                                                                            ║
# ║  The UI polls these endpoints every 2s for live updates:                  ║
# ║    GET /runs/{run_id}/messages  - chat history                            ║
# ║    GET /approvals               - pending approval requests               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# 
# =============================================================================
# 🛠️ HOW TO MAKE THE APP BETTER: EXTENDING THE UI
# =============================================================================
# This file contains the entire frontend HTML, CSS, and Javascript.
# 
# 1. ADDING NEW BUTTONS OR UI PANELS:
#    Scroll down to the HTML section (inside the `<body>` tag). You can add new 
#    `<button>`, `<div>`, or `<input>` elements. For example, add a new button 
#    next to the "Settings" button in the sidebar footer.
# 
# 2. ADDING NEW THEMES/STYLES:
#    Scroll up to the `<style>` block. You can change colors (e.g. background 
#    #0b0f19) to create a light mode or change font sizes and padding.
# 
# 3. ADDING FRONTEND LOGIC (JAVASCRIPT):
#    Scroll to the bottom `<script>` tag. To make your new buttons work, add 
#    an event listener: `document.getElementById('my-btn').addEventListener(...)`. 
#    You can use `fetch('/my-new-endpoint')` to call a custom API route you 
#    add in `agent/api.py`.
# 
# 4. VIEWING RAW AI OUTPUT:
#    Open your browser's Developer Tools (F12 or Right Click -> Inspect), and 
#    go to the "Console" or "Network" tab to see all API responses (like the 
#    steps JSON) coming from the server.

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
from agent.config import AgentConfig


# ─────────────────────────────────────────────────────────────────────────────
# HTML TEMPLATE (render_ui_html)
# Returns the full HTML page as a string, with config values interpolated.
# ─────────────────────────────────────────────────────────────────────────────

def render_ui_html(cfg: AgentConfig) -> str:
	return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Agent Chat</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
        
        .markdown-body p {{ margin-top: 0; margin-bottom: 12px; }}
        .markdown-body ul, .markdown-body ol {{ margin-top: 0; margin-bottom: 12px; padding-left: 20px; }}
        .markdown-body li {{ margin-bottom: 4px; }}
        .markdown-body pre {{ background: #000; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 13px; margin: 12px 0; border: 1px solid #1f2937; }}
        .markdown-body code {{ font-family: monospace; font-size: 13px; background: #1f2937; padding: 2px 4px; border-radius: 4px; }}
        .markdown-body pre code {{ background: transparent; padding: 0; }}
        .markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {{ margin-top: 16px; margin-bottom: 8px; color: #f8fafc; font-weight: bold; font-size: 16px; }}
        .markdown-body a {{ color: #3b82f6; text-decoration: none; }}
        
        /* Collapsible Sidebar */
        .sidebar {{ width: 300px; background: #111827; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; border-right: 1px solid #1f2937; height: 100%; transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), padding 0.3s ease, border-right-width 0.3s ease; overflow-y: auto; position: relative; flex-shrink: 0; }}
        .sidebar.collapsed {{ width: 0; padding: 0; border-right: none; overflow: hidden; }}
        
        .sidebar-section {{ margin-bottom: 24px; }}
        .sidebar-title {{ font-size: 11px; font-weight: bold; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #1f2937; padding-bottom: 6px; }}
        
        /* Sessions List */
        .sessions-list {{ display: flex; flex-direction: column; gap: 8px; max-height: 380px; overflow-y: auto; }}
        .session-item {{ padding: 10px 12px; border-radius: 6px; background: #1f2937; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; font-size: 13px; transition: background 0.15s, border-color 0.15s; }}
        .session-item:hover {{ background: #374151; }}
        .session-item.active {{ border-color: #3b82f6; background: #0b0f19; }}
        .session-goal {{ font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 170px; color: #f1f5f9; }}
        
        /* Sidebar footer & Settings gear */
        .sidebar-footer {{ margin-top: auto; padding-top: 16px; border-top: 1px solid #1f2937; display: flex; align-items: center; justify-content: space-between; }}
        .gear-btn {{ background: transparent; border: none; color: #94a3b8; font-size: 14px; cursor: pointer; display: flex; align-items: center; gap: 8px; padding: 6px; transition: color 0.15s; width: 100%; border-radius: 4px; }}
        .gear-btn:hover {{ color: #f8fafc; background: #1f2937; }}
        
        /* Main Chat Window */
        .chat-area {{ flex: 1; display: flex; flex-direction: column; background: #0b0f19; height: 100%; min-width: 0; }}
        
        /* Chat Header */
        .chat-header {{ display: flex; align-items: center; gap: 16px; padding: 12px 24px; background: #111827; border-bottom: 1px solid #1f2937; }}
        .toggle-sidebar-btn {{ background: transparent; border: none; color: #cbd5e1; font-size: 18px; cursor: pointer; padding: 4px 8px; border-radius: 4px; display: flex; align-items: center; justify-content: center; }}
        .toggle-sidebar-btn:hover {{ background: #1f2937; color: #f8fafc; }}
        #active-session-title {{ font-weight: 600; font-size: 14px; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 600px; }}
        
        /* Chat History Feed */
        .chat-history {{ flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; scroll-behavior: smooth; }}
        
        /* Chat Input */
        .chat-input-area {{ background: #111827; padding: 16px 24px; border-top: 1px solid #1f2937; position: relative; z-index: 10; }}
        .input-box {{ display: flex; gap: 12px; }}
        input[type="text"], select, input[type="number"] {{ padding: 10px 14px; border-radius: 6px; border: 1px solid #374151; background: #1f2937; color: #f8fafc; outline: none; box-sizing: border-box; font-size: 13px; }}
        input[type="text"] {{ flex: 1; }}
        button {{ background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; transition: background 0.15s, opacity 0.15s; }}
        button:hover {{ background: #2563eb; }}
        button:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        .btn-danger {{ background: #ef4444; }}
        .btn-danger:hover {{ background: #dc2626; }}
        
        /* Chat Bubbles */
        .message {{ max-width: 85%; display: flex; flex-direction: column; margin-bottom: 8px; }}
        .msg-user {{ align-self: flex-end; align-items: flex-end; }}
        .msg-agent {{ align-self: flex-start; align-items: flex-start; width: 100%; max-width: 90%; }}
        
        .bubble {{ padding: 16px 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); line-height: 1.6; border: 1px solid transparent; font-size: 14px; box-sizing: border-box; width: 100%; }}
        .msg-user .bubble {{ background: #2563eb; color: white; border-bottom-right-radius: 4px; max-width: 70%; width: auto; }}
        .msg-agent .bubble {{ background: #111827; color: #e2e8f0; border-bottom-left-radius: 4px; border-color: #1f2937; }}
        .timestamp {{ font-size: 11px; color: #4b5563; margin-top: 6px; font-family: monospace; }}
        
        /* Action Links / Buttons below agent replies */
        .agent-actions {{ display: flex; gap: 14px; margin-top: 10px; padding-left: 4px; }}
        .action-link {{ color: #3b82f6; text-decoration: none; font-size: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: color 0.15s; }}
        .action-link:hover {{ color: #60a5fa; }}
        .action-link-danger {{ color: #ef4444; }}
        .action-link-danger:hover {{ color: #f87171; }}
        
        /* Collapsible details inside bubble */
        details {{ margin-top: 12px; background: #0b0f19; border: 1px solid #1f2937; border-radius: 8px; padding: 12px; box-sizing: border-box; }}
        summary {{ font-size: 13px; font-weight: 600; color: #60a5fa; cursor: pointer; outline: none; user-select: none; display: flex; align-items: center; gap: 6px; }}
        
        /* Step Timeline */
        .step-card {{ background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 10px; margin-top: 10px; }}
        .step-header {{ display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 11px; color: #94a3b8; }}
        .step-body {{ font-size: 12px; color: #cbd5e1; margin-top: 6px; white-space: pre-wrap; font-family: monospace; line-height: 1.4; }}
        
        /* Status Badges */
        .status-badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 9px; font-weight: bold; text-transform: uppercase; font-family: monospace; }}
        .status-done {{ background: #065f46; color: #34d399; }}
        .status-blocked {{ background: #7f1d1d; color: #fca5a5; }}
        .status-stopped {{ background: #7f1d1d; color: #fca5a5; }}
        .status-running {{ background: #78350f; color: #fcd34d; }}
        .status-queued {{ background: #374151; color: #cbd5e1; }}
        
        .spinner {{ width: 14px; height: 14px; border: 2px solid #3b82f6; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        
        /* Premium Backdrop Blurred Modals */
        .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(3, 7, 18, 0.8); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); align-items: center; justify-content: center; z-index: 1000; }}
        .modal-content {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 24px; width: 560px; max-width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5), 0 10px 10px -5px rgba(0,0,0,0.5); position: relative; }}
        .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1f2937; padding-bottom: 12px; }}
        .modal-title {{ font-size: 16px; font-weight: bold; color: #f8fafc; }}
        .modal-close {{ background: transparent; border: none; color: #94a3b8; font-size: 18px; cursor: pointer; padding: 4px; }}
        .modal-close:hover {{ color: #f8fafc; }}
        
        /* Tab Navigation inside Modal */
        .modal-tabs {{ display: flex; gap: 8px; border-bottom: 1px solid #1f2937; margin-bottom: 20px; padding-bottom: 8px; overflow-x: auto; }}
        .modal-tab {{ background: transparent; border: none; color: #94a3b8; padding: 6px 12px; font-size: 13px; cursor: pointer; border-radius: 6px; white-space: nowrap; }}
        .modal-tab:hover {{ color: #cbd5e1; background: #1f2937; }}
        .modal-tab.active {{ color: #f8fafc; background: #2563eb; font-weight: bold; }}
        .modal-tab-content {{ display: none; }}
        .modal-tab-content.active {{ display: block; }}
        
        /* Form inputs in Modal */
        .form-group {{ margin-bottom: 16px; display: flex; flex-direction: column; gap: 6px; }}
        .form-group label {{ font-size: 12px; font-weight: bold; color: #94a3b8; }}
        .form-row {{ display: flex; gap: 12px; }}
        .form-row .form-group {{ flex: 1; }}
        
        /* Queue Box right above input */
        #queue-box {{ background: #111827; border: 1px dashed #ef4444; border-radius: 8px; padding: 12px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; }}
        
        /* Tools list styling */
        .tool-desc-item {{ padding: 8px 12px; background: #1f2937; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 12px; }}
        .tool-desc-name {{ font-family: monospace; color: #60a5fa; font-weight: bold; }}
        
        /* Custom Scrollbars */
        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #1f2937; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #374151; }}
    </style>
</head>
<body>
    <!-- Left Sidebar -->
    <div class="sidebar" id="sidebar">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
            <h2 style="margin: 0; font-size: 18px; letter-spacing: -0.02em; color:#f8fafc;">AI Agent</h2>
        </div>
        
        <div class="sidebar-section" style="flex:1; display:flex; flex-direction:column; overflow:hidden;">
            <div class="sidebar-title">
                <span>Chat Sessions</span>
                <button id="new-session-btn" style="padding: 4px 8px; font-size: 10px; background:#1f2937; border:1px solid #374151;">＋ New</button>
            </div>
            <div class="sessions-list" id="sessions-container" style="flex:1;"></div>
        </div>
        
        <div class="sidebar-section" id="sidebar-approvals-section" style="display:none; border-top:1px solid #1f2937; padding-top:12px; max-height: 200px; overflow-y:auto;">
            <div class="sidebar-title" style="color: #fca5a5;">Approvals Required</div>
            <div id="approvals-container"></div>
        </div>

        <div class="sidebar-footer" style="gap: 8px;">
            <button class="gear-btn" id="workspace-btn">📁 Workspace</button>
            <button class="gear-btn" id="gear-btn">⚙️ Settings</button>
        </div>
    </div>
    
    <!-- Main Chat Content -->
    <div class="chat-area">
        <div class="chat-header">
            <button class="toggle-sidebar-btn" id="toggle-sidebar-btn">☰</button>
            <span id="active-session-title">Select or start a chat session...</span>
        </div>
        
        <div class="chat-history" id="chat-history"></div>
        
        <div class="chat-input-area">
            <!-- Queued Tasks Area -->
            <div id="queue-box" style="display:none;">
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#f87171; font-weight:bold;">
                    <span>⏳ QUEUED TASK</span>
                    <span>Pending Execution</span>
                </div>
                <div style="display:flex; gap:8px; align-items:center;">
                    <input type="text" id="queue-goal-input" style="flex:1; padding:6px 10px; background:#0b0f19; font-size:13px;">
                    <button id="queue-save-btn" style="background:#10b981; padding:6px 12px; font-size:12px;">Save</button>
                    <button id="queue-cancel-btn" class="btn-danger" style="padding:6px 12px; font-size:12px;">Cancel</button>
                </div>
            </div>

            <!-- Suggestion Banner Card -->
            <div id="suggestion-banner" style="display:none; background:#1e293b; border-left:4px solid #10b981; border-radius:6px; padding:10px 16px; margin-bottom:12px; font-size:12px; color:#cbd5e1; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span id="suggestion-icon">💡</span>
                    <span id="suggestion-text">It looks like you want to create a new tool.</span>
                </div>
                <button id="suggestion-btn" style="background:#10b981; color:#fff; font-size:11px; padding:4px 8px; border-radius:4px;" onclick="acceptSuggestion()">Accept & Create</button>
            </div>

            <!-- Input Box -->
            <div class="input-box">
                <input type="text" id="goal" placeholder="Type a message or describe a task..." autofocus>
                <button id="run-btn" style="width: 100px;">Send</button>
            </div>
            
            <div style="display: flex; gap: 16px; margin-top: 12px;">
                <div style="font-size: 12px; display: flex; align-items: center; gap: 8px; color:#cbd5e1;">
                    <label style="margin:0;">Mode:</label>
                    <select id="mode" style="width: auto; margin:0; padding: 4px 8px; background:#111827; border-color:#1f2937;">
                        <option value="coding">Coding</option>
                        <option value="planning">Planning</option>
                    </select>
                </div>
                <div style="font-size: 12px; display: flex; align-items: center; gap: 8px; color:#cbd5e1;">
                    <label style="margin:0;">Keep Tests:</label>
                    <select id="keep-tests" style="width: auto; margin:0; padding: 4px 8px; background:#111827; border-color:#1f2937;">
                        <option value="true">True</option>
                        <option value="false" selected>False</option>
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Backdrop Settings Modal Popup -->
    <div class="modal-overlay" id="settings-modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">⚙️ Global Settings</div>
                <button class="modal-close" onclick="closeModal('settings-modal')">✕</button>
            </div>
            
            <!-- Tabs Header -->
            <div class="modal-tabs">
                <button class="modal-tab active" id="btn-tab-models" onclick="switchTab('tab-models')">Models</button>
                <button class="modal-tab" id="btn-tab-policy" onclick="switchTab('tab-policy')">Test Policy</button>
                <button class="modal-tab" id="btn-tab-custom-tools" onclick="switchTab('tab-custom-tools')">Custom Tools</button>
                <button class="modal-tab" id="btn-tab-skills" onclick="switchTab('tab-skills')">Skills</button>
                <button class="modal-tab" id="btn-tab-mcp" onclick="switchTab('tab-mcp')">MCP</button>
            </div>

            <!-- Tab Content: Models -->
            <div id="tab-models" class="modal-tab-content active">
                <div style="font-size:13px; font-weight:bold; color:#cbd5e1; border-bottom:1px solid #1f2937; margin-bottom:12px; padding-bottom:4px;">Model Engine</div>
                <div class="form-row">
                    <div class="form-group" style="flex:1;">
                        <label>Provider</label>
                        <select id="provider" style="width:100%;"><option value="lmstudio">LM Studio</option><option value="ollama">Ollama</option></select>
                    </div>
                    <div class="form-group" style="flex:1; display:flex; align-items:flex-end;">
                        <button id="auto-detect-btn" style="background:#10b981; width:100%; padding: 10px;">Probe & Auto-Fill</button>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Planner</label>
                        <select id="model-planner" style="width:100%;"></select>
                    </div>
                    <div class="form-group">
                        <label>Executor</label>
                        <select id="model-executor" style="width:100%;"></select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Verifier</label>
                        <select id="model-verifier" style="width:100%;"></select>
                    </div>
                    <div class="form-group">
                        <label>Max Tokens</label>
                        <input type="number" id="max-tokens" value="{cfg.llm.max_tokens}" style="width:100%;">
                    </div>
                </div>
                <div id="models-status" style="font-size: 11px; color: #94a3b8; margin-top:-8px; margin-bottom:8px;"></div>
                <button id="save-llm-btn" style="background:#3b82f6; width:100%; margin-bottom:10px;">Save Model Config</button>
            </div>
            
            <!-- Tab Content: Policy -->
            <div id="tab-policy" class="modal-tab-content">
                <div style="font-size:13px; font-weight:bold; color:#cbd5e1; border-bottom:1px solid #1f2937; margin-bottom:12px; padding-bottom:4px;">Test Lifecycle Policy</div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Delete Tests After Task</label>
                        <select id="tp-delete" style="width:100%;">
                            <option value="true" {'selected' if cfg.test_policy.delete_tests_after_task else ''}>True</option>
                            <option value="false" {'selected' if not cfg.test_policy.delete_tests_after_task else ''}>False</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Max Fix Attempts</label>
                        <input type="number" id="tp-retries" value="{cfg.test_policy.max_test_fix_attempts}" style="width:100%;">
                    </div>
                </div>
                <button id="save-policy-btn" style="background:#3b82f6; width:100%; margin-bottom:10px;">Save Policy</button>
            </div>

            <!-- Tab Content: Custom Tools -->
            <div id="tab-custom-tools" class="modal-tab-content">
                <div style="font-size:13px; font-weight:bold; color:#cbd5e1; border-bottom:1px solid #1f2937; margin-bottom:12px; padding-bottom:4px;">Custom Tools</div>
                <div id="custom-tools-list" style="display:flex; flex-direction:column; gap:6px; margin-bottom:12px; max-height: 150px; overflow-y: auto; background:#111827; padding:4px;"></div>
                <div style="font-weight:bold; font-size:11px; color:#94a3b8; margin-bottom:8px;">Add Custom Python Tool:</div>
                <div class="form-group">
                    <label>Tool Name (lowercase, e.g. calculate_fibonacci)</label>
                    <input type="text" id="custom-tool-name" placeholder="e.g. timezone_helper">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <input type="text" id="custom-tool-desc" placeholder="e.g. Retrieves the current timezone">
                </div>
                <div class="form-group">
                    <label>Python Code (must define run(args: dict) -> dict)</label>
                    <textarea id="custom-tool-code" rows="6" style="width:100%; background:#1f2937; color:#cbd5e1; border:1px solid #374151; font-family:monospace; padding:8px; font-size:11px;" placeholder="def run(args: dict) -> dict:&#10;    return {{'ok': True, 'result': 'hello'}}"></textarea>
                </div>
                <button id="add-custom-tool-btn" style="background:#10b981; width:100%;">Create Dynamic Tool</button>
            </div>

            <!-- Tab Content: Skills -->
            <div id="tab-skills" class="modal-tab-content">
                <div style="font-size:13px; font-weight:bold; color:#cbd5e1; border-bottom:1px solid #1f2937; margin-bottom:12px; padding-bottom:4px;">Skills</div>
                <div id="skills-list" style="display:flex; flex-direction:column; gap:6px; margin-bottom:12px; max-height: 150px; overflow-y: auto; background:#111827; padding:4px;"></div>
                <div style="font-weight:bold; font-size:11px; color:#94a3b8; margin-bottom:8px;">Add New Agent Skill:</div>
                <div class="form-group">
                    <label>Skill Name (e.g. Translator)</label>
                    <input type="text" id="skill-name" placeholder="e.g. translate_expert">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <input type="text" id="skill-desc" placeholder="e.g. Translation helper skill">
                </div>
                <div class="form-group">
                    <label>Instructions (Markdown guidelines for the agent)</label>
                    <textarea id="skill-instructions" rows="6" style="width:100%; background:#1f2937; color:#cbd5e1; border:1px solid #374151; padding:8px; font-size:11px;" placeholder="# Instructions&#10;- Do this when translating..."></textarea>
                </div>
                <button id="add-skill-btn" style="background:#10b981; width:100%;">Create Skill</button>
            </div>
            
            <!-- Tab Content: MCP -->
            <div id="tab-mcp" class="modal-tab-content">
                <div style="font-size:13px; font-weight:bold; color:#cbd5e1; border-bottom:1px solid #1f2937; margin-bottom:12px; padding-bottom:4px;">MCP Integrations</div>
                <div id="mcp-servers-list" style="display:flex; flex-direction:column; gap:6px; margin-bottom:12px;"></div>
                <div style="font-weight:bold; font-size:11px; color:#94a3b8; margin-bottom:8px;">Register New MCP Server:</div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Server Name</label>
                        <input type="text" id="mcp-name" placeholder="e.g. gsearch">
                    </div>
                    <div class="form-group">
                        <label>Command</label>
                        <input type="text" id="mcp-cmd" placeholder="e.g. npx">
                    </div>
                </div>
                <div class="form-group">
                    <label>Arguments (comma separated)</label>
                    <input type="text" id="mcp-args" placeholder="e.g. -m, gsearch_mcp">
                </div>
                <button id="add-mcp-btn" style="background:#10b981; width:100%;">Add MCP Server</button>
            </div>
        </div>
    </div>

    <!-- Backdrop View Details Modal Popup -->
    <div class="modal-overlay" id="details-modal">
        <div class="modal-content" style="width: 750px; max-width: 95%;">
            <div class="modal-header">
                <div class="modal-title">🛠️ Run Session Detailed Report</div>
                <button class="modal-close" onclick="closeModal('details-modal')">✕</button>
            </div>
            <div id="details-modal-body"></div>
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
      let deleteConfirmRunId = null;
      
      function openModal(id) {{
          document.getElementById(id).style.display = 'flex';
      }}
      
      function closeModal(id) {{
          document.getElementById(id).style.display = 'none';
      }}

      window.switchTab = function(tabId) {{
          document.querySelectorAll('.modal-tab-content').forEach(el => el.classList.remove('active'));
          document.querySelectorAll('.modal-tab').forEach(el => el.classList.remove('active'));
          
          document.getElementById(tabId).classList.add('active');
          const btnMap = {{
              'tab-models': 'btn-tab-models',
              'tab-policy': 'btn-tab-policy',
              'tab-custom-tools': 'btn-tab-custom-tools',
              'tab-skills': 'btn-tab-skills',
              'tab-mcp': 'btn-tab-mcp'
          }};
          document.getElementById(btnMap[tabId]).classList.add('active');
          
          if (tabId === 'tab-custom-tools') fetchCustomTools();
          if (tabId === 'tab-skills') fetchSkills();
      }};

      async function fetchCustomTools() {{
          const list = document.getElementById('custom-tools-list');
          list.innerHTML = '<div style="color:#94a3b8; font-size:11px;">Loading...</div>';
          try {{
              const res = await fetch('/custom-tools');
              const data = await res.json();
              const tools = data.tools || [];
              if (tools.length === 0) {{
                  list.innerHTML = '<div style="color:#94a3b8; font-size:11px;">No custom tools created yet.</div>';
                  list.innerHTML = tools.map(t => `
                      <div class="tool-desc-item">
                          <span class="tool-desc-name">${{t}}</span>
                          <span style="color:#94a3b8; font-size:10px;">custom_tools/${{t}}.py</span>
                      </div>
                  `).join('');
              }}
          }} catch (e) {{
              list.innerHTML = '<div style="color:#ef4444; font-size:11px;">Error loading tools</div>';
          }}
      }}

      async function fetchSkills() {{
          const list = document.getElementById('skills-list');
          list.innerHTML = '<div style="color:#94a3b8; font-size:11px;">Loading...</div>';
          try {{
              const res = await fetch('/skills');
              const data = await res.json();
              const skills = data.skills || [];
              if (skills.length === 0) {{
                  list.innerHTML = '<div style="color:#94a3b8; font-size:11px;">No skills created yet.</div>';
              }} else {{
                  list.innerHTML = skills.map(s => `
                      <div class="tool-desc-item" style="flex-direction:column; align-items:flex-start; gap:4px;">
                          <div style="display:flex; justify-content:space-between; width:100%;">
                              <span style="font-weight:bold; color:#10b981;">${{s.name}}</span>
                              <span style="color:#94a3b8; font-size:10px;">.agents/skills/${{s.folder}}/</span>
                          </div>
                          <span style="color:#cbd5e1; font-size:11px;">${{s.description || 'No description'}}</span>
                      </div>
                  `).join('');
              }}
          }} catch (e) {{
              list.innerHTML = '<div style="color:#ef4444; font-size:11px;">Error loading skills</div>';
          }}
      }}

      async function createCustomTool() {{
          const name = document.getElementById('custom-tool-name').value.trim();
          const desc = document.getElementById('custom-tool-desc').value.trim();
          const code = document.getElementById('custom-tool-code').value;
          if (!name || !code) {{
              alert("Name and Python Code are required.");
              return;
          }}
          try {{
              const res = await fetch('/custom-tools', {{
                  method: 'POST',
                  headers: {{'Content-Type': 'application/json'}},
                  body: JSON.stringify({{name: name, description: desc, code: code}})
              }});
              if (res.ok) {{
                  document.getElementById('custom-tool-name').value = '';
                  document.getElementById('custom-tool-desc').value = '';
                  document.getElementById('custom-tool-code').value = '';
                  fetchCustomTools();
              }} else {{
                  const err = await res.text();
                  alert("Failed to create tool: " + err);
              }}
          }} catch (e) {{
              alert("Error creating tool: " + e.message);
          }}
      }}

      async function createSkill() {{
          const name = document.getElementById('skill-name').value.trim();
          const desc = document.getElementById('skill-desc').value.trim();
          const instructions = document.getElementById('skill-instructions').value;
          if (!name || !instructions) {{
              alert("Name and Instructions are required.");
              return;
          }}
          try {{
              const res = await fetch('/skills', {{
                  method: 'POST',
                  headers: {{'Content-Type': 'application/json'}},
                  body: JSON.stringify({{name: name, description: desc, instructions: instructions}})
              }});
              if (res.ok) {{
                  document.getElementById('skill-name').value = '';
                  document.getElementById('skill-desc').value = '';
                  document.getElementById('skill-instructions').value = '';
                  fetchSkills();
              }} else {{
                  const err = await res.text();
                  alert("Failed to create skill: " + err);
              }}
          }} catch (e) {{
              alert("Error creating skill: " + e.message);
          }}
      }}
      
      // Sidebar Toggle
      document.getElementById('toggle-sidebar-btn').addEventListener('click', () => {{
          document.getElementById('sidebar').classList.toggle('collapsed');
      }});
      
      document.getElementById('gear-btn').addEventListener('click', () => {{
          openModal('settings-modal');
      }});

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
          if (!model_planner || !model_executor || !model_verifier) return;
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
      }}

      async function fetchMCPServers() {{
         try {{
           const res = await fetch('/settings/mcp');
           const data = await res.json();
           const container = document.getElementById('mcp-servers-list');
           if (!data.servers || Object.keys(data.servers).length === 0) {{
               container.innerHTML = '<div style="color:#94a3b8; font-style:italic; font-size:12px;">No custom servers registered</div>';
               return;
           }}
           let html = '';
           Object.keys(data.servers).forEach(name => {{
              const srv = data.servers[name];
              html += `
                <div class="tool-desc-item">
                   <div>
                      <span class="tool-desc-name">${{name}}</span>
                      <div style="font-size:10px; color:#cbd5e1; margin-top:2px;">${{srv.command}} ${{srv.args.join(' ')}}</div>
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
         fetchModels();
      }};

      document.getElementById('workspace-btn').addEventListener('click', async () => {{
          try {{
              const res = await fetch('/workspace/select', {{ method: 'POST' }});
              const data = await res.json();
              if (data.ok) {{
                  alert("Workspace directory set to:\\n" + data.path);
              }} else if (data.error !== "Folder selection cancelled") {{
                  alert("Error selecting folder: " + data.error);
              }}
          }} catch (e) {{
              console.error(e);
          }}
      }});

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
         fetchMCPServers();
      }});

      async function refreshApprovals() {{
        const res = await fetch('/approvals?status=pending');
        const data = await res.json();
        const c = document.getElementById('approvals-container');
        const section = document.getElementById('sidebar-approvals-section');
        if (!data.approvals || data.approvals.length === 0) {{
            section.style.display = 'none';
            return;
        }}
        section.style.display = 'block';
        let html = '';
        data.approvals.forEach(a => {{
           let p = ''; try {{ p = JSON.stringify(JSON.parse(a.payload_json), null, 2); }} catch(e){{}}
           html += `
             <div class="approval-card" style="background: #7f1d1d; border: 1px solid #dc2626; border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 12px;">
               <div style="font-weight:bold; margin-bottom:2px;">${{a.action}}</div>
               <div style="margin-bottom:6px; color:#fca5a5;">${{a.reason}}</div>
               <button style="background:#10b981; padding:2px 8px; font-size:10px; margin-right:4px;" onclick="decideApproval('${{a.approval_id}}', 'approved')">Yes</button>
               <button style="background:#ef4444; padding:2px 8px; font-size:10px;" onclick="decideApproval('${{a.approval_id}}', 'rejected')">No</button>
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
             const isConfirming = deleteConfirmRunId === run.run_id;
             const deleteText = isConfirming ? 'Confirm?' : '✕';
             const btnStyle = isConfirming ? 'padding: 2px 6px; font-size: 10px; margin-left: 8px; border-radius: 4px; background:#ef4444; color:#fff;' : 'padding: 2px 6px; font-size: 10px; margin-left: 8px; border-radius: 4px;';
             
             html += `
                <div class="session-item ${{isActive}}" onclick="selectSession('${{run.run_id}}')">
                   <div style="display:flex; flex-direction:column; gap:4px; flex:1; overflow:hidden;">
                      <div class="session-goal">${{run.goal || 'Session'}}</div>
                      <span class="status-badge ${{stClass}}" style="font-size:9px; align-self:flex-start;">${{run.status}}</span>
                   </div>
                   <button class="btn-danger" style="${{btnStyle}}" onclick="deleteSession(event, '${{run.run_id}}')">${{deleteText}}</button>
                </div>
             `;
          }});
          container.innerHTML = html;
      }}

      window.deleteSession = async (event, runId) => {{
          event.stopPropagation();
          if (deleteConfirmRunId !== runId) {{
              deleteConfirmRunId = runId;
              renderSessionsSidebar(runsCache);
              return;
          }}
          try {{
              const res = await fetch(`/runs/${{runId}}`, {{ method: 'DELETE' }});
              if (res.ok) {{
                  if (activeRunId === runId) activeRunId = null;
                  deleteConfirmRunId = null;
                  refreshChat();
              }}
          }} catch(e) {{
              alert("Error: " + e.message);
              deleteConfirmRunId = null;
              refreshChat();
          }}
      }};

      function selectSession(runId) {{
          activeRunId = runId;
          lastChatHash = '';
          refreshChat().then(() => setTimeout(scrollToBottom, 200));
      }}

      function startNewSession() {{
          activeRunId = "new";
          renderedRunId = "new";
          lastChatHash = '';
          document.getElementById('active-session-title').textContent = "Start a New Chat Session";
          document.getElementById('chat-history').innerHTML = `
              <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #94a3b8;">
                  <h3 style="margin-bottom: 8px;">Start a New Session</h3>
                  <p style="font-size: 13px; margin: 0;">Type your goal below to launch the agent.</p>
              </div>
          `;
          document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
      }}

      async function fetchMessages(runId) {{
          try {{
              const res = await fetch(`/runs/${{runId}}/messages`);
              const data = await res.json();
              return data.messages || [];
          }} catch(e) {{ return []; }}
      }}

      window.copyOutputText = (text) => {{
          navigator.clipboard.writeText(text);
          alert("Copied to clipboard!");
      }};

      window.exportMarkdown = (text, goal) => {{
          const doc = `# Goal: ${{goal}}\\n\\n## Agent Response\\n${{text}}\\n`;
          const blob = new Blob([doc], {{ type: 'text/markdown' }});
          const el = document.createElement('a');
          el.href = URL.createObjectURL(blob);
          el.download = `agent_response_${{activeRunId}}.md`;
          el.click();
      }};

      async function triggerRerun(runId) {{
          await retryRun(runId);
      }}

      async function viewResponseDetails(runId) {{
          const run = runsCache.find(r => r.run_id === runId);
          if (!run) return;
          
          const sRes = await fetch(`/runs/${{runId}}/steps`);
          const sData = await sRes.json();
          const steps = sData.steps || [];
          
          let fileLinksHtml = '';
          const detectedFiles = new Set();
          steps.forEach(s => {{
              const msg = s.message || '';
              const matches = msg.match(/\\/Users\\/[^\\s'"]+/g) || msg.match(/[a-zA-Z0-9_\\-\\.]+\\.(html|py|md|txt|css|js)/g);
              if (matches) {{
                  matches.forEach(m => {{
                      const parts = m.split('/');
                      const name = parts[parts.length - 1];
                      if (name && name.includes('.')) detectedFiles.add(name);
                  }});
              }}
          }});
          if (run.goal.toLowerCase().includes('birds') || run.goal.toLowerCase().includes('html')) {{
              detectedFiles.add('birds_animals.html');
          }}
          if (detectedFiles.size > 0) {{
              fileLinksHtml += `<div style="margin-top:14px; font-weight:bold; font-size:12px; color:#cbd5e1;">Generated Files:</div>`;
              fileLinksHtml += `<div style="display:flex; flex-direction:column; gap:6px; margin-top:6px;">`;
              detectedFiles.forEach(file => {{
                  const url = `/workspace/${{file}}`;
                  fileLinksHtml += `
                      <div class="tool-desc-item">
                          <span style="font-family:monospace; color:#60a5fa;">${{file}}</span>
                          <a href="${{url}}" target="_blank" style="color:#10b981; font-weight:bold; text-decoration:none;">Open Workspace Preview ↗</a>
                      </div>
                  `;
              }});
              fileLinksHtml += `</div>`;
          }}
          
          let stepsTimeline = '';
          steps.forEach(s => {{
              const stepStClass = `status-${{s.status.toLowerCase()}}`;
              stepsTimeline += `
                  <div class="step-card">
                      <div class="step-header">
                          <span>Step ${{s.step_id}}: ${{s.title}}</span>
                          <span class="status-badge ${{stepStClass}}">${{s.status}}</span>
                      </div>
                      ${{s.message ? '<div class="step-body">' + s.message + '</div>' : ''}}
                  </div>
              `;
          }});
          
          const body = document.getElementById('details-modal-body');
          body.innerHTML = `
              <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
                  <span style="font-size:13px; color:#94a3b8; font-weight:bold;">Run ID: ${{runId}}</span>
                  <span class="status-badge status-${{run.status.toLowerCase()}}" style="font-size:11px; padding:4px 8px;">${{run.status}}</span>
              </div>
              <div style="font-size:14px; color:#f8fafc; font-weight:bold; margin-bottom:8px;">Goal:</div>
              <div style="background:#1f2937; padding:12px; border-radius:6px; font-size:13px; color:#cbd5e1; margin-bottom:16px;">${{run.goal}}</div>
              
              ${{fileLinksHtml}}
              
              <div style="margin-top:20px;">
                  <div style="font-weight:bold; font-size:13px; color:#cbd5e1; border-bottom:1px solid #1f2937; padding-bottom:4px; margin-bottom:8px;">Timeline Steps</div>
                  ${{stepsTimeline || '<div style="font-style:italic; font-size:12px; color:#94a3b8;">No execution logs logged.</div>'}}
              </div>
          `;
          
          openModal('details-modal');
      }}

      let lastChatHash = '';
      async function renderChatMessages(messages, run) {{
          const h = document.getElementById('chat-history');
          
          const res = await fetch(`/runs/${{run.run_id}}/steps`);
          const sData = await res.json();
          const steps = sData.steps || [];
          
          // Hash state to prevent flickering - we keep a global hash just to skip entirely if NOTHING changed
          const currentStateHash = JSON.stringify({{
              msgCount: messages.length,
              lastMsg: messages.length > 0 ? messages[messages.length-1].content : '',
              stepsHash: steps.map(s => s.status + s.message).join(','),
              runStatus: run.status,
              runError: run.error
          }});
          
          if (lastChatHash === currentStateHash) return;
          lastChatHash = currentStateHash;
          
          const wasScrolled = h.scrollHeight - h.scrollTop - h.clientHeight < 50;
          
          if (messages.length === 0) {{
              h.innerHTML = '';
              const userBubble = document.createElement('div');
              userBubble.className = 'message msg-user';
              userBubble.innerHTML = `<div class="bubble">${{run.goal || 'No goal specified'}}</div><div class="timestamp">${{run.created_at}}</div>`;
              h.appendChild(userBubble);
              
              const agentBubble = document.createElement('div');
              agentBubble.className = 'message msg-agent';
              agentBubble.innerHTML = `<div class="bubble"><div style="color: #94a3b8; font-style:italic;">Initializing task execution...</div></div>`;
              h.appendChild(agentBubble);
              return;
          }}
          
          // Remove any initialization or loading bubbles that aren't real messages
          Array.from(h.children).forEach(child => {{
              if (!child.id || !child.id.startsWith('msg-idx-')) {{
                  h.removeChild(child);
              }}
          }});
          
          messages.forEach((m, mIdx) => {{
              let msgDiv = document.getElementById(`msg-idx-${{mIdx}}`);
              if (!msgDiv) {{
                  msgDiv = document.createElement('div');
                  msgDiv.id = `msg-idx-${{mIdx}}`;
                  h.appendChild(msgDiv);
              }}
              msgDiv.className = `message ${{m.role === 'user' ? 'msg-user' : 'msg-agent'}}`;
              
              // Calculate a hash for this specific message to see if we need to redraw it
              const isLastMsg = mIdx === messages.length - 1;
              const msgHash = JSON.stringify({{
                  content: m.content, 
                  role: m.role,
                  steps: (m.role === 'agent' && isLastMsg) ? steps : null // Only the last agent message shows steps
              }});
              
              if (msgDiv.dataset.hash === msgHash) {{
                  return; // Skip re-rendering this specific message
              }}
              
              // Preserve details state if we are going to redraw this message
              let detailsOpen = false;
              const existingDetails = msgDiv.querySelector('details');
              if (existingDetails) detailsOpen = existingDetails.open;

              let contentHtml = '';
              if (m.role === 'agent') {{
                  let stepsListHtml = '';
                  if (isLastMsg) {{
                      steps.forEach(s => {{
                          const stepStClass = `status-${{s.status.toLowerCase()}}`;
                          stepsListHtml += `
                              <div class="step-card" style="margin-bottom:8px; background:#0b0f19;">
                                  <div class="step-header">
                                      <span>Step ${{s.step_id}}: ${{s.title}}</span>
                                      <span class="status-badge ${{stepStClass}}">${{s.status}}</span>
                                  </div>
                                  ${{s.message ? '<div class="step-body" style="font-size:11px;">' + s.message + '</div>' : ''}}
                              </div>
                          `;
                      }});
                  }}
                  
                  contentHtml = `
                      <div class="bubble" style="border-left: 4px solid #3b82f6;">
                          ${{isLastMsg ? `
                          <!-- Expandable Details Block -->
                          <details ${{detailsOpen ? 'open' : ''}} style="margin-bottom: 12px; font-size: 13px; color: #94a3b8;">
                              <summary style="cursor: pointer; user-select: none;">💡 Thought process & execution (${{steps.length}} steps)</summary>
                              <div style="margin-top:10px; max-height: 250px; overflow-y:auto; border-left: 2px solid #334155; padding-left: 10px;">
                                  ${{stepsListHtml || '<div style="font-style:italic; font-size:11px; color:#cbd5e1;">Planning...</div>'}}
                              </div>
                          </details>` : ''}}
                          
                          <div class="markdown-body" style="font-size: 14px; color: #cbd5e1; line-height:1.6;">${{marked.parse(m.content)}}</div>
                      </div>
                      
                      <!-- Action buttons under bubble -->
                      <div class="agent-actions">
                          <span class="action-link" onclick="viewResponseDetails('${{run.run_id}}')">🔍 View</span>
                          <span class="action-link" onclick="triggerRerun('${{run.run_id}}')">🔄 Rerun</span>
                          <span class="action-link" onclick="copyOutputText(\`${{m.content.replace(/`/g, '\\`').replace(/\$/g, '\\$')}}\`)">📋 Copy</span>
                          <span class="action-link" onclick="exportMarkdown(\`${{m.content.replace(/`/g, '\\`').replace(/\$/g, '\\$')}}\`, \`${{run.goal.replace(/`/g, '\\`').replace(/\$/g, '\\$')}}\`)">📥 Export</span>
                          <span class="action-link" onclick="alert('Edit message feature coming soon!')">✏️ Edit</span>
                          <span class="action-link" onclick="deleteMessage(${{m.id}})">🗑️ Delete</span>
                      </div>
                  `;
              }} else {{
                  contentHtml = `
                      <div class="bubble" style="white-space: pre-wrap; font-size: 14px;">${{m.content}}</div>
                      <div class="agent-actions" style="justify-content: flex-end; margin-right: 12px; margin-top: 4px;">
                          <span class="action-link" onclick="triggerRerun('${{run.run_id}}')">🔄 Rerun</span>
                          <span class="action-link" onclick="alert('Edit message feature coming soon!')">✏️ Edit</span>
                          <span class="action-link" onclick="deleteMessage(${{m.id}})">🗑️ Delete</span>
                      </div>
                  `;
              }}
              msgDiv.innerHTML = `${{contentHtml}}<div class="timestamp">${{m.created_at || ''}}</div>`;
              msgDiv.dataset.hash = msgHash;
          }});
          
          if (wasScrolled) scrollToBottom();

          // Handle the "running" spinner which isn't a real message
          let spinnerDiv = document.getElementById('msg-spinner-running');
          if (['running', 'queued'].includes(run.status.toLowerCase())) {{
              if (!spinnerDiv) {{
                  spinnerDiv = document.createElement('div');
                  spinnerDiv.id = 'msg-spinner-running';
                  spinnerDiv.className = 'message msg-agent';
                  spinnerDiv.innerHTML = `
                      <div class="bubble" style="border-color: #3b82f6;">
                          <div style="display:flex; align-items:center; gap:8px; font-size: 13px; color: #94a3b8;">
                              <div class="spinner"></div>
                              <span>Agent is running steps...</span>
                          </div>
                      </div>
                  `;
                  h.appendChild(spinnerDiv);
              }}
          }} else {{
              if (spinnerDiv) spinnerDiv.remove();
          }}

          let errorDiv = document.getElementById('msg-run-error');
          if (run.status.toLowerCase() === 'failed' && run.error) {{
              if (!errorDiv) {{
                  errorDiv = document.createElement('div');
                  errorDiv.id = 'msg-run-error';
                  errorDiv.className = 'message msg-agent';
                  errorDiv.innerHTML = `
                      <div class="bubble" style="border-left: 4px solid #ef4444; background: #450a0a;">
                          <div style="font-weight:bold; color: #fca5a5; margin-bottom: 4px;">⚠️ Agent Execution Error</div>
                          <div style="white-space: pre-wrap; font-size: 13px; color: #fecaca; line-height:1.5;">${{run.error}}</div>
                      </div>
                  `;
                  h.appendChild(errorDiv);
              }}
          }} else {{
              if (errorDiv) errorDiv.remove();
          }}
      }}
      
      window.deleteMessage = async (msgId) => {{
          if (!confirm("Are you sure you want to delete this message?")) return;
          try {{
              const res = await fetch(`/messages/${{msgId}}`, {{ method: 'DELETE' }});
              if (res.ok) {{
                  lastChatHash = ''; // Force full redraw
                  refreshChat();
              }} else {{
                  alert("Failed to delete message");
              }}
          }} catch (e) {{
              alert("Error deleting message: " + e.message);
          }}
      }};

      async function refreshChat() {{
        const res = await fetch('/runs?limit=20');
        const data = await res.json();
        const runs = data.runs || [];
        runsCache = runs;
        
        renderSessionsSidebar(runs);
        refreshApprovals();
        
        if (activeRunId === null && runs.length > 0) {{
            activeRunId = runs[0].run_id;
        }}
        
        if (activeRunId === "new") {{
            if (renderedRunId !== "new") startNewSession();
            document.getElementById('queue-box').style.display = 'none';
            
            const btn = document.getElementById('run-btn');
            btn.textContent = "Send";
            btn.className = "";
            btn.onclick = sendGoal;
            return;
        }}
        
        const activeRun = runs.find(r => r.run_id === activeRunId);
        if (activeRun) {{
            document.getElementById('active-session-title').textContent = activeRun.goal;
            if (renderedRunId !== activeRunId) {{
                document.getElementById('chat-history').innerHTML = '';
                renderedRunId = activeRunId;
            }}
            
            const messages = await fetchMessages(activeRun.run_id);
            renderChatMessages(messages, activeRun);
            
            // Queue task management above input
            const qBox = document.getElementById('queue-box');
            if (activeRun.status.toLowerCase() === 'queued') {{
                qBox.style.display = 'flex';
                document.getElementById('queue-goal-input').value = activeRun.goal;
            }} else {{
                qBox.style.display = 'none';
            }}
            
            // Dynamic Send/Stop button state
            const btn = document.getElementById('run-btn');
            if (['queued', 'running'].includes(activeRun.status.toLowerCase())) {{
                btn.textContent = "Stop";
                btn.className = "btn-danger";
                btn.onclick = stopActiveRun;
            }} else {{
                btn.textContent = "Send";
                btn.className = "";
                btn.onclick = sendGoal;
            }}
        }}
      }}

      window.stopActiveRun = async () => {{
          if (activeRunId && activeRunId !== "new") {{
              const res = await fetch(`/runs/${{activeRunId}}/stop`, {{ method: 'POST' }});
              if (res.ok) refreshChat();
          }}
      }};

      window.saveQueuedGoal = async () => {{
          const goal = document.getElementById('queue-goal-input').value.trim();
          if (!goal || !activeRunId) return;
          const res = await fetch(`/runs/${{activeRunId}}/goal`, {{
              method: 'PUT',
              headers: {{'Content-Type':'application/json'}},
              body: JSON.stringify({{goal: goal}})
          }});
          if (res.ok) refreshChat();
      }};

      window.cancelQueuedTask = async () => {{
          if (confirm("Cancel this queued task?")) {{
              const res = await fetch(`/runs/${{activeRunId}}`, {{ method: 'DELETE' }});
              if (res.ok) {{
                  activeRunId = null;
                  refreshChat();
              }}
          }}
      }};

      async function sendGoal() {{
        const input = document.getElementById('goal');
        const goal = input.value.trim();
        if (!goal) return;
        
        input.disabled = true;
        
        try {{
          await saveLLMSettings(); 
          
          const payload = {{
            goal: goal,
            mode: document.getElementById('mode').value,
            keep_tests: document.getElementById('keep-tests').value === 'true'
          }};
          if (activeRunId && activeRunId !== "new") {{
              payload.run_id = activeRunId;
          }}
          
          const res = await fetch('/run', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(payload)
          }});
          if (!res.ok) {{
              const errText = await res.text();
              console.error("Failed to enqueue task:", errText);
              alert("Failed to start task: " + errText);
          }} else {{
              input.value = '';
              
              if (!payload.run_id) {{
                  activeRunId = "new";
                  document.getElementById('chat-history').innerHTML = '';
                  
                  const selectNewRunInterval = setInterval(async () => {{
                      const rRes = await fetch('/runs?limit=5');
                      const rData = await rRes.json();
                      if (rData.runs && rData.runs.length > 0) {{
                          const found = rData.runs.find(r => r.goal === goal);
                          if (found) {{
                              activeRunId = found.run_id;
                              refreshChat().then(() => setTimeout(scrollToBottom, 200));
                              clearInterval(selectNewRunInterval);
                          }}
                      }}
                  }}, 500);
              }} else {{
                  refreshChat().then(() => setTimeout(scrollToBottom, 200));
              }}
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
          
          try {{
              await saveLLMSettings(); 
              const res = await fetch('/run', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                  goal: run.goal,
                  mode: document.getElementById('mode').value,
                  keep_tests: document.getElementById('keep-tests').value === 'true',
                  run_id: runId
                }})
              }});
              if (res.ok) refreshChat().then(() => setTimeout(scrollToBottom, 200));
          }} catch (err) {{
              console.error("Error retrying task:", err);
          }}
      }}

      document.getElementById('run-btn').addEventListener('click', sendGoal);
      document.getElementById('goal').addEventListener('keypress', e => {{ if (e.key === 'Enter') sendGoal(); }});
      document.getElementById('save-llm-btn').addEventListener('click', async () => {{
          await saveLLMSettings();
          closeModal('settings-modal');
      }});
      document.getElementById('save-policy-btn').addEventListener('click', async () => {{
          await savePolicy();
          closeModal('settings-modal');
      }});
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

      // Bind events to queue save and cancel
      document.getElementById('queue-save-btn').addEventListener('click', saveQueuedGoal);
      document.getElementById('queue-cancel-btn').addEventListener('click', cancelQueuedTask);

      // Dynamic tools and skills buttons
      document.getElementById('add-custom-tool-btn').addEventListener('click', createCustomTool);
      document.getElementById('add-skill-btn').addEventListener('click', createSkill);

      // Click outside to clear delete confirmations
      document.addEventListener('click', (e) => {{
          if (deleteConfirmRunId !== null && !e.target.closest('.session-item')) {{
              deleteConfirmRunId = null;
              renderSessionsSidebar(runsCache);
          }}
      }});

      // Interactive Suggestions Scanner
      let suggestionType = null;
      let suggestedName = '';

      document.getElementById('goal').addEventListener('input', (e) => {{
          const val = e.target.value.toLowerCase();
          const banner = document.getElementById('suggestion-banner');
          const textEl = document.getElementById('suggestion-text');
          
          if (val.includes('tool') && (val.includes('create') || val.includes('new') || val.includes('add') || val.includes('make'))) {{
              suggestionType = 'tool';
              const match = val.match(/(?:tool\s+named\s+|tool\s+called\s+|tool\s+)(\w+)/);
              suggestedName = match ? match[1] : 'my_custom_tool';
              textEl.textContent = `💡 Create dynamic custom tool "${{suggestedName}}" suggested!`;
              banner.style.display = 'flex';
          }} else if (val.includes('skill') && (val.includes('create') || val.includes('new') || val.includes('add') || val.includes('teach'))) {{
              suggestionType = 'skill';
              const match = val.match(/(?:skill\s+named\s+|skill\s+called\s+|skill\s+)(\w+)/);
              suggestedName = match ? match[1] : 'my_custom_skill';
              textEl.textContent = `💡 Create dynamic agent skill "${{suggestedName}}" suggested!`;
              banner.style.display = 'flex';
          }} else {{
              banner.style.display = 'none';
          }}
      }});

      window.acceptSuggestion = () => {{
          openModal('settings-modal');
          const banner = document.getElementById('suggestion-banner');
          banner.style.display = 'none';
          
          if (suggestionType === 'tool') {{
              switchTab('tab-custom-tools');
              document.getElementById('custom-tool-name').value = suggestedName;
              document.getElementById('custom-tool-desc').value = `Dynamic tool to handle ${{suggestedName}}`;
              document.getElementById('custom-tool-code').value = `def run(args: dict) -> dict:\n    # Dynamic execution logic for ${{suggestedName}}\n    return {{"ok": True, "result": "completed"}}\n`;
          }} else if (suggestionType === 'skill') {{
              switchTab('tab-skills');
              document.getElementById('skill-name').value = suggestedName;
              document.getElementById('skill-desc').value = `Specialized skill for ${{suggestedName}}`;
              document.getElementById('skill-instructions').value = `# Specialized Skill: ${{suggestedName}}\n\nAdd markdown instructions for the agent to specialize in ${{suggestedName}} automatically.\n`;
          }}
      }};

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
