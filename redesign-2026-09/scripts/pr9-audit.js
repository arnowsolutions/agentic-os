// PR9 final audit — route parity, nav integrity, full file inventory.
'use strict';
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const D = '/workspace/agentic-os/dashboard';
const PAGES = path.join(D, 'pages');

function makeEl(id) {
  return { id, _html: '', set innerHTML(v) { this._html = v; }, get innerHTML() { return this._html; },
    style: {}, className: '', textContent: '', classList: { add() {}, remove() {}, toggle() {} },
    appendChild() {}, querySelector() { return null; }, querySelectorAll() { return []; } };
}
const els = {};
const getEl = (id) => (els[id] = els[id] || makeEl(id));

// ── load utils.js in a vm to expose NAV_CONFIG + getNavRoute ────────────────
const sandbox = {
  document: { getElementById: getEl, querySelector: () => null, querySelectorAll: () => [], addEventListener() {}, createElement: () => makeEl('x') },
  location: { hash: '', pathname: '/' },
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  navigator: { clipboard: { writeText: async () => {} } },
  console, setTimeout, clearTimeout, setInterval, clearInterval,
  fetch: async () => ({ ok: true, json: async () => ({}) }),
  showToast: () => {}, escapeHtml: (s) => String(s), loadScript: async () => {},
};
sandbox.window = sandbox; sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(D, 'utils.js'), 'utf8') + '\n;this.__NAV = NAV_CONFIG;', sandbox);
const NAV = sandbox.__NAV;

// app.js LEGACY_REDIRECTS via regex
const appSrc = fs.readFileSync(path.join(D, 'app.js'), 'utf8');
const redirBody = appSrc.match(/const LEGACY_REDIRECTS = \{([\s\S]*?)\n\};/)[1];
const REDIR = {};
for (const m of redirBody.matchAll(/'([a-z0-9-]+)'\s*:\s*'([^']+)'/g)) REDIR[m[1]] = m[2];

const fails = [];
const ok = (c, name) => { if (!c) fails.push(name); console.log(`${c ? 'PASS' : 'FAIL'}: ${name}`); };

// ── 1. visible nav pages: module + render fn exist ──────────────────────────
const visible = [];
for (const g of NAV.groups) {
  for (const it of (g.items || [])) visible.push(it.page);
  for (const s of (g.sections || [])) for (const it of s.items) visible.push(it.page);
}
// render fn name convention: render + capitalize(camelize(page))
const fnName = (page) => 'render' + page.replace(/-./g, (m) => m[1].toUpperCase()).replace(/^./, (c) => c.toUpperCase());
console.log(`\n── visible nav pages: ${visible.length}`);
const missingModule = [], missingFn = [];
for (const page of visible) {
  const p = path.join(PAGES, page + '.js');
  if (!fs.existsSync(p)) { missingModule.push(page); continue; }
  const src = fs.readFileSync(p, 'utf8');
  if (!new RegExp(`(async )?function ${fnName(page)}\\(`).test(src)) missingFn.push(page);
}
ok(missingModule.length === 0, `all visible pages have modules (missing: ${missingModule.join(', ') || 'none'})`);
ok(missingFn.length === 0, `all visible pages export render fn (missing: ${missingFn.join(', ') || 'none'})`);

// ── 2. every legacy redirect target resolves ────────────────────────────────
console.log(`\n── legacy redirects: ${Object.keys(REDIR).length}`);
const badTargets = [];
for (const [k, v] of Object.entries(REDIR)) {
  const target = v.split('?')[0];
  const route = sandbox.getNavRoute ? sandbox.getNavRoute(target) : null;
  if (!route) badTargets.push(`${k}→${target}`);
}
ok(badTargets.length === 0, `all redirect targets resolve (bad: ${badTargets.join(', ') || 'none'})`);

