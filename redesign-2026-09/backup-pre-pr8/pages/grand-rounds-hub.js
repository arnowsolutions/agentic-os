/**
 * Grand Rounds Hub — merged Grand Rounds schedule manager + Attendance tracker (PR6).
 *
 * Delegates each tab to its original module's render function (loaded on first
 * use). Legacy hashes (grand-rounds, grand-rounds-attendance) redirect here via
 * LEGACY_REDIRECTS in app.js. No emoji.
 */

var GR_HUB_TABS = [
  { key: 'events',         label: 'Grand Rounds',   module: 'grand-rounds.js',            fn: 'renderGrandRounds' },
  { key: 'attendance',     label: 'Attendance',     module: 'grand-rounds-attendance.js', fn: 'renderGrandRoundsAttendance' },
  { key: 'invites',        label: 'Invites',        module: 'conference-email.js',        fn: 'renderConferenceEmail' },
  { key: 'chief-meetings', label: 'Chief Meetings', module: 'chief-meetings.js',          fn: 'renderChiefMeetings' },
];

function grHubActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return GR_HUB_TABS.some(function (t) { return t.key === key; }) ? key : 'events';
}

/** Switch tab: sync hash without a full route cycle, then re-render in place. */
async function grHubSetTab(key) {
  var target = 'grand-rounds-hub?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderGrandRoundsHub();
}

/** Load the tab's source module once; a loaded module keeps its function. */
async function ensureGrHubModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderGrandRoundsHub() {
  const content = document.getElementById('pageContent');
  const active = grHubActiveTab();
  const tab = GR_HUB_TABS.find(function (t) { return t.key === active; }) || GR_HUB_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${GR_HUB_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="grHubSetTab('${t.key}')">${t.label}</button>`;
      }).join('')}
    </div>
    <div id="suitePane"><div class="loading"><div class="loading-spinner"></div><span>Loading ${tab.label}…</span></div></div>
  `;

  const pane = document.getElementById('suitePane');
  try {
    await ensureGrHubModule(tab.module, tab.fn);
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
          <button class="btn btn-primary mt-3" onclick="renderGrandRoundsHub()">Retry</button>
        </div>`;
    }
  }
}
