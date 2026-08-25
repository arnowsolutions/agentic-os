// ──────────────────────────────────────────────────────────────
// Mass Email & Invites Hub — consolidated Outlook deeplink tools
// One page, sub-tabs per category, all in the clean iframe layout
// (same format as Sub-I Exit Interviews / Calendar Invites).
// ──────────────────────────────────────────────────────────────

// Category definitions: key → label, icon, iframe src, live-toggle support
const MASSTEMAIL_CATEGORIES = [
  {
    key: 'grand-rounds',
    label: 'Grand Rounds',
    icon: '🎓',
    src: '/api/calendar-invites',
    liveParam: 'test=false',
    desc: 'Grand Rounds & Monday conferences — one-click Outlook invites',
    live: true,
  },
  {
    key: 'subi-exit',
    label: 'Sub-I Exit Interviews',
    icon: '🎓',
    src: '/api/subi-exit-invites',
    liveParam: 'test=false',
    desc: 'Sub-I exit interviews — interviewee & time per row',
    live: true,
  },
  // Chief Meetings — embedded table for now (no server page yet)
  {
    key: 'chief-meetings',
    label: 'Chief Meetings',
    icon: '👑',
    src: null,
    desc: "Chief Residents' meetings — 12 PM, Penthouse, 6 fixed dates",
    live: false,
    renderInline: true,
  },
  {
    key: 'conference-email',
    label: 'Email Resend',
    icon: '📧',
    src: null,
    desc: 'Grand Rounds & Resident Conference invite resend',
    live: false,
    renderInline: true,
  },
];

// Active sub-tab
let massEmailActive = 'grand-rounds';
// Live vs Test toggle per page (client-side override on the iframe src)
let massEmailLive = true;

