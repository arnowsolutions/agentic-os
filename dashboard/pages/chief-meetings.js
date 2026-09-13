// ──────────────────────────────────────────────────────────────
// Chief Residents' Meetings — Outlook deeplink + .eml generator
// Embedded into Agentic OS dashboard
//
// Data comes from the canonical API (GET /api/chief-meetings), which reads
// unified.chief_meetings + unified.chief_meeting_attendees. NO schedule or
// attendee list is hardcoded here — edit the DB/API and this page follows.
// ──────────────────────────────────────────────────────────────

// Cached so the Outlook openers can read it synchronously after render.
let chiefState = { meetings: [], attendees: [], loaded: false };

async function loadChiefData(force) {
  if (chiefState.loaded && !force) return chiefState;
  const data = await api.getChiefMeetings();
  if (!data || data.error) throw new Error((data && data.error) || 'chief meetings unavailable');
  chiefState = {
    meetings: data.meetings || [],
    attendees: data.attendees || [],
    loaded: true,
  };
  return chiefState;
}

function chiefTimeRange(m) {
  return `${m.start_time || '12:00 PM'} – ${m.end_time || '1:00 PM'}`;
}

async function renderChiefMeetings(target) {
  const content = target || document.getElementById('suitePane') || document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Chief Residents' Meetings</h1>
        <p class="page-subtitle">Click to open Outlook with pre-filled invite — just press Send</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="openAllChiefOutlook()">Open All in Outlook</button>
        <button class="btn" onclick="renderChiefMeetings()">↻ Refresh</button>
      </div>
    </div>
    <div id="chiefContent" style="display:flex;flex-direction:column;gap:16px">Loading...</div>
  `;
  try {
    await loadChiefData(true);
  } catch (err) {
    document.getElementById('chiefContent').innerHTML =
      `<div class="card" style="padding:16px 20px"><strong>Could not load chief meetings</strong><br>
       <span style="font-size:13px;color:var(--text-muted)">${escapeHtml(String(err.message || err))}</span></div>`;
    return;
  }
  renderChiefDashboard();
}

function renderChiefDashboard() {
  const container = document.getElementById('chiefContent');
  if (!container) return;

  const meetings = chiefState.meetings || [];
  const attendees = chiefState.attendees || [];
  const loc = meetings[0] ? meetings[0].location : 'Penthouse';
  const times = meetings[0] ? chiefTimeRange(meetings[0]) : '';

  let html = '';

  // ── Status card ──────────────────────────────────────────
  html += `
    <div class="card" style="padding:16px 20px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Total Meetings</span>
          <span style="font-size:20px;font-weight:700;margin-left:8px">${meetings.length}</span>
        </div>
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Attendees</span>
          <span style="font-size:20px;font-weight:700;margin-left:8px">${attendees.length}</span>
        </div>
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Duration</span>
          <span style="font-size:16px;font-weight:600;margin-left:8px">${escapeHtml(times)}</span>
        </div>
        <div>
          <span style="font-size:13px;color:var(--text-muted)">Location</span>
          <span style="font-size:16px;font-weight:600;margin-left:8px">${escapeHtml(loc)}</span>
        </div>
      </div>
    </div>
  `;

  // ── Attendees card ───────────────────────────────────────
  html += `
    <div class="card" style="padding:16px 20px">
      <h3 style="margin:0 0 10px 0;font-size:14px">Attendees</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        ${attendees.map(a => `<span class="tag" style="background:var(--accent-bg,rgba(59,130,246,0.1));color:var(--accent,#60a5fa);padding:4px 12px;border-radius:999px;font-size:12px">${escapeHtml(a.display || a.name)}</span>`).join('')}
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
          ${meetings.map((m, i) => {
            const dt = new Date(m.date + 'T12:00:00');
            const dayName = dt.toLocaleDateString('en-US', { weekday: 'long' });
            const formatted = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const isPast = new Date(m.date + 'T23:59:59') < new Date();
            return `<tr style="${i % 2 === 1 ? 'background:var(--bg-secondary,#1e293b)' : ''}${isPast ? 'opacity:0.5' : ''}">
              <td style="padding:10px 16px;white-space:nowrap"><strong>${dayName}</strong><br><span style="font-size:12px;color:var(--text-muted)">${formatted}</span></td>
              <td style="padding:10px 16px">${escapeHtml(m.label || '—')}</td>
              <td style="padding:10px 16px;white-space:nowrap">${escapeHtml(chiefTimeRange(m))}</td>
              <td style="padding:10px 16px">${escapeHtml(m.location || '')}</td>
              <td style="padding:10px 16px;text-align:center">
                <button class="btn btn-sm" style="font-size:16px;padding:3px 8px" onclick="openChiefOutlook('${m.date}')" title="Open in Outlook">✉</button>
              </td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;

  container.innerHTML = html;
}

function chiefAttendeeLines() {
  return (chiefState.attendees || []).map(a => a.name);
}

function chiefRecipients() {
  return (chiefState.attendees || []).map(a => a.email).join(';');
}

async function openChiefOutlook(date) {
  if (!chiefState.loaded) { try { await loadChiefData(true); } catch (e) { return; } }
  const m = (chiefState.meetings || []).find(x => x.date === date);
  if (!m) return;
  const dt = new Date(m.date + 'T12:00:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const labelStr = m.label ? ` — ${m.label}` : '';
  const summary = `Chief Residents' Meeting${labelStr}`;

  const body = window.buildRsvpBody({
    header: `Montefiore Urology — Chief Residents' Meeting${m.label ? ` — ${m.label}` : ''}`,
    date: formatted,
    time: `${m.start_time || '12:00 PM'} - ${m.end_time || '1:00 PM'} (Eastern)`,
    location: `${m.location || 'Penthouse'} — Montefiore Medical Center`,
    extra: [
      '<strong>Attendees</strong>',
      ...chiefAttendeeLines(),
      '',
      'Please Accept or Decline to confirm your attendance.',
    ],
  });

  const start24 = to24h(m.start_time || '12:00 PM');
  const end24 = to24h(m.end_time || '1:00 PM');
  window.openEventEditor({
    subject: `Invitation: ${summary}`,
    body,
    to: chiefRecipients(),
    startdt: `${m.date}T${start24}:00`,
    enddt: `${m.date}T${end24}:00`,
    location: m.location || 'Penthouse', bodyType: 'HTML',
  });
}

async function openAllChiefOutlook() {
  if (!chiefState.loaded) { try { await loadChiefData(true); } catch (e) { return; } }
  (chiefState.meetings || []).forEach((m) => {
    const dt = new Date(m.date + 'T12:00:00');
    const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    const labelStr = m.label ? ` — ${m.label}` : '';
    const body = window.buildRsvpBody({
      header: `Montefiore Urology — Chief Residents' Meeting${m.label ? ` — ${m.label}` : ''}`,
      date: formatted,
      time: `${m.start_time || '12:00 PM'} - ${m.end_time || '1:00 PM'} (Eastern)`,
      location: `${m.location || 'Penthouse'} — Montefiore Medical Center`,
      extra: ['<strong>Attendees</strong>', ...chiefAttendeeLines(), '', 'Please Accept or Decline to confirm your attendance.'],
    });
    window.openEventDirect({
      subject: `Invitation: Chief Residents' Meeting${labelStr}`,
      body,
      to: chiefRecipients(),
      startdt: `${m.date}T${to24h(m.start_time || '12:00 PM')}:00`,
      enddt: `${m.date}T${to24h(m.end_time || '1:00 PM')}:00`,
      location: m.location || 'Penthouse', bodyType: 'HTML',
    });
  });
}

// "12:00 PM" / "1:00 PM" → "12:00" / "13:00" (24h, for Outlook startdt/enddt)
function to24h(t) {
  const m = String(t || '').trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i);
  if (!m) return '12:00';
  let h = parseInt(m[1], 10);
  const min = m[2];
  const ap = (m[3] || '').toUpperCase();
  if (ap === 'PM' && h !== 12) h += 12;
  if (ap === 'AM' && h === 12) h = 0;
  return `${String(h).padStart(2, '0')}:${min}`;
}

// ── Helper ──────────────────────────────────────────────
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
