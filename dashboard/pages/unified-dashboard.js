/* Unified Montefiore Urology Admin Dashboard */
/* Tier 1 — Shareef's full view: GME, Coverage, Call-outs, Residents */

let unifiedCache = {};

async function renderUnifiedDashboard() {
  const content = document.getElementById('pageContent');
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  
  content.innerHTML = `
    <style>
      .u-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
      .u-card-header { font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .5px; color: var(--text-muted); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
      .u-stat { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border); }
      .u-stat:last-child { border-bottom: none; }
      .u-stat-value { font-size: 24px; font-weight: 700; line-height: 1; }
      .u-stat-label { font-size: 12px; color: var(--text-muted); }
      .u-stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
      .u-bar { height: 6px; border-radius: 4px; background: var(--bg-card-alt); overflow: hidden; flex: 1; min-width: 60px; }
      .u-bar-fill { height: 100%; border-radius: 4px; transition: width .6s ease; }
      .u-badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 500; }
      .u-badge-green { background: rgba(52,199,89,.15); color: #34c759; }
      .u-badge-yellow { background: rgba(255,204,0,.15); color: #ffcc00; }
      .u-badge-red { background: rgba(255,69,58,.15); color: #ff453a; }
      .u-badge-blue { background: rgba(0,122,255,.15); color: #007aff; }
      .u-grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 20px; }
      .u-grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 16px; margin-bottom: 20px; }
      .u-grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }
      .u-resident-row { display: grid; grid-template-columns: 1.5fr 1fr 1.5fr 1.2fr 1fr 60px; gap: 8px; padding: 8px 0; align-items: center; font-size: 13px; border-bottom: 1px solid var(--border); }
      .u-resident-header { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: var(--text-muted); padding: 0 0 8px 0; border-bottom: 2px solid var(--border); font-weight: 600; }
      .u-resident-row:last-child { border-bottom: none; }
      .u-action-btn { padding: 10px 20px; border-radius: 8px; border: none; font-weight: 500; font-size: 13px; cursor: pointer; transition: all .15s; display: flex; align-items: center; gap: 8px; }
      .u-action-btn:hover { transform: translateY(-1px); }
      .u-action-btn:active { transform: translateY(0); }
      .u-quick-actions { display: flex; flex-wrap: wrap; gap: 10px; }
      .u-empty { text-align: center; padding: 30px 0; color: var(--text-muted); font-size: 13px; }
      .u-callout-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
      .u-callout-item:last-child { border-bottom: none; }
      .u-date-bar { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; }
      .u-section-title { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
      .u-section-sub { font-size: 12px; color: var(--text-muted); margin-bottom: 16px; }
    </style>
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title" style="font-size:22px">🏥 Montefiore Urology</div>
        <div class="page-subtitle">Admin Dashboard — ${dateStr}</div>
      </div>
    </div>

    <!-- Top stats row -->
    <div class="u-grid-4" id="topStats">
      <div class="skeleton" style="height:80px;border-radius:12px"></div>
      <div class="skeleton" style="height:80px;border-radius:12px"></div>
      <div class="skeleton" style="height:80px;border-radius:12px"></div>
      <div class="skeleton" style="height:80px;border-radius:12px"></div>
    </div>

    <!-- Main 2-column grid -->
    <div class="u-grid-2">
      <!-- Left: GME Overview -->
      <div class="u-card">
        <div class="u-card-header">💰 GME Reimbursement Overview</div>
        <div class="u-section-sub">Annual cap: $1,250/resident · Fiscal year Jul–Jun</div>
        <div id="gmeSummaryCards" style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap">
          <div class="skeleton" style="height:50px;flex:1;border-radius:8px"></div>
          <div class="skeleton" style="height:50px;flex:1;border-radius:8px"></div>
          <div class="skeleton" style="height:50px;flex:1;border-radius:8px"></div>
        </div>
        <div id="gmeResidentTable">
          <div class="skeleton" style="height:200px;border-radius:8px"></div>
        </div>
      </div>

      <!-- Right: Coverage & Call-Outs -->
      <div>
        <div class="u-card" style="margin-bottom:16px">
          <div class="u-card-header">📅 Today's Coverage</div>
          <div id="todayCoverage">
            <div class="skeleton" style="height:100px;border-radius:8px"></div>
          </div>
        </div>
        <div class="u-card">
          <div class="u-card-header">🤒 Recent Call-Outs</div>
          <div id="calloutList">
            <div class="skeleton" style="height:100px;border-radius:8px"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="u-card" style="margin-bottom:20px">
      <div class="u-card-header">⚡ Quick Actions</div>
      <div class="u-quick-actions">
        <button class="u-action-btn" style="background:var(--bg-card-alt);color:var(--text)" onclick="showToast('Coming soon — opens GME add form','info')">
          💰 Add Reimbursement
        </button>
        <button class="u-action-btn" style="background:var(--bg-card-alt);color:var(--text)" onclick="navigate('manager')">
          📋 Manager Command Center
        </button>
        <button class="u-action-btn" style="background:var(--bg-card-alt);color:var(--text)" onclick="navigate('oncall')">
          📅 View Full Schedule
        </button>
        <button class="u-action-btn" style="background:var(--bg-card-alt);color:var(--text)" onclick="showToast('Coming soon — opens swap request form','info')">
          🔄 Request Swap
        </button>
        <button class="u-action-btn" style="background:var(--bg-card-alt);color:var(--text)" onclick="showToast('Coming soon — opens call-out form','info')">
          🏥 Report Unavailable
        </button>
        <button class="u-action-btn" style="background:var(--bg-card-alt);color:var(--text)" onclick="showToast('Coming soon — generates PDF report','info')">
          📄 Generate Report
        </button>
      </div>
    </div>

    <!-- Schedule Range Info -->
    <div class="u-card" id="scheduleInfo">
      <div class="u-card-header">📋 Faculty Call Schedule</div>
      <div id="scheduleInfoContent">
        <div class="skeleton" style="height:60px;border-radius:8px"></div>
      </div>
    </div>
  `;

  // Load all data
  await Promise.all([
    loadGmeData(),
    loadCoverageData(),
    loadCalloutData(),
    loadScheduleInfo(),
  ]);
}

