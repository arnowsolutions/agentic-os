/**
 * Schedule Suite — merged Weekly Call / Staff / PDF Export (PR5).
 *
 * The three legacy pages (#oncall, #staff-schedule, #call-schedule-pdf) now
 * render as tabs here. Each tab delegates to its original module's render
 * function (loaded on first use) — the modules stay single-sourced, so the
 * suite adds zero duplicated logic. Legacy hashes redirect here via
 * LEGACY_REDIRECTS in app.js and land on the matching tab.
 *
 * Tab state lives in the hash: #schedule-suite?tab=call|staff|pdf, so tabs
 * are linkable, survive refresh, and back/forward keeps the final tab.
 * No emoji.
 */

var SCHEDULE_SUITE_TABS = [
  { key: 'call',  label: 'Weekly Call', module: 'oncall.js',            fn: 'renderOncall' },
  { key: 'staff', label: 'Staff',       module: 'staff-schedule.js',    fn: 'renderStaffSchedule' },
  { key: 'pdf',   label: 'PDF Export',  module: 'call-schedule-pdf.js', fn: 'renderCallSchedulePdf' },
];

function scheduleSuiteActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return SCHEDULE_SUITE_TABS.some(function (t) { return t.key === key; }) ? key : 'call';
}

/** Switch tab: sync hash without a full route cycle, then re-render in place. */
async function scheduleSuiteSetTab(key) {
  var target = 'schedule-suite?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderScheduleSuite();
}

/** Load the tab's source module once; a loaded module keeps its function. */
async function ensureSuiteModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderScheduleSuite() {
  const content = document.getElementById('pageContent');
  const active = scheduleSuiteActiveTab();
  const tab = SCHEDULE_SUITE_TABS.find(function (t) { return t.key === active; }) || SCHEDULE_SUITE_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${SCHEDULE_SUITE_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="scheduleSuiteSetTab('${t.key}')">${t.label}</button>`;
      }).join('')}
    </div>
    <div id="suitePane"><div class="loading"><div class="loading-spinner"></div><span>Loading ${tab.label}…</span></div></div>
  `;

  const pane = document.getElementById('suitePane');
  try {
    await ensureSuiteModule(tab.module, tab.fn);
    const fn = window[tab.fn];
    if (typeof fn !== 'function') throw new Error('Suite module not available: ' + tab.module);
    await fn(pane);
  } catch (err) {
    if (pane) {
      pane.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">!</div>
          <div class="empty-state-title">Could not load ${tab.label}</div>
          <div class="empty-state-desc">${escapeHtml(err.message)}</div>
          <button class="btn btn-primary mt-3" onclick="renderScheduleSuite()">Retry</button>
        </div>`;
    }
  }
}
