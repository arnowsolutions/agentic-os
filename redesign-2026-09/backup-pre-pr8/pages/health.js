/* System Health — detailed view of /api/health/full */
async function renderHealth() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="pages-health">
      <style>
        .pages-health .hlt-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px,1fr)); gap:16px; margin-bottom:20px; }
        .pages-health .hlt-card { background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:16px; }
        .pages-health .hlt-card h3 { margin:0 0 12px; font-size:14px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; }
        .pages-health .hlt-service { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid var(--border-dim); }
        .pages-health .hlt-service:last-child { border:none; }
        .pages-health .hlt-ok { color:var(--green); font-weight:600; }
        .pages-health .hlt-down { color:var(--red); font-weight:600; }
        .pages-health .hlt-mono { font-family:monospace; font-size:12px; color:var(--text-muted); }
        .pages-health .hlt-raw { background:var(--bg); border:1px solid var(--border); border-radius:8px; padding:12px; max-height:300px; overflow:auto; font-family:monospace; font-size:11px; white-space:pre-wrap; }
        .pages-health .hlt-bar { height:6px; background:var(--border); border-radius:3px; overflow:hidden; margin-top:4px; }
        .pages-health .hlt-bar-fill { height:100%; background:var(--accent); border-radius:3px; }
      </style>

      <div class="mc-header" style="margin-bottom:24px">
        <div class="mc-header-left">
          <h1>🏥 System Health</h1>
          <p>Central monitor for dashboard, data service, Vapi bridge, cron, disk, and reports</p>
        </div>
        <div class="btn-group">
          <button class="btn btn-sm btn-ghost" onclick="renderHealth()">🔄 Refresh</button>
        </div>
      </div>

      <div id="healthDetail" class="hlt-grid">
        <div class="hlt-card"><div class="loading"><div class="loading-spinner"></div><span>Loading health...</span></div></div>
      </div>

      <div class="hlt-card" style="margin-top:16px">
        <h3>🔄 Cron Raw Output</h3>
        <div id="healthCronRaw" class="hlt-raw">Loading...</div>
      </div>
    </div>
  `;
  await loadHealthDetail();
}

async function loadHealthDetail() {
  const detail = document.getElementById('healthDetail');
  const raw = document.getElementById('healthCronRaw');
  try {
    const data = await fetch('/api/health/full').then(r => r.json());
    const services = data.services || {};
    const disk = data.disk || {};
    const reports = data.reports || {};
    const cron = data.cron || {};

    const serviceHtml = Object.entries(services).map(([name, info]) => `
      <div class="hlt-service">
        <span>${escapeHtml(name)}</span>
        <span class="${info.ok ? 'hlt-ok' : 'hlt-down'}">${info.ok ? '✓ OK' : '✕ DOWN'}</span>
      </div>
      ${info.error ? `<div class="hlt-mono" style="margin-bottom:8px">${escapeHtml(info.error)}</div>` : ''}
    `).join('');

    const diskHtml = Object.entries(disk).map(([name, info]) => {
      if (info.error) return `<div class="hlt-service"><span>${escapeHtml(name)}</span><span class="hlt-down">${escapeHtml(info.error)}</span></div>`;
      const pct = info.percent || 0;
      const color = pct > 90 ? 'var(--red)' : pct > 70 ? 'var(--yellow)' : 'var(--green)';
      return `
        <div class="hlt-service">
          <span>${escapeHtml(name)}</span>
          <span class="hlt-mono">${formatBytes(info.used)} / ${formatBytes(info.total)} (${pct}%)</span>
        </div>
        <div class="hlt-bar"><div class="hlt-bar-fill" style="width:${Math.min(pct,100)}%;background:${color}"></div></div>
      `;
    }).join('');

    detail.innerHTML = `
      <div class="hlt-card">
        <h3>🔧 Services</h3>
        ${serviceHtml || '<div class="text-muted">No services configured</div>'}
      </div>
      <div class="hlt-card">
        <h3>⏰ Cron</h3>
        <div class="hlt-service"><span>Total jobs</span><span class="hlt-mono">${cron.total ?? '?'}</span></div>
        <div class="hlt-service"><span>Failing</span><span class="${(cron.failing || 0) > 0 ? 'hlt-down' : 'hlt-ok'}">${cron.failing ?? 0}</span></div>
        <div class="hlt-service"><span>Delivery errors</span><span class="${(cron.delivery_errors || 0) > 0 ? 'hlt-down' : 'hlt-ok'}">${cron.delivery_errors ?? 0}</span></div>
        ${cron.error ? `<div class="hlt-mono" style="margin-top:8px">${escapeHtml(cron.error)}</div>` : ''}
      </div>
      <div class="hlt-card">
        <h3>💾 Disk</h3>
        ${diskHtml || '<div class="text-muted">No disk data</div>'}
      </div>
      <div class="hlt-card">
        <h3>📊 Reports</h3>
        <div class="hlt-service"><span>PDF count</span><span class="hlt-mono">${reports.report_count ?? 0}</span></div>
        <div class="hlt-service"><span>Latest</span><span class="hlt-mono">${reports.latest_pdf ? escapeHtml(reports.latest_pdf.split('/').pop()) : 'none'}</span></div>
        <div class="hlt-service"><span>Age</span><span class="hlt-mono">${reports.latest_pdf_age_seconds !== null ? timeAgo(new Date(Date.now() - reports.latest_pdf_age_seconds * 1000).toISOString()) : '-'}</span></div>
      </div>
    `;

    raw.textContent = (cron.raw_lines || []).join('\n') || 'No cron output';
  } catch (err) {
    detail.innerHTML = `<div class="hlt-card"><div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-title">Health check failed</div><div class="empty-state-desc">${escapeHtml(err.message)}</div></div></div>`;
    raw.textContent = err.message;
  }
}
