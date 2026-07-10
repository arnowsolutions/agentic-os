// ──────────────────────────────────────────────────────────────
// Email Send Log — tracks which Grand Rounds events have been
// sent as real emails to the full team vs test-only or pending.
// Data is embedded from the send log JSON + GR schedule.
// ──────────────────────────────────────────────────────────────

// Real sends (from /workspace/agentic-os/data/grand_rounds_send_log.json)
const SEND_LOG = {
  realSends: [
    { date: "2026-07-10", title: "[ PEDS ] Urology Grand Rounds - Peds / Peds Multidisciplinary", emails: 43, failed: 0, sentAt: "2026-07-08" },
    { date: "2026-07-17", title: "[ GR ] Urology Grand Rounds - Sankin expectations overview (1hr) / Sub-I talks - 0.75 hr (3)", emails: 43, failed: 0, sentAt: "2026-07-08" },
  ],
  testOnlyDates: [
    "2026-07-17","2026-07-24","2026-07-31","2026-08-07","2026-08-14","2026-08-28",
    "2026-09-11","2026-09-18","2026-09-25","2026-10-02","2026-10-09","2026-10-23",
    "2026-10-30","2026-11-06","2026-11-13","2026-12-04","2026-12-11","2026-12-18",
    "2027-01-08","2027-01-15","2027-01-22","2027-02-05","2027-02-12","2027-02-19",
    "2027-02-26","2027-03-05","2027-03-12","2027-03-19","2027-03-26"
  ]
};

