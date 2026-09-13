// ──────────────────────────────────────────────────────────────
// Grand Rounds Schedule Manager — Full interactive editor
// Embedded into Agentic OS dashboard
// ──────────────────────────────────────────────────────────────

// Embedded schedule data (2026-2027 Grand Rounds)
// Columns: 0=Month, 1=Monday Date, 2=Mon AM Conference, 3=Resident, 4=Attending,
//          5=CME7-8, 6=CME8-9, 7=Friday Date, 8=GR 7-8, 9=GR 8-9, 10=Other
// Schedule data loads from the CANONICAL store (unified.grand_rounds)
// via GET /api/conference/schedule — NO embedded schedule arrays (single source).
let GR_DATA = [];

async function ensureGRData() {
  if (GR_DATA.length > 0) return true;
  try {
    const resp = await fetch('/api/conference/schedule');
    const data = await resp.json();
    if (!data || !data.rows) throw new Error((data && data.error) || 'no rows');
    GR_DATA = data.rows.map(r => [
      r.month || '', r.mon_date || '', r.mon_topic || '', r.resident || '',
      r.attending || '', '', '', r.fri_date || '', r.gr_7_8 || '', r.gr_8_9 || '',
      r.notes || '', (r.tb || '')
    ]);
    return true;
  } catch (err) {
    console.error('GR schedule load failed:', err);
    const c = document.getElementById('suitePane') || document.getElementById('pageContent');
    if (c) c.innerHTML = '<div class="card" style="padding:24px;color:var(--red)">⚠️ Could not load schedule from the database: ' + escapeHtml(String(err && err.message || err)) + '</div>';
    return false;
  }
}

let grFilters = { skipNoGR: true, skipFaculty: false, skipHoliday: true, search: '', month: '' };
let grCmeCodes = {};  // { "YYYY-MM-DD": { hour1: "code", hour2: "code" } }

