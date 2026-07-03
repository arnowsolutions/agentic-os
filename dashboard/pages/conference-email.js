async function renderConferenceEmail() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📧 One-Click Email Resend</h1>
        <p class="page-subtitle">Grand Rounds & Resident Conference — resend invites instantly</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderConferenceEmail()">🔄 Refresh</button>
      </div>
    </div>
    <div id="confEmailContent" style="display:flex;flex-direction:column;gap:16px">Loading events & groups...</div>
  `;
  await loadConferenceData();
}

let confEvents = [];
let confGroups = {};
let confLoading = false;

async function loadConferenceData() {
  try {
    const [eventsData, groupsData] = await Promise.all([
      api.get('/api/conference/events'),
      api.get('/api/crm/email-groups')
    ]);
    confEvents = (eventsData.events || []).filter(e => e.type !== 'no_grand_rounds');
    confGroups = groupsData;
    renderConferenceDashboard();
  } catch (err) {
    document.getElementById('confEmailContent').innerHTML =
      `<div class="card" style="padding:24px;text-align:center;color:var(--red)">
        ⚠️ Failed to load: ${escapeHtml(err.message)}
      </div>`;
  }
}

function renderConferenceDashboard() {
  const container = document.getElementById('confEmailContent');

  // Show group status
  let groupsHtml = '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px">';
  for (const [key, group] of Object.entries(confGroups)) {
    const count = (group.emails || []).length;
    const modeColor = group.test_mode ? '#f59e0b' : '#10b981';
    const modeEmoji = group.test_mode ? '🧪' : '🚀';
    groupsHtml += `
      <div class="card" style="flex:1;min-width:200px;padding:12px 16px">
        <div style="font-weight:600;font-size:14px;margin-bottom:4px">${escapeHtml(group.label)}</div>
        <div style="font-size:12px;color:var(--text-muted)">${count} recipients</div>
        <span style="display:inline-block;margin-top:4px;font-size:11px;color:${modeColor};font-weight:600">${modeEmoji} ${group.test_mode ? 'TEST' : 'LIVE'}</span>
      </div>`;
  }
  groupsHtml += '</div>';
  container.innerHTML = groupsHtml;

  // Upcoming events
  const today = new Date().toISOString().slice(0, 10);
  const upcoming = confEvents.filter(e => e.date >= today).slice(0, 12);
  const past = confEvents.filter(e => e.date < today).slice(-6).reverse();

  let eventsHtml = '<h3 style="margin:16px 0 8px 0;font-size:15px">📅 Upcoming Conferences</h3>';

  if (!upcoming.length) {
    eventsHtml += '<div class="card" style="padding:16px;text-align:center;color:var(--text-muted)">No upcoming conferences</div>';
  } else {
    eventsHtml += '<div style="display:flex;flex-direction:column;gap:8px">';
    for (const event of upcoming) {
      eventsHtml += buildEventCard(event);
    }
    eventsHtml += '</div>';
  }

  if (past.length > 0) {
    eventsHtml += '<h3 style="margin:24px 0 8px 0;font-size:15px;color:var(--text-muted)">📭 Recent Past</h3>';
    eventsHtml += '<div style="display:flex;flex-direction:column;gap:8px">';
    for (const event of past) {
      eventsHtml += buildEventCard(event, true);
    }
    eventsHtml += '</div>';
  }

  container.innerHTML += eventsHtml;
}

function buildEventCard(event, isPast = false) {
  const dt = new Date(event.date + 'T12:00:00-04:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  const typeLabel = {
    grand_rounds: '🎓 Grand Rounds',
    peds: '🧒 Peds Grand Rounds',
    faculty_meeting: '👥 Faculty Meeting',
    journal_club: '📖 Journal Club',
    resident_conference: '📋 Resident Conference'
  }[event.type] || event.type;

  const topic = [event.topic_7_8, event.topic_8_9].filter(Boolean).join(' / ') || 'TBD';
  const opacity = isPast ? 'opacity:0.6' : '';
  const groupKey = event.type === 'resident_conference' ? 'resident_conference' : 'grand_rounds';
  const group = confGroups[groupKey];
  const hasRecipients = group && (group.emails || []).length > 0;

  return `
    <div class="card" style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;gap:16px;${opacity}">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span style="font-weight:600;font-size:14px">${formatted}</span>
          <span class="tag" style="font-size:11px">${typeLabel}</span>
        </div>
        <div style="font-size:12px;color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(topic)}">
          ${escapeHtml(topic)}
        </div>
      </div>
      <div style="display:flex;gap:8px;flex-shrink:0">
        ${hasRecipients ? `
          <button class="btn" style="font-size:12px;padding:6px 14px" onclick="resendInvite('${groupKey}', '${event.date}')"
                  ${confLoading ? 'disabled' : ''}>
            📤 Resend
          </button>
        ` : `
          <button class="btn" style="font-size:12px;padding:6px 14px;opacity:0.5" disabled title="Configure recipients in Email Groups first">
            ⚠ No recipients
          </button>
        `}
      </div>
    </div>`;
}

async function resendInvite(groupKey, date) {
  if (confLoading) return;
  confLoading = true;
  showToast(`Resending invite for ${date}...`, 'info');

  try {
    const data = await api.post(`/api/crm/email-groups/${encodeURIComponent(groupKey)}/resend`, {
      date: date,
      group: groupKey
    });

    if (data.success) {
      showToast(`✅ Invite resent to ${data.recipients} recipients`, 'success');
    } else {
      showToast(`⚠️ Resend completed with issues: ${escapeHtml(data.error || 'unknown')}`, 'warning');
    }
  } catch (err) {
    showToast(`❌ Resend failed: ${escapeHtml(err.message)}`, 'error');
  } finally {
    confLoading = false;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
