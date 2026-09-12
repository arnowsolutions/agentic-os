async function renderSmartRouter() {
  const content = document.getElementById('pageContent');
  
  // Load router config from backend
  let config = { routing_rules: [], agent_capabilities: {} };
  try {
    config = await api.getRouterConfig();
  } catch (err) {
    console.warn('Failed to load router config:', err);
  }
  
  // Build rules table from config
  const rulesHtml = config.routing_rules ? config.routing_rules.map(rule => {
    const agentIcons = { opencode: '🔧', hermes: '⚡', gemini: '🧠' };
    return `
      <tr>
        <td><strong>${agentIcons[rule.target] || '🤖'} ${rule.target}</strong></td>
        <td class="text-muted text-sm">${rule.description || 'Pattern match'}</td>
        <td class="text-muted text-sm">${rule.pattern}</td>
        <td><span class="badge badge-info">P${rule.priority}</span></td>
      </tr>
    `;
  }).join('') : '';
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Smart Router</div>
        <div class="page-subtitle">Intelligent task routing — auto-suggest or manually pick an agent</div>
      </div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <div class="card-title">Route a Task</div>
      </div>
      <div class="form-group">
        <label class="form-label">Describe your task</label>
        <textarea class="form-textarea" id="routerTaskInput" placeholder="e.g., Deploy the CloudMart infrastructure to GCP..." rows="3"></textarea>
      </div>
      <div class="flex gap-3" style="align-items:flex-end">
        <div class="form-group" style="flex:1">
          <label class="form-label">Route to Agent</label>
          <select class="form-select" id="routerAgentSelect">
            <option value="auto">🤖 Auto (AI suggests)</option>
            <option value="opencode">🔧 opencode (Code/DevOps)</option>
            <option value="hermes">⚡ Hermes (Memory/Scheduling)</option>
            <option value="gemini">🧠 Gemini CLI (Research/Analysis)</option>
          </select>
        </div>
        <button class="btn btn-primary" onclick="suggestRouter()" style="margin-bottom:16px">🤖 Suggest Agent</button>
        <button class="btn btn-gradient" onclick="routeTask()" style="margin-bottom:16px">🚀 Route Task</button>
      </div>
    </div>
    <div id="routerResult"></div>
    <div class="section-title" style="margin-top:20px">Routing Rules (from data/agent-routes.json)</div>
    <div class="card">
      <table>
        <tr><th>Agent</th><th>Description</th><th>Pattern</th><th>Priority</th></tr>
        ${rulesHtml || `
          <tr><td><strong>🔧 opencode</strong></td><td>Code, DevOps, infra, git, file operations</td><td class="text-muted text-sm">code|devops|deploy|git|terraform|docker</td><td><span class="badge badge-info">P10</span></td></tr>
          <tr><td><strong>⚡ Hermes</strong></td><td>Memory, scheduling, messaging, skills</td><td class="text-muted text-sm">memory|schedule|cron|reminder|brain|plugin</td><td><span class="badge badge-info">P10</span></td></tr>
          <tr><td><strong>🧠 Gemini</strong></td><td>Research, analysis, study, document, review</td><td class="text-muted text-sm">research|analyze|search|explain|study|learn</td><td><span class="badge badge-info">P10</span></td></tr>
        `}
      </table>
    </div>
  `;
}

async function suggestRouter() {
  const task = document.getElementById('routerTaskInput').value.trim();
  if (!task) { showToast('Describe your task first', 'warning'); return; }
  const btn = document.querySelector('button[onclick="suggestRouter()"]');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Thinking...'; }
  try {
    const data = await api.suggestRouter(task);
    const result = document.getElementById('routerResult');
    const agentIcons = { opencode: '🔧', hermes: '⚡', gemini: '🧠' };
    const confidenceColors = { high: 'var(--green)', medium: 'var(--yellow)', low: 'var(--text-muted)', fallback: 'var(--text-muted)' };
    
    // Build matched rules section
    const rulesHtml = data.matched_rules && data.matched_rules.length > 0 
      ? `
        <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
          <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px">Matched Rules:</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            ${data.matched_rules.map(r => `
              <span class="badge badge-info" title="Pattern: ${r.pattern}">${r.target} (P${r.priority})</span>
            `).join('')}
          </div>
        </div>
      ` 
      : '';
    
    // Build capabilities section
    const capsHtml = data.capabilities && data.capabilities.length > 0
      ? `
        <div style="margin-top:8px">
          <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px">Capabilities:</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            ${data.capabilities.map(c => `<span class="badge badge-success">${c}</span>`).join('')}
          </div>
        </div>
      `
      : '';
    
    result.innerHTML = `
      <div class="card" style="border-color:${confidenceColors[data.confidence] || 'var(--border)'};margin-bottom:12px">
        <div class="router-suggestion" style="border:none;padding:0;background:none">
          <div>
            <div class="router-suggestion-agent" style="font-size:18px">
              ${agentIcons[data.suggested_agent] || '🤖'} ${data.suggested_agent}
            </div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">
              Confidence: <span style="color:${confidenceColors[data.confidence] || 'var(--text-muted)'}">${data.confidence}</span>
              ${data.confidence === 'high' ? '✅' : data.confidence === 'medium' ? '⚠️' : '❓'}
            </div>
          </div>
          <div style="flex:1;text-align:right">
            <span class="badge badge-accent">Best Match</span>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">
          ${Object.entries(data.scores || {}).map(([agent, score]) => `
            <span class="badge ${score > 0 ? 'badge-success' : 'badge-info'}">
              ${agentIcons[agent] || '🤖'} ${agent}: ${score}
            </span>
          `).join('')}
        </div>
        ${rulesHtml}
        ${capsHtml}
      </div>
    `;
    document.getElementById('routerAgentSelect').value = data.suggested_agent || 'auto';
  } catch (err) {
    showToast('Suggestion failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🤖 Suggest Agent'; }
  }
}

