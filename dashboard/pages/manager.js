/* Manager Command Center — Tier 2 */
/* For Jessie (schedules), Winnie (coverage), Kelly (reimbursements) */
/* 6 predetermined commands only: /coverage /team /approve /gap /today /swap */

let managerLastResult = '';

async function renderManager() {
  return renderManagerCommandCenter();
}

async function renderManagerCommandCenter() {
  const content = document.getElementById('pageContent');
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
  
  content.innerHTML = `
    <style>
      .mcc-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
      .mcc-header { font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: .5px; color: var(--text-muted); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
      .mcc-cmd-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 20px; }
      .mcc-cmd-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 16px 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-card-alt); cursor: pointer; transition: all .15s; font-size: 12px; }
      .mcc-cmd-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
      .mcc-cmd-btn:active { transform: translateY(0); }
      .mcc-cmd-btn .cmd-icon { font-size: 24px; }
      .mcc-cmd-btn .cmd-label { font-weight: 600; font-size: 13px; }
      .mcc-cmd-btn .cmd-desc { font-size: 10px; color: var(--text-muted); }
      .mcc-cmd-btn.loading { opacity: 0.6; pointer-events: none; }
      .mcc-cmd-btn.loading .cmd-icon { animation: spin 1s linear infinite; }
      @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      .mcc-result { background: var(--bg-card-alt); border-radius: 10px; padding: 16px; margin-top: 16px; white-space: pre-wrap; font-size: 13px; line-height: 1.6; min-height: 60px; }
      .mcc-result .r-header { font-weight: 600; margin-bottom: 8px; font-size: 14px; display: flex; align-items: center; gap: 8px; }
      .mcc-result .r-line { padding: 4px 0; display: flex; align-items: center; gap: 8px; }
      .mcc-result .r-tag { display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }
      .mcc-result .r-tag-green { background: rgba(52,199,89,.2); color: #34c759; }
      .mcc-result .r-tag-yellow { background: rgba(255,204,0,.2); color: #ffcc00; }
      .mcc-result .r-tag-red { background: rgba(255,69,58,.2); color: #ff453a; }
      .mcc-result .r-tag-blue { background: rgba(0,122,255,.2); color: #007aff; }
      .mcc-result .r-divider { height: 1px; background: var(--border); margin: 8px 0; }
    </style>

    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title" style="font-size:22px">📋 Manager Command Center</div>
        <div class="page-subtitle">Schedule, coverage, approvals — ${dateStr}</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderManagerCommandCenter()">🔄 Refresh</button>
      </div>
    </div>

    <!-- Command buttons -->
    <div class="mcc-card" style="margin-bottom:20px">
      <div class="mcc-header">🎮 Commands</div>
      <div class="mcc-cmd-grid">
        <div class="mcc-cmd-btn" id="cmdCoverage" onclick="runManagerCmd('coverage')">
          <span class="cmd-icon">📅</span>
          <span class="cmd-label">/coverage</span>
          <span class="cmd-desc">Today's call + gaps</span>
        </div>
        <div class="mcc-cmd-btn" id="cmdTeam" onclick="runManagerCmd('team')">
          <span class="cmd-icon">👥</span>
          <span class="cmd-label">/team</span>
          <span class="cmd-desc">Your residents' status</span>
        </div>
        <div class="mcc-cmd-btn" id="cmdApprove" onclick="runManagerCmd('approve')">
          <span class="cmd-icon">✅</span>
          <span class="cmd-label">/approve</span>
          <span class="cmd-desc">Pending actions</span>
        </div>
        <div class="mcc-cmd-btn" id="cmdGap" onclick="runManagerCmd('gap')">
          <span class="cmd-icon">⚠️</span>
          <span class="cmd-label">/gap</span>
          <span class="cmd-desc">Uncovered shifts</span>
        </div>
        <div class="mcc-cmd-btn" id="cmdToday" onclick="runManagerCmd('today')">
          <span class="cmd-icon">🏥</span>
          <span class="cmd-label">/today</span>
          <span class="cmd-desc">Who's where now</span>
        </div>
        <div class="mcc-cmd-btn" id="cmdSwap" onclick="runManagerCmd('swap')">
          <span class="cmd-icon">🔄</span>
          <span class="cmd-label">/swap</span>
          <span class="cmd-desc">Pending swaps</span>
        </div>
      </div>
    </div>

    <!-- Result window -->
    <div class="mcc-card">
      <div class="mcc-header">📄 Result</div>
      <div class="mcc-result" id="mccResult">
        <span style="color:var(--text-muted)">Tap a command above to run it</span>
      </div>
    </div>

    <!-- Quick reference -->
    <div class="mcc-card" style="margin-top:16px">
      <div class="mcc-header">📖 Quick Reference</div>
      <div style="font-size:12px;color:var(--text-muted);line-height:1.8">
        <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/coverage</code> — Shows today's call schedule, backup, and any gaps in coverage</div>
        <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/team</code> — Lists all residents with their current status (on call, clinic, off, PTO)</div>
        <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/approve</code> — Shows pending swap requests and call-outs awaiting approval</div>
        <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/gap</code> — Identifies uncovered shifts that need assignment</div>
        <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/today</code> — Full snapshot: who's on call, who's out, reported unavailable, and coverage gaps</div>
        <div><code style="background:var(--bg-card-alt);padding:2px 6px;border-radius:4px">/swap</code> — Lists all pending swap requests with status</div>
      </div>
    </div>
  `;
  
  // Auto-run coverage on load
  runManagerCmd('coverage');
}

