// ──────────────────────────────────────────────────────────────
// Chief Residents' Meetings — Outlook deeplink + .eml generator
// Embedded into Agentic OS dashboard
// ──────────────────────────────────────────────────────────────

// Chief Meetings data (2026-2027)
const CHIEF_DATA = [
  ["2026-09-04", "Kick Off",       "Penthouse", "12:00 PM", "1:00 PM"],
  ["2026-10-16", "",                "Penthouse", "12:00 PM", "1:00 PM"],
  ["2026-12-04", "",                "Penthouse", "12:00 PM", "1:00 PM"],
  ["2027-01-14", "",                "Penthouse", "12:00 PM", "1:00 PM"],
  ["2027-02-26", "",                "Penthouse", "12:00 PM", "1:00 PM"],
  ["2027-04-09", "",                "Penthouse", "12:00 PM", "1:00 PM"],
  ["2027-06-04", "",                "Penthouse", "12:00 PM", "1:00 PM"],
];

// Attendees
const CHIEF_ATTENDEES_EMAILS = [
  "asankin@montefiore.org",    // Dr. Sankin
  "alesmall@montefiore.org",   // Dr. Small
  "mschoenb@montefiore.org",   // Dr. Schoenberg
  "johill@montefiore.org",     // John Hill (Chief)
  "johordines@montefiore.org", // John Hordines (Chief)
  "sopak@montefiore.org",      // So Yeon (Jen) Pak (Chief)
];

const CHIEF_ATTENDEES_DISPLAY = [
  "Dr. Schoenberg",
  "Dr. Sankin",
  "Dr. Small",
  "John Hill (Chief)",
  "John Hordines (Chief)",
  "So Yeon (Jen) Pak (Chief)",
];

async function renderChiefMeetings() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">👑 Chief Residents' Meetings</h1>
        <p class="page-subtitle">Click 📧 to open Outlook with pre-filled invite — just press Send</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="openAllChiefOutlook()">📧 Open All in Outlook</button>
        <button class="btn" onclick="renderChiefMeetings()">🔄 Refresh</button>
      </div>
    </div>
    <div id="chiefContent" style="display:flex;flex-direction:column;gap:16px">Loading...</div>
  `;
  renderChiefDashboard();
}

function renderChiefDashboard() {
  const container = document.getElementById('chiefContent');
  if (!container) return;

  let html = '';

  // ── Status card ──────────────────────────────────────────
  html += `
    <div class="card" style="padding:16px 20px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Total Meetings</span>
          <span style="font-size:20px;font-weight:700;margin-left:8px">${CHIEF_DATA.length}</span>
        </div>
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Attendees</span>
          <span style="font-size:20px;font-weight:700;margin-left:8px">${CHIEF_ATTENDEES_DISPLAY.length}</span>
        </div>
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Duration</span>
          <span style="font-size:16px;font-weight:600;margin-left:8px">12:00 PM – 1:00 PM ET</span>
        </div>
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Location</span>
          <span style="font-size:16px;font-weight:600;margin-left:8px">Penthouse</span>
        </div>
      </div>
    </div>
  `;

  // ── Attendees card ───────────────────────────────────────
  html += `
    <div class="card" style="padding:16px 20px">
      <h3 style="margin:0 0 10px 0;font-size:14px">Attendees</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        ${CHIEF_ATTENDEES_DISPLAY.map(a => `<span class="tag" style="background:var(--accent-bg,rgba(59,130,246,0.1));color:var(--accent,#60a5fa);padding:4px 12px;border-radius:999px;font-size:12px">${escapeHtml(a)}</span>`).join('')}
      </div>
    </div>
  `;

  // ── Meeting schedule table ────────────────────────────────
  html += `
    <div class="card" style="padding:0;overflow:hidden">
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:var(--bg-secondary,#1e293b)">
            <th style="text-align:left;padding:10px 16px">Date</th>
            <th style="text-align:left;padding:10px 16px">Label</th>
            <th style="text-align:left;padding:10px 16px">Time</th>
            <th style="text-align:left;padding:10px 16px">Location</th>
            <th style="text-align:center;padding:10px 16px">Outlook</th>
          </tr>
        </thead>
        <tbody>
          ${CHIEF_DATA.map((row, i) => {
            const [date, label, loc, startTime, endTime] = row;
            const dt = new Date(date + 'T12:00:00');
            const dayName = dt.toLocaleDateString('en-US', { weekday: 'long' });
            const formatted = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const labelDisplay = label || '—';
            const isPast = new Date(date + 'T23:59:59') < new Date();
            return `<tr style="${i % 2 === 1 ? 'background:var(--bg-secondary,#1e293b)' : ''}${isPast ? 'opacity:0.5' : ''}">
              <td style="padding:10px 16px;white-space:nowrap"><strong>${dayName}</strong><br><span style="font-size:12px;color:var(--text-muted)">${formatted}</span></td>
              <td style="padding:10px 16px">${escapeHtml(labelDisplay)}</td>
              <td style="padding:10px 16px;white-space:nowrap">${startTime} – ${endTime}</td>
              <td style="padding:10px 16px">${escapeHtml(loc)}</td>
              <td style="padding:10px 16px;text-align:center">
                <button class="btn btn-sm" style="font-size:16px;padding:3px 8px" onclick="openChiefOutlook('${date}')" title="Open in Outlook">📧</button>
              </td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;

  container.innerHTML = html;
}

function openChiefOutlook(date) {
  const row = CHIEF_DATA.find(r => r[0] === date);
  if (!row) return;
  const [d, label, loc] = row;
  const dt = new Date(d + 'T12:00:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const labelStr = label ? ` — ${label}` : '';
  const summary = `Chief Residents' Meeting${labelStr}`;
  const subj = `Invitation: ${summary}`;

  const body = [
    `<strong>Montefiore Urology — Chief Residents' Meeting${label ? ` — ${label}` : ''}</strong>`,
    ``,
    `<strong>Date:</strong> ${formatted}`,
    `<strong>Time:</strong> 12:00 PM – 1:00 PM (ET)`,
    `<strong>Location:</strong> Penthouse — Montefiore Medical Center`,
    ``,
    `<strong>Attendees:</strong>`,
    `Dr. Mark Schoenberg, Dr. Alex Sankin, Dr. Alex Small`,
    `John Hill (Chief), John Hordines (Chief), So Yeon (Jen) Pak (Chief)`,
    ``,
    `This is an automated calendar invitation.`,
    `Please Accept or Decline to confirm your attendance.`,
  ].join('<br>');

  const attendees = CHIEF_ATTENDEES_EMAILS.join(';');
  const params = new URLSearchParams({
    subject: subj,
    body: body,
    location: 'Penthouse',
    startdt: `${d}T12:00:00`,
    enddt: `${d}T13:00:00`,
    to: attendees,
  });
  window.open(`https://outlook.office.com/calendar/deeplink/compose?${params}`, '_blank');
}

function openAllChiefOutlook() {
  const dates = CHIEF_DATA.map(r => r[0]);
  dates.forEach((d, i) => {
    setTimeout(() => openChiefOutlook(d), i * 800);
  });
}

// ── Helper ──────────────────────────────────────────────
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
