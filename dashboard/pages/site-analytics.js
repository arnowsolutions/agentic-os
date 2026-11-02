/* ═══════════════════════════════════════════════════════════════════════
   Site Traffic — every site tracked in the self-hosted Umami instance.
   Live numbers via /api/site-analytics. Nothing here is stored or hardcoded:
   every value comes from the API on render, so the page cannot drift.
   ═══════════════════════════════════════════════════════════════════════ */

const SITE_ANALYTICS_URL = 'https://analytics.srv1738752.hstgr.cloud';
let _saChart = null;
let _saDays = 30;
let _saSite = null;
let _saSites = [];

async function renderSiteAnalytics() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Site Traffic</h1>
        <p class="page-subtitle" id="saSubtitle">Visitors, sources and leads across the sites you track</p>
      </div>
      <div class="btn-group">
        <button class="btn btn-sm" id="saRange7" onclick="saSetRange(7)">7d</button>
        <button class="btn btn-sm" id="saRange30" onclick="saSetRange(30)">30d</button>
        <button class="btn btn-sm" id="saRange90" onclick="saSetRange(90)">90d</button>
        <a class="btn btn-sm" href="${SITE_ANALYTICS_URL}" target="_blank" rel="noopener">Open Umami</a>
      </div>
    </div>
    <div class="btn-group" id="saSites" style="margin-bottom:18px"></div>
    <div id="saBody"><div class="loading"><div class="loading-spinner"></div><span>Loading traffic…</span></div></div>
  `;

  try {
    const s = await api.get('/api/site-analytics/sites', 15000);
    _saSites = (s && s.sites) || [];
  } catch (e) {
    _saSites = [];
  }
  if (!_saSites.length) _saSites = [{ key: 'arnow', name: 'Arnow Solutions', domain: 'arnowsolutions.com' }];
  if (!_saSite || !_saSites.some(s => s.key === _saSite)) _saSite = _saSites[0].key;

  saRenderSiteTabs();
  saHighlightRange();
  await saLoad();
}

function saSetSite(key) {
  _saSite = key;
  saRenderSiteTabs();
  saLoad();
}

function saRenderSiteTabs() {
  const host = document.getElementById('saSites');
  const sub = document.getElementById('saSubtitle');
  const active = _saSites.find(s => s.key === _saSite) || {};
  if (sub) sub.textContent = active.domain
    ? `${active.domain} — who is visiting, from where, and what they do`
    : 'Visitors, sources and leads across the sites you track';
  if (!host) return;
  host.innerHTML = _saSites.length > 1
    ? _saSites.map(s => `<button class="btn btn-sm ${s.key === _saSite ? 'btn-primary' : ''}"
        onclick="saSetSite('${s.key}')">${escapeHtml(s.name)}</button>`).join('')
    : '';
}

function saSetRange(days) {
  _saDays = days;
  saHighlightRange();
  saLoad();
}

function saHighlightRange() {
  [7, 30, 90].forEach(d => {
    const b = document.getElementById('saRange' + d);
    if (b) b.classList.toggle('btn-primary', d === _saDays);
  });
}

function saNum(n) { return (n || 0).toLocaleString('en-US'); }

function saDelta(now, prev) {
  if (!prev) return '<div class="stat-change" style="color:var(--text-muted)">no prior data</div>';
  const pct = Math.round(((now - prev) / prev) * 100);
  if (!isFinite(pct) || pct === 0) return '<div class="stat-change" style="color:var(--text-muted)">no change</div>';
  const up = pct > 0;
  return `<div class="stat-change" style="color:${up ? 'var(--green)' : 'var(--red)'}">`
       + `${up ? '▲' : '▼'} ${Math.abs(pct)}% vs prev</div>`;
}

function saBars(rows, emptyLabel) {
  if (!rows || !rows.length) return `<div class="text-muted" style="padding:12px 0">${emptyLabel}</div>`;
  const max = Math.max(...rows.map(r => r.value), 1);
  return rows.map(r => `
    <div style="margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px">
        <span title="${escapeHtml(r.label || 'direct')}">${escapeHtml(r.label || 'direct')}</span>
        <span class="text-muted">${saNum(r.value)}</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" style="width:${Math.round((r.value / max) * 100)}%"></div></div>
    </div>`).join('');
}

async function saLoad() {
  const host = document.getElementById('saBody');
  if (!host) return;
  const site = _saSites.find(s => s.key === _saSite) || {};
  try {
    const d = await api.get(`/api/site-analytics/overview?site=${encodeURIComponent(_saSite)}&days=${_saDays}`, 20000);
    const t = d.totals || {};
    const c = d.comparison || {};

    if (!t.visitors) {
      host.innerHTML = `
        <div class="card">
          <div class="empty-state" style="padding:48px 20px">
            <div class="empty-state-title">No visitors in the last ${_saDays} days</div>
            <div class="empty-state-desc">Tracking is installed and running on ${escapeHtml(site.domain || 'this site')}.
              Numbers appear here as soon as someone lands on it.</div>
            <a class="btn btn-primary mt-3" href="${SITE_ANALYTICS_URL}" target="_blank" rel="noopener">Open Umami</a>
          </div>
        </div>`;
      return;
    }

    host.innerHTML = `
      <div class="grid grid-4 mb-4" id="saStats">
        <div class="card stat-card">
          <div class="stat-icon"></div>
          <div class="stat-label">Visitors</div>
          ${saDelta(t.visitors, c.visitors)}
          <div class="stat-value">${saNum(t.visitors)}</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon"></div>
          <div class="stat-label">Pageviews</div>
          ${saDelta(t.pageviews, c.pageviews)}
          <div class="stat-value">${saNum(t.pageviews)}</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon"></div>
          <div class="stat-label">Leads</div>
          <div class="stat-change" style="color:var(--text-muted)">${t.lead_rate}% of visitors</div>
          <div class="stat-value">${saNum(t.leads)}</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon"></div>
          <div class="stat-label">Bounce rate</div>
          <div class="stat-change" style="color:var(--text-muted)">${Math.round(t.avg_seconds)}s avg · ${t.active_now} on site now</div>
          <div class="stat-value">${t.bounce_rate}%</div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header"><span class="card-title">Traffic over time</span>
          <span class="text-muted" style="font-size:12px">last ${_saDays} days</span></div>
        <div class="chart-container" style="height:260px"><canvas id="saChart"></canvas></div>
      </div>

      <div class="grid grid-2 mb-4">
        <div class="card">
          <div class="card-header"><span class="card-title">Top pages</span></div>
          ${saBars(d.top_pages, 'No page views yet.')}
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Where they came from</span></div>
          ${saBars(d.sources, 'All visits were direct — no referrer recorded.')}
        </div>
      </div>

      <div class="grid grid-3 mb-4">
        <div class="card"><div class="card-header"><span class="card-title">Countries</span></div>
          ${saBars(d.countries, 'No location data yet.')}</div>
        <div class="card"><div class="card-header"><span class="card-title">Devices</span></div>
          ${saBars(d.devices, 'No device data yet.')}</div>
        <div class="card"><div class="card-header"><span class="card-title">Browsers</span></div>
          ${saBars(d.browsers, 'No browser data yet.')}</div>
      </div>

      <div class="card">
        <div class="card-header"><span class="card-title">Recent activity</span>
          <span class="text-muted" style="font-size:12px">${d.recent.length} most recent</span></div>
        <div class="table-wrapper">
          <table>
            <thead><tr><th>When</th><th>Page</th><th>Source</th><th>Location</th><th>Device</th><th>Event</th></tr></thead>
            <tbody>
              ${d.recent.map(r => `
                <tr>
                  <td class="text-muted" style="white-space:nowrap">${saWhen(r.when)}</td>
                  <td>${escapeHtml(r.path || '/')}</td>
                  <td>${escapeHtml(r.source || 'direct')}</td>
                  <td>${escapeHtml([r.city, r.country].filter(Boolean).join(', ') || '—')}</td>
                  <td>${escapeHtml([r.device, r.browser].filter(Boolean).join(' · ') || '—')}</td>
                  <td>${r.event ? `<strong>${escapeHtml(r.event)}</strong>` : '<span class="text-muted">pageview</span>'}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    saDrawChart(d);
  } catch (err) {
    host.innerHTML = `
      <div class="card"><div class="empty-state" style="padding:40px 20px">
        <div class="empty-state-title">Could not load traffic</div>
        <div class="empty-state-desc">${escapeHtml(err.message || 'Unknown error')}</div>
        <button class="btn btn-primary mt-3" onclick="saLoad()">Try again</button>
      </div></div>`;
  }
}

function saWhen(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return '—';
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function saDrawChart(d) {
  const canvas = document.getElementById('saChart');
  if (!canvas) return;
  if (typeof Chart === 'undefined') {
    // Chart.js loads async from a CDN; try once more shortly.
    setTimeout(() => { if (typeof Chart !== 'undefined') saDrawChart(d); }, 1200);
    return;
  }
  const labels = (d.trend || []).map(p => p.date.slice(5));
  const views = (d.trend || []).map(p => p.pageviews);
  const visitors = (d.sessions_trend || []).map(p => p.visitors);

  if (_saChart) { _saChart.destroy(); _saChart = null; }
  _saChart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Pageviews', data: views, borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.12)',
          fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2 },
        { label: 'Visitors', data: visitors, borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.10)',
          fill: false, tension: 0.35, pointRadius: 0, borderWidth: 2 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { color: '#94a3b8', boxWidth: 12 } } },
      scales: {
        x: { grid: { color: 'rgba(148,163,184,0.12)' }, ticks: { color: '#94a3b8', maxTicksLimit: 10 } },
        y: { beginAtZero: true, grid: { color: 'rgba(148,163,184,0.12)' }, ticks: { color: '#94a3b8', precision: 0 } },
      },
    },
  });
}