async function runManagerCmd(cmd) {
  const resultEl = document.getElementById('mccResult');
  if (!resultEl) return;
  
  // Show loading on the button
  const btn = document.getElementById(`cmd${cmd.charAt(0).toUpperCase() + cmd.slice(1)}`);
  if (btn) btn.classList.add('loading');
  
  resultEl.innerHTML = `<div class="r-header"><span class="cmd-icon">⏳</span> Running /${cmd}...</div>`;
  
  try {
    let output = '';
    
    switch(cmd) {
      case 'coverage':
        output = await cmdCoverage();
        break;
      case 'team':
        output = await cmdTeam();
        break;
      case 'approve':
        output = await cmdApprove();
        break;
      case 'gap':
        output = await cmdGap();
        break;
      case 'today':
        output = await cmdToday();
        break;
      case 'swap':
        output = await cmdSwap();
        break;
    }
    
    resultEl.innerHTML = output;
  } catch (err) {
    resultEl.innerHTML = `
      <div class="r-header"><span style="color:var(--red)">✕</span> Error</div>
      <div class="r-line">${escapeHtml(err.message)}</div>
    `;
  } finally {
    if (btn) btn.classList.remove('loading');
  }
}

async function cmdCoverage() {
  const now = await api.get('/api/oncall/now');
  const schedule = await api.getOncallSchedule();
  
  let html = `<div class="r-header">📅 Today's Coverage</div>`;
  
  if (now.oncall && now.oncall.length > 0) {
    const byHospital = {};
    for (const e of now.oncall) {
      if (!byHospital[e.hospital]) byHospital[e.hospital] = [];
      byHospital[e.hospital].push(e);
    }
    for (const [hosp, entries] of Object.entries(byHospital)) {
      html += `<div style="margin-top:8px"><strong>🏥 ${escapeHtml(hosp)}</strong>`;
      for (const e of entries) {
        html += `<div class="r-line"><span class="r-tag r-tag-blue">Primary</span> ${escapeHtml(e.primary_attending || '—')}</div>`;
        if (e.backup_attending && e.backup_attending !== 'None') {
          html += `<div class="r-line"><span class="r-tag r-tag-yellow">Backup</span> ${escapeHtml(e.backup_attending)}</div>`;
        }
      }
      html += `</div>`;
    }
  } else {
    html += `<div class="r-line">📅 ${now.message || 'No data for today'}</div>`;
  }
  
  // Add schedule range info
  if (schedule && schedule.hospitals) {
    html += `<div class="r-divider"></div>`;
    for (const h of schedule.hospitals) {
      html += `<div class="r-line" style="font-size:12px;color:var(--text-muted)">
        <strong>${escapeHtml(h.name)}</strong>: ${h.start_date} – ${h.end_date} (${h.total_dates} dates)
      </div>`;
    }
  }
  
  // Check for gaps
  html += `<div class="r-divider"></div>`;
  html += `<div class="r-line"><span class="r-tag r-tag-green">✅</span> Schedule loaded for ${schedule.hospitals ? schedule.hospitals.length : 0} hospitals</div>`;
  
  return html;
}

async function cmdTeam() {
  const residentsData = await api.getGmeResidents();
  const gmeSummary = await api.getGmeSummary();
  
  let html = `<div class="r-header">👥 Residents (${residentsData.residents.length})</div>`;
  
  for (const r of residentsData.residents) {
    const pct = (r.total_used / 1250 * 100).toFixed(0);
    const remaining = 1250 - r.total_used;
    const statusColor = remaining <= 0 ? 'red' : remaining < 300 ? 'yellow' : 'green';
    const name = `${r.firstName || ''} ${r.lastName || ''}`;
    const reimCount = r.reimbursements ? r.reimbursements.length : 0;
    
    html += `<div class="r-line">
      <strong>${escapeHtml(name)}</strong>
      <span class="r-tag r-tag-blue">${escapeHtml(r.pgy || '')}</span>
      <span class="r-tag r-tag-${statusColor}">$${remaining} left</span>
      <span style="font-size:12px;color:var(--text-muted)">${reimCount} items · ${pct}% used</span>
    </div>`;
  }
  
  html += `<div class="r-divider"></div>`;
  html += `<div class="r-line" style="font-size:12px;color:var(--text-muted)">
    💰 $${(gmeSummary.total_used || 0).toLocaleString()} used · $${(gmeSummary.total_remaining || 0).toLocaleString()} remaining · ${gmeSummary.residents_with_funds || 0} have funds
  </div>`;
  
  return html;
}