async function loadGmeData() {
  try {
    const [summary, residentsData] = await Promise.all([
      api.getGmeSummary('all'),
      api.getGmeResidents('all')
    ]);

    residentsData.residents.sort((a, b) => {
      const pctA = (a.total_used / 1250) * 100;
      const pctB = (b.total_used / 1250) * 100;
      return pctB - pctA;
    });

    // Summary cards
    const sumEl = document.getElementById('gmeSummaryCards');
    sumEl.innerHTML = `
      <div class="u-stat" style="border:none;padding:8px;flex:1;background:var(--bg-card-alt);border-radius:8px">
        <div><div class="u-stat-value">$${(summary.total_used || 0).toLocaleString()}</div><div class="u-stat-label">Total Used</div></div>
      </div>
      <div class="u-stat" style="border:none;padding:8px;flex:1;background:var(--bg-card-alt);border-radius:8px">
        <div><div class="u-stat-value" style="color:var(--yellow)">$${(summary.total_remaining || 0).toLocaleString()}</div><div class="u-stat-label">Remaining</div></div>
      </div>
      <div class="u-stat" style="border:none;padding:8px;flex:1;background:var(--bg-card-alt);border-radius:8px">
        <div><div class="u-stat-value">${summary.residents_with_funds || 0}</div><div class="u-stat-label">Have Funds Left</div></div>
      </div>
    `;

    // Resident table
    const tableEl = document.getElementById('gmeResidentTable');
    let html = `
      <div class="u-resident-header" style="display:grid;grid-template-columns:1.5fr 1fr 1.5fr 1.2fr 1fr">
        <span>Resident</span><span>PGY</span><span>Used / Cap</span><span>Remaining</span><span>Items</span>
      </div>`;
    
    for (const r of residentsData.residents) {
      const pct = r.total_used / 1250 * 100;
      const barColor = pct >= 90 ? '#ff453a' : pct >= 70 ? '#ffcc00' : '#34c759';
      const remaining = 1250 - r.total_used;
      const name = `${r.firstName || ''} ${r.lastName || ''}`;
      
      html += `
        <div class="u-resident-row" style="display:grid;grid-template-columns:1.5fr 1fr 1.5fr 1.2fr 1fr">
          <strong>${escapeHtml(name)}</strong>
          <span class="u-badge u-badge-blue">${escapeHtml(r.pgy || '—')}</span>
          <div style="display:flex;align-items:center;gap:8px">
            <div class="u-bar"><div class="u-bar-fill" style="width:${Math.min(pct, 100)}%;background:${barColor}"></div></div>
            <span style="font-size:12px;min-width:55px">$${r.total_used.toLocaleString()}</span>
          </div>
          <span style="${remaining <= 0 ? 'color:#ff453a;font-weight:600' : remaining < 300 ? 'color:#ffcc00' : ''}">
            ${remaining <= 0 ? 'Exhausted' : '$' + remaining.toLocaleString()}
          </span>
          <span>${r.reimbursements ? r.reimbursements.length : 0}</span>
        </div>`;
    }
    tableEl.innerHTML = html;
    
  } catch (err) {
    document.getElementById('gmeSummaryCards').innerHTML = `<div class="u-empty">⚠ Couldn't load GME data: ${escapeHtml(err.message)}</div>`;
  }
}

