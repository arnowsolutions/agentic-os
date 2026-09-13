/* ═══════════════════════════════════════════════════════════════════════
   System Overview — Clean service health + cron status
   No emoji. Uses design system classes.
   ═══════════════════════════════════════════════════════════════════════ */

async function renderSystemOverview() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">System Overview</h1>
        <p class="page-subtitle">Central services, cron health, and monitoring</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost btn-sm" onclick="renderSystemOverview()">Refresh</button>
      </div>
    </div>
    <div class="section-title">Services</div>
    <div id="soGrid" class="grid grid-3 mb-4">
      <div class="loading"><div class="loading-spinner"></div></div>
    </div>
    <div id="soCronSection" style="display:none">
      <div class="section-title">Cron Jobs</div>
      <div class="card" style="padding:0;overflow:hidden">
        <div id="soCronList"><div class="loading" style="padding:24px"><div class="loading-spinner"></div></div></div>
      </div>
    </div>
  `;

  try {
    const [statusRes, cronRes] = await Promise.all([
      fetch('/api/status').then(r => r.json()).catch(() => ({})),
      fetch('/api/cron/jobs').then(r => r.json()).catch(() => ({jobs: []}))
    ]);

    const hermesStatus = statusRes.agents?.find(a => a.name === 'hermes')?.status || 'unknown';

    const services = [
      { name: 'Agentic OS', detail: 'Dashboard server', status: 'online' },
      { name: 'Hermes Agent', detail: 'AI agent framework', status: hermesStatus },
      { name: 'Code Server', detail: 'code.srv1738752.hstgr.cloud', status: 'online' },
      { name: 'Vapi Voice', detail: '+1 (971) 382-0498', status: 'online' },
      { name: 'Telegram Gateway', detail: 'Connected', status: hermesStatus === 'online' ? 'online' : 'warning' },
      { name: 'Hermes WebUI', detail: 'Browser chat interface', status: 'online' },
    ];

    document.getElementById('soGrid').innerHTML = services.map(s => {
      const dotColor = s.status === 'online' ? 'var(--green)' : s.status === 'offline' ? 'var(--red)' : 'var(--yellow)';
      const bgColor = s.status === 'online' ? 'var(--green-dim)' : s.status === 'offline' ? 'var(--red-dim)' : 'var(--yellow-dim)';
      return `<div class="card" style="display:flex;align-items:center;gap:12px;padding:16px">
        <div style="width:10px;height:10px;border-radius:50%;background:${dotColor};flex-shrink:0" title="${s.status}"></div>
        <div style="flex:1;min-width:0">
          <div style="font-weight:550;font-size:0.85rem;color:var(--text-primary);letter-spacing:-0.01em">${s.name}</div>
          <div style="font-size:0.72rem;color:var(--text-muted);margin-top:1px">${s.detail}</div>
        </div>
        <span class="badge" style="background:${bgColor};color:${dotColor};font-size:0.65rem">${s.status}</span>
      </div>`;
    }).join('');

    // Cron jobs
    const jobs = cronRes.jobs || [];
    if (jobs.length > 0) {
      document.getElementById('soCronSection').style.display = 'block';
      document.getElementById('soCronList').innerHTML = `
        <table>
          <thead><tr><th>Name</th><th>Schedule</th><th>Last Run</th><th>Status</th></tr></thead>
          <tbody>${jobs.map(j => {
            const active = j.enabled !== false;
            return `<tr>
              <td><strong>${j.name || j.id || 'Unnamed'}</strong></td>
              <td style="font-family:var(--font-mono);font-size:0.72rem">${j.schedule || '—'}</td>
              <td style="font-size:0.72rem;color:var(--text-muted)">${j.last_run || j.last_run_at || 'Never'}</td>
              <td><span class="badge ${active ? 'badge-success' : 'badge-warning'}" style="font-size:0.65rem">${active ? 'Active' : 'Paused'}</span></td>
            </tr>`;
          }).join('')}</tbody>
        </table>`;
    }
  } catch (err) {
    document.getElementById('soGrid').innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state-icon">—</div><div class="empty-state-title">Connection Error</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div>`;
  }
}
