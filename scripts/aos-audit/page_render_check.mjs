// Headless render check for the Agentic OS dashboard pages that changed.
// Run on the VPS:  NODE_PATH=/opt/webcapture/node_modules node page_render_check.mjs
import fs from 'fs';
import { chromium } from 'playwright';

const BASE = 'https://os.srv1738752.hstgr.cloud/dashboard/';
// The workspace is a docker volume: the host path differs from the in-container
// /workspace. Override with AOS_REPO when running somewhere else.
const REPO = process.env.AOS_REPO || '/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data/agentic-os';
const sessions = JSON.parse(fs.readFileSync(REPO + '/data/sessions.json', 'utf8'));
const entries = Object.entries(sessions).map(([tok, v]) => [v.created_at || '', tok]);
entries.sort((a, b) => (a[0] < b[0] ? 1 : -1));
const TOKEN = entries[0][1];

const CHECKS = [
  { hash: 'chief-meetings', must: ["Chief Residents' Meetings", 'Oct 16, 2026', 'John Hill (Chief)', 'Kick Off'], mustNot: ['Could not load'] },
  { hash: 'platforms',      must: ['reimb'], mustNot: [] },
  { hash: 'tools',          must: ['NotebookLM'], mustNot: ['undefined'] },
  { hash: 'mass-email',     must: ['Mass Email'], mustNot: [] },
  { hash: 'resident-letters', must: ['Resident Letters'], mustNot: [] },
  { hash: 'subi-exit-interviews', must: ['Sub-I'], mustNot: [] },
  { hash: 'workspace-suite', must: ['Files'], mustNot: ['not available in this environment'] },
  { hash: 'ai-builder-suite', must: [], mustNot: [] },
  { hash: 'crm-suite',       must: [], mustNot: [] },
  { hash: 'schedule-suite',  must: [], mustNot: [] },
  { hash: 'dashboard',       must: [], mustNot: ['undefined is not'] },
  { hash: 'today',          must: [], mustNot: [] },
  { hash: 'health',         must: [], mustNot: [] },
  { hash: 'health-suite',   must: [], mustNot: [] },
];

const browser = await chromium.launch({
  executablePath: '/root/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome',
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
});
const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
await ctx.addCookies([{ name: 'aos_session', value: TOKEN, domain: 'os.srv1738752.hstgr.cloud', path: '/', httpOnly: true, secure: true }]);

const results = [];
for (const c of CHECKS) {
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + String(e.message).slice(0, 160)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text().slice(0, 160)); });
  let text = '';
  try {
    await page.goto(BASE + '#' + c.hash, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForTimeout(4500);
    if (c.hash === 'mass-email') {
      // click the Chief Meetings sub-tab if present
      try {
        await page.getByText('Chief Meetings', { exact: false }).first().click({ timeout: 5000 });
        await page.waitForTimeout(2500);
      } catch (e) { errors.push('tab click: ' + String(e.message).slice(0, 80)); }
    }
    text = await page.evaluate(() => document.body.innerText || '');
  } catch (e) {
    errors.push('goto: ' + String(e.message).slice(0, 140));
  }
  const missing = c.must.filter((m) => !text.includes(m));
  const leaked = c.mustNot.filter((m) => text.includes(m));
  results.push({ hash: c.hash, chars: text.length, missing, leaked, errors: errors.slice(0, 4), sample: text.replace(/\s+/g, ' ').slice(0, 160) });
  await page.close();
}
await browser.close();

const bad = results.filter((r) => r.missing.length || r.leaked.length || r.errors.length);
console.log(JSON.stringify({ checked: results.length, problems: bad.length, results }, null, 1));
