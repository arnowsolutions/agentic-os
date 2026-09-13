/**
 * Workspace Suite — merged Files / Scripts / VS Coder / Apps Script (PR7).
 *
 * The four legacy pages (#file-browser, #script-runner, #vs-coder,
 * #google-studio) render as tabs here. Each tab delegates to its original
 * module's render function (loaded on first use) — the modules stay
 * single-sourced, so the suite adds zero duplicated logic. Legacy hashes
 * redirect here via LEGACY_REDIRECTS in app.js and land on the matching tab.
 *
 * Tab state lives in the hash: #workspace-suite?tab=files|scripts|coder|apps,
 * so tabs are linkable, survive refresh, and back/forward keeps the final tab.
 * No emoji.
 */

var WORKSPACE_SUITE_TABS = [
  { key: 'files',   label: 'Files',       module: 'file-browser.js',  fn: 'renderFileBrowser' },
  { key: 'scripts', label: 'Scripts',     module: 'script-runner.js', fn: 'renderScriptRunner' },
  { key: 'coder',   label: 'VS Coder',    module: 'vs-coder.js',      fn: 'renderVsCoder' },
  { key: 'apps',    label: 'Apps Script', module: 'google-studio.js', fn: 'renderGoogleStudio' },
];

function workspaceSuiteActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return WORKSPACE_SUITE_TABS.some(function (t) { return t.key === key; }) ? key : 'files';
}

/** Switch tab: sync hash without a full route cycle, then re-render in place. */
async function workspaceSuiteSetTab(key) {
  var target = 'workspace-suite?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderWorkspaceSuite();
}

/** Load the tab's source module once; a loaded module keeps its function. */
async function ensureSuiteModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderWorkspaceSuite() {
  const content = document.getElementById('pageContent');
  const active = workspaceSuiteActiveTab();
  const tab = WORKSPACE_SUITE_TABS.find(function (t) { return t.key === active; }) || WORKSPACE_SUITE_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${WORKSPACE_SUITE_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="workspaceSuiteSetTab('${t.key}')">${t.label}</button>`;
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
          <button class="btn btn-primary mt-3" onclick="renderWorkspaceSuite()">Retry</button>
        </div>`;
    }
  }
}
