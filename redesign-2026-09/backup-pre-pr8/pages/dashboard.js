/* ═══════════════════════════════════════════════════════════════════════
   Dashboard — Launchpad
   See & launch everything on the VPS.
   Tier 1: service tiles from GET /api/crm/launchpad (data/launchpad.json,
           health-probed server-side, 60s cache).
   Tier 2: agent + cron strip (single row of pills).
   Tier 3: quick-actions rail (2-column list).
   No emoji. Previous dashboard content lives in pages/operations.js.
   ═══════════════════════════════════════════════════════════════════ */

async function renderDashboard() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Launchpad</h1>
        <p class="page-subtitle">Everything on the VPS — live status and one-click launch</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-sm" onclick="lpLoadServices(1)">Refresh Status</button>
        <button class="btn btn-sm" onclick="runQuickSkill()">Run Skill</button>
      </div>
    </div>
    <div id="lpServices"><div class="skeleton" style="height:120px"></div></div>
    <div id="lpStrip" class="lp-strip"><span class="lp-pill lp-pill-quiet">Loading agents &amp; cron…</span></div>
    <div id="lpActions"></div>
  `;
  lpLoadServices(0);
  lpLoadStrip();
  lpRenderQuickActions();
  lpScheduleRefresh();
}

/* ── Tier 1: service tiles ─────────────────────────────────────────── */

async function lpLoadServices(refresh = 0) {
  const host = document.getElementById('lpServices');
  if (!host) return;
  if (refresh) host.innerHTML = '<div class="skeleton" style="height:120px"></div>';
  const { data, error } = await api.fetchSafe('/api/crm/launchpad' + (refresh ? '?refresh=1' : ''), {}, 25000);
  if (!document.getElementById('lpServices')) return;   // navigated away
  if (error || !data) {
    host.innerHTML = `<div class="card"><div class="empty-state">` +
      `<div class="empty-state-icon">—</div>` +
      `<div class="empty-state-title">Launchpad unavailable</div>` +
      `<div class="empty-state-desc">${escapeHtml(error || 'No data returned')}</div>` +
      `<button class="btn btn-primary mt-3" onclick="lpLoadServices(1)">Retry</button></div></div>`;
    return;
  }
  const services = data.services || [];
  const up = services.filter(s => s.status && s.status.state === 'up').length;
  const checked = String(data.generated_at || '').replace('T', ' ').replace('Z', ' UTC');
  const byGroup = {};
  services.forEach(s => { (byGroup[s.group] = byGroup[s.group] || []).push(s); });
  let html = `<div class="lp-summary">${up}/${services.length} services up` +
    ` <span class="lp-sep">·</span> checked ${escapeHtml(checked)}` +
    ` <span class="lp-sep">·</span> auto-refresh ${data.ttl_seconds || 60}s</div>`;
  (data.groups || []).forEach(g => {
    const tiles = byGroup[g.id] || [];
    if (!tiles.length) return;
    const gup = tiles.filter(t => t.status && t.status.state === 'up').length;
    html += `<section class="lp-zone">` +
      `<div class="lp-zone-head">` +
        `<span class="lp-zone-label">${escapeHtml(g.label)}</span>` +
        `<span class="lp-zone-count">${gup}/${tiles.length} up</span>` +
      `</div>` +
      `<div class="lp-grid">${tiles.map(lpTileHtml).join('')}</div>` +
    `</section>`;
  });
  host.innerHTML = html;
}

function lpTileHtml(s) {
  const st = (s.status && s.status.state) || 'unknown';
  const lat = (s.status && typeof s.status.latency_ms === 'number') ? s.status.latency_ms + ' ms' : '';
  const tip = st === 'down' ? ((s.status && s.status.detail) || 'down') : st;
  return `<a class="lp-tile lp-tile-${st}" href="${escapeHtml(s.url || '#')}" target="_blank" rel="noopener" title="${escapeHtml(tip)}">` +
    `<div class="lp-tile-head">` +
      `<span class="lp-dot lp-dot-${st}"></span>` +
      `<span class="lp-tile-label">${escapeHtml(s.label || s.id || '')}</span>` +
      `<span class="lp-kind">${escapeHtml(s.kind || 'web')}</span>` +
    `</div>` +
    `<div class="lp-tile-desc">${escapeHtml(s.desc || '')}</div>` +
    `<div class="lp-tile-meta">` +
      `<span>${escapeHtml(s.host || '')}</span>` +
      (lat ? `<span class="lp-lat">${lat}</span>` : '') +
      `<span class="lp-launch">Launch ↗</span>` +
    `</div>` +
  `</a>`;
}

function lpScheduleRefresh() {
  if (window.__lpTimer) clearTimeout(window.__lpTimer);
  window.__lpTimer = setTimeout(async () => {
    if (!document.getElementById('lpServices')) return;   // navigated away
    await lpLoadServices(0);
    lpScheduleRefresh();
  }, 60000);
}

/* ── Tier 2: agents + cron strip ───────────────────────────────────── */

async function lpLoadStrip() {
  const host = document.getElementById('lpStrip');
  if (!host) return;
  const [statusR, cronR] = await Promise.all([
    api.fetchSafe('/api/status', {}, 12000),
    api.fetchSafe('/api/cron/jobs', {}, 18000),
  ]);
  if (!document.getElementById('lpStrip')) return;
  const pills = [];
  const agents = (statusR.data && statusR.data.agents) || [];
  agents.forEach(a => {
    const ok = a.status === 'online';
    pills.push(`<span class="lp-pill" title="Agent status"><span class="lp-dot lp-dot-${ok ? 'up' : 'down'}"></span>` +
      `${escapeHtml(a.name)} · ${ok ? 'online' : escapeHtml(a.status || 'offline')}</span>`);
  });
  const jobs = (cronR.data && cronR.data.jobs) || [];
  if (jobs.length) {
    const enabled = jobs.filter(j => j.enabled);
    const withNext = enabled
      .map(j => ({ name: j.name || j.id || 'cron job', at: lpWhen(j.next_run_at) }))
      .filter(j => j.at)
      .sort((a, b) => a.at.t - b.at.t)
      .slice(0, 3);
    pills.push(`<span class="lp-pill lp-pill-quiet">${enabled.length} cron jobs enabled</span>`);
    withNext.forEach(j => pills.push(
      `<span class="lp-pill"><span class="lp-next-glyph">▸</span>${escapeHtml(j.name)}` +
      ` <span class="lp-sep">·</span> <span class="lp-when">${escapeHtml(j.at.label)}</span></span>`));
    if (!withNext.length) pills.push('<span class="lp-pill lp-pill-quiet">next runs pending</span>');
  }
  host.innerHTML = pills.length ? pills.join('') : '<span class="lp-pill lp-pill-quiet">No data</span>';
}

function lpWhen(v) {
  if (v === null || v === undefined || v === '') return null;
  let t;
  if (typeof v === 'number') { t = v < 1e12 ? v * 1000 : v; }
  else { t = Date.parse(String(v)); if (isNaN(t)) return null; }
  const d = new Date(t);
  if (isNaN(d.getTime())) return null;
  let label;
  try { label = d.toLocaleString(undefined, { weekday: 'short', hour: 'numeric', minute: '2-digit' }); }
  catch { label = d.toISOString().slice(0, 16).replace('T', ' '); }
  return { t, label };
}

/* ── Tier 3: quick actions rail ────────────────────────────────────── */

function lpRenderQuickActions() {
  const host = document.getElementById('lpActions');
  if (!host) return;
  const links = [
    ['chat', 'AI Chat'], ['skills', 'Skills Hub'],
    ['scheduler', 'Scheduler'], ['calendar', 'Calendar'],
    ['manager', 'Command Center'], ['mass-email', 'Mass Email'],
    ['kanban', 'Kanban'], ['cost', 'Cost Analytics'],
    ['audit', 'Audit Log'], ['backups', 'Backups'],
    ['operations', 'Operations'], ['tools', 'My Tools'],
  ];
  host.innerHTML = `<div class="card"><div class="card-header"><span class="card-title">Quick Actions</span></div>` +
    `<div class="lp-actions">` +
    links.map(([p, l]) => `<button class="lp-action" onclick="navigate('${p}')"><span class="lp-action-glyph">▸</span>${l}</button>`).join('') +
    `</div></div>`;
}

/* ── Run Skill (shared modal) ──────────────────────────────────────── */

async function runQuickSkill() {
  showModal('Run Skill', `
    <div class="form-group">
      <label class="form-label">Skill</label>
      <select id="qrSkill" class="form-input">
        <option value="">Select a skill...</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Input (optional)</label>
      <textarea id="qrInput" class="form-textarea" rows="3" placeholder="Enter input for the skill..."></textarea>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
    <button class="btn btn-primary" onclick="executeQuickRun()">Run</button>
  `);
  try {
    const skills = await api.getSkills();
    const select = document.getElementById('qrSkill');
    skills.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.name;
      opt.textContent = s.name.replace(/-/g, ' ');
      select.appendChild(opt);
    });
  } catch {}
}

async function executeQuickRun() {
  const name = document.getElementById('qrSkill').value;
  const input = document.getElementById('qrInput').value;
  if (!name) { showToast('Please select a skill', 'warning'); return; }
  try {
    const r = await api.runSkill(name, input);
    closeModal();
    showToast(`"${name}" dispatched to ${r.agent} #${r.run_id}`, 'success');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}
