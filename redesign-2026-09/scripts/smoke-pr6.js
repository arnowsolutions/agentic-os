// Smoke test: all three PR6 suites — tab parsing + delegation to #suitePane.
const fs = require('fs');
global.window = { location: { hash: '#x' } };
const els = {};
global.document = { getElementById: id => (els[id] = els[id] || { innerHTML: '', appendChild() {}, className: '' }) };
global.loadScript = async () => {};
global.escapeHtml = s => String(s);

const assert = (c, m) => { if (!c) { console.log('FAIL:', m); process.exit(1); } };
const P = '/workspace/agentic-os/dashboard/pages/';
let got = null, got2 = null, got3 = null;

// compliance-suite
eval(fs.readFileSync(P + 'compliance-suite.js', 'utf8'));
window.location.hash = '#compliance-suite';
assert(complianceSuiteActiveTab() === 'overview', 'compliance default tab');
window.location.hash = '#compliance-suite?tab=gme-tracker';
assert(complianceSuiteActiveTab() === 'gme-tracker', 'compliance gme-tracker tab');
window.location.hash = '#compliance-suite?tab=bogus';
assert(complianceSuiteActiveTab() === 'overview', 'compliance bogus → default');
window.renderCompliance = async t => { got = t; };
window.renderGmeTracker = async t => { got = t; };
window.renderEvalDashboard = async t => { got = t; };
window.location.hash = '#compliance-suite?tab=eval-dashboard';
renderComplianceSuite().then(() => {
  assert(got === els['suitePane'], 'compliance delegated to suitePane');
  assert(els['pageContent'].innerHTML.includes('Eval Portal') && els['pageContent'].innerHTML.includes('GME Deep Dive'), 'compliance tab row');

  // grand-rounds-hub
  eval(fs.readFileSync(P + 'grand-rounds-hub.js', 'utf8'));
  window.location.hash = '#grand-rounds-hub';
  assert(grHubActiveTab() === 'events', 'grhub default');
  window.location.hash = '#grand-rounds-hub?tab=attendance';
  assert(grHubActiveTab() === 'attendance', 'grhub attendance');
  window.location.hash = '#grand-rounds-hub?tab=invites';
  assert(grHubActiveTab() === 'invites', 'grhub invites');
  window.location.hash = '#grand-rounds-hub?tab=chief-meetings';
  assert(grHubActiveTab() === 'chief-meetings', 'grhub chief-meetings');
  window.renderConferenceEmail = async t => { got2 = t; };
  window.renderChiefMeetings = async t => { got2 = t; };
  window.location.hash = '#grand-rounds-hub?tab=invites';
  return renderGrandRoundsHub();
}).then(() => {
  assert(got2 === els['suitePane'], 'grhub delegated to suitePane');

  // crm-suite
  eval(fs.readFileSync(P + 'crm-suite.js', 'utf8'));
  window.location.hash = '#crm-suite';
  assert(crmSuiteActiveTab() === 'people', 'crm default');
  window.location.hash = '#crm-suite?tab=residents';
  assert(crmSuiteActiveTab() === 'residents', 'crm residents');
  window.location.hash = '#crm-suite?tab=nope';
  assert(crmSuiteActiveTab() === 'people', 'crm bogus → default');
  window.renderCrmAudit = async t => { got3 = t; };
  window.location.hash = '#crm-suite?tab=audit';
  return renderCrmSuite();
}).then(() => {
  assert(got3 === els['suitePane'], 'crm delegated to suitePane');

  // legacy map completeness
  const appjs = fs.readFileSync('/workspace/agentic-os/dashboard/app.js', 'utf8');
  for (const k of ["'compliance'", "'eval-portal'", "'eval-dashboard'", "'gme-tracker'", "'gme-detail'", "'grand-rounds'", "'grand-rounds-attendance'", "'conference-email'", "'chief-meetings'", "'people'", "'contacts'", "'resident-roster'", "'crm-audit'"])
    assert(appjs.includes(k + ':'), 'LEGACY_REDIRECTS has ' + k);
  console.log('SMOKE PASS: all three suites + legacy map');
});