async function cmdApprove() {
  let html = `<div class="r-header">✅ Pending Actions</div>`;
  
  try {
    // Check for residents who are at cap and might need attention
    const residentsData = await api.getGmeResidents();
    const atCap = residentsData.residents.filter(r => (1250 - r.total_used) <= 0);
    const nearCap = residentsData.residents.filter(r => {
      const remaining = 1250 - r.total_used;
      return remaining > 0 && remaining <= 200;
    });
    
    let hasItems = false;
    
    if (atCap.length > 0) {
      hasItems = true;
      html += `<div class="r-line" style="margin-top:8px"><span class="r-tag r-tag-red">⚠️</span> <strong>GME Cap Reached (${atCap.length})</strong></div>`;
      for (const r of atCap) {
        html += `<div class="r-line" style="padding-left:16px;font-size:12px">• ${escapeHtml(r.firstName || '')} ${escapeHtml(r.lastName || '')} — $0 remaining</div>`;
      }
    }
    
    if (nearCap.length > 0) {
      hasItems = true;
      html += `<div class="r-line" style="margin-top:8px"><span class="r-tag r-tag-yellow">⚠️</span> <strong>Near GME Cap (${nearCap.length})</strong></div>`;
      for (const r of nearCap) {
        const remaining = 1250 - r.total_used;
        html += `<div class="r-line" style="padding-left:16px;font-size:12px">• ${escapeHtml(r.firstName || '')} ${escapeHtml(r.lastName || '')} — $${remaining} left</div>`;
      }
    }
    
    if (!hasItems) {
      html += `<div class="r-line"><span class="r-tag r-tag-green">✅</span> No pending actions</div>`;
    }
    
    // Also show schedule info
    const schedule = await api.getOncallSchedule();
    if (schedule.hospitals) {
      html += `<div class="r-divider"></div>`;
      html += `<div class="r-line" style="font-size:12px;color:var(--text-muted)">📅 Faculty schedule: ${schedule.hospitals.length} hospitals active</div>`;
    }
    
  } catch (err) {
    html += `<div class="r-line" style="color:var(--red)">⚠ ${escapeHtml(err.message)}</div>`;
  }
  
  return html;
}

async function cmdGap() {
  let html = `<div class="r-header">⚠️ Coverage Gaps</div>`;
  
  try {
    const now = await api.get('/api/oncall/now');
    
    if (now.oncall && now.oncall.length > 0) {
      // Check each entry — flag if backup is None or missing
      let gaps = 0;
      for (const e of now.oncall) {
        if (!e.backup_attending || e.backup_attending === 'None' || e.backup_attending === '') {
          gaps++;
          html += `<div class="r-line"><span class="r-tag r-tag-red">GAP</span> <strong>${escapeHtml(e.hospital)}</strong> — Primary: ${escapeHtml(e.primary_attending || 'None')} — No backup assigned</div>`;
        }
      }
      
      if (gaps === 0) {
        html += `<div class="r-line"><span class="r-tag r-tag-green">✅</span> All hospitals have backup coverage today</div>`;
      }
    } else {
      html += `<div class="r-line">📅 ${now.message || 'No schedule data for today'}</div>`;
    }
    
    // Check if there's a weekend gap
    const today = new Date();
    const dayOfWeek = today.getDay();
    if (dayOfWeek === 5 || dayOfWeek === 6 || dayOfWeek === 0) {
      html += `<div class="r-divider"></div>`;
      html += `<div class="r-line"><span class="r-tag r-tag-yellow">Weekend</span> Weekend coverage in effect — verify all 3 hospitals have coverage</div>`;
    }
    
  } catch (err) {
    html += `<div class="r-line" style="color:var(--red)">⚠ ${escapeHtml(err.message)}</div>`;
  }
  
  return html;
}

