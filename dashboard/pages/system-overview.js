async function renderSystemOverview() {
  const content = document.getElementById('pageContent');
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">🏥 System Overview</div>
        <div class="page-subtitle">Central services, cron health & monitoring at a glance</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderSystemOverview()">🔄 Refresh</button>
      </div>
    </div>
    <div id="soGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin-top:16px">
      <div class="loading"><div class="loading-spinner"></div><span>Loading system status...</span></div>
    </div>
    <div class="so-section" id="soCronSection" style="margin-top:20px;display:none">
      <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">⏱ Cron Jobs</h3>
      <div id="soCronList"><div class="loading"><div class="loading-spinner"></div></div></div>
    </div>
    <style>
      .so-card {
        background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border);
        padding: 16px; transition: all 0.2s ease;
      }
      .so-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
      .so-card .so-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
      .so-card .so-name { font-size: 14px; font-weight: 600; }
      .so-card .so-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
      .so-card .so-dot.online { background: #00b894; }
      .so-card .so-dot.offline { background: #d63031; }
      .so-card .so-dot.warning { background: #fdcb6e; }
      .so-card .so-detail { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
      .so-card .so-detail strong { color: var(--text); }
      .so-table { width: 100%; border-collapse: collapse; font-size: 12px; }
      .so-table th { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 11px; text-transform: uppercase; color: var(--text-muted); }
      .so-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
      .so-table tr:hover td { background: rgba(255,255,255,0.03); }
      .so-section { background: var(--bg-card); border-radius: var(--radius-md); border: 1px solid var(--border); padding: 16px; }
    </style>
  `;

  // Fetch system status
  try {
    const [statusRes, cronRes] = await Promise.all([
      fetch('/api/status').then(r => r.json()).catch(() => ({})),
      fetch('/api/cron/jobs').then(r => r.json()).catch(() => ({jobs: []}))
    ]);

    const services = [
      { name: 'Agentic OS Dashboard', port: 8090, status: 'online', detail: 'FastAPI + Tailwind SPA' },
      { name: 'Hermes Agent', port: null, status: statusRes.agents?.find(a => a.name === 'hermes')?.status || 'unknown', detail: 'AI agent framework' },
      { name: 'Code Server', port: 8080, status: 'online', detail: 'code.srv1738752.hstgr.cloud — VS Code in browser' },
      { name: 'Vapi Voice Assistant', port: null, status: 'online', detail: '+1 (971) 382-0498 — 22 tools, GPT-4o' },
      { name: 'Telegram Gateway', port: null, status: statusRes.agents?.find(a => a.name === 'telegram')?.status || 'unknown', detail: 'Connected ✓' },
      { name: 'Hermes WebUI', port: 8787, status: 'online', detail: 'Browser chat interface' },
    ];

    const grid = document.getElementById('soGrid');
    grid.innerHTML = services.map(s => `
      <div class="so-card">
        <div class="so-header">
          <span class="so-name">${s.name}</span>
          <span class="so-dot ${s.status === 'online' ? 'online' : s.status === 'offline' ? 'offline' : 'warning'}"></span>
        </div>
        <div class="so-detail">
          ${s.port ? `<strong>Port:</strong> ${s.port}<br>` : ''}
          ${s.detail}
        </div>
      </div>
    `).join('');

    // Cron jobs section
    const jobs = cronRes.jobs || [];
    if (jobs.length > 0) {
      const cronSection = document.getElementById('soCronSection');
      const cronList = document.getElementById('soCronList');
      cronSection.style.display = 'block';
      cronList.innerHTML = `
        <table class="so-table">
          <thead><tr><th>Name</th><th>Schedule</th><th>Last Run</th><th>Status</th></tr></thead>
          <tbody>
            ${jobs.map(j => `
              <tr>
                <td><strong>${j.name || j.id || 'Unnamed'}</strong></td>
                <td>${j.schedule || '-'}</td>
                <td style="font-size:11px;color:var(--text-muted)">${j.last_run || j.last_run_at || 'Never'}</td>
                <td><span class="so-dot ${j.enabled !== false ? 'online' : 'offline'}" style="width:8px;height:8px;vertical-align:middle;margin-right:4px"></span>${j.enabled !== false ? 'Active' : 'Paused'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    document.getElementById('soGrid').innerHTML = `
      <div class="so-card" style="grid-column:1/-1;text-align:center;padding:32px">
        <div style="font-size:24px;margin-bottom:8px">⚠️</div>
        <div style="color:var(--text-muted)">Could not fetch system status: ${escapeHtml(err.message)}</div>
      </div>
    `;
  }
}