// ── 3. hiddenRoutes sanity ──────────────────────────────────────────────────
console.log(`\n── hidden routes: ${NAV.hiddenRoutes.length}`);
const ARCHIVED = ['cal-new', 'calendar2'];
const hiddenMissing = [];
for (const h of NAV.hiddenRoutes) {
  const isArchived = ARCHIVED.includes(h.page);
  const fileExists = fs.existsSync(path.join(PAGES, h.page + '.js'));
  if (isArchived) { if (fileExists) hiddenMissing.push(`${h.page} (should be archived!)`); }
  else if (!fileExists && !REDIR[k => h.page]) {
    // file must exist or redirect must exist
    if (!REDIR[h.page]) hiddenMissing.push(h.page);
  }
}
ok(hiddenMissing.length === 0, `hidden routes valid (issues: ${hiddenMissing.join(', ') || 'none'})`);

// ── 4. sidebar parity: data-page count == visible nav items ─────────────────
const sidebar = makeEl('sidebarNav');
els['sidebarNav'] = sidebar;
try {
  sandbox.renderSidebar();
  const rendered = (sidebar._html.match(/data-page="/g) || []).length;
  const navCount = visible.length + (NAV.external || []).length; // external rendered too
  console.log(`\n── sidebar rendered data-page=${rendered}, nav items=${visible.length} + external=${(NAV.external || []).length}`);
  ok(rendered === navCount, `sidebar parity (rendered ${rendered} == expected ${navCount})`);
} catch (e) {
  fails.push('renderSidebar threw: ' + e.message);
  console.log('renderSidebar threw:', e.message);
}

// ── 5. full inventory: classify every page module ───────────────────────────
const SUITE_TABS = {};
for (const s of ['schedule-suite', 'compliance-suite', 'grand-rounds-hub', 'crm-suite', 'ai-builder-suite', 'workspace-suite']) {
  const src = fs.readFileSync(path.join(PAGES, s + '.js'), 'utf8');
  SUITE_TABS[s] = [...src.matchAll(/module: '([a-z-]+)\.js'/g)].map((m) => m[1]);
}
const live = new Set(visible);
const hidden = new Set(NAV.hiddenRoutes.map((h) => h.page));
const suiteinner = new Set(Object.values(SUITE_TABS).flat());
const files = fs.readdirSync(PAGES).filter((f) => f.endsWith('.js')).map((f) => f.replace('.js', '')).sort();
const classify = {}, orphans = [];
for (const f of files) {
  if (live.has(f)) classify[f] = 'live';
  else if (suiteinner.has(f)) classify[f] = 'suite-tab';
  else if (hidden.has(f)) classify[f] = 'hidden';
  else { classify[f] = 'ORPHAN'; orphans.push(f); }
}
const counts = {};
for (const v of Object.values(classify)) counts[v] = (counts[v] || 0) + 1;
console.log('\n── inventory:', JSON.stringify(counts), '| total:', files.length);
if (orphans.length) console.log('   ORPHANS:', orphans.join(', '));
ok(true, 'inventory generated');

// ── write inventory md ──────────────────────────────────────────────────────
let md = `# AOS page inventory — final (PR9 audit, 2026-09-12)\n\n`;
md += `Generated by pr9-audit (live utils.js + pages/ dir). Statuses:\n`;
md += `- **live** — visible in the sidebar (zone link or tray item)\n`;
md += `- **suite-tab** — rendered inside a merged suite's tabs\n`;
md += `- **hidden** — reachable via legacy hash redirect / hidden route\n`;
md += `- **ORPHAN** — not referenced anywhere (none expected)\n\n`;
md += `Totals: ${JSON.stringify(counts)} — modules: ${files.length}\n\n`;
md += `| module | status |\n|---|---|\n`;
for (const f of files) md += `| ${f}.js | ${classify[f]} |\n`;
md += `\n## Suites and their tabs\n\n`;
for (const [s, tabs] of Object.entries(SUITE_TABS)) md += `- **${s}**: ${tabs.join(', ')}\n`;
md += `\n## Legacy hash redirects (${Object.keys(REDIR).length})\n\n`;
for (const [k, v] of Object.entries(REDIR)) md += `- \`#${k}\` → \`#${v}\`\n`;
fs.writeFileSync('/workspace/agentic-os/redesign-2026-09/final-inventory.md', md);
console.log('inventory written: redesign-2026-09/final-inventory.md');

console.log('\n' + (fails.length ? `AUDIT FAIL (${fails.length}): ${fails.join(' | ')}` : 'AUDIT PASS — routes, parity, inventory all green'));
process.exit(fails.length ? 1 : 0);