async function cmdToday() {
  let html = `<div class="r-header">🏥 Today's Full Snapshot</div>`;
  
  try {
    const [now, schedule, residentsData, gmeSummary] = await Promise.all([
      api.get('/api/oncall/now'),
      api.getOncallSchedule(),
      api.getGmeResidents(),
      api.getGmeSummary()
    ]);
    
    // Coverage
    html += `<div style="margin-top:4px"><strong>📅 Coverage</strong></div>`;
    if (now.oncall && now.oncall.length > 0) {
      const byHospital = {};
      for (const e of now.oncall) {
        if (!byHospital[e.hospital]) byHospital[e.hospital] = [];
        byHospital[e.hospital].push(e);
      }
      for (const [hosp, entries] of Object.entries(byHospital)) {
        html += `<div class="r-line"><strong>${escapeHtml(hosp)}:</strong> `;
        html += entries.map(e => `Primary: ${escapeHtml(e.primary_attending || '—')}${e.backup_attending && e.backup_attending !== 'None' ? ` (Backup: ${escapeHtml(e.backup_attending)})` : ' ⚠️ No backup'}`).join(' · ');
        html += `</div>`;
      }
    } else {
      html += `<div class="r-line">📅 ${now.message || 'No data'}</div>`;
    }
    
    // GME
    html += `<div class="r-divider"></div>`;
    html += `<div style="margin-top:4px"><strong>💰 GME Funds</strong></div>`;
    html += `<div class="r-line">$${(gmeSummary.total_used || 0).toLocaleString()} used · $${(gmeSummary.total_remaining || 0).toLocaleString()} remaining · ${gmeSummary.residents_with_funds || 0}/${gmeSummary.total_residents || 0} residents have funds left</div>`;
    
    // Residents near cap
    const nearCap = residentsData.residents.filter(r => (1250 - r.total_used) <= 200);
    if (nearCap.length > 0) {
      html += `<div class="r-line" style="font-size:12px;color:var(--red)">⚠️ ${nearCap.length} resident(s) near/exceeded GME cap:</div>`;
      for (const r of nearCap) {
        html += `<div class="r-line" style="font-size:12px;padding-left:16px">• ${escapeHtml(r.firstName || '')} ${escapeHtml(r.lastName || '')} — $${(1250 - r.total_used).toFixed(0)} remaining</div>`;
      }
    }
    
    // Schedule info
    if (schedule && schedule.hospitals) {
      html += `<div class="r-divider"></div>`;
      html += `<div style="margin-top:4px"><strong>🏥 Hospitals (${schedule.hospitals.length})</strong></div>`;
      for (const h of schedule.hospitals) {
        html += `<div class="r-line" style="font-size:12px">
          <strong>${escapeHtml(h.name)}</strong> — ${h.start_date} to ${h.end_date} (${(h.unique_primary_attendings || []).length} attendings)
        </div>`;
      }
    }
    
  } catch (err) {
    html += `<div class="r-line" style="color:var(--red)">⚠ ${escapeHtml(err.message)}</div>`;
  }
  
  return html;
}

async function cmdSwap() {
  let html = `<div class="r-header">🔄 Swap Processor</div>`;
  
  html += `
    <div class="r-line">Run the call-schedule swap email processor manually.</div>
    <div class="r-line" style="display:flex;gap:10px;margin-top:12px">
      <button class="btn btn-sm btn-ghost" id="btnSwapTest" onclick="runSwapProcessor(true)">🔍 Test (dry-run)</button>
      <button class="btn btn-sm btn-primary" id="btnSwapLive" onclick="runSwapProcessor(false)">▶ Run live</button>
    </div>
    <div id="swapResult" class="mcc-result" style="margin-top:12px;min-height:40px"><span style="color:var(--text-muted)">Click a button above to process swap requests.</span></div>
  `;
  
  return html;
}

async function runSwapProcessor(dryRun) {
  const resultEl = document.getElementById('swapResult');
  const testBtn = document.getElementById('btnSwapTest');
  const liveBtn = document.getElementById('btnSwapLive');
  if (!resultEl) return;
  
  if (testBtn) testBtn.disabled = true;
  if (liveBtn) liveBtn.disabled = true;
  resultEl.innerHTML = `<div class="r-header"><span class="cmd-icon">⏳</span> ${dryRun ? 'Dry-run' : 'Live'} swap processor running...</div>`;
  
  try {
    const res = await fetch(`/api/swap/process?dry_run=${dryRun}`, { method: 'POST' });
    const data = await res.json();
    const output = (data.stdout || '') + (data.stderr ? '\n---stderr---\n' + data.stderr : '');
    const ok = data.success;
    resultEl.innerHTML = `
      <div class="r-header"><span style="color:${ok ? 'var(--green)' : 'var(--red)'}">${ok ? '✓' : '✕'}</span> ${dryRun ? 'Dry-run' : 'Live'} ${ok ? 'completed' : 'failed'}</div>
      <pre style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;max-height:300px;overflow:auto;font-size:11px;white-space:pre-wrap">${escapeHtml(output.slice(0, 3000))}</pre>
    `;
  } catch (err) {
    resultEl.innerHTML = `<div class="r-header"><span style="color:var(--red)">✕</span> Error</div><div class="r-line">${escapeHtml(err.message)}</div>`;
  } finally {
    if (testBtn) testBtn.disabled = false;
    if (liveBtn) liveBtn.disabled = false;
  }
}
