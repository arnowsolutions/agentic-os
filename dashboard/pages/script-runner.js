async function renderScriptRunner() {
  const content = document.getElementById('pageContent');
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">⚙️ Script Runner</div>
        <div class="page-subtitle">Run any workspace script from the dashboard — live output</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderScriptRunner()">🔄 Reset</button>
      </div>
    </div>
    <div class="sr-layout">
      <div class="sr-panel sr-controls-panel">
        <h3 style="font-size:13px;font-weight:600;margin-bottom:10px">📜 Scripts</h3>
        <div id="srQuickList" class="sr-quick-list"></div>
        <hr style="border-color:var(--border);margin:12px 0">
        <h3 style="font-size:13px;font-weight:600;margin-bottom:8px">🔧 Custom Command</h3>
        <div class="sr-custom">
          <input type="text" id="srCustomCmd" class="sr-input" placeholder="python3 /workspace/agentic-os/script.py --flag" 
                 onkeydown="if(event.key==='Enter')runCustomScript()">
          <button class="btn btn-primary" onclick="runCustomScript()" id="srRunBtn">▶️ Run</button>
        </div>
      </div>
      <div class="sr-panel sr-output-panel">
        <div class="sr-output-header">
          <span id="srOutputTitle">Output</span>
          <div>
            <button class="btn btn-ghost btn-xs" onclick="clearSrOutput()">🗑️ Clear</button>
            <button class="btn btn-ghost btn-xs" onclick="copySrOutput()">📋 Copy</button>
          </div>
        </div>
        <pre id="srOutput" class="sr-output"><span style="color:var(--text-muted)">Run a script to see output here</span></pre>
      </div>
    </div>
    <style>
      .sr-layout { display: grid; grid-template-columns: 360px 1fr; gap: 12px; margin-top: 16px; min-height: 400px; }
      @media (max-width: 800px) { .sr-layout { grid-template-columns: 1fr; } }
      .sr-panel { background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border); padding: 16px; }
      .sr-output-panel { display: flex; flex-direction: column; }
      .sr-output-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 12px; font-weight: 600; }
      .sr-output { flex: 1; background: #0d1117; border-radius: 4px; padding: 12px; font-size: 12px; font-family: 'JetBrains Mono', monospace; line-height: 1.5; overflow-y: auto; white-space: pre-wrap; color: #c9d1d9; min-height: 300px; margin: 0; }
      .sr-output .sr-running { color: var(--yellow); }
      .sr-output .sr-done { color: #00b894; }
      .sr-output .sr-error { color: #d63031; }
      .sr-quick-list { display: flex; flex-direction: column; gap: 4px; }
      .sr-script-btn { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; background: transparent; color: var(--text); font-size: 12px; cursor: pointer; text-align: left; transition: all 0.15s; }
      .sr-script-btn:hover { background: rgba(255,255,255,0.05); border-color: var(--primary); }
      .sr-script-btn .sr-icon { font-size: 16px; }
      .sr-script-btn .sr-name { font-weight: 500; }
      .sr-script-btn .sr-path { font-size: 10px; color: var(--text-muted); }
      .sr-custom { display: flex; gap: 6px; }
      .sr-input { flex: 1; padding: 8px 12px; border: 1px solid var(--border); border-radius: 4px; background: #1a1a2e; color: #eee; font-size: 12px; font-family: monospace; }
      .btn-xs { padding: 4px 8px; font-size: 11px; }
    </style>
  `;

  // Quick script list
  const SCRIPTS = [
    { name: 'Generate Call Schedule', icon: '📋', path: 'python3 /workspace/agentic-os/deliver_messages.py --type schedule' },
    { name: 'Send GME Report', icon: '💰', path: 'python3 /workspace/agentic-os/deliver_messages.py --type gme' },
    { name: 'Deploy Vapi Assistant', icon: '🌙', path: 'python3 /workspace/agentic-os/deploy_vapi_v5.py' },
    { name: 'Send Test Email', icon: '📧', path: 'python3 /workspace/send-report.py --test' },
    { name: 'Sync Schedule to Calendar', icon: '🗓️', path: 'python3 /workspace/agentic-os/daily_sync.py' },
    { name: 'Grand Rounds Report', icon: '📊', path: 'python3 /workspace/agentic-os/deliver_messages.py --type grand-rounds' },
    { name: 'Check Vapi Status', icon: '🔍', path: 'python3 /workspace/agentic-os/check_vapi.py' },
    { name: 'Check Call Status', icon: '📞', path: 'python3 /workspace/agentic-os/check_calls.py' },
  ];

  const list = document.getElementById('srQuickList');
  list.innerHTML = SCRIPTS.map(s => `
    <button class="sr-script-btn" onclick="runScriptWithOutput('${escapeHtml(s.path)}', '${s.name}')">
      <span class="sr-icon">${s.icon}</span>
      <div><div class="sr-name">${s.name}</div><div class="sr-path">${escapeHtml(s.path)}</div></div>
    </button>
  `).join('');
}

async function runScriptWithOutput(cmd, name) {
  const output = document.getElementById('srOutput');
  const title = document.getElementById('srOutputTitle');
  title.textContent = `▶️ Running: ${name || cmd}`;
  output.innerHTML = '<span class="sr-running">⏳ Running...</span>\n';

  try {
    const res = await fetch('/api/script/run', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ cmd })
    });
    const data = await res.json();
    
    if (data.exit_code === 0) {
      output.innerHTML = `<span class="sr-done">✅ Completed (exit 0)</span>\n${escapeHtml(data.stdout || '(no output)')}`;
    } else {
      output.innerHTML = `<span class="sr-error">❌ Failed (exit ${data.exit_code})</span>\n${escapeHtml(data.stderr || data.stdout || '(no output)')}`;
    }
    title.textContent = `✓ ${name || 'Script'} — exit ${data.exit_code}`;
  } catch (err) {
    output.innerHTML = `<span class="sr-error">❌ Error: ${escapeHtml(err.message)}</span>`;
    title.textContent = `✗ ${name || 'Script'} — error`;
  }
}

async function runCustomScript() {
  const cmd = document.getElementById('srCustomCmd').value.trim();
  if (!cmd) return;
  await runScriptWithOutput(cmd, 'Custom Command');
}

function clearSrOutput() {
  document.getElementById('srOutput').innerHTML = '<span style="color:var(--text-muted)">Cleared</span>';
  document.getElementById('srOutputTitle').textContent = 'Output';
}

function copySrOutput() {
  const text = document.getElementById('srOutput').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('Copied to clipboard', 'success'));
}
