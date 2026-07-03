async function renderMorningBriefing() {
  const content = document.getElementById('pageContent');
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const now = new Date();
  const today = `${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}, ${now.getFullYear()}`;

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">🌅 Morning Briefing</div>
        <div class="page-subtitle">${today} — Everything you need to know today</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderMorningBriefing()">🔄 Refresh</button>
      </div>
    </div>
    <div class="mb-grid" id="mbGrid">
      <div class="loading"><div class="loading-spinner"></div><span>Building your briefing...</span></div>
    </div>
    <style>
      .mb-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:12px; margin-top:16px; }
      .mb-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:16px; }
      .mb-card h3 { font-size:13px; font-weight:600; margin-bottom:8px; display:flex; align-items:center; gap:6px; }
      .mb-row { display:flex; justify-content:space-between; padding:4px 0; font-size:12px; border-bottom:1px solid rgba(255,255,255,0.04); }
      .mb-row:last-child { border-bottom:none; }
      .mb-tag { padding:1px 6px; border-radius:4px; font-size:10px; font-weight:600; }
      .mb-tag.green { background:rgba(0,184,148,0.15); color:#00b894; }
      .mb-tag.yellow { background:rgba(253,203,110,0.15); color:#fdcb6e; }
      .mb-tag.red { background:rgba(214,48,49,0.15); color:#d63031; }
      .mb-greeting { font-size:18px; font-weight:700; margin-bottom:4px; }
      .mb-sub { font-size:12px; color:var(--text-muted); margin-bottom:16px; }
    </style>
  `;

  try {
    const res = await fetch('/api/morning-briefing').then(r => r.json()).catch(() => ({}));
    const onCall = res.on_call_today || '—';
    const grandRounds = res.grand_rounds_today || null;
    const pendingEvals = res.pending_evals || 0;
    const cronStatus = res.cron_status || {ok: 0, failed: 0};
    const upcoming = res.upcoming_events || [];
    const commute = res.commute || [];

    const greet = now.getHours() < 12 ? 'Good Morning' : now.getHours() < 17 ? 'Good Afternoon' : 'Good Evening';

    document.getElementById('mbGrid').innerHTML = `
      <div class="mb-card" style="grid-column:1/-1">
        <div class="mb-greeting">${greet}, Shareef ☕</div>
        <div class="mb-sub">${today} — Here's your urology briefing</div>
        <div style="display:flex;gap:16px;flex-wrap:wrap">
          <div style="flex:1;min-width:120px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">📞 On Call Today</div>
            <div style="font-size:16px;font-weight:600">${onCall}</div>
          </div>
          <div style="flex:1;min-width:120px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">📝 Pending Evals</div>
            <div style="font-size:16px;font-weight:600;color:${pendingEvals > 5 ? '#d63031' : pendingEvals > 2 ? '#fdcb6e' : '#00b894'}">${pendingEvals}</div>
          </div>
          <div style="flex:1;min-width:120px;padding:10px;background:rgba(255,255,255,0.03);border-radius:var(--radius-sm);text-align:center">
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">⏱ Cron Jobs</div>
            <div style="font-size:16px;font-weight:600">${cronStatus.ok}✅ ${cronStatus.failed > 0 ? cronStatus.failed+'❌' : ''}</div>
          </div>
        </div>
      </div>

      <div class="mb-card">
        <h3>📋 Grand Rounds</h3>
        ${grandRounds ? `
          <div class="mb-row"><span>Today's Topic</span><span style="font-weight:500">${grandRounds.topic || 'TBD'}</span></div>
          <div class="mb-row"><span>Speaker</span><span>${grandRounds.speaker || 'TBD'}</span></div>
          <div class="mb-row"><span>Time</span><span>${grandRounds.time || '7:00 AM'}</span></div>
        ` : `<div style="color:var(--text-muted);font-size:12px;padding:8px 0">📭 No grand rounds scheduled today</div>`}
      </div>

      <div class="mb-card">
        <h3>📅 Upcoming This Week</h3>
        ${upcoming.length > 0 ? upcoming.map(e => `
          <div class="mb-row"><span>${e.day || '?'}</span><span style="font-weight:500">${e.event || e}</span></div>
        `).join('') : `
          <div style="color:var(--text-muted);font-size:12px;padding:8px 0">📭 No upcoming events this week</div>
        `}
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
          <a href="#grand-rounds" class="btn btn-ghost btn-sm" style="font-size:11px">📋 Grand Rounds</a>
          <a href="#eval-portal" class="btn btn-ghost btn-sm" style="font-size:11px">📝 Evals</a>
          <a href="#oncall" class="btn btn-ghost btn-sm" style="font-size:11px">📅 Schedule</a>
        </div>
      </div>


      <div class="mb-card">
        <h3> Commute</h3>
        ${commute.length > 0 ? commute.map(r => `
          <div class="mb-row">
            <span>${r.name === 'shareef' ? ' Shareef' : r.name.charAt(0).toUpperCase() + r.name.slice(1)}</span>
            <span>${r.error ? ' No address' : r.distance + '  ' + r.duration + ', now <strong>' + r.duration_in_traffic + '</strong>' + (r.delta_text || '')}</span>
          </div>
        `).join('') : `
          <div style="color:var(--text-muted);font-size:12px;padding:8px 0"> Commute loading...</div>
        `}
      </div>

      <div class="mb-card">
        <h3>⚡ Quick Actions</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
          <button class="btn btn-sm btn-primary" onclick="navigate('call-schedule-pdf')">📄 Generate PDF</button>
          <button class="btn btn-sm btn-primary" onclick="navigate('eval-portal')">📝 Check Evals</button>
          <button class="btn btn-sm btn-primary" onclick="navigate('system-overview')">🏥 System</button>
          <button class="btn btn-sm btn-primary" onclick="navigate('quick-actions')">⚡ Actions</button>
        </div>
      </div>
    `;
  } catch(e) {
    document.getElementById('mbGrid').innerHTML = `<div class="mb-card" style="grid-column:1/-1;text-align:center;padding:32px;color:var(--text-muted)">⚠️ ${escapeHtml(e.message)}</div>`;
  }
}
