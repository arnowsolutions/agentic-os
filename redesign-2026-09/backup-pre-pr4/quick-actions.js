async function renderQuickActions() {
  const content = document.getElementById('pageContent');
  
  const actions = [
    { icon: '📋', title: 'Generate Call Schedule PDF', desc: 'Create the Q3-Q4 call schedule PDF and email it', cmd: 'schedule', color: '#6c5ce7' },
    { icon: '💰', title: 'Send GME Report', desc: 'Run GME reimbursement report and email to coordinators', cmd: 'gme', color: '#0984e3' },
    { icon: '📊', title: 'Grand Rounds Report', desc: 'Generate attendance compliance report', cmd: 'grand-rounds', color: '#00b894' },
    { icon: '📝', title: 'CMS Eval Portal', desc: 'Check evaluation form completion status', cmd: 'eval', color: '#fdcb6e' },
    { icon: '🗓️', title: 'Sync Schedule to Calendar', desc: 'Push call schedule to Google Calendar', cmd: 'calendar-sync', color: '#e17055' },
    { icon: '📧', title: 'Send Test Email', desc: 'Send an email report to test@email.com', cmd: 'test-email', color: '#fd79a8' },
    { icon: '🔑', title: 'Vapi PIN Manager', desc: 'Reset voice assistant PINs', cmd: 'pin-manager', color: '#a29bfe' },
    { icon: '🌙', title: 'Deploy Vapi Assistant', desc: 'Re-deploy the Vapi voice assistant', cmd: 'deploy-vapi', color: '#636e72' },
    { icon: '💻', title: 'Open VS Coder', desc: 'Launch the code editor', cmd: 'vs-coder', color: '#00cec9' },
    { icon: '⏱', title: 'Restart Dashboard Server', desc: 'Restart the agentic-os server', cmd: 'restart-server', color: '#d63031' },
  ];

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">⚡ Quick Actions</div>
        <div class="page-subtitle">One-click operations for your most common workflows</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderQuickActions()">🔄 Refresh Status</button>
      </div>
    </div>
    <div class="qa-grid" id="qaGrid"></div>
    <div id="qaResult" class="qa-result" style="display:none"></div>
    <style>
      .qa-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-top: 16px; }
      .qa-card {
        background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border);
        padding: 20px; cursor: pointer; transition: all 0.2s ease; position: relative; overflow: hidden;
      }
      .qa-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
      .qa-card:active { transform: scale(0.98); }
      .qa-card .accent { position: absolute; top: 0; left: 0; width: 4px; height: 100%; border-radius: 4px 0 0 4px; }
      .qa-card .qa-icon { font-size: 24px; margin-bottom: 8px; }
      .qa-card .qa-title { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
      .qa-card .qa-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4; }
      .qa-card .qa-status { margin-top: 8px; font-size: 11px; font-weight: 500; }
      .qa-card.running { pointer-events: none; opacity: 0.7; }
      .qa-card.running .qa-status { color: var(--yellow); }
      .qa-card.done .qa-status { color: var(--green); }
      .qa-card.fail .qa-status { color: var(--red); }
      .qa-result {
        background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border);
        padding: 16px; margin-top: 16px; font-size: 13px; line-height: 1.5; white-space: pre-wrap;
        max-height: 300px; overflow-y: auto;
      }
    </style>
  `;

  const grid = document.getElementById('qaGrid');
  grid.innerHTML = actions.map((a, i) => `
    <div class="qa-card" data-idx="${i}" onclick="runQuickAction(${i})">
      <div class="accent" style="background:${a.color}"></div>
      <div class="qa-icon">${a.icon}</div>
      <div class="qa-title">${a.title}</div>
      <div class="qa-desc">${a.desc}</div>
      <div class="qa-status" id="qaStatus${i}">Ready</div>
    </div>
  `).join('');
}

async function runQuickAction(idx) {
  const actions = [
    { icon: '📋', title: 'Generate Call Schedule PDF', cmd: 'schedule' },
    { icon: '💰', title: 'Send GME Report', cmd: 'gme' },
    { icon: '📊', title: 'Grand Rounds Report', cmd: 'grand-rounds' },
    { icon: '📝', title: 'CMS Eval Portal', cmd: 'eval' },
    { icon: '🗓️', title: 'Sync Schedule to Calendar', cmd: 'calendar-sync' },
    { icon: '📧', title: 'Send Test Email', cmd: 'test-email' },
    { icon: '🔑', title: 'Vapi PIN Manager', cmd: 'pin-manager' },
    { icon: '🌙', title: 'Deploy Vapi Assistant', cmd: 'deploy-vapi' },
    { icon: '💻', title: 'Open VS Coder', cmd: 'vs-coder' },
    { icon: '⏱', title: 'Restart Dashboard Server', cmd: 'restart-server' },
  ];

  const action = actions[idx];
  const card = document.querySelector(`.qa-card[data-idx="${idx}"]`);
  const statusEl = document.getElementById(`qaStatus${idx}`);
  
  card.classList.add('running');
  statusEl.textContent = '⏳ Running...';

  // Non-nav actions call the API
  if (action.cmd === 'vs-coder') {
    navigate('vs-coder');
    return;
  }
  if (action.cmd === 'pin-manager') {
    navigate('pin-manager');
    return;
  }

  try {
    const res = await fetch('/api/quick-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action.cmd })
    });
    const data = await res.json();
    
    if (data.success) {
      card.classList.add('done');
      statusEl.textContent = '✅ Done';
      showToast(`${action.title} completed`, 'success');
    } else {
      card.classList.add('fail');
      statusEl.textContent = `❌ Failed: ${data.error || 'Unknown error'}`;
    }

    const resultDiv = document.getElementById('qaResult');
    if (data.output) {
      resultDiv.textContent = data.output;
      resultDiv.style.display = 'block';
    }
  } catch (err) {
    card.classList.add('fail');
    statusEl.textContent = '❌ Error: ' + err.message;
  }

  setTimeout(() => {
    card.classList.remove('running', 'done', 'fail');
    statusEl.textContent = 'Ready';
  }, 5000);
}
