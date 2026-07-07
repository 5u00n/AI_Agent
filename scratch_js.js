      const PRE_LOADED_MODELS = {
          "planner": "qwen/qwen3-coder-30b",
          "executor": "qwen/qwen3-coder-30b",
          "verifier": "qwen/qwen3-coder-30b",
      };
      
      let activeRunId = null;
      let renderedRunId = null;
      let runsCache = [];
      
      async function fetchModels() {
        const provider = document.getElementById('provider').value;
        const status = document.getElementById('models-status');
        status.textContent = "Fetching...";
        try {
          const res = await fetch(`/models?provider=${provider}`);
          const data = await res.json();
          const models = data.models || [];
          if (models.length === 0) {
              status.textContent = "No active models found on provider.";
          } else {
              status.textContent = `Found ${models.length} models.`;
          }
          
          const isStub = (m) => ["planner-model", "executor-model", "verifier-model"].includes(m);
          
          ['model-planner', 'model-executor', 'model-verifier'].forEach(id => {
             const sel = document.getElementById(id);
             sel.innerHTML = '';
             const key = id.replace('model-', '');
             const curr = PRE_LOADED_MODELS[key];
             const needsAutoFix = isStub(curr) && models.length > 0;
             
             models.forEach(m => {
               const opt = document.createElement('option');
               opt.value = m;
               opt.textContent = m;
               if (m === curr || (needsAutoFix && m === models[0])) {
                   opt.selected = true;
                   if (needsAutoFix) PRE_LOADED_MODELS[key] = m;
               }
               sel.appendChild(opt);
             });
             if (!models.includes(curr) && curr && !isStub(curr)) {
                 const opt = document.createElement('option');
                 opt.value = curr;
                 opt.textContent = curr + " (Current)";
                 opt.selected = true;
                 sel.appendChild(opt);
             }
          });
        } catch (err) { status.textContent = "Error fetching models."; }
      }

      async function saveLLMSettings() {
        const payload = {
          provider: document.getElementById('provider').value,
          model_planner: document.getElementById('model-planner').value,
          model_executor: document.getElementById('model-executor').value,
          model_verifier: document.getElementById('model-verifier').value,
          max_tokens: parseInt(document.getElementById('max-tokens').value || "4096", 10),
        };
        await fetch('/settings/llm', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        PRE_LOADED_MODELS.planner = payload.model_planner;
        PRE_LOADED_MODELS.executor = payload.model_executor;
        PRE_LOADED_MODELS.verifier = payload.model_verifier;
        document.getElementById('save-llm-result').textContent = "Saved!";
        setTimeout(() => document.getElementById('save-llm-result').textContent = "", 2000);
      }

      async function savePolicy() {
        const payload = {
          delete_tests_after_task: document.getElementById('tp-delete').value === 'true',
          max_test_fix_attempts: Number(document.getElementById('tp-retries').value || 0),
        };
        await fetch('/settings/test-policy', { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        document.getElementById('save-policy-result').textContent = "Saved!";
        setTimeout(() => document.getElementById('save-policy-result').textContent = "", 2000);
      }

      async function fetchMCPServers() {
         try {
           const res = await fetch('/settings/mcp');
           const data = await res.json();
           const container = document.getElementById('mcp-servers-list');
           if (!data.servers || Object.keys(data.servers).length === 0) {
               container.innerHTML = '<div style="color:#94a3b8; font-style:italic;">No custom servers</div>';
               return;
           }
           let html = '';
           Object.keys(data.servers).forEach(name => {
              const srv = data.servers[name];
              html += `
                <div class="tool-desc-item">
                   <div>
                      <span class="tool-desc-name">${name}</span>
                      <div style="font-size:10px; color:#94a3b8;">${srv.command} ${srv.args.join(' ')}</div>
                   </div>
                   <button class="btn-danger" style="padding: 2px 6px; font-size: 10px;" onclick="removeMCPServer('${name}')">✕</button>
                </div>
              `;
           });
           container.innerHTML = html;
         } catch (err) {}
      }

      window.removeMCPServer = async (name) => {
         await fetch(`/settings/mcp/${name}`, { method: 'DELETE' });
         fetchMCPServers();
         fetchModels(); // Refresh available tools list
      };

      document.getElementById('add-mcp-btn').addEventListener('click', async () => {
         const name = document.getElementById('mcp-name').value.trim();
         const command = document.getElementById('mcp-cmd').value.trim();
         const argsStr = document.getElementById('mcp-args').value.trim();
         if (!name || !command) return;
         
         const payload = {
            name: name,
            command: command,
            args: argsStr ? argsStr.split(',').map(s => s.trim()) : []
         };
         
         await fetch('/settings/mcp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
         });
         
         document.getElementById('mcp-name').value = '';
         document.getElementById('mcp-cmd').value = '';
         document.getElementById('mcp-args').value = '';
         
         document.getElementById('mcp-add-result').textContent = "Added!";
         setTimeout(() => document.getElementById('mcp-add-result').textContent = "", 2000);
         
         fetchMCPServers();
      });

      async function refreshApprovals() {
        const res = await fetch('/approvals?status=pending');
        const data = await res.json();
        const c = document.getElementById('approvals-container');
        if (!data.approvals || data.approvals.length === 0) { c.innerHTML = '<div style="font-size:12px; color:#cbd5e1;">None</div>'; return; }
        
        let html = '';
        data.approvals.forEach(a => {
           let p = ''; try { p = JSON.stringify(JSON.parse(a.payload_json), null, 2); } catch(e){}
           html += `
             <div class="approval-card">
               <div style="font-weight:bold; margin-bottom:4px;">${a.action}</div>
               <div style="margin-bottom:8px;">${a.reason}</div>
               <pre>${p}</pre>
               <button class="btn-approve" onclick="decideApproval('${a.approval_id}', 'approved')">Approve</button>
               <button class="btn-reject" onclick="decideApproval('${a.approval_id}', 'rejected')">Reject</button>
             </div>
           `;
        });
        c.innerHTML = html;
      }

      window.decideApproval = async (id, dec) => {
        await fetch(`/approvals/${id}/decision`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({decision: dec, reviewer:'local-user'}) });
        refreshApprovals();
      };

      function scrollToBottom() {
          const h = document.getElementById('chat-history');
          h.scrollTop = h.scrollHeight;
      }

      function renderSessionsSidebar(runs) {
          const container = document.getElementById('sessions-container');
          let html = '';
          runs.forEach(run => {
             const isActive = run.run_id === activeRunId ? 'active' : '';
             const stClass = `status-${run.status.toLowerCase()}`;
             html += `
                <div class="session-item ${isActive}" onclick="selectSession('${run.run_id}')">
                   <div class="session-goal">${run.goal || 'Session'}</div>
                   <span class="status-badge ${stClass}" style="font-size:9px;">${run.status}</span>
                </div>
             `;
          });
          container.innerHTML = html;
      }

      function selectSession(runId) {
          activeRunId = runId;
          refreshChat();
      }

      function startNewSession() {
          activeRunId = "new";
          renderedRunId = "new";
          document.getElementById('chat-history').innerHTML = `
              <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #94a3b8;">
                  <h3 style="margin-bottom: 8px;">Start a New Session</h3>
                  <p style="font-size: 13px; margin: 0;">Type your goal below to launch the agent.</p>
              </div>
          `;
          document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
      }

      function renderRunToChat(run) {
          const h = document.getElementById('chat-history');
          
          let userMsg = document.getElementById(`usr-${run.run_id}`);
          if (!userMsg) {
              userMsg = document.createElement('div');
              userMsg.className = 'message msg-user';
              userMsg.id = `usr-${run.run_id}`;
              userMsg.innerHTML = `<div class="bubble">${run.goal || 'No goal specified'}</div><div class="timestamp">${run.created_at}</div>`;
              h.appendChild(userMsg);
          }
          
          let agentMsg = document.getElementById(`agt-${run.run_id}`);
          if (!agentMsg) {
              agentMsg = document.createElement('div');
              agentMsg.className = 'message msg-agent';
              agentMsg.id = `agt-${run.run_id}`;
              
              const stClass = `status-${run.status.toLowerCase()}`;
              let summaryText = run.status === 'done' ? 'Task Completed' : (run.status === 'blocked' ? 'Task Blocked' : 'Agent is working...');
              
              agentMsg.innerHTML = `
                <div class="bubble">
                   <div id="response-text-${run.run_id}" style="white-space: pre-wrap; font-size: 14px; color: #f8fafc; margin-bottom: 8px;"></div>
                   <details class="agent-work" id="details-${run.run_id}" ${['running', 'queued'].includes(run.status.toLowerCase()) ? 'open' : ''}>
                      <summary>
                         <span id="summary-text-${run.run_id}">${summaryText}</span> <span class="status-badge ${stClass}" id="badge-${run.run_id}">${run.status}</span>
                      </summary>
                      <div id="steps-${run.run_id}" class="steps-container">Loading steps...</div>
                   </details>
                </div>
              `;
              h.appendChild(agentMsg);
          } else {
              const stClass = `status-${run.status.toLowerCase()}`;
              const badge = document.getElementById(`badge-${run.run_id}`);
              if (badge) {
                  badge.className = `status-badge ${stClass}`;
                  badge.textContent = run.status;
              }
              const summary = document.getElementById(`summary-text-${run.run_id}`);
              if (summary) {
                  summary.textContent = run.status === 'done' ? 'Task Completed' : (run.status === 'blocked' ? 'Task Blocked' : 'Agent is working...');
              }
          }
      }

      async function fetchStepsForRun(runId) {
          try {
            const res = await fetch(`/runs/${runId}/steps`);
            const data = await res.json();
            const el = document.getElementById(`steps-${runId}`);
            if (!el) return;
            
            if (!data.steps || data.steps.length === 0) {
                el.innerHTML = '<div style="color: #94a3b8;">No steps logged yet...</div>';
                return;
            }
            
            let html = '';
            let mainResponse = '';
            data.steps.forEach(s => {
               let msg = s.message || '';
               let testMeta = '';
               
               const idx = msg.indexOf('\n\n(');
               if (idx !== -1) {
                   testMeta = msg.substring(idx + 4, msg.length - 1);
                   msg = msg.substring(0, idx);
               } else if (msg.startsWith('Step completed') || msg.startsWith('Step blocked')) {
                   testMeta = msg;
                   msg = '';
               }
               
               if (msg && !mainResponse) {
                   mainResponse = msg;
               }
               
               const stClass = `status-${s.status.toLowerCase()}`;
               
               html += `
                 <div class="step-card">
                    <div class="step-header">
                       <span>Step ${s.step_id}: ${s.title}</span>
                       <span class="status-badge ${stClass}">${s.status}</span>
                    </div>
                    ${msg ? '<div class="step-body">' + msg + '</div>' : ''}
                    ${testMeta ? '<div class="step-footer"><span>Verifier status:</span><span style="color:#10b981; font-weight:600;">✓ ' + testMeta + '</span></div>' : ''}
                 </div>
               `;
            });
            
            if (mainResponse) {
                const textEl = document.getElementById(`response-text-${runId}`);
                if (textEl && textEl.textContent !== mainResponse) {
                    textEl.textContent = mainResponse;
                }
            }
            
            if (el.innerHTML.length !== html.length) {
                el.innerHTML = html;
            }
          } catch(e) {}
      }

      async function refreshChat() {
        const res = await fetch('/runs?limit=20');
        const data = await res.json();
        const runs = data.runs || [];
        runsCache = runs;
        
        renderSessionsSidebar(runs);
        
        // Initial page load auto-selection
        if (activeRunId === null && runs.length > 0) {
            activeRunId = runs[0].run_id;
        }
        
        if (activeRunId === "new") {
            // New Session Sentinel Mode
            if (renderedRunId !== "new") {
                startNewSession();
            }
            return;
        }
        
        const activeRun = runs.find(r => r.run_id === activeRunId);
        if (activeRun) {
            // Clean view shift if run changed
            if (renderedRunId !== activeRunId) {
                document.getElementById('chat-history').innerHTML = '';
                renderedRunId = activeRunId;
            }
            
            renderRunToChat(activeRun);
            const details = document.getElementById(`details-${activeRun.run_id}`);
            if (details && details.open) {
                fetchStepsForRun(activeRun.run_id);
            }
        }
      }

      async function sendGoal() {
        const input = document.getElementById('goal');
        const goal = input.value.trim();
        if (!goal) return;
        
        input.value = '';
        input.disabled = true;
        
        activeRunId = "new";
        document.getElementById('chat-history').innerHTML = '';
        
        await saveLLMSettings(); 
        
        await fetch('/run', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            goal: goal,
            mode: document.getElementById('mode').value,
            keep_tests: document.getElementById('keep-tests').value === 'true'
          })
        });
        
        input.disabled = false;
        input.focus();
        
        const selectNewRunInterval = setInterval(async () => {
            const rRes = await fetch('/runs?limit=5');
            const rData = await rRes.json();
            if (rData.runs && rData.runs.length > 0) {
                const found = rData.runs.find(r => r.goal === goal);
                if (found) {
                    activeRunId = found.run_id;
                    refreshChat();
                    clearInterval(selectNewRunInterval);
                }
            }
        }, 500);
      }

      document.getElementById('run-btn').addEventListener('click', sendGoal);
      document.getElementById('goal').addEventListener('keypress', e => { if (e.key === 'Enter') sendGoal(); });
      document.getElementById('save-llm-btn').addEventListener('click', saveLLMSettings);
      document.getElementById('save-policy-btn').addEventListener('click', savePolicy);
      document.getElementById('new-session-btn').addEventListener('click', () => selectSession('new'));
      
      document.getElementById('auto-detect-btn').addEventListener('click', async () => {
         const btn = document.getElementById('auto-detect-btn');
         const status = document.getElementById('models-status');
         btn.disabled = true;
         status.textContent = "Probing ports...";
         try {
            const res = await fetch('/models/auto-detect', { method: 'POST' });
            const data = await res.json();
            if (data.ok) {
                document.getElementById('provider').value = data.provider;
                status.textContent = `Allocated: ${data.allocated.planner}`;
                await fetchModels();
            } else {
                status.textContent = data.error || "Auto-detect failed.";
            }
         } catch(e) {
            status.textContent = "Error during auto-detect.";
         }
         btn.disabled = false;
      });

      document.getElementById('provider').addEventListener('change', fetchModels);

      fetchModels();
      fetchMCPServers();
      refreshChat().then(() => setTimeout(scrollToBottom, 500));
      refreshApprovals();
      
      setInterval(refreshChat, 2000);
      setInterval(refreshApprovals, 2000);
