/**
 * Health Suite — merged System Health / System Overview / Operations /
 * Agent Health into one tabbed page (2026-09 SSOT redesign, stage 3).
 *
 * Same delegation pattern as compliance-suite.js: legacy hashes
 * (#health, #system-overview, #operations, #agent-health) redirect here
 * via LEGACY_REDIRECTS in app.js. Modules are loaded unmodified and
 * render into #suitePane (target-parameter support added this pass).
 */

var HEALTH_SUITE_TABS = [
  { key: 'services', label: 'Services',    module: 'health.js',          fn: 'renderHealth' },
  { key: 'overview', label: 'Overview',    module: 'system-overview.js', fn: 'renderSystemOverview' },
  { key: 'metrics',  label: 'Operations',  module: 'operations.js',      fn: 'renderOperations' },
  { key: 'agents',   label: 'Agents',      module: 'agent-health.js',    fn: 'renderAgentHealth' },
];

function healthSuiteActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return HEALTH_SUITE_TABS.some(function (t) { return t.key === key; }) ? key : 'services';
}

async function healthSuiteSetTab(key) {
  var target = 'health-suite?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderHealthSuite();
}

async function ensureHealthModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderHealthSuite() {
  const content = document.getElementById('pageContent');
  const active = healthSuiteActiveTab();
  const tab = HEALTH_SUITE_TABS.find(function (t) { return t.key === active; }) || HEALTH_SUITE_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${HEALTH_SUITE_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="healthSuiteSetTab('${t.key}')">${t.label}</button>`;
      }).join('')}
    </div>
    <div id="suitePane"><div class="loading"><div class="loading-spinner"></div><span>Loading ${tab.label}…</span></div></div>
  `;

  const pane = document.getElementById('suitePane');
  try {
    await ensureHealthModule(tab.module, tab.fn);
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
          <button class="btn btn-primary mt-3" onclick="renderHealthSuite()">Retry</button>
        </div>`;
    }
  }
}
