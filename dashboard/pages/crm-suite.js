/**
 * CRM Suite — merged People / Contacts / Resident Roster / Audit Log (PR6).
 *
 * Delegates each tab to its original module's render function (loaded on first
 * use). Legacy hashes (people, contacts, resident-roster, crm-audit) redirect
 * here via LEGACY_REDIRECTS in app.js. No emoji.
 */

var CRM_SUITE_TABS = [
  { key: 'people',    label: 'People',    module: 'people.js',          fn: 'renderPeople' },
  { key: 'contacts',  label: 'Contacts',  module: 'contacts.js',        fn: 'renderContacts' },
  { key: 'residents', label: 'Residents', module: 'resident-roster.js', fn: 'renderResidentRoster' },
  { key: 'audit',     label: 'Audit',     module: 'crm-audit.js',       fn: 'renderCrmAudit' },
];

function crmSuiteActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return CRM_SUITE_TABS.some(function (t) { return t.key === key; }) ? key : 'people';
}

/** Switch tab: sync hash without a full route cycle, then re-render in place. */
async function crmSuiteSetTab(key) {
  var target = 'crm-suite?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderCrmSuite();
}

/** Load the tab's source module once; a loaded module keeps its function. */
async function ensureCrmModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderCrmSuite() {
  const content = document.getElementById('pageContent');
  const active = crmSuiteActiveTab();
  const tab = CRM_SUITE_TABS.find(function (t) { return t.key === active; }) || CRM_SUITE_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${CRM_SUITE_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="crmSuiteSetTab('${t.key}')">${t.label}</button>`;
      }).join('')}
    </div>
    <div id="suitePane"><div class="loading"><div class="loading-spinner"></div><span>Loading ${tab.label}…</span></div></div>
  `;

  const pane = document.getElementById('suitePane');
  try {
    await ensureCrmModule(tab.module, tab.fn);
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
          <button class="btn btn-primary mt-3" onclick="renderCrmSuite()">Retry</button>
        </div>`;
    }
  }
}
