async function renderMorningBriefing() {
  const content = document.getElementById('pageContent');
  const now = new Date();
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const today = `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}`;

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📡 Briefings & Cron</h1>
        <p class="page-subtitle">${today} — All outgoing briefs, scheduled jobs, and deliveries</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderMorningBriefing()">🔄 Refresh</button>
      </div>
    </div>
    <div id="bcGrid"><div class="loading"><div class="loading-spinner"></div><span>Loading briefings & cron data...</span></div></div>
    <style>
      .bc-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:12px; margin-top:16px; }
      .bc-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:16px; }
      .bc-card h3 { font-size:13px; font-weight:600; margin-bottom:8px; display:flex; align-items:center; gap:6px; }
      .bc-row { display:flex; justify-content:space-between; padding:4px 0; font-size:12px; border-bottom:1px solid rgba(255,255,255,0.04); }
      .bc-row:last-child { border-bottom:none; }
      .bc-tag { padding:1px 6px; border-radius:4px; font-size:10px; font-weight:600; }
      .bc-tag.ok { background:rgba(0,184,148,0.15); color:#00b894; }
      .bc-tag.err { background:rgba(214,48,49,0.15); color:#d63031; }
      .bc-tag.paused { background:rgba(253,203,110,0.15); color:#fdcb6e; }
      .bc-tag.telegram { background:rgba(0,136,204,0.15); color:#08c; }
      .bc-tag.email { background:rgba(162,155,254,0.15); color:#a29bfe; }
      .bc-tag.local { background:rgba(99,110,114,0.15); color:#636e72; }
      .bc-tag.all { background:rgba(108,92,231,0.2); color:#6c5ce7; }
      .bc-greeting { font-size:18px; font-weight:700; margin-bottom:4px; }
      .bc-sub { font-size:12px; color:var(--text-muted); margin-bottom:12px; }
      .bc-cron-table { width:100%; font-size:11px; border-collapse:collapse; }
      .bc-cron-table th { text-align:left; padding:6px 8px; color:var(--text-muted); font-weight:600; border-bottom:1px solid var(--border); white-space:nowrap; }
      .bc-cron-table td { padding:5px 8px; border-bottom:1px solid rgba(255,255,255,0.03); vertical-align:top; }
      .bc-cron-table tr:hover { background:rgba(255,255,255,0.02); }
      .bc-filter { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; }
      .bc-filter button { font-size:11px; padding:4px 10px; background:var(--bg-input); border:1px solid var(--border); border-radius:12px; color:var(--text-secondary); cursor:pointer; }
      .bc-filter button.active { background:var(--accent); color:#fff; border-color:var(--accent); }
    </style>
  `;

  try {
    const briefRes = await fetch('/api/morning-briefing').then(r => r.json()).catch(() => ({}));

    const onCall = briefRes.on_call_today || '—';
    const grandRounds = briefRes.grand_rounds_today || null;
    const pendingEvals = briefRes.pending_evals || 0;
    const cronStatus = briefRes.cron_status || {ok: 0, failed: 0};
    const upcoming = briefRes.upcoming_events || [];
    const commute = briefRes.commute || [];
    const jobs = briefRes.cron_jobs || [];

    const greet = now.getHours() < 12 ? 'Good Morning' : now.getHours() < 17 ? 'Good Afternoon' : 'Good Evening';

    document.getElementById('bcGrid').innerHTML = `
      <div class="bc-card" style="grid-column:1/-1">
        <div class="bc-greeting">${greet}, Shareef ☕</div>
        <div class="bc-sub">${today} — ${jobs.length} cron jobs scheduled</div>
        <div style="display:flex;gap:16px;flex-wrap:wrap">
          <div style="flex:1;min-width:110px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">📞 On Call</div>
            <div style="font-size:16px;font-weight:600">${onCall}</div>
          </div>
          <div style="flex:1;min-width:110px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">📝 Evals</div>
            <div style="font-size:16px;font-weight:600;color:${pendingEvals > 5 ? '#d63031' : pendingEvals > 2 ? '#fdcb6e' : '#00b894'}">${pendingEvals}</div>
          </div>
          <div style="flex:1;min-width:110px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">⏱ Cron</div>
            <div style="font-size:16px;font-weight:600">${cronStatus.ok}✅ ${cronStatus.failed ? cronStatus.failed+'❌' : ''}</div>
          </div>
          <div style="flex:1;min-width:110px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">📡 Delivery</div>
            <div style="font-size:16px;font-weight:600">${jobs.filter(j => j.deliver && j.deliver.includes('telegram')).length} TG / ${jobs.filter(j => j.deliver && j.deliver.includes('all')).length} All</div>
          </div>
        </div>
      </div>

      <div class="bc-card">
        <h3>📋 Grand Rounds</h3>
        ${grandRounds ? `
          <div class="bc-row"><span>Topic</span><span style="font-weight:500">${grandRounds.topic || 'TBD'}</span></div>
          <div class="bc-row"><span>Speaker</span><span>${grandRounds.speaker || 'TBD'}</span></div>
          <div class="bc-row"><span>Time</span><span>${grandRounds.time || '7:00 AM'}</span></div>
        ` : `<div style="color:var(--text-muted);font-size:12px;padding:8px 0">📭 No grand rounds today</div>`}
      </div>

      <div class="bc-card">
        <h3>📅 Upcoming</h3>
        ${upcoming.length > 0 ? upcoming.map(e => `
          <div class="bc-row"><span>${e.day || '?'}</span><span style="font-weight:500">${e.event || e}</span></div>
        `).join('') : `<div style="color:var(--text-muted);font-size:12px;padding:8px 0">📭 No upcoming events</div>`}
        <div style="margin-top:8px;display:flex;gap:6px">
          <a href="#grand-rounds" class="btn btn-ghost btn-sm" style="font-size:11px">📋 Grand Rounds</a>
          <a href="#oncall" class="btn btn-ghost btn-sm" style="font-size:11px">📅 Schedule</a>
        </div>
      </div>

      <div class="bc-card">
        <h3>🚗 Commute</h3>
        ${commute.length > 0 ? commute.map(r => `
          <div class="bc-row"><span>${r.name}</span><span>${r.error ? 'No address' : r.duration + ' (' + r.duration_in_traffic + ' traffic)'}</span></div>
        `).join('') : `<div style="color:var(--text-muted);font-size:12px;padding:8px 0">Loading commute...</div>`}
      </div>
    `;

    // Cron jobs table — full-width
    const container = document.getElementById('bcGrid');
    const cronHtml = buildCronJobsTable(jobs);
    container.innerHTML += `<div class="bc-card" style="grid-column:1/-1">${cronHtml}</div>`;

    // Filter handlers
    window.filterCronJobs = function(filter) {
      document.querySelectorAll('.bc-filter button').forEach(b => b.classList.remove('active'));
      document.querySelector(`.bc-filter button[data-filter="${filter}"]`).classList.add('active');
      const rows = document.querySelectorAll('#cronJobsBody tr');
      rows.forEach(row => {
        const delivery = row.dataset.delivery || '';
        if (filter === 'all' || delivery.includes(filter)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    };

  } catch(e) {
    document.getElementById('bcGrid').innerHTML = `<div class="bc-card" style="grid-column:1/-1;text-align:center;padding:32px;color:var(--red)">⚠️ ${escapeHtml(e.message)}</div>`;
  }
}

function buildCronJobsTable(jobs) {
  const sorted = [...jobs].sort((a, b) => {
    if (a.last_status === 'error' && b.last_status !== 'error') return -1;
    if (b.last_status === 'error' && a.last_status !== 'error') return 1;
    return (a.name || '').localeCompare(b.name || '');
  });

  // Count delivery types
  const tgCount = jobs.filter(j => j.deliver && j.deliver.includes('telegram')).length;
  const emailCount = jobs.filter(j => j.deliver && (j.deliver.includes('all') || j.deliver.includes('email'))).length;
  const localCount = jobs.filter(j => !j.deliver || j.deliver === 'local').length;

  let html = `
    <h3 style="margin-bottom:4px">⏱ All Cron Jobs (${jobs.length})</h3>
    <div style="font-size:11px;color:var(--text-muted);margin-bottom:10px">
      ${tgCount} Telegram · ${emailCount} Email/All · ${localCount} Local · 
      ${jobs.filter(j => j.last_status === 'error').length} failing · 
      ${jobs.filter(j => !j.enabled).length} paused
    </div>
    <div class="bc-filter">
      <button class="active" data-filter="all" onclick="filterCronJobs('all')">All</button>
      <button data-filter="telegram" onclick="filterCronJobs('telegram')">📱 Telegram</button>
      <button data-filter="all," onclick="filterCronJobs('all,')">📧 Email</button>
      <button data-filter="local" onclick="filterCronJobs('local')">💾 Local</button>
      <button data-filter="origin" onclick="filterCronJobs('origin')">🔔 Origin</button>
    </div>
    <div style="overflow-x:auto">
    <table class="bc-cron-table">
      <thead><tr>
        <th>Job</th><th>Schedule</th><th>Delivery</th><th>Last Run</th><th>Status</th>
      </tr></thead>
      <tbody id="cronJobsBody">
  `;

  for (const j of sorted) {
    const delivery = j.deliver || 'local';
    const delTag = delivery.includes('telegram') && delivery.includes('all') ? 'all' :
                   delivery.includes('telegram') ? 'telegram' :
                   delivery.includes('all') ? 'email' :
                   delivery === 'local' ? 'local' : 'origin';
    const delLabel = delivery.length > 40 ? delivery.substring(0,40)+'...' : delivery;

    const statusTag = !j.enabled ? 'paused' : j.last_status === 'error' ? 'err' : 'ok';
    const statusLabel = !j.enabled ? 'Paused' : j.last_status === 'error' ? 'Failed' : 'OK';

    const lastRun = j.last_run_at ? timeAgo(j.last_run_at) : 'never';
    const schedule = j.schedule || '—';

    html += `
      <tr data-delivery="${delivery}">
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(j.name)}">${escapeHtml(j.name)}</td>
        <td><code style="font-size:10px">${escapeHtml(schedule)}</code></td>
        <td><span class="bc-tag ${delTag}">${delLabel}</span></td>
        <td style="white-space:nowrap">${lastRun}</td>
        <td><span class="bc-tag ${statusTag}">${statusLabel}</span></td>
      </tr>`;
  }

  html += `</tbody></table></div>`;
  return html;
}