async function routeTask() {
  const task = document.getElementById('routerTaskInput').value.trim();
  if (!task) { showToast('Describe your task first', 'warning'); return; }
  let agent = document.getElementById('routerAgentSelect').value;
  if (agent === 'auto') {
    showToast('Click "Suggest Agent" first or pick an agent manually', 'warning');
    return;
  }
  const btn = document.querySelector('button[onclick="routeTask()"]');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Routing...'; }
  try {
    const data = await api.routeTask(task, agent);
    const result = document.getElementById('routerResult');
    
    // Build dispatch status display
    const dispatchStatus = data.dispatch_status === 'queued' 
      ? '<span style="color:var(--green)">✅ Queued</span>'
      : '<span style="color:var(--red)">❌ Failed</span>';
    
    const traceHtml = `
      <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);font-size:11px;color:var(--text-muted)">
        <div><strong>Route ID:</strong> <code>${data.route_id || 'N/A'}</code></div>
        <div><strong>Event ID:</strong> <code>${data.event_id || 'N/A'}</code></div>
        <div><strong>Dispatch Status:</strong> ${dispatchStatus}</div>
        ${data.dispatch_error ? `<div style="color:var(--red);margin-top:4px">Error: ${data.dispatch_error}</div>` : ''}
      </div>
    `;
    
    result.innerHTML += `
      <div class="card" style="margin-top:8px;border-color:${data.dispatch_status === 'queued' ? 'var(--green)' : 'var(--red)'}">
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:24px">${data.dispatch_status === 'queued' ? '✅' : '❌'}</span>
          <div style="flex:1">
            <div style="font-weight:600">Task ${data.dispatch_status === 'queued' ? 'Routed' : 'Failed'}</div>
            <div class="text-muted text-sm">${data.message}</div>
            ${traceHtml}
          </div>
        </div>
      </div>
    `;
    
    showToast(`${data.dispatch_status === 'queued' ? '✅' : '❌'} Task ${data.dispatch_status} to ${agent}`, data.dispatch_status === 'queued' ? 'success' : 'error');
  } catch (err) {
    showToast('Routing failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🚀 Route Task'; }
  }
}
