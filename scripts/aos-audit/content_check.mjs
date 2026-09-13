// Focused content check: do the DB-driven panels actually show the new data?
import fs from 'fs';
import { chromium } from 'playwright';

const BASE = 'https://os.srv1738752.hstgr.cloud/dashboard/';
const REPO = process.env.AOS_REPO || '/var/lib/docker/volumes/hermes-webui-gsga_hermes-workspace/_data/agentic-os';
const sessions = JSON.parse(fs.readFileSync(REPO + '/data/sessions.json', 'utf8'));
const entries = Object.entries(sessions).map(([tok, v]) => [v.created_at || '', tok]).sort((a, b) => (a[0] < b[0] ? 1 : -1));
const TOKEN = entries[0][1];

const browser = await chromium.launch({
  executablePath: '/root/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome',
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
});
const ctx = await browser.newContext({ viewport: { width: 1440, height: 1200 } });
await ctx.addCookies([{ name: 'aos_session', value: TOKEN, domain: 'os.srv1738752.hstgr.cloud', path: '/', httpOnly: true, secure: true }]);
const out = {};

async function grab(hash, fn) {
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message).slice(0, 140)));
  await page.goto(BASE + '#' + hash, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(5000);
  const res = fn ? await fn(page) : {};
  out[hash] = { ...res, errors };
  await page.close();
}

// chief-meetings: table rows + attendee chips
await grab('chief-meetings', async (page) => {
  const t = (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ');
  const i = t.indexOf("Chief Residents' Meetings");
  return {
    slice: t.slice(i, i + 480),
    rows: await page.evaluate(() => document.querySelectorAll('table tbody tr').length),
    chips: await page.evaluate(() => document.querySelectorAll('.tag').length),
  };
});

// platforms: the reimbursement panel should now hold real audit rows
await grab('platforms', async (page) => {
  const panel = await page.evaluate(() => {
    const el = document.getElementById('body-reimbursement');
    return el ? el.innerText : '(panel #body-reimbursement not found)';
  });
  return { slice: String(panel).replace(/\s+/g, ' ').slice(0, 420) };
});

// tools: NotebookLM panels per profile
await grab('tools', async (page) => {
  const t = (await page.evaluate(() => document.body.innerText)).replace(/\s+/g, ' ');
  const i = t.indexOf('NotebookLM');
  return { slice: t.slice(Math.max(0, i - 60), i + 420) };
});

// mass-email → click the Chief Meetings tab, then read the inline table
await grab('mass-email', async (page) => {
  const clicked = await page.evaluate(() => {
    const els = [...document.querySelectorAll('button, a, div, span')];
    const el = els.find((e) => (e.textContent || '').trim() === 'Chief Meetings' && e.offsetParent !== null);
    if (el) { el.click(); return true; }
    return false;
  });
  await page.waitForTimeout(4000);
  const pane = await page.evaluate(() => {
    const el = document.getElementById('massEmailBody');
    return el ? el.innerText : '(pane #massEmailBody not found)';
  });
  const t = String(pane).replace(/\s+/g, ' ');
  return { clicked, slice: t.slice(0, 460) };
});

await browser.close();
fs.writeFileSync(REPO + '/scripts/aos-audit/content-report.json', JSON.stringify(out, null, 1));
console.log('written');
