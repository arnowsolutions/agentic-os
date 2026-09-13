// PR7 smoke test — AI Builder Suite + Workspace suite + colophon + redirects + nav.
// DOM-stub based (no browser): eval modules in a vm context where window === global.
'use strict';
const fs = require('fs');
const vm = require('vm');

const P = '/workspace/agentic-os/dashboard';
let fails = [];
const ok = (name, cond) => { console.log(`${cond ? 'PASS' : 'FAIL'}: ${name}`); if (!cond) fails.push(name); };

function makeEl(id) {
  return {
    id, _html: '',
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = v; },
    style: {}, className: '', textContent: '',
    classList: { add() {}, remove() {}, toggle() {} },
  };
}
function makeCtx(hash) {
  const e = {};
  const sandbox = {
    __els: e,
    location: { hash },
    document: { getElementById: (id) => (e[id] = e[id] || makeEl(id)) },
    history: { replaceState: (a, b, url) => { sandbox.location.hash = '#' + String(url).replace(/^#/, ''); } },
    Date, console,
    escapeHtml: (s) => String(s),
  };
  sandbox.window = sandbox;        // window IS the global (browser semantics)
  vm.createContext(sandbox);
  return sandbox;
}

const el = (ctx, id) => (ctx.__els[id] = ctx.__els[id] || makeEl(id));

const load = (ctx, file) =>
  vm.runInContext(fs.readFileSync(`${P}/pages/${file}`, 'utf8'), ctx, { filename: file });

// ── 1. Workspace suite ───────────────────────────────────────────────────────
{
  const ctx = makeCtx('#workspace-suite?tab=apps');
  load(ctx, 'workspace-suite.js');
  let got = null;
  ctx.renderGoogleStudio = async (pane) => { got = pane; };
  vm.runInContext('renderWorkspaceSuite()', ctx).then(() => {}, () => {});
  setTimeout(() => {
    ok('workspace: ?tab=apps → active apps', ctx.workspaceSuiteActiveTab() === 'apps');
    ok('workspace: delegation receives #suitePane', got === el(ctx, 'suitePane'));
    ok('workspace: 4 tabs rendered', (el(ctx, 'pageContent')._html.match(/class="tab[ "]/g) || []).length >= 4);
    ok('workspace: active class on apps tab', /tab active"[^>]*>Apps Script/.test(el(ctx, 'pageContent')._html));

    const c2 = makeCtx('#workspace-suite?tab=bogus');
    load(c2, 'workspace-suite.js');
    ok('workspace: bogus tab → files', c2.workspaceSuiteActiveTab() === 'files');

    const c3 = makeCtx('#workspace-suite');
    load(c3, 'workspace-suite.js');
    ok('workspace: no tab param → files', c3.workspaceSuiteActiveTab() === 'files');

    const c4 = makeCtx('#workspace-suite?tab=files');
    load(c4, 'workspace-suite.js');
    c4.renderWorkspaceSuite = async () => {};
    vm.runInContext("workspaceSuiteSetTab('coder')", c4).then(() => {}, () => {});
    setTimeout(() => {
      ok('workspace: setTab(coder) updates hash', c4.location.hash === '#workspace-suite?tab=coder');
      runAB();
    }, 10);
  }, 10);
}

// ── 2. AI Builder suite ──────────────────────────────────────────────────────
let abDone = false;
function runAB() {
  const ctx = makeCtx('#ai-builder-suite?tab=image');
  load(ctx, 'ai-builder-suite.js');
  vm.runInContext('renderAiBuilderSuite()', ctx).then(() => {}, () => {});
  setTimeout(() => {
    const html = el(ctx, 'suitePane')._html || '';
    ok('aibuilder: image tab embeds prompt-image.html', html.includes('prompt-image.html') && html.includes('suite-embed'));
    ok('aibuilder: ?tab=image active', ctx.aiBuilderSuiteActiveTab() === 'image');

    const c2 = makeCtx('#ai-builder-suite?tab=gallery');
    load(c2, 'ai-builder-suite.js');
    let got2 = null;
    c2.renderImageGallery = async (pane) => { got2 = pane; };
    vm.runInContext('renderAiBuilderSuite()', c2).then(() => {}, () => {});
    setTimeout(() => {
      ok('aibuilder: gallery delegates to renderImageGallery', got2 === el(c2, 'suitePane'));

      const c3 = makeCtx('#ai-builder-suite?tab=zzz');
      load(c3, 'ai-builder-suite.js');
      ok('aibuilder: ?tab=zzz → builder', c3.aiBuilderSuiteActiveTab() === 'builder');

      const c4 = makeCtx('#ai-builder-suite?tab=video');
      load(c4, 'ai-builder-suite.js');
      vm.runInContext('renderAiBuilderSuite()', c4).then(() => {}, () => {});
      setTimeout(() => {
        ok('aibuilder: video tab embeds prompt-video.html', (el(c4, 'suitePane')._html || '').includes('prompt-video.html'));
        abDone = true;
      }, 10);
    }, 10);
  }, 10);
}

// ── 3. Colophon ──────────────────────────────────────────────────────────────
function runColophon() {
  const ctx = makeCtx('#colophon');
  load(ctx, 'colophon.js');
  vm.runInContext('renderColophon()', ctx).then(() => {}, () => {});
  setTimeout(() => {
    const html = el(ctx, 'pageContent')._html || '';
    ok('colophon: renders ledger with PR7', html.includes('Redesign ledger') && html.includes('PR7'));
    const WL = new Set(['\u2713','\u2715','\u21bb','\u2315','\u25cf','\u25d0','\u25b8','\u25a3','\u25c6','\u25cb','\u25a4','\u25a6','\u2197','\u2191','\u2193','\u2192']);
    const bad = [...html].filter(c => /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(c) && !WL.has(c));
    ok('colophon: no emoji (approved glyphs allowed)', bad.length === 0);
  }, 10);
}

// ── 4. LEGACY_REDIRECTS in app.js ────────────────────────────────────────────
function checkRedirects() {
  const src = fs.readFileSync(`${P}/app.js`, 'utf8');
  const m = src.match(/const LEGACY_REDIRECTS = \{([\s\S]*?)\n\};/);
  ok('app.js: LEGACY_REDIRECTS block found', !!m);
  const body = m ? m[1] : '';
  const expect = {
    "ai-builder": "ai-builder-suite?tab=builder",
    "prompt-tools-image": "ai-builder-suite?tab=image",
    "prompt-tools-video": "ai-builder-suite?tab=video",
    "image-gallery": "ai-builder-suite?tab=gallery",
    "file-browser": "workspace-suite?tab=files",
    "script-runner": "workspace-suite?tab=scripts",
    "vs-coder": "workspace-suite?tab=coder",
    "google-studio": "workspace-suite?tab=apps",
  };
  for (const [k, v] of Object.entries(expect)) {
    const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp(`'${esc(k)}'\\s*:\\s*'${esc(v)}'`);
    ok(`redirect ${k} → ${v}`, re.test(body));
  }
}

// ── 5. utils v5 nav sanity ───────────────────────────────────────────────────
function checkNav() {
  const t = fs.readFileSync('/tmp/utils-v5.js', 'utf8');
  ok('nav: ai-builder-suite row', t.includes("page: 'ai-builder-suite'"));
  ok('nav: workspace-suite row', t.includes("page: 'workspace-suite'"));
  ok('nav: colophon row', t.includes("page: 'colophon'"));
  ok('nav: old ai-builder row gone (hidden only)', (t.match(/page: 'ai-builder',/g) || []).length === 1);
  ok('nav: trays removed', !t.includes("'Media & prompts'") && !t.includes("'Dev environment'"));
}

// ── run ──────────────────────────────────────────────────────────────────────
setTimeout(() => {
  checkRedirects();
  checkNav();
  runColophon();
}, 30);

const wait = setInterval(() => {
  if (abDone) {
    clearInterval(wait);
    setTimeout(() => {
      console.log(fails.length ? `\nSMOKE FAIL — ${fails.length} issue(s)` : '\nSMOKE PASS: all PR7 checks green');
      process.exit(fails.length ? 1 : 0);
    }, 60);
  }
}, 20);
setTimeout(() => { console.log('TIMEOUT'); process.exit(2); }, 6000);