// ──────────────────────────────────────────────────────────────
// Main render function
// ──────────────────────────────────────────────────────────────
async function renderGrandRounds(target) {
  const content = target || document.getElementById('suitePane') || document.getElementById('pageContent');
  
  // Build the parsed meeting list from embedded data
  const meetings = await parseGrandRoundsData();
  
content.innerHTML = `
  <div class="page-header">
    <div class="page-header-left">
      <h1 class="page-title">📋 Grand Rounds Schedule Manager</h1>
      <p class="page-subtitle">Urology Academic Schedule 2026-2027 — Edit CME codes & send invites</p>
    </div>
    <div class="btn-group">
      <button class="btn" onclick="renderGrandRounds()">🔄 Refresh</button>
      <button class="btn" onclick="viewMonday()">📋 View Monday SASP</button>
    </div>
  </div>

    <div style="display:grid;grid-template-columns:280px 1fr;gap:14px;align-items:start">
      <!-- Sidebar Controls -->
      <div class="card" style="position:sticky;top:70px">
        <div class="card-header"><span class="card-title">⚙ Controls</span></div>
        <div class="card-body" style="font-size:13px">
          
          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--text-muted);margin-bottom:4px;font-size:12px">Distribution Lists</label>
            <select id="grListPicker" onchange="applyGrDistribution(this.value)" style="width:100%;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:5px 7px;font-size:12px;margin-bottom:4px">
              <option value="">Load a saved list…</option>
            </select>
            <input type="text" id="grResidentList" placeholder="Recipients (comma-separated)" style="width:100%;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:5px 7px;font-size:12px;margin-bottom:4px" />
            <input type="text" id="grFacultyList" placeholder="Faculty list" style="display:none" />
            <div style="display:flex;gap:4px;align-items:center;font-size:11px;color:var(--text-muted)">
              <span id="grListCount">0 recipients</span>
              <button class="btn btn-sm" style="margin-left:auto;font-size:11px" onclick="loadGrEmailGroups()">↻ Refresh</button>
              <button class="btn btn-sm" style="font-size:11px" onclick="navigate('distribution')" title="Open full Distribution Lists tab">👥 Manage</button>
            </div>
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--text-muted);margin-bottom:4px;font-size:12px">Location / Zoom</label>
            <input type="text" id="grLocation" placeholder="Room or Zoom link" style="width:100%;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:5px 7px;font-size:12px" />
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--text-muted);margin-bottom:4px;font-size:12px">Filters</label>
            <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin:3px 0;cursor:pointer">
              <input type="checkbox" id="grFilterNoGR" ${grFilters.skipNoGR?'checked':''} onchange="grFilters.skipNoGR=this.checked;renderGrandRounds()" /> Hide "NO GRAND ROUNDS"
            </label>
            <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin:3px 0;cursor:pointer">
              <input type="checkbox" id="grFilterFaculty" ${grFilters.skipFaculty?'checked':''} onchange="grFilters.skipFaculty=this.checked;renderGrandRounds()" /> Hide FACULTY MEETING
            </label>
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--text-muted);margin-bottom:4px;font-size:12px">Month Jump</label>
            <select id="grMonthJump" onchange="grFilters.month=this.value;renderGrandRounds()" style="width:100%;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:5px 7px;font-size:12px">
              <option value="">All months</option>
              ${['July','August','September','October','November','December','January','February','March','April','May','June','July 2027'].map(m => 
                '<option value="' + m + '"' + (grFilters.month===m?' selected':'') + '>' + m + '</option>'
              ).join('')}
            </select>
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--text-muted);margin-bottom:4px;font-size:12px">Bulk Paste CME Codes</label>
            <textarea id="grBulkCodes" placeholder="YYYY-MM-DD, CODE1, CODE2" style="width:100%;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:5px 7px;font-size:11px;min-height:60px;font-family:monospace"></textarea>
            <button class="btn btn-sm" style="margin-top:4px;width:100%;font-size:11px" onclick="applyBulkCodes()">Apply Codes</button>
          </div>

          <div style="display:flex;flex-direction:column;gap:4px;margin-top:8px">
            <button class="btn btn-sm" style="font-size:11px" onclick="openAllOutlook()">📧 Open All in Outlook</button>
            <button class="btn btn-sm" style="font-size:11px" onclick="downloadAllIcs()">📥 Download All .ics</button>
            <button class="btn btn-sm" style="font-size:11px" onclick="saveCodesLocally()">💾 Save Codes</button>
          </div>
        </div>
      </div>

      <!-- Main Table -->
      <div>
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap">
          <span style="font-size:13px;color:var(--text-muted)">
            <span id="grCount">${meetings.length}</span> meetings visible
          </span>
          <input type="text" placeholder="Search..." id="grSearch" oninput="grFilters.search=this.value;renderGrandRounds()" style="var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:4px 8px;font-size:12px;flex:1;min-width:150px" />
        </div>

        <div style="overflow-x:auto;border:1px solid var(--border);border-radius:8px">
          <table style="width:100%;border-collapse:collapse;font-size:12px">
            <thead>
              <tr style="var(--bg-input);border-bottom:1px solid var(--border)">
                <th style="padding:8px 10px;text-align:left;white-space:nowrap">Date</th>
                <th style="padding:8px 10px;text-align:left">Meeting (7-8 AM)</th>
                <th style="padding:8px 10px;text-align:left;width:85px">CME Code 1</th>
                <th style="padding:8px 10px;text-align:left">Conference (8-9 AM)</th>
                <th style="padding:8px 10px;text-align:left;width:85px">CME Code 2</th>
                <th style="padding:8px 10px;text-align:center;width:130px">Actions</th>
              </tr>
            </thead>
            <tbody id="grTableBody">
              ${renderTableRows(meetings)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  // Load saved codes from localStorage
  loadCodes();
  loadGrEmailGroups();
}

// ──────────────────────────────────────────────────────────────
// Parse schedule data into meeting rows
// ──────────────────────────────────────────────────────────────
async function parseGrandRoundsData() {
  await ensureGRData();
  const results = [];
  
  for (const row of GR_DATA) {
    const fri = row[7];
    const gr1 = (row[8] || '').trim();
    const gr2 = (row[9] || '').trim();
    const other = (row[10] || '').trim();
    const monAM = (row[2] || '').trim();
    const resident = (row[3] || '').trim();
    const attending = (row[4] || '').trim();
    const month = row[0] || '';
    
    if (!fri) continue;
    const isFaculty = /faculty\s*meeting/i.test(gr1);
    const isNoGR = /no\s*grand\s*rounds/i.test(gr1);
    
    // Apply filters
    if (grFilters.skipNoGR && isNoGR) continue;
    if (grFilters.skipFaculty && isFaculty) continue;
    if (grFilters.month && !fri.startsWith(grFilters.month.substring(0,4))) continue;
    if (grFilters.search) {
      const q = grFilters.search.toLowerCase();
      if (!gr1.toLowerCase().includes(q) && !gr2.toLowerCase().includes(q) && !other.toLowerCase().includes(q) &&
          !monAM.toLowerCase().includes(q) && !resident.toLowerCase().includes(q)) continue;
    }
    
    results.push({
      date: fri,
      month,
      title1: gr1 || '—',
      title2: gr2 || '—',
      notes: other,
      monAM,
      resident,
      attending,
      isFaculty,
      isNoGR,
      row
    });
  }
  
  return results;
}

// ──────────────────────────────────────────────────────────────
// Render table rows
// ──────────────────────────────────────────────────────────────
function renderTableRows(meetings) {
  return meetings.map((m, i) => {
    const codes = grCmeCodes[m.date] || {};
    const code1 = codes.hour1 || '';
    const code2 = codes.hour2 || '';
    const facBadge = m.isFaculty ? '<span style="background:var(--yellow-dim);border:1px solid transparent;color:var(--yellow);padding:1px 6px;border-radius:999px;font-size:10px;font-weight:600">FACULTY</span>' : '';
    
    return `
      <tr style="border-bottom:1px solid var(--border);${m.isNoGR ? 'opacity:0.6' : ''} ${m.isFaculty ? 'background:rgba(251,191,36,.04)' : ''}">
        <td style="padding:8px 10px;white-space:nowrap;vertical-align:top">
          <strong>${m.date}</strong>
          <div style="font-size:10px;color:var(--text-muted)">${getDayOfWeek(m.date)}</div>
        </td>
        <td style="padding:8px 10px;vertical-align:top">
          ${escapeHtml(m.title1)}
          ${m.notes ? `<div style="font-size:10px;color:var(--text-muted);margin-top:2px">${escapeHtml(m.notes)}</div>` : ''}
          ${facBadge}
        </td>
        <td style="padding:8px 10px;vertical-align:top">
          ${m.title1 !== '—' ? `<input type="text" value="${code1}" data-date="${m.date}" data-slot="hour1" class="gr-code-input" style="width:80px;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;padding:3px 5px;font-size:12px;font-family:monospace" onchange="updateCode('${m.date}','hour1',this.value)" />` : '<span style="color:var(--text-muted)">—</span>'}
        </td>
        <td style="padding:8px 10px;vertical-align:top">${escapeHtml(m.title2)}</td>
        <td style="padding:8px 10px;vertical-align:top">
          ${m.title2 !== '—' ? `<input type="text" value="${code2}" data-date="${m.date}" data-slot="hour2" class="gr-code-input" style="width:80px;var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:4px;padding:3px 5px;font-size:12px;font-family:monospace" onchange="updateCode('${m.date}','hour2',this.value)" />` : '<span style="color:var(--text-muted)">—</span>'}
        </td>
        <td style="padding:8px 10px;text-align:center;white-space:nowrap">
          <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="openOutlookForDate('${m.date}','${m.title1}','${m.title2}')" title="Open in Outlook">📧</button>
          <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="downloadIcsForDate('${m.date}','${m.title1}','${m.title2}')" title="Download .ics">📥</button>
        </td>
      </tr>
    `;
  }).join('');
}

function getDayOfWeek(dateStr) {
  const d = new Date(dateStr + 'T12:00:00');
  return ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][d.getDay()];
}

// ──────────────────────────────────────────────────────────────
// Monday Resident Conference Table + ICS Sent Status
// ──────────────────────────────────────────────────────────────
let monIcsProgress = null;

async function loadMonIcsProgress() {
  try {
    const resp = await fetch('/api/progress/ics');
    monIcsProgress = await resp.json();
  } catch { monIcsProgress = null; }
}

function icsSentBadge(date) {
  if (!monIcsProgress) return '<span style="color:var(--text-muted);font-size:11px">⋯</span>';
  const sent = monIcsProgress.monday_sasp?.ics_sent_dates || [];
  return sent.includes(date)
    ? '<span style="color:var(--green);font-weight:600;font-size:13px">✅ Sent</span>'
    : '<span style="color:var(--text-muted);font-size:11px">—</span>';
}

async function renderMondayTable() {
  await ensureGRData();
  const tbody = document.getElementById('grTableBody');
  if (!tbody) return;
  
  await loadMonIcsProgress();
  
  const rows = [];
  
  for (const row of GR_DATA) {
    const monDate = row[1];
    const topic = (row[2] || '').trim();
    const resident = (row[3] || '').trim();
    const attending = (row[4] || '').trim();
    const other = (row[10] || '').trim();
    
    if (!monDate) continue;
    
    // Skip empty/holiday rows if filter is on
    if (grFilters.skipHoliday && (!topic || /holiday/i.test(topic))) continue;
    
    // Search filter
    if (grFilters.search) {
      const q = grFilters.search.toLowerCase();
      if (!topic.toLowerCase().includes(q) && !resident.toLowerCase().includes(q) && 
          !attending.toLowerCase().includes(q)) continue;
    }
    
    rows.push({
      date: monDate,
      topic: topic || '—',
      resident: resident || '—',
      attending: attending || '—',
      notes: other
    });
  }
  
  // Update count
  const countEl = document.getElementById('grCount');
  if (countEl) countEl.textContent = rows.length;
  
if (rows.length === 0) {
  tbody.innerHTML = `<tr><td colspan="6" style="padding:30px;text-align:center;color:var(--text-muted)">No matching Monday conferences</td></tr>`;
  return;
}
  
tbody.innerHTML = rows.map(r => `
  <tr style="border-bottom:1px solid var(--border)">
    <td style="padding:8px 10px;white-space:nowrap;vertical-align:top">
      <strong>${r.date}</strong>
      <div style="font-size:10px;color:var(--text-muted)">${getDayOfWeek(r.date)}</div>
    </td>
    <td style="padding:8px 10px;vertical-align:top">
      <strong>${escapeHtml(r.topic)}</strong>
      ${r.notes ? `<div style="font-size:10px;color:var(--text-muted);margin-top:2px">${escapeHtml(r.notes)}</div>` : ''}
    </td>
    <td style="padding:8px 10px;vertical-align:top">${escapeHtml(r.resident)}</td>
    <td style="padding:8px 10px;vertical-align:top">${escapeHtml(r.attending)}</td>
    <td style="padding:8px 10px;text-align:center;vertical-align:top">${icsSentBadge(r.date)}</td>
    <td style="padding:8px 10px;text-align:center;white-space:nowrap">
      <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="openMondayOutlook('${r.date}','${r.topic.replace(/'/g,"\\'")}','${r.resident.replace(/'/g,"\\'")}','${r.attending.replace(/'/g,"\\'")}')" title="Open in Outlook">📧</button>
      <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="downloadMondayIcs('${r.date}','${r.topic.replace(/'/g,"\\'")}','${r.resident.replace(/'/g,"\\'")}','${r.attending.replace(/'/g,"\\'")}')" title="Download .ics">📥</button>
    </td>
  </tr>
`).join('');
}

// ─── View Monday SASP table ─────────────────────────────────

async function viewMonday() {
  await ensureGRData();
  const content = document.getElementById('suitePane') || document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📋 Monday SASP Conferences</h1>
        <p class="page-subtitle">Urology Resident Monday Morning Conferences 2026-2027</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderGrandRounds()">📋 View Grand Rounds</button>
      </div>
    </div>

    <div>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap">
        <span style="font-size:13px;color:var(--text-muted)">
          <span id="grCount">0</span> Monday meetings
        </span>
        <input type="text" placeholder="Search..." id="grSearch" oninput="grFilters.search=this.value;renderMondayTable()" style="var(--bg-input);color:var(--text-primary);border:1px solid var(--border);border-radius:5px;padding:4px 8px;font-size:12px;flex:1;min-width:150px" />
      </div>

      <div style="overflow-x:auto;border:1px solid var(--border);border-radius:8px">
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="var(--bg-input);border-bottom:1px solid var(--border)">
              <th style="padding:8px 10px;text-align:left;white-space:nowrap">Date</th>
              <th style="padding:8px 10px;text-align:left">Topic</th>
              <th style="padding:8px 10px;text-align:left">Resident</th>
              <th style="padding:8px 10px;text-align:left">Attending</th>
              <th style="padding:8px 10px;text-align:center">ICS Sent</th>
              <th style="padding:8px 10px;text-align:center;width:90px">Actions</th>
            </tr>
          </thead>
          <tbody id="grTableBody">
            <tr><td colspan="6" style="padding:30px;text-align:center;color:var(--text-muted)">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
  await renderMondayTable();
}

function openMondayOutlook(date, topic, resident, attending) {
  const loc = document.getElementById('grLocation')?.value || 'Hutch I PH2 Conf A';
  const rList = document.getElementById('grResidentList')?.value || '';
  const attendees = rList;

  const subj = `Urology Monday Conference — ${topic}${attending ? ', Dr. ' + attending : ''}`;
  const dt = new Date(date + 'T12:00:00');
  const formatted = dt.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  const body = window.buildRsvpBody({
    header: 'Montefiore Urology - Resident AM Conference',
    date: formatted,
    time: '7:00 - 8:00 AM (Eastern)',
    location: loc,
    extra: [
      `<strong>Topic</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;${topic || 'TBD'}`,
      `<strong>Resident</strong>&nbsp;&nbsp;&nbsp;${resident || 'TBD'}`,
      `<strong>Attending</strong>&nbsp;&nbsp;${attending || 'TBD'}`,
    ],
  });

  window.openEventEditor({
    subject: subj, body, to: attendees,
    startdt: `${date}T07:00:00`, enddt: `${date}T08:00:00`,
    location: loc, bodyType: 'HTML',
  });
}

function downloadMondayIcs(date, topic, resident, attending) {
  const loc = document.getElementById('grLocation')?.value || '';
  const subj = `Resident AM Conference: ${topic}`;
  
  let ics = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Resident Conference//EN\r\n';
  ics += `BEGIN:VEVENT\r\nUID:mon-${date}@resident-conf\r\nDTSTART:${date.replace(/-/g,'')}T070000\r\nDTEND:${date.replace(/-/g,'')}T080000\r\nSUMMARY:${subj}\r\nLOCATION:${loc}\r\nDESCRIPTION:Resident: ${resident}\\nAttending: ${attending}\r\nEND:VEVENT\r\n`;
  ics += 'END:VCALENDAR';
  
  const blob = new Blob([ics], {type: 'text/calendar'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `resident-conf-${date}.ics`;
  a.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ──────────────────────────────────────────────────────────────
// CME Code Management
// ──────────────────────────────────────────────────────────────
function updateCode(date, slot, value) {
  if (!grCmeCodes[date]) grCmeCodes[date] = {};
  grCmeCodes[date][slot] = value.trim();
  saveCodesLocally();
}

function loadCodes() {
  try {
    const saved = localStorage.getItem('grCmeCodes');
    if (saved) grCmeCodes = JSON.parse(saved);
  } catch {}
}

function saveCodesLocally() {
  try {
    localStorage.setItem('grCmeCodes', JSON.stringify(grCmeCodes));
    showToast('💾 Codes saved locally', 'success');
  } catch {}
}

function applyBulkCodes() {
  const text = document.getElementById('grBulkCodes').value;
  if (!text.trim()) { showToast('Paste codes first', 'warning'); return; }
  
  const lines = text.split('\n').filter(l => l.trim() && !l.startsWith('#'));
  let count = 0;
  
  for (const line of lines) {
    const parts = line.split(/[,\t;]+/).map(s => s.trim());
    if (parts.length < 2) continue;
    const date = parts[0];
    if (!grCmeCodes[date]) grCmeCodes[date] = {};
    grCmeCodes[date].hour1 = parts[1] || '';
    if (parts.length >= 3) grCmeCodes[date].hour2 = parts[2] || '';
    count++;
  }
  
  saveCodesLocally();
  renderGrandRounds();
  showToast(`✅ Applied ${count} code entries`, 'success');
}

// ──────────────────────────────────────────────────────────────
// Outlook & ICS Actions
// ──────────────────────────────────────────────────────────────
// Build a Grand Rounds event dict (shared rich template), then
// open the edit-then-send modal. Batch "Open All" uses the direct path.
function buildGrandRoundsEvent(date, title1, title2) {
  const residentList = document.getElementById('grResidentList')?.value || '';
  const facultyList = document.getElementById('grFacultyList')?.value || '';

  const isFaculty = /faculty\s*meeting/i.test(title1);
  const isPeds = /peds/i.test(title1);
  // grand_rounds list already includes both residents and faculty — don't combine
  const attendees = isFaculty ? facultyList : residentList;

  const dt = new Date(date + 'T12:00:00');
  const dayNames = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const formatted = dayNames[dt.getDay()] + ', ' + months[dt.getMonth()] + ' ' + dt.getDate() + ', ' + dt.getFullYear();

  const topic7 = (title1 && title1 !== '\u2014') ? title1 : '';
  const topic8 = (title2 && title2 !== '\u2014' && title2 !== title1) ? title2 : '';
  const mainTopic = topic7 || topic8;

  const loc7 = 'Hutch I PH2 Conf A';
  const loc8 = 'Hutch I PH2 Conf B';
  const locationStr = topic8 ? loc7 + ' (7-8) / ' + loc8 + ' (8-9)' : loc7;

  const prefix = isFaculty ? 'Faculty Meeting' : (isPeds ? 'PEDS: Urology Grand Rounds - ' : 'Urology Grand Rounds - ');
  const subject = 'Invitation: ' + prefix + mainTopic;

  const typeLabel = isFaculty ? 'Faculty Meeting' : (isPeds ? 'Peds Grand Rounds' : 'Grand Rounds');
  const zoomLink = 'https://us02web.zoom.us/j/86773878358?pwd=RUxySVVzUjFWL0lyRWtjdDBacTVPZz09';

  // Shared rich template — same structure for every event type
  const body = window.buildRsvpBody({
    header: 'Montefiore Urology - Grand Rounds',
    date: formatted,
    time: '7:00 - 9:00 AM (Eastern)',
    location: locationStr,
    type: typeLabel,
    agenda: [
      { time: '7:00 - 8:00 AM', item: topic7 || '' },
      { time: '8:00 - 9:00 AM', item: topic8 || topic7 || '' },
    ],
    zoom: { link: zoomLink, id: '867 7387 8358', passcode: '466916' },
  });

  return {
    subject: subject,
    body: body,
    to: attendees,
    startdt: date + 'T07:00:00',
    enddt: date + 'T09:00:00',
    location: locationStr,
    bodyType: 'HTML',
  };
}

function openOutlookForDate(date, title1, title2) {
  window.openEventEditor(buildGrandRoundsEvent(date, title1, title2));
}

function downloadIcsForDate(date, title1, title2) {
  const codes = grCmeCodes[date] || {};
  const loc = document.getElementById('grLocation')?.value || '';
  let ics = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Grand Rounds Scheduler//EN\r\n';
  
  if (title1 && title1 !== '—') {
    const subj = codes.hour1 ? `[CME ${codes.hour1}] Grand Rounds: ${title1}` : `Grand Rounds: ${title1}`;
    ics += `BEGIN:VEVENT\r\nUID:${date}-1@grand-rounds\r\nDTSTART:${date.replace(/-/g,'')}T070000\r\nDTEND:${date.replace(/-/g,'')}T080000\r\nSUMMARY:${subj}\r\nLOCATION:${loc}\r\nDESCRIPTION:CME Code: ${codes.hour1||'N/A'}\\nUrology Grand Rounds\r\nEND:VEVENT\r\n`;
  }
  if (title2 && title2 !== '—') {
    const subj2 = codes.hour2 ? `[CME ${codes.hour2}] Grand Rounds Conference: ${title2}` : `Grand Rounds Conference: ${title2}`;
    ics += `BEGIN:VEVENT\r\nUID:${date}-2@grand-rounds\r\nDTSTART:${date.replace(/-/g,'')}T080000\r\nDTEND:${date.replace(/-/g,'')}T090000\r\nSUMMARY:${subj2}\r\nLOCATION:${loc}\r\nDESCRIPTION:CME Code: ${codes.hour2||'N/A'}\\nUrology Grand Rounds Conference\r\nEND:VEVENT\r\n`;
  }
  ics += 'END:VCALENDAR';
  
  const blob = new Blob([ics], {type: 'text/calendar'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `grand-rounds-${date}.ics`;
  a.click();
  URL.revokeObjectURL(url);
}

async function openAllOutlook() {
  const inputs = document.querySelectorAll('.gr-code-input');
  inputs.forEach(inp => {
    updateCode(inp.dataset.date, inp.dataset.slot, inp.value);
  });
  showToast('Opening all in Outlook... (pop-ups must be allowed)', 'info');
  
  // Collect unique dates
  const dates = [...new Set(Array.from(document.querySelectorAll('.gr-code-input')).map(i => i.dataset.date))];
  // Use the meetings list
  const meetings = await parseGrandRoundsData();
  let idx = 0;
  for (const m of meetings) {
    setTimeout(() => window.openEventDirect(buildGrandRoundsEvent(m.date, m.title1, m.title2)), idx * 800);
    idx++;
    if (idx > 20) {
      showToast('Opening first 20 meetings to avoid overwhelming your browser', 'warning');
      break;
    }
  }
}

async function downloadAllIcs() {
  const meetings = await parseGrandRoundsData();
  if (meetings.length === 0) { showToast('No meetings to download', 'warning'); return; }
  
  // Download one combined .ics file
  let combinedIcs = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Grand Rounds Scheduler//EN\r\n';
  const loc = document.getElementById('grLocation')?.value || '';
  
  for (const m of meetings) {
    const codes = grCmeCodes[m.date] || {};
    if (m.title1 && m.title1 !== '—') {
      const subj = codes.hour1 ? `[CME ${codes.hour1}] Grand Rounds: ${m.title1}` : `Grand Rounds: ${m.title1}`;
      combinedIcs += `BEGIN:VEVENT\r\nUID:${m.date}-1@gr\r\nDTSTART:${m.date.replace(/-/g,'')}T070000\r\nDTEND:${m.date.replace(/-/g,'')}T080000\r\nSUMMARY:${subj}\r\nLOCATION:${loc}\r\nEND:VEVENT\r\n`;
    }
    if (m.title2 && m.title2 !== '—') {
      const subj2 = codes.hour2 ? `[CME ${codes.hour2}] Grand Rounds Conference: ${m.title2}` : `Grand Rounds Conference: ${m.title2}`;
      combinedIcs += `BEGIN:VEVENT\r\nUID:${m.date}-2@gr\r\nDTSTART:${m.date.replace(/-/g,'')}T080000\r\nDTEND:${m.date.replace(/-/g,'')}T090000\r\nSUMMARY:${subj2}\r\nLOCATION:${loc}\r\nEND:VEVENT\r\n`;
    }
  }
  combinedIcs += 'END:VCALENDAR';
  
  const blob = new Blob([combinedIcs], {type: 'text/calendar'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'all-grand-rounds-2026-2027.ics';
  a.click();
  URL.revokeObjectURL(url);
  showToast(`✅ Downloaded ${meetings.length} meetings as .ics`, 'success');
}


// ── Load real email groups from API ─────────────────────────
async function loadGrEmailGroups() {
  try {
    const data = await api.get('/api/crm/email-groups');
    if (!data) return;
    // Populate the "Load a saved list…" picker with all groups
    const picker = document.getElementById('grListPicker');
    if (picker) {
      const opts = Object.entries(data).map(([key, g]) =>
        `<option value="${key}">${escapeHtml(g.label || key)} (${(g.emails||[]).length})</option>`
      ).join('');
      picker.innerHTML = '<option value="">Load a saved list…</option>' + opts;
    }
    // Pre-fill the recipient fields from the default groups
    const resEl = document.getElementById('grResidentList');
    const facEl = document.getElementById('grFacultyList');
    const res = data.grand_rounds;
    const fac = data.faculty;
    if (resEl && res && res.emails && res.emails.length) {
      resEl.value = res.emails.join(', ');
    }
    if (facEl && fac && fac.emails && fac.emails.length) {
      facEl.value = fac.emails.join(', ');
    }
    updateGrListCount();
  } catch(e) {
    console.warn('Could not load email groups:', e);
  }
}

// Load a chosen saved distribution list into the recipient field
function applyGrDistribution(key) {
  if (!key) return;
  api.get('/api/crm/email-groups').then(data => {
    const g = data && data[key];
    const resEl = document.getElementById('grResidentList');
    if (g && g.emails && resEl) {
      resEl.value = g.emails.join(', ');
      updateGrListCount();
      showToast(`Loaded ${g.emails.length} recipients (${g.label || key})`, 'success');
    }
  }).catch(() => showToast('Could not load list', 'error'));
}

function updateGrListCount() {
  const resEl = document.getElementById('grResidentList');
  const countEl = document.getElementById('grListCount');
  if (resEl && countEl && resEl.value) {
    const n = resEl.value.split(',').filter(e => e.trim().includes('@')).length;
    countEl.textContent = n + ' recipient' + (n === 1 ? '' : 's');
  }
}

// Hook the count to update as the user edits the field
document.addEventListener('input', (ev) => {
  if (ev.target && ev.target.id === 'grResidentList') updateGrListCount();
});