// All Grand Rounds events from the schedule (re-extracted from GR_DATA)
const ALL_GR_EVENTS = [
  { date: "2026-07-10", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2026-07-17", topic: "Sankin expectations overview (1hr) / Sub-I talks - 0.75 hr (3)", type: "Grand Rounds" },
  { date: "2026-07-31", topic: "Quality Improvement: Stats/M&Ms/Indications June/ July", type: "Grand Rounds" },
  { date: "2026-08-07", topic: "SASP Review with Dr. Lipsky", type: "Grand Rounds" },
  { date: "2026-08-14", topic: "Sub-I talks - 0.5 hr (2)", type: "Grand Rounds" },
  { date: "2026-08-28", topic: "PGY-4 Subspeciality Presentations / Sub-I talks - 0.75 hr (3)", type: "Grand Rounds" },
  { date: "2026-09-11", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2026-09-18", topic: "FACULTY MEETING", type: "Faculty Meeting" },
  { date: "2026-09-25", topic: "Sub-I talks - 0.75 hr (3)", type: "Grand Rounds" },
  { date: "2026-10-02", topic: "Quality Improvement: Stats/M&Ms/Indications Aug/ Sept", type: "Grand Rounds" },
  { date: "2026-10-09", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2026-10-23", topic: "Sub-Intern Presentations - 1 hr (4)", type: "Grand Rounds" },
  { date: "2026-10-30", topic: "PGY-4 Subspeciality Presentations", type: "Grand Rounds" },
  { date: "2026-11-06", topic: "FACULTY MEETING", type: "Faculty Meeting" },
  { date: "2026-11-13", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2026-12-04", topic: "Quality Improvement: Stats/M&Ms/Indications Oct-Nov", type: "Grand Rounds" },
  { date: "2026-12-11", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2026-12-18", topic: "Valentine Essay Submission Presentations / Resident QI Updates", type: "Grand Rounds" },
  { date: "2027-01-08", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2027-01-15", topic: "FACULTY MEETING", type: "Faculty Meeting" },
  { date: "2027-01-22", topic: "Journal Club", type: "Journal Club" },
  { date: "2027-02-05", topic: "Quality Improvement: Stats/M&Ms/Indications - Dec/Jan", type: "Grand Rounds" },
  { date: "2027-02-12", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2027-02-19", topic: "PGY-4 Subspeciality Presentations (1 hr) / Visiting Lecture: Fed Ghali (Yale) - Uro-oncology", type: "Grand Rounds" },
  { date: "2027-02-26", topic: "Prisoner Ethics - Ari / Prisoner Ethics - Small", type: "Grand Rounds" },
  { date: "2027-03-05", topic: "FACULTY MEETING", type: "Faculty Meeting" },
  { date: "2027-03-12", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2027-03-19", topic: "Journal Club", type: "Journal Club" },
  { date: "2027-03-26", topic: "Quality Improvement: Stats/M&Ms/Indications - Feb/ March / Sub-I Presentation (1 - 15 min)", type: "Grand Rounds" },
  { date: "2027-04-09", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2027-04-16", topic: "Guest Speaker - Contract Negotiations / Prosthetics Talk - Dr. Pedro Maria", type: "Grand Rounds" },
  { date: "2027-04-23", topic: "Sub-I Presentation (15 min)/PGY 4 Subspecialty / Dr Kelvin Davies - Testing a Paradigm Shift: Erectile Dysfunction as a Causal Driver of Cardiovascular Disease.", type: "Grand Rounds" },
  { date: "2027-04-30", topic: "Quality Improvement: Stats/M&Ms/Indications - March/April", type: "Grand Rounds" },
  { date: "2027-05-07", topic: "Peds / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2027-05-28", topic: "Journal Club/ STATs with Dr. Aggaliu", type: "Journal Club" },
  { date: "2027-06-04", topic: "Quality Improvement: Stats/M&Ms/Indications - May", type: "Grand Rounds" },
  { date: "2027-06-11", topic: "Dr. Kryger VP / Peds Multidisciplinary", type: "Peds Grand Rounds" },
  { date: "2027-06-25", topic: "FACULTY MEETING", type: "Faculty Meeting" },
];

// Zoom details shown on the page
const ZOOM_DETAILS = { id: "867 7387 8358", passcode: "466916" };

async function renderEmailSendLog() {
  const content = document.getElementById('pageContent');

  // Build lookup maps
  const realSendMap = {};
  SEND_LOG.realSends.forEach(s => { realSendMap[s.date] = s; });
  const testOnlySet = new Set(SEND_LOG.testOnlyDates);

  // Stats
  const totalEvents = ALL_GR_EVENTS.length;
  const realSentCount = SEND_LOG.realSends.length;
  const pendingCount = totalEvents - realSentCount;

  // Build event rows
  const rows = ALL_GR_EVENTS.map((e, i) => {
    const real = realSendMap[e.date];
    const isTest = !real && testOnlySet.has(e.date);
    const isPending = !real && !isTest;

    let badge, badgeClass, statusIcon;
    if (real) {
      badge = 'SENT TO ALL';
      badgeClass = 'status-sent';
      statusIcon = '✅';
    } else if (isTest) {
      badge = 'TEST ONLY';
      badgeClass = 'status-test';
      statusIcon = '🧪';
    } else {
      badge = 'PENDING';
      badgeClass = 'status-pending';
      statusIcon = '⬜';
    }

    // Type tag
    let typeTag = '';
    if (e.type === 'Peds Grand Rounds') typeTag = '<span class="tag tag-peds">PEDS</span>';
    else if (e.type === 'Faculty Meeting') typeTag = '<span class="tag tag-faculty">FACULTY</span>';
    else if (e.type === 'Journal Club') typeTag = '<span class="tag tag-jc">JC</span>';
    else typeTag = '<span class="tag tag-gr">GR</span>';

    // Format date nicely
    const d = new Date(e.date + 'T00:00:00');
    const dateStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

    // Detail line for sent events
    let detail = '';
    if (real) {
      detail = `<div class="event-detail">
        <span class="detail-item">📧 ${real.emails} emails sent</span>
        <span class="detail-item">❌ ${real.failed} failed</span>
        <span class="detail-item">📅 Sent on ${real.sentAt}</span>
        <span class="detail-item">🔗 Zoom ${ZOOM_DETAILS.id}</span>
      </div>`;
    } else if (isTest) {
      detail = `<div class="event-detail"><span class="detail-item warn">⚠️ Only sent to test address (sfrasier@montefiore.org) — not delivered to team</span></div>`;
    } else {
      detail = `<div class="event-detail"><span class="detail-item muted">Not yet sent to the team</span></div>`;
    }

    return `
      <div class="send-log-row ${real ? 'row-sent' : ''}">
        <div class="row-status">${statusIcon}</div>
        <div class="row-content">
          <div class="row-main">
            <span class="row-date">${dateStr}</span>
            ${typeTag}
            <span class="row-topic">${escapeHtml(e.topic)}</span>
          </div>
          ${detail}
        </div>
        <div class="row-badge">
          <span class="send-badge ${badgeClass}">${badge}</span>
        </div>
      </div>`;
  }).join('');

  content.innerHTML = `
    <style>
      .send-log-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
      }
      .summary-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
      }
      .summary-card .num { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
      .summary-card .lbl { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
      .summary-card.sent .num { color: var(--green); }
      .summary-card.pending .num { color: var(--yellow); }
      .summary-card.total .num { color: var(--text); }

      .send-log-row {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        padding: 14px 16px;
        border-bottom: 1px solid var(--border);
        transition: background 0.15s;
      }
      .send-log-row:hover { background: var(--bg-hover); }
      .send-log-row.row-sent { background: var(--green-dim, rgba(34,197,94,0.05)); }
      .row-status { font-size: 18px; padding-top: 2px; flex-shrink: 0; }
      .row-content { flex: 1; min-width: 0; }
      .row-main { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
      .row-date { font-weight: 600; font-size: 14px; white-space: nowrap; }
      .row-topic { font-size: 14px; color: var(--text-secondary); }
      .event-detail { margin-top: 6px; display: flex; gap: 16px; flex-wrap: wrap; }
      .detail-item { font-size: 12px; color: var(--text-muted); }
      .detail-item.warn { color: var(--yellow); }
      .detail-item.muted { color: var(--text-muted); }
      .row-badge { flex-shrink: 0; }

      .send-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }
      .send-badge.status-sent { background: var(--green-dim, rgba(34,197,94,0.15)); color: var(--green); }
      .send-badge.status-test { background: var(--yellow-dim, rgba(234,179,8,0.15)); color: var(--yellow); }
      .send-badge.status-pending { background: var(--bg-card); color: var(--text-muted); border: 1px solid var(--border); }

      .tag {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
      }
      .tag-peds { background: #dbeafe; color: #1d4ed8; }
      .tag-faculty { background: #fef3c7; color: #92400e; }
      .tag-jc { background: #e0e7ff; color: #4338ca; }
      .tag-gr { background: #d1fae5; color: #065f46; }

      .send-log-container {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
      }
      .send-log-header {
        padding: 14px 16px;
        border-bottom: 1px solid var(--border);
        font-weight: 600;
        font-size: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .zoom-info {
        font-size: 12px;
        color: var(--text-muted);
        font-weight: 400;
      }
      .legend {
        display: flex;
        gap: 16px;
        margin-bottom: 16px;
        font-size: 12px;
        color: var(--text-muted);
      }
      .legend-item { display: flex; align-items: center; gap: 6px; }
    </style>

    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📤 Email Send Log</h1>
        <p class="page-subtitle">Grand Rounds calendar invites — tracking real sends vs test/pending</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderEmailSendLog()">🔄 Refresh</button>
      </div>
    </div>

    <div class="send-log-summary">
      <div class="summary-card sent">
        <div class="num">${realSentCount}</div>
        <div class="lbl">Sent to Team</div>
      </div>
      <div class="summary-card pending">
        <div class="num">${pendingCount}</div>
        <div class="lbl">Pending</div>
      </div>
      <div class="summary-card total">
        <div class="num">${totalEvents}</div>
        <div class="lbl">Total Events</div>
      </div>
      <div class="summary-card sent">
        <div class="num">${SEND_LOG.realSends.reduce((a, s) => a + s.emails, 0)}</div>
        <div class="lbl">Total Emails Sent</div>
      </div>
    </div>

    <div class="legend">
      <div class="legend-item"><span class="send-badge status-sent">SENT TO ALL</span> Individual .ics with RSVP — delivered to all 42 recipients</div>
      <div class="legend-item"><span class="send-badge status-test">TEST ONLY</span> Only sent to test address — team did NOT receive</div>
      <div class="legend-item"><span class="send-badge status-pending">PENDING</span> Not yet sent</div>
    </div>

    <div class="send-log-container">
      <div class="send-log-header">
        <span>Grand Rounds Schedule — Send Status</span>
        <span class="zoom-info">Zoom: ${ZOOM_DETAILS.id} · Passcode: ${ZOOM_DETAILS.passcode}</span>
      </div>
      ${rows}
    </div>
  `;
}