async function loadCoverageData() {
  const el = document.getElementById('todayCoverage');
  try {
    const [now, schedule] = await Promise.all([
      api.get('/api/oncall/now'),
      api.getOncallSchedule()
    ]);

    if (now.oncall && now.oncall.length > 0) {
      const hospitals = {};
      for (const e of now.oncall) {
        if (!hospitals[e.hospital]) hospitals[e.hospital] = [];
        hospitals[e.hospital].push(e);
      }
      let html = '';
      for (const [hosp, entries] of Object.entries(hospitals)) {
        html += `<div style="margin-bottom:12px"><strong>${escapeHtml(hosp)}</strong>`;
        for (const e of entries) {
          html += `<div style="display:flex;gap:12px;font-size:13px;padding:4px 0">
            <span class="u-badge u-badge-blue">Primary</span>
            <span>${escapeHtml(e.primary_attending || '—')}</span>
          </div>`;
          if (e.backup_attending && e.backup_attending !== 'None') {
            html += `<div style="display:flex;gap:12px;font-size:13px;padding:4px 0">
              <span class="u-badge u-badge-yellow">Backup</span>
              <span>${escapeHtml(e.backup_attending)}</span>
            </div>`;
          }
        }
        html += '</div>';
      }
      el.innerHTML = html;
    } else {
      let msg = now.message || 'No call data for today';
      html = `<div class="u-empty">📅 ${escapeHtml(msg)}</div>`;
      
      // Show schedule range
      if (schedule && schedule.hospitals) {
        const first = schedule.hospitals[0];
        html += `<div style="font-size:12px;color:var(--text-muted);margin-top:8px">Schedule loaded: ${first.start_date} – ${first.end_date} (${first.total_dates} dates, ${schedule.hospitals.length} hospitals)</div>`;
      }
      el.innerHTML = html;
    }
  } catch (err) {
    el.innerHTML = `<div class="u-empty">⚠ ${escapeHtml(err.message)}</div>`;
  }
}

async function loadCalloutData() {
  const el = document.getElementById('calloutList');
  try {
    // Use the call schedule contact data as a proxy for call-outs
    const schedule = await api.getOncallSchedule();
    let html = '';
    if (schedule.hospitals && schedule.hospitals.length > 0) {
      let totalDocs = 0;
      const allDocs = new Set();
      for (const h of schedule.hospitals) {
        for (const d of (h.unique_primary_attendings || [])) {
          allDocs.add(d);
        }
        totalDocs += h.total_dates;
      }
      html = `
        <div class="u-stat" style="border:none;padding:8px 0">
          <div class="u-stat-icon" style="background:rgba(0,122,255,.1)">🏥</div>
          <div>
            <div class="u-stat-value" style="font-size:18px">${schedule.hospitals.length}</div>
            <div class="u-stat-label">Hospitals tracked</div>
          </div>
        </div>
        <div class="u-stat" style="border:none;padding:8px 0">
          <div class="u-stat-icon" style="background:rgba(255,204,0,.1)">👨‍⚕️</div>
          <div>
            <div class="u-stat-value" style="font-size:18px">${allDocs.size}</div>
            <div class="u-stat-label">Attending physicians</div>
          </div>
        </div>
        <div class="u-stat" style="border:none;padding:8px 0">
          <div class="u-stat-icon" style="background:rgba(52,199,89,.1)">📅</div>
          <div>
            <div class="u-stat-value" style="font-size:18px">${totalDocs}</div>
            <div class="u-stat-label">Total scheduled dates</div>
          </div>
        </div>`;
    } else {
      html = `<div class="u-empty">ℹ Call-out system — coming when wired to Sick Call Line</div>`;
    }
    el.innerHTML = html;
  } catch (err) {
    el.innerHTML = `<div class="u-empty">⚠ ${escapeHtml(err.message)}</div>`;
  }
}

async function loadScheduleInfo() {
  const el = document.getElementById('scheduleInfoContent');
  try {
    const schedule = await api.getOncallSchedule();
    if (schedule.hospitals && schedule.hospitals.length > 0) {
      let html = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px">`;
      for (const h of schedule.hospitals) {
        html += `
          <div style="background:var(--bg-card-alt);padding:12px;border-radius:8px">
            <strong>${escapeHtml(h.name)}</strong>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px">
              ${h.start_date} – ${h.end_date}<br>
              ${h.total_dates} dates · ${(h.unique_primary_attendings || []).length} attendings
            </div>
          </div>`;
      }
      html += `</div>`;
      el.innerHTML = html;
    } else {
      el.innerHTML = `<div class="u-empty">No schedule loaded</div>`;
    }
  } catch (err) {
    el.innerHTML = `<div class="u-empty">⚠ ${escapeHtml(err.message)}</div>`;
  }
}
