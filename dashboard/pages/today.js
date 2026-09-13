/**
 * Today — the operator's action surface (2026-09 SSOT redesign).
 *
 * Job-first: what needs you right now, who's on call, what's next, and one
 * click to everything else. Absorbs the old Command Center (#manager) and
 * Unified Dashboard (#unified-dashboard) as tabs — their modules are loaded
 * unmodified and rendered into the tab pane (additive-first: legacy hashes
 * redirect here from app.js LEGACY_REDIRECTS).
 *
 * Sources: /api/attention, /api/oncall/now, /api/calendar/events,
 * /api/crm/launchpad — all live, all stamped. No emoji (DESIGN.md).
 */

let _todayTabCache = {};

const TODAY_TABS = [
  { key: 'queue',    label: 'Needs You',     local: true },
  { key: 'overview', label: 'Dept Overview', module: 'unified-dashboard.js', fn: 'renderUnifiedDashboard' },
  { key: 'manager',  label: 'Call Board',    module: 'manager-command-center.js', fn: 'renderManagerCommandCenter' },
];

function todayActiveTab() {
  const m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  const key = m ? m[1] : '';
  return TODAY_TABS.some(t => t.key === key) ? key : 'queue';
}

async function todaySetTab(key) {
  const target = 'today?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return;
  }
  await renderToday();
}