async function renderMassEmail() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📧 Mass Email & Invites</h1>
        <p class="page-breadcrumb">One-click Outlook deeplinks — Grand Rounds, Sub-I, Meetings & more</p>
      </div>
      <div class="btn-group">
        <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;margin-right:4px">
          <input type="checkbox" id="massEmailLiveToggle" ${massEmailLive ? 'checked' : ''} onchange="massEmailLive=this.checked;renderMassEmailFrame()" />
          ${massEmailLive ? '🚀 LIVE' : '🧪 TEST'}
        </label>
        <button class="btn" onclick="renderMassEmail()">🔄 Refresh</button>
      </div>
    </div>

    <!-- Sub-tabs -->
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px;border-bottom:1px solid var(--line,#334155);padding-bottom:10px">
      ${MASSTEMAIL_CATEGORIES.map(c => `
        <button onclick="setMassEmailTab('${c.key}')"
          data-mastab="${c.key}"
          style="padding:7px 16px;border-radius:8px;border:1px solid ${massEmailActive === c.key ? 'var(--accent,#60a5fa)' : 'var(--line,#334155)'};background:${massEmailActive === c.key ? 'rgba(96,165,250,0.12)' : 'transparent'};color:${massEmailActive === c.key ? '#93c5fd' : 'var(--muted,#94a3b8)'};font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:6px">
          <span>${c.icon}</span><span>${c.label}</span>
        </button>
      `).join('')}
    </div>

    <div id="massEmailBody" style="width:100%">
      <div class="loading"><div class="loading-spinner"></div><span>Loading...</span></div>
    </div>
  `;

  await renderMassEmailFrame();
}

async function renderMassEmailFrame() {
  const body = document.getElementById('massEmailBody');
  if (!body) return;

  const cat = MASSTEMAIL_CATEGORIES.find(c => c.key === massEmailActive) || MASSTEMAIL_CATEGORIES[0];

  // Highlight active tab
  document.querySelectorAll('[data-mastab]').forEach(b => {
    const isActive = b.dataset.mastab === cat.key;
    b.style.borderColor = isActive ? 'var(--accent,#60a5fa)' : 'var(--line,#334155)';
    b.style.background = isActive ? 'rgba(96,165,250,0.12)' : 'transparent';
    b.style.color = isActive ? '#93c5fd' : 'var(--muted,#94a3b8)';
  });

  // Category intro
  let html = `<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;font-size:13px;color:var(--muted)">
    <span style="font-size:16px">${cat.icon}</span>
    <strong style="color:var(--ink,#e2e8f0)">${cat.label}</strong>
    <span>— ${cat.desc}</span>
  </div>`;

  if (cat.renderInline) {
    // Inline-rendered categories (Chief Meetings, Conference Email)
    body.innerHTML = html + '<div style="width:100%"><div class="loading"><div class="loading-spinner"></div><span>Loading...</span></div></div>';
    if (cat.key === 'chief-meetings') {
      await renderChiefMeetingsInline(body);
    } else if (cat.key === 'conference-email') {
      await renderConferenceEmailInline(body);
    }
    return;
  }

  // Iframe categories — full-height clean layout (matches Sub-I / Calendar Invites)
  const src = cat.src + (massEmailLive && cat.live ? `?${cat.liveParam}` : `?test=true`);
  html += `
    <div style="position:relative;width:100%;height:calc(100vh - 260px);min-height:600px;border:1px solid var(--border-color,#334155);border-radius:12px;overflow:hidden;background:#0f172a">
      <iframe src="${src}" style="width:100%;height:100%;border:none" title="${cat.label}"></iframe>
    </div>
  `;
  body.innerHTML = html;
}

function setMassEmailTab(key) {
  massEmailActive = key;
  renderMassEmailFrame();
}

// ── Chief Meetings inline render (self-contained compact table) ──
async function renderChiefMeetingsInline(container) {
  container.innerHTML = buildChiefMeetingsInline();
}

function buildChiefMeetingsInline() {
  const CHIEF_DATA = [
    ["2026-09-04", "Kick Off", "Penthouse", "12:00 PM", "1:00 PM"],
    ["2026-10-16", "", "Penthouse", "12:00 PM", "1:00 PM"],
    ["2026-12-04", "", "Penthouse", "12:00 PM", "1:00 PM"],
    ["2027-01-14", "", "Penthouse", "12:00 PM", "1:00 PM"],
    ["2027-02-26", "", "Penthouse", "12:00 PM", "1:00 PM"],
    ["2027-04-09", "", "Penthouse", "12:00 PM", "1:00 PM"],
    ["2027-06-04", "", "Penthouse", "12:00 PM", "1:00 PM"],
  ];
  const CHIEF_ATTENDEES = [
    "Dr. Schoenberg", "Dr. Sankin", "Dr. Small",
    "John Hill (Chief)", "John Hordines (Chief)", "So Yeon (Jen) Pak (Chief)",
  ];
  let rows = CHIEF_DATA.map((row, i) => {
    const [date, label, loc, st, et] = row;
    const dt = new Date(date + 'T12:00:00');
    const day = dt.toLocaleDateString('en-US', { weekday: 'long' });
    const fm = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `<tr style="${i % 2 === 1 ? 'background:var(--bg-secondary,#1e293b)' : ''}">
      <td style="padding:10px 16px;white-space:nowrap"><strong>${day}</strong><br><span style="font-size:12px;color:var(--muted)">${fm}</span></td>
      <td style="padding:10px 16px">${escapeHtml(label || '—')}</td>
      <td style="padding:10px 16px">${st} – ${et}</td>
      <td style="padding:10px 16px">${escapeHtml(loc)}</td>
      <td style="padding:10px 16px;text-align:center"><button class="btn btn-sm" onclick="openChiefOutlookHub('${date}')">📧</button></td>
    </tr>`;
  }).join('');
  return `
    <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:14px">
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Meetings</div><div style="font-size:20px;font-weight:700">${CHIEF_DATA.length}</div></div>
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Attendees</div><div style="font-size:20px;font-weight:700">${CHIEF_ATTENDEES.length}</div></div>
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Time</div><div style="font-size:16px;font-weight:600">12–1 PM</div></div>
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Location</div><div style="font-size:16px;font-weight:600">Penthouse</div></div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">
      ${CHIEF_ATTENDEES.map(a => `<span class="tag" style="background:rgba(96,165,250,0.1);color:#60a5fa;padding:4px 12px;border-radius:999px;font-size:12px">${escapeHtml(a)}</span>`).join('')}
    </div>
    <div class="card" style="padding:0;overflow:hidden;background:#0f172a">
      <table style="width:100%;border-collapse:collapse;font-size:13px;color:var(--ink,#e2e8f0)">
        <thead><tr style="background:#1e293b">
          <th style="text-align:left;padding:10px 16px">Date</th><th style="text-align:left;padding:10px 16px">Label</th>
          <th style="text-align:left;padding:10px 16px">Time</th><th style="text-align:left;padding:10px 16px">Location</th>
          <th style="text-align:center;padding:10px 16px">Outlook</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ── Conference Email inline render (compact resend list) ──
async function renderConferenceEmailInline(container) {
  container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📧</div><div class="empty-state-title">Email Resend</div><div class="empty-state-desc">Grand Rounds & Resident Conference invite resend tool</div></div>`;
}

// ── Chief Meetings outlook opener ──
function openChiefOutlookHub(date) {
  const CHIEF_ATTENDEES_EMAILS = [
    "asankin@montefiore.org", "alesmall@montefiore.org", "mschoenb@montefiore.org",
    "johill@montefiore.org", "johordines@montefiore.org", "sopak@montefiore.org",
  ];
  const dt = new Date(date + 'T12:00:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const body = [
    `<strong>Montefiore Urology — Chief Residents' Meeting</strong>`, ``,
    `<strong>Date:</strong> ${formatted}`, `<strong>Time:</strong> 12:00 PM – 1:00 PM (ET)`,
    `<strong>Location:</strong> Penthouse — Montefiore Medical Center`, ``,
    `<strong>Attendees:</strong>`, `Dr. Mark Schoenberg`, `Dr. Alex Sankin`, `Dr. Alex Small`,
    `Dr. John Hill (Chief)`, `Dr. John Hordines (Chief)`, `Dr. So Yeon (Jen) Pak (Chief)`, ``,
    `Please Accept or Decline to confirm your attendance.`,
  ].join('<br>');
  const params = new URLSearchParams({
    subject: `Invitation: Chief Residents' Meeting`,
    body, location: 'Penthouse',
    startdt: `${date}T12:00:00`, enddt: `${date}T13:00:00`,
    to: CHIEF_ATTENDEES_EMAILS.join(';'),
  });
  window.open(`https://outlook.office.com/calendar/deeplink/compose?${params}`, '_blank');
}
