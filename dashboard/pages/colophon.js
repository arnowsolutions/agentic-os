/**
 * Colophon (PR7) — production notes for the Agentic OS dashboard:
 * identity, redesign ledger, deployment mechanics and the design system.
 * A colophon is the page at the end of a book with its production details;
 * this is the same idea for the dashboard. Static, no emoji.
 */

async function renderColophon() {
  const content = document.getElementById('pageContent');

  const LEDGER = [
    ['PR1', 'Chrome cleanup + gate fixes (logo, rogue links, cache-bust)', '2026-09-12'],
    ['PR2', 'Navigation zones v3 — Home · Work · Build · System + trays', '2026-09-12'],
    ['PR3', 'Launchpad home — live VPS service grid (/api/crm/launchpad)', '2026-09-12'],
    ['PR4', 'Visual pass 1 — card weight, stat strips, table rhythm', '2026-09-12'],
    ['PR5', 'Schedule Suite + canonical Calendar (2 dupes retired)', '2026-09-12'],
    ['PR6', 'Compliance Suite · Grand Rounds Hub · CRM suite', '2026-09-12'],
    ['PR7', 'AI Builder Suite · Workspace suite · Colophon', '2026-09-12'],
    ['PR8', 'Full emoji sweep · light-mode hardening · mobile nav', '2026-09-12'],
    ['PR9', 'Cleanup — archive dupes, parity checks, final audit', '2026-09-12'],
  ];

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Colophon</div>
        <div class="page-subtitle">Production notes — identity, redesign ledger & deployment mechanics</div>
      </div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <h3 style="font-size:13px;font-weight:600;margin-bottom:10px">Identity</h3>
      <div class="table-wrapper">
        <table>
          <tbody>
            <tr><td style="width:180px;color:var(--text-muted)">System</td><td>Agentic OS — control plane for the Hermes workspace & VPS services</td></tr>
            <tr><td style="color:var(--text-muted)">Runtime</td><td>FastAPI backend (server.py) + dependency-free JS SPA — no build step</td></tr>
            <tr><td style="color:var(--text-muted)">License</td><td>MIT</td></tr>
            <tr><td style="color:var(--text-muted)">Upstream</td><td><a href="https://github.com/modimihir07/agentic-os" target="_blank" rel="noopener">github.com/modimihir07/agentic-os</a></td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <h3 style="font-size:13px;font-weight:600;margin-bottom:10px">Redesign ledger — 2026-09</h3>
      <div class="table-wrapper">
        <table>
          <thead><tr><th style="width:70px">Slice</th><th>Scope</th><th style="width:120px">Shipped</th></tr></thead>
          <tbody>
            ${LEDGER.map(function (row) {
              return `<tr><td>${row[0]}</td><td>${escapeHtml(row[1])}</td><td>${row[2]}</td></tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <div class="card" style="margin-bottom:16px">
      <h3 style="font-size:13px;font-weight:600;margin-bottom:10px">Deployment</h3>
      <div class="table-wrapper">
        <table>
          <tbody>
            <tr><td style="width:180px;color:var(--text-muted)">Domain</td><td>os.srv1738752.hstgr.cloud (Traefik edge)</td></tr>
            <tr><td style="color:var(--text-muted)">Static deploy</td><td>Dashboard files are volume-mounted — edits are live immediately, no restart</td></tr>
            <tr><td style="color:var(--text-muted)">Cache policy</td><td>?v= build stamp on utils/api/app (current: 20260918); page modules revalidate per load</td></tr>
            <tr><td style="color:var(--text-muted)">Backups</td><td>redesign-2026-09/backup-pre-pr* snapshots before every merge slice</td></tr>
            <tr><td style="color:var(--text-muted)">Inventory</td><td>86 page modules classified — 58 live · 22 suite tabs · 6 hidden · 0 orphan (redesign-2026-09/final-inventory.md)</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h3 style="font-size:13px;font-weight:600;margin-bottom:10px">Design system</h3>
      <div class="table-wrapper">
        <table>
          <tbody>
            <tr><td style="width:180px;color:var(--text-muted)">Typography</td><td>Inter — h1 20px/600 · stat 24px/700 · body 13.5px · tabular numerals on data</td></tr>
            <tr><td style="color:var(--text-muted)">Accent</td><td>Teal #14b8a6 — no purple, no pink</td></tr>
            <tr><td style="color:var(--text-muted)">Glyphs</td><td>▸ ● ◆ ○ ✓ ✕ ↻ ⌕ — decorative emoji retired; data glyphs only</td></tr>
            <tr><td style="color:var(--text-muted)">Themes</td><td>Dark + light, CSS custom properties</td></tr>
            <tr><td style="color:var(--text-muted)">Suites</td><td>Six merged suites replace 24 standalone links (schedule, compliance, grand rounds, CRM, AI builder, workspace)</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
}