async function renderToday() {
  const content = document.getElementById('pageContent');
  const active = todayActiveTab();
  const tab = TODAY_TABS.find(t => t.key === active) || TODAY_TABS[0];

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Today</div>
        <div class="page-subtitle">${new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })} · your action queue at a glance</div>
        <div id="dataStamp"></div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderToday()">↻ Refresh</button>
      </div>
    </div>
    <div class="tabs">
      ${TODAY_TABS.map(t => `<button class="tab${t.key === active ? ' active' : ''}" onclick="todaySetTab('${t.key}')">${t.label}</button>`).join('')}
    </div>
    <div id="suitePane"><div class="loading"><div class="loading-spinner"></div><span>Loading ${tab.label}…</span></div></div>
    <style>
      .tdy-wrap { display: grid; grid-template-columns: 1fr 380px; gap: 16px; margin-top: 16px; }
      @media (max-width: 1279px) { .tdy-wrap { grid-template-columns: 1fr; } }
      .tdy-sec { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; }
      .tdy-sec h3 { font-size: 13px; font-weight: 600; margin: 0 0 10px; color: var(--text); display: flex; justify-content: space-between; align-items: center; }
      .tdy-sec h3 .cnt { font-size: 11px; color: var(--text-muted); font-weight: 500; }
      .tdy-row { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-top: 1px solid var(--border-soft); font-size: 13px; }
      .tdy-row:first-of-type { border-top: none; }
      .tdy-row .lbl { color: var(--text-muted); flex: none; font-size: 12px; padding-top: 1px; }
      .tdy-kpi { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 14px; }
      .tdy-kpi .k { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; cursor: pointer; }
      .tdy-kpi .k:hover { border-color: var(--accent); }
      .tdy-kpi .k .n { font-size: 22px; font-weight: 700; font-feature-settings: "tnum"; }
      .tdy-kpi .k .n.zero { color: var(--text-muted); }
      .tdy-kpi .k .n.hot { color: #f59e0b; }
      .tdy-kpi .k .l { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
      .tdy-link { color: var(--accent); text-decoration: none; font-size: 12px; }
      .tdy-chip { display: inline-block; font-size: 11px; border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px; margin: 2px 4px 2px 0; color: var(--text-muted); }
      .tdy-chip.warn { color: #f59e0b; border-color: rgba(245,158,11,.35); }
    </style>
  `;

  const pane = document.getElementById('suitePane');

  if (!tab.local) {
    try {
      if (typeof window[tab.fn] !== 'function') {
        await loadScript('/dashboard/pages/' + tab.module + '?v=' + Date.now());
      }
      const fn = window[tab.fn];
      if (typeof fn !== 'function') throw new Error('Module not available: ' + tab.module);
      await fn(pane);
    } catch (err) {
      pane.innerHTML = `<div class="empty-state"><div class="empty-state-icon">!</div>
        <div class="empty-state-title">Could not load ${tab.label}</div>
        <div class="empty-state-desc">${escapeHtml(err.message)}</div>
        <button class="btn btn-primary mt-3" onclick="renderToday()">Retry</button></div>`;
    }
    return;
  }

  // ── Needs You queue ────────────────────────────────────────────────
  const [att, oncall, cal, act] = await Promise.all([
    api.fetchSafe('/api/attention', {}, 20000).then(r => r.data),
    api.fetchSafe('/api/oncall/now', {}, 12000).then(r => r.data),
    api.fetchSafe('/api/calendar/events?days=7', {}, 12000).then(r => r.data),
    api.fetchSafe('/api/agent-activity', {}, 10000).then(r => r.data),  // AI-generalist rail
  ]);

  if (!att) {
    pane.innerHTML = `<div class="empty-state"><div class="empty-state-icon">!</div>
      <div class="empty-state-title">Attention feed unavailable</div>
      <div class="empty-state-desc">/api/attention did not respond.</div></div>`;
    return;
  }

  const stampEl = document.getElementById('dataStamp');
  if (stampEl && att.sync) {
    stampEl.innerHTML = renderDataStamp(att.sync);
  }

  const A = att;
  const kpis = [
    { n: A.pending_email_count, label: 'Email drafts awaiting approval', go: '#mass-email', hot: A.pending_email_count > 0 },
    { n: A.open_swap_count, label: 'Open shift swaps', go: '#schedule-suite?tab=call', hot: A.open_swap_count > 0 },
    { n: A.data_gaps.count, label: 'CRM records with gaps', go: '#data-gaps', hot: A.data_gaps.count > 50 },
    { n: A.cron.enabled, label: 'Cron jobs enabled', go: '#morning-briefing', hot: false },
  ];

  const emails = (A.pending_emails || []).slice(0, 6).map(e => {
    const age = e.created ? Math.max(0, Math.round((Date.now() / 1000 - e.created) / 3600)) : null;
    return `<div class="tdy-row"><span>${escapeHtml(e.subject || '(no subject)')} <span class="lbl">→ ${escapeHtml((e.to || '').split('@')[0])}</span></span>
      <span class="lbl">${age != null ? age + ' h ago' : ''}</span></div>`;
  }).join('') || '<div class="tdy-row"><span class="lbl">No pending drafts — review queue is clear.</span></div>';

  const gaps = (A.data_gaps.items || []).map(i => `<span class="tdy-chip">${escapeHtml(i.field)} ×${i.count}</span>`).join('');
  const stale = (A.stale_sources || []).map(s => `<span class="tdy-chip warn">${escapeHtml(s.label)} · ${s.age_days}d</span>`).join('')
    || '<span class="tdy-chip">no frozen sources over 7 days</span>';

  const oc = (oncall && oncall.oncall) || [];
  const oncallRows = oc.length ? oc.map(e => `
    <div class="tdy-row"><span><strong>${escapeHtml(e.hospital || '')}</strong>
      <span class="lbl"> · ${escapeHtml(e.primary_attending || '—')} (primary) · ${escapeHtml(e.backup_attending || '—')} (backup)</span></span></div>`).join('')
    : `<div class="tdy-row"><span class="lbl">${escapeHtml((oncall && oncall.message) || 'No on-call data for today')}</span></div>`;

  const now = new Date();
  const week = ((cal && cal.events) || [])
    .filter(e => { const s = (e.start || {}).date; return s && new Date(s + 'T12:00:00') >= new Date(now.toDateString()); })
    .slice(0, 7)
    .map(e => `<div class="tdy-row"><span>${escapeHtml(e.summary || '(event)')}</span><span class="lbl">${escapeHtml(((e.start || {}).date) || '')}</span></div>`).join('')
    || '<div class="tdy-row"><span class="lbl">No calendar events in the next 7 days.</span></div>';

  pane.innerHTML = `
    <div class="tdy-kpi">
      ${kpis.map(k => `<div class="k" onclick="location.hash='${k.go}'">
        <div class="n ${k.n ? (k.hot ? 'hot' : '') : 'zero'}">${k.n == null ? '—' : k.n}</div>
        <div class="l">${escapeHtml(k.label)}</div></div>`).join('')}
    </div>
    <div class="tdy-wrap">
      <div>
        <div class="tdy-sec">
          <h3>Email drafts awaiting your approval <a class="tdy-link" href="#mass-email">open send tools →</a></h3>
          ${emails}
        </div>
        <div class="tdy-sec">
          <h3>On call today <a class="tdy-link" href="#schedule-suite?tab=call">full schedule →</a></h3>
          ${oncallRows}
        </div>
        <div class="tdy-sec">
          <h3>Next 7 days <a class="tdy-link" href="#calendar">calendar →</a></h3>
          ${week}
        </div>
      </div>
      <div>
        <div class="tdy-sec">
          <h3>Data gaps <a class="tdy-link" href="#data-gaps">details →</a></h3>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px">${escapeHtml(A.data_gaps.source || '')}</div>
          ${gaps || '<span class="tdy-chip">none</span>'}
        </div>
        <div class="tdy-sec">
          <h3>Frozen sources</h3>
          ${stale}
        </div>
        <div class="tdy-sec">
          <h3>Cron</h3>
          <div class="tdy-row"><span>${A.cron.enabled}/${A.cron.total} enabled</span><a class="tdy-link" href="#briefings">briefings & cron →</a></div>
        </div>
        ${agentActivitySec(act)}
      </div>
    </div>`;
}

// ─── Agent activity rail (AI-generalist layer, 2026-09 Stage 5c) ─────
// Recent work performed by AI agents: chat turns, skill runs, scheduled runs.
function agentActivitySec(act) {
  if (!act || !act.events || !act.events.length) return '';
  const ago = (ts) => {
    if (!ts) return '';
    const mins = Math.max(0, Math.round((Date.now() - new Date(ts).getTime()) / 60000));
    if (mins < 60) return mins + 'm ago';
    if (mins < 24 * 60) return Math.round(mins / 60) + 'h ago';
    return Math.round(mins / 1440) + 'd ago';
  };
  const kindLabel = { chat_message: 'chat', skill_run: 'skill', agent_run: 'run', task_routed: 'routed', scheduler_run: 'sched' };
  const rows = act.events.slice(0, 8).map(e => `
    <div class="tdy-row">
      <span><strong>${escapeHtml(kindLabel[e.kind] || e.kind)}</strong>
        <span class="lbl">${escapeHtml(e.agent || '')}${e.page ? ' · #' + escapeHtml(e.page) : ''}</span></span>
      <span class="lbl">${ago(e.ts)}</span>
    </div>`).join('');
  return `
    <div class="tdy-sec">
      <h3>Agent activity <a class="tdy-link" href="#audit">full log →</a></h3>
      ${rows}
    </div>`;
}
