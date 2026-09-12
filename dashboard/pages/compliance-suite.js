/**
 * Compliance Suite — merged Overview / Eval Portal / Eval Dashboard / GME Tracker / GME Deep Dive (PR6).
 *
 * Delegates each tab to its original module's render function (loaded on first
 * use). Legacy hashes (compliance, eval-portal, eval-dashboard, gme-tracker,
 * gme-detail) redirect here via LEGACY_REDIRECTS in app.js. No emoji.
 */

var COMPLIANCE_SUITE_TABS = [
  { key: 'overview',       label: 'Overview',       module: 'compliance.js',      fn: 'renderCompliance' },
  { key: 'eval-portal',    label: 'Eval Portal',    module: 'eval-portal.js',     fn: 'renderEvalPortal' },
  { key: 'eval-dashboard', label: 'Eval Dashboard', module: 'eval-dashboard.js',  fn: 'renderEvalDashboard' },
  { key: 'gme-tracker',    label: 'GME Tracker',    module: 'gme-tracker.js',     fn: 'renderGmeTracker' },
  { key: 'gme-detail',     label: 'GME Deep Dive',  module: 'gme-detail.js',      fn: 'renderGmeDetail' },
];

function complianceSuiteActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return COMPLIANCE_SUITE_TABS.some(function (t) { return t.key === key; }) ? key : 'overview';
}

/** Switch tab: sync hash without a full route cycle, then re-render in place. */
async function complianceSuiteSetTab(key) {
  var target = 'compliance-suite?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderComplianceSuite();
}

/** Load the tab's source module once; a loaded module keeps its function. */
async function ensureComplianceModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderComplianceSuite() {
  const content = document.getElementById('pageContent');
  const active = complianceSuiteActiveTab();
  const tab = COMPLIANCE_SUITE_TABS.find(function (t) { return t.key === active; }) || COMPLIANCE_SUITE_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${COMPLIANCE_SUITE_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="complianceSuiteSetTab('${t.key}')">${t.label}</button>`;
      }).join('')}
    </div>
    <div id="suitePane"><div class="loading"><div class="loading-spinner"></div><span>Loading ${tab.label}…</span></div></div>
  `;

  const pane = document.getElementById('suitePane');
  try {
    await ensureComplianceModule(tab.module, tab.fn);
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
          <button class="btn btn-primary mt-3" onclick="renderComplianceSuite()">Retry</button>
        </div>`;
    }
  }
}
