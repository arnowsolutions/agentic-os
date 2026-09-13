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
    icon: '▸',
    src: '/api/calendar-invites',
    liveParam: 'test=false',
    desc: 'Grand Rounds & Monday conferences — one-click Outlook invites',
    live: true,
  },
  {
    key: 'subi-exit',
    label: 'Sub-I Exit Interviews',
    icon: '▸',
    src: '/api/subi-exit-invites',
    liveParam: 'test=false',
    desc: 'Sub-I exit interviews — interviewee & time per row',
    live: true,
  },
  // Chief Meetings — embedded table for now (no server page yet)
  {
    key: 'chief-meetings',
    label: 'Chief Meetings',
    icon: '▸',
    src: null,
    desc: "Chief Residents' meetings — 12 PM, Penthouse, 6 fixed dates",
    live: false,
    renderInline: true,
  },
  // Interview Days — standalone sub-tab, completely separate from Grand Rounds
  {
    key: 'interview-days',
    label: 'Interview Days',
    icon: '▸',
    src: null,
    desc: '2026-2027 Residency Interview Days — invites to faculty + residents',
    live: false,
    renderInline: true,
  },
  {
    key: 'conference-email',
    label: 'Email Resend',
    icon: '▸',
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
        <h1 class="page-title">Mass Email & Invites</h1>
        <p class="page-breadcrumb">One-click Outlook deeplinks — Grand Rounds, Sub-I, Meetings & more</p>
      </div>
      <div class="btn-group">
        <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);cursor:pointer;margin-right:4px">
          <input type="checkbox" id="massEmailLiveToggle" ${massEmailLive ? 'checked' : ''} onchange="massEmailLive=this.checked;renderMassEmailFrame()" />
          ${massEmailLive ? 'LIVE' : 'TEST'}
        </label>
        <button class="btn" onclick="renderMassEmail()">↻ Refresh</button>
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
    // Inline-rendered categories (Chief Meetings, Conference Email, Interview Days)
    body.innerHTML = html + '<div style="width:100%"><div class="loading"><div class="loading-spinner"></div><span>Loading...</span></div></div>';
    if (cat.key === 'chief-meetings') {
      await renderChiefMeetingsInline(body);
    } else if (cat.key === 'interview-days') {
      await renderInterviewDaysInline(body);
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

// ── Chief Meetings inline render (canonical API — no hardcoded schedule) ──
// Same source as the standalone Chief Meetings page: GET /api/chief-meetings
// (unified.chief_meetings + unified.chief_meeting_attendees).
let chiefHubState = { meetings: [], attendees: [], loaded: false };

async function loadChiefHubData(force) {
  if (chiefHubState.loaded && !force) return chiefHubState;
  const data = await api.getChiefMeetings();
  if (!data || data.error) throw new Error((data && data.error) || 'chief meetings unavailable');
  chiefHubState = { meetings: data.meetings || [], attendees: data.attendees || [], loaded: true };
  return chiefHubState;
}

async function renderChiefMeetingsInline(container) {
  try {
    await loadChiefHubData(true);
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-title">Could not load chief meetings</div><div class="empty-state-desc">${escapeHtml(String(err.message || err))}</div></div>`;
    return;
  }
  container.innerHTML = buildChiefMeetingsInline();
}

function buildChiefMeetingsInline() {
  const CHIEF_DATA = chiefHubState.meetings.map(m => [m.date, m.label, m.location, m.start_time, m.end_time]);
  const CHIEF_ATTENDEES = chiefHubState.attendees.map(a => a.display || a.name);
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
      <td style="padding:10px 16px;text-align:center"><button class="btn btn-sm" onclick="openChiefOutlookHub('${date}')"></button></td>
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
  container.innerHTML = `<div class="empty-state"><div class="empty-state-icon"></div><div class="empty-state-title">Email Resend</div><div class="empty-state-desc">Grand Rounds & Resident Conference invite resend tool</div></div>`;
}

// ── Chief Meetings outlook opener ──
function openChiefOutlookHub(date) {
  const CHIEF_ATTENDEES_EMAILS = (chiefHubState.attendees || []).map(a => a.email);
  const hubMeeting = (chiefHubState.meetings || []).find(m => m.date === date) || {};
  const dt = new Date(date + 'T12:00:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  // Shared rich template — same structure as Grand Rounds & Monday invites
  const body = window.buildRsvpBody({
    header: 'Montefiore Urology — Chief Residents\' Meeting',
    date: formatted,
    time: `${hubMeeting.start_time || '12:00 PM'} - ${hubMeeting.end_time || '1:00 PM'} (Eastern)`,
    location: `${hubMeeting.location || 'Penthouse'} — Montefiore Medical Center`,
    extra: [
      '<strong>Attendees</strong>',
      ...(chiefHubState.attendees || []).map(a => a.display || a.name),
      '',
      'Please Accept or Decline to confirm your attendance.',
    ],
  });

  window.openEventEditor({
    subject: `Invitation: Chief Residents' Meeting`,
    body,
    to: CHIEF_ATTENDEES_EMAILS.join(';'),
    startdt: `${date}T12:00:00`, enddt: `${date}T13:00:00`,
    location: hubMeeting.location || 'Penthouse', bodyType: 'HTML',
  });
}

// ──────────────────────────────────────────────────────────────
// Interview Days — 2026-2027 Urology Residency Interview Days
// Completely separate from Grand Rounds. Two fixed interview days,
// each emailed to the full faculty + residents list.
// ──────────────────────────────────────────────────────────────
const INTERVIEW_DAYS = [
  { day: 'Interview Day 1', label: '2026-2027 Residency Interview Day 1',
    date: '2026-11-13', start: '08:00:00', end: '16:00:00' },
  { day: 'Interview Day 2', label: '2026-2027 Residency Interview Day 2',
    date: '2026-12-10', start: '08:00:00', end: '16:00:00' },
];
const INTERVIEW_DAY_LOCATION = 'Penthouse PH-2 — Montefiore Medical Center, 1250 Waters Place, Tower One, Bronx, NY 10461';

// Global so openInterviewDayOutlook can read it after load
let interviewDayEmails = [];

// Archived/graduated residents + non-faculty staff who should NOT receive
// current interview-day invites (which go to faculty + active residents only).
const INTERVIEW_DAY_EXCLUDE = [
  'azallen@montefiore.org',  // Ariel Allen — graduated June 2026
  'dkarki@montefiore.org',   // Dimindra Karki — graduated June 2026
  'fkassam@montefiore.org',  // Farzaan Kassam — graduated June 2026
  'sfrasier@montefiore.org', // Shareef Frasier — Admin/coordinator (not faculty or resident)
].map(e => e.toLowerCase());

async function renderInterviewDaysInline(container) {
  // Recipients = Faculty (all attendings) + Residents (active) only.
  // Merge the 'faculty' and 'resident_conference' groups, then drop any
  // archived/graduated residents (e.g. Ariel Allen) so only current
  // faculty + residents receive the invite.
  try {
    const groupsData = await api.get('/api/crm/email-groups');
    const faculty = (groupsData && groupsData.faculty && groupsData.faculty.emails) || [];
    const residents = (groupsData && groupsData.resident_conference && groupsData.resident_conference.emails) || [];
    const supervisors = (groupsData && groupsData.supervisors && groupsData.supervisors.emails) || [];
    const merged = {};
    [...faculty, ...residents, ...supervisors].forEach(e => {
      const key = String(e).trim().toLowerCase();
      if (!key) return;
      if (INTERVIEW_DAY_EXCLUDE.includes(key)) return; // skip archived/graduated residents + coordinator
      merged[key] = String(e).trim();
    });
    interviewDayEmails = Object.keys(merged).sort().map(k => merged[k]);
  } catch (e) {
    console.warn('Could not load interview-day email list:', e);
  }

  const dayRows = INTERVIEW_DAYS.map((d) => {
    const dt = new Date(d.date + 'T12:00:00');
    const day = dt.toLocaleDateString('en-US', { weekday: 'long' });
    const fm = dt.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    return `<tr>
      <td style="padding:12px 16px;white-space:nowrap"><strong>${day}</strong><br><span style="font-size:12px;color:var(--muted)">${fm}</span></td>
      <td style="padding:12px 16px"><strong>${escapeHtml(d.label)}</strong></td>
      <td style="padding:12px 16px">8:00 AM – 4:00 PM</td>
      <td style="padding:12px 16px;text-align:center"><button class="btn btn-sm" onclick="openInterviewDayOutlook('${d.date}')">Open in Outlook</button></td>
    </tr>`;
  }).join('');

  container.innerHTML = `
    <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:14px">
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Interview Days</div><div style="font-size:20px;font-weight:700">${INTERVIEW_DAYS.length}</div></div>
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Recipients (Faculty + Residents + Supervisors)</div><div style="font-size:20px;font-weight:700">${interviewDayEmails.length}</div></div>
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Time</div><div style="font-size:16px;font-weight:600">8 AM – 4 PM</div></div>
      <div class="card" style="flex:1;min-width:150px;padding:12px 16px"><div style="font-size:12px;color:var(--muted)">Location</div><div style="font-size:14px;font-weight:600">Penthouse PH-2</div></div>
    </div>
    <div class="card" style="padding:0;overflow:hidden;background:#0f172a">
      <table style="width:100%;border-collapse:collapse;font-size:13px;color:var(--ink,#e2e8f0)">
        <thead><tr style="background:#1e293b">
          <th style="text-align:left;padding:10px 16px">Date</th><th style="text-align:left;padding:10px 16px">Day</th>
          <th style="text-align:left;padding:10px 16px">Time</th><th style="text-align:center;padding:10px 16px">Outlook</th>
        </tr></thead>
        <tbody>${dayRows}</tbody>
      </table>
    </div>
    <div style="margin-top:12px;font-size:12px;color:var(--muted)">
      Each button opens Outlook with the invite pre-filled for the full faculty + resident list. No body text — just the calendar invite.
    </div>
  `;
}

function openInterviewDayOutlook(date) {
  const day = INTERVIEW_DAYS.find(d => d.date === date) || INTERVIEW_DAYS[0];
  const addresses = interviewDayEmails.length ? interviewDayEmails.join(';') : 'sfrasier@montefiore.org';
  const dt = new Date(date + 'T12:00:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  // Shared rich template structure (editable, minimal body per requirement)
  const body = window.buildRsvpBody({
    header: 'Montefiore Urology — Residency Interview Day',
    date: formatted,
    time: '8:00 AM - 4:00 PM (Eastern)',
    location: INTERVIEW_DAY_LOCATION,
    type: day.label,
  });

  window.openEventEditor({
    subject: `Invitation: ${day.label}`,
    body,
    to: addresses,
    startdt: `${date}T${day.start}`, enddt: `${date}T${day.end}`,
    location: INTERVIEW_DAY_LOCATION, bodyType: 'HTML',
  });
}
