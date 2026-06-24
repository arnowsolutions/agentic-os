// ──────────────────────────────────────────────────────────────
// Grand Rounds Schedule Manager — Full interactive editor
// Embedded into Agentic OS dashboard
// ──────────────────────────────────────────────────────────────

// Embedded schedule data (2026-2027 Grand Rounds)
// Columns: 0=Month, 1=Monday Date, 2=Mon AM Conference, 3=Resident, 4=Attending,
//          5=CME7-8, 6=CME8-9, 7=Friday Date, 8=GR 7-8, 9=GR 8-9, 10=Other
const GR_DATA = [
  ["July","2026-07-06","SASP","Val","Laudano","","","2026-07-03","NO GRAND ROUNDS","","7/4 - Independence Day"],
  ["","2026-07-13","SASP","Jake","Raskolnikov","","","2026-07-10","Peds","Peds Multidisciplinary","confirmed"],
  ["","2026-07-20","SASP","Sam","Lowe","","","2026-07-17","Sankin expectations overview (1hr)","Sub-I talks - 0.75 hr (3)",""],
  ["","2026-07-27","SASP","Rutul","Theofanides","","","2026-07-24","SASP Review with Dr. Lowe/Lipsky","",""],
  ["August","2026-08-03","SASP","Kelli","Maria","","","2026-07-31","Quality Improvement: Stats/M&Ms/Indications June/ July","",""],
  ["","2026-08-10","SASP","Joe","Ohmann","","","2026-08-07","SASP Review with Dr. Lipsky","",""],
  ["","2026-08-17","SASP","Hordines","Small","","","2026-08-14","","Sub-I talks - 0.5 hr (2)","No PEDS GR"],
  ["","2026-08-24","SASP","Hill","Abraham","","","2026-08-21","NO GRAND ROUNDS","",""],
  ["","2026-08-31","SASP","N/A","Lipsky","","","2026-08-28","PGY-4 Subspeciality Presentations","Sub-I talks - 0.75 hr (3)",""],
  ["September","2026-09-07","SASP","Dimindra","Donnelly","","","2026-09-04","NO GRAND ROUNDS vs QPS","","9/7 - Labor Day"],
  ["","2026-09-14","SASP","Farz","Chalouhy / Cedar","","","2026-09-11","Peds","Peds Multidisciplinary","Rosh Hashana Sept 12-13"],
  ["","2026-09-21","SASP","Ari","Reese","","","2026-09-18","FACULTY MEETING","",""],
  ["","2026-09-28","SASP","Val","Sankin","","","2026-09-25","","Sub-I talks - 0.75 hr (3)","Yom Kipur 9/21; Sukkot 9/26-27"],
  ["October","2026-10-05","UTUCC & Urinary diversions","Jake","Cedars","","","2026-10-02","Quality Improvement: Stats/M&Ms/Indications Aug/ Sept","","Sukkot 10/3-4"],
  ["","2026-10-12","Renal neoplasms benign, malignant + metastatic","Sam","Dr Mallahan","","","2026-10-09","Peds","Peds Multidisciplinary",""],
  ["","2026-10-19","Penile Ca & Urethral Ca","SASP","Lowe","","","2026-10-16","","",""],
  ["","2026-10-26","Testis Ca","Joe","Sankin","","","2026-10-23","Sub-Intern Presentations - 1 hr (4)","",""],
  ["November","2026-11-02","Prostate Cancer eval/risk, localized tx and advanced tx","Kelli","Watts","","","2026-10-30","","PGY-4 Subspeciality Presentations",""],
  ["","2026-11-09","Round robin ISE #1 (covering peds + onc)","","Lipsky","","","2026-11-06","FACULTY MEETING","","Diwali 11/8"],
  ["","2026-11-16","Round robin ISE #2 (UDS/female + endo/sex/infertility)","","Lowe","","","2026-11-13","Peds ","Peds Multidisciplinary","11/15 - ISE"],
  ["","2026-11-23","Interstitial cystitis (PBS) and prostatitis","Hordines","","","","2026-11-20","","",""],
  ["December","2026-11-30","Urinary fistulas and Diverticula","Hill","Waldschmidtt","","","2026-11-27","NO GRAND ROUNDS","","11/27 - Thanksgiving"],
  ["","2026-12-07","Female SUI / POP","Pak","Laudano","","","2026-12-04","Quality Improvement: Stats/M&Ms/Indications Oct-Nov","",""],
  ["","2026-12-14","A/P orgasm and ejaculation & Female sexual dysfunction","Farz","Clearwater","","","2026-12-11","Peds","Peds Multidisciplinary",""],
  ["","2026-12-21","SASP","","","","","2026-12-18","Valentine Essay Submission Presentations","Resident QI Updates",""],
  ["","2026-12-28","Urethral stricture, posterior urethral recon and male SUI ","Pak","Cedars","","","2026-12-25","NO GRAND ROUNDS","","12/25 - Christmas"],
  ["January","2026-12-31","Holiday","","","","","2027-01-01","NO GRAND ROUNDS","","1/1 - New Year"],
  ["","2026-01-07","Urodynamics presentation, Dr. Laudano","","Laudano","","","2027-01-08","Peds ","Peds Multidisciplinary",""],
  ["","2026-01-14","A/P Low T & Treatment of hypogonadism","Dimindra","Lowe","","","2027-01-15","FACULTY MEETING","",""],
  ["","2026-01-21","UTI + STIs","Ari","","","","2027-01-22","Journal Club","","1/19 - MLK Day"],
  ["February","2026-01-28","Surgical incisions / Thermal energy","","Danzig","","","2027-01-29","","",""],
  ["","2026-02-04","SASP","Val","","","","2027-02-05","Quality Improvement: Stats/M&Ms/Indications - Dec/Jan","",""],
  ["","2026-02-11","SASP","Jake","","","","2027-02-12","Peds ","Peds Multidisciplinary",""],
  ["","2026-02-18","SASP","Sam","","","","2027-02-19","PGY-4 Subspeciality Presentations (1 hr)","Visiting Lecture: Fed Ghali (Yale) - Uro-oncology","2/16 - President's Day"],
  ["March","2026-02-25","SASP","Joe","","","","2027-02-26","Prisoner Ethics - Ari","Prisoner Ethics - Small",""],
  ["","2026-03-04","SASP","Kelli","Cedars","","","2027-03-05","FACULTY MEETING","","Inlexzo Mobile Lab 8-12"],
  ["","2026-03-11","SASP","Rutul","","","","2027-03-12","Peds ","Peds Multidisciplinary",""],
  ["","2026-03-18","SASP","Nate","","","","2027-03-19","Journal Club","","Eid al-Fitr 3-20"],
  ["","2026-03-25","SASP","Dinora","Small","","","2027-03-26","Quality Improvement: Stats/M&Ms/Indications - Feb/ March","Sub-I Presentation (1 - 15 min)",""],
  ["April","2026-04-01","SASP - Nephrolithiasis","Jasmin","Raskolnikov","","","2027-04-02","NO GRAND ROUNDS - Good Friday/ Passover","","GoodFriday 4/3; Passover 4/3-4/4"],
  ["","2026-04-08","SASP - Prolapse/SUI","Hordines","Clearwater","","","2027-04-09","Peds ","Peds Multidisciplinary","Easter 4/5; 4/8-4-9 Passover"],
  ["","2026-04-15","SASP - BPH","Hill","Lipsky","","","2027-04-16","Guest Speaker - Contract Negotiations","Prosthetics Talk - Dr. Pedro Maria",""],
  ["","2026-04-22","SASP - Stats","Jen","","","","2027-04-23","Sub-I Presentation (15 min)/PGY 4 Subspecialty","Dr Kelvin Davies - \"Testing a Paradigm Shift: Erectile Dysfunction as a Causal Driver of Cardiovascular Disease\"",""],
  ["May","2026-04-29","SASP - Prostate cancer","Ari","Watts","","","2027-04-30","Quality Improvement: Stats/M&Ms/Indications - March/April","","Resident Anatomy Simulation - Ileal Ureter"],
  ["","2026-05-06","SASP - Renal tumors","Farz","Aboumohamed","","","2027-05-07","Peds ","Peds Multidisciplinary",""],
  ["","2026-05-13","SASP - Strictures","Dimindra","Cedars","","","2027-05-14","NO GRAND ROUNDS - AUA","","AUA 5/15-18"],
  ["","2026-05-20","SASP - ED","Nate","Maria","","","2027-05-21","","",""],
  ["","2026-05-27","SASP - Testicular Tumors","Dinora","Sankin","","","2027-05-28","Journal Club/ STATs with Dr. Aggaliu","","Eid al-adha 5/27 - Memorial Day - 5/25"],
  ["June","2026-06-03","SASP - Infertility","Jasmin","Ohmann","","","2027-06-04","Quality Improvement: Stats/M&Ms/Indications - May","",""],
  ["","2026-06-10","SASP - Anatomy","Val","Lipsky","","","2027-06-11","Dr. Kryger VP","Peds Multidisciplinary",""],
  ["","2026-06-17","End of year debrief","",":(","","","2027-06-18","","","6/19 - Juneteenth, 6/17 - Graduation!"],
  ["","2026-06-24","Expectations Meeting","","","","","2027-06-25","FACULTY MEETING","",""],
  ["July","2026-07-01","SASP?","","","","","2027-07-02","","","7/4 - July 4th"],
];

let grFilters = { skipNoGR: true, skipFaculty: false, skipHoliday: true, search: '', month: '' };
let grCmeCodes = {};  // { "YYYY-MM-DD": { hour1: "code", hour2: "code" } }

// ──────────────────────────────────────────────────────────────
// Main render function
// ──────────────────────────────────────────────────────────────
async function renderGrandRounds() {
  const content = document.getElementById('pageContent');
  
  // Build the parsed meeting list from embedded data
  const meetings = parseGrandRoundsData();
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📋 Grand Rounds Schedule Manager</h1>
        <p class="page-subtitle">Urology Academic Schedule 2026-2027 — Edit CME codes & send invites</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderGrandRounds()">🔄 Refresh</button>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:280px 1fr;gap:14px;align-items:start">
      <!-- Sidebar Controls -->
      <div class="card" style="position:sticky;top:70px">
        <div class="card-header"><span class="card-title">⚙ Controls</span></div>
        <div class="card-body" style="font-size:13px">
          
          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Distribution Lists</label>
            <input type="text" id="grResidentList" placeholder="Residents email" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px;margin-bottom:4px" value="residents@x.org" />
            <input type="text" id="grFacultyList" placeholder="Faculty email" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px" value="faculty@x.org" />
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Location / Zoom</label>
            <input type="text" id="grLocation" placeholder="Room or Zoom link" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px" />
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Filters</label>
            <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin:3px 0;cursor:pointer">
              <input type="checkbox" id="grFilterNoGR" ${grFilters.skipNoGR?'checked':''} onchange="grFilters.skipNoGR=this.checked;renderGrandRounds()" /> Hide "NO GRAND ROUNDS"
            </label>
            <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin:3px 0;cursor:pointer">
              <input type="checkbox" id="grFilterFaculty" ${grFilters.skipFaculty?'checked':''} onchange="grFilters.skipFaculty=this.checked;renderGrandRounds()" /> Hide FACULTY MEETING
            </label>
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Month Jump</label>
            <select id="grMonthJump" onchange="grFilters.month=this.value;renderGrandRounds()" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px">
              <option value="">All months</option>
              ${['July','August','September','October','November','December','January','February','March','April','May','June','July 2027'].map(m => 
                `<option value="${m}" ${grFilters.month===m?'selected':''}>${m}</option>`
              ).join('')}
            </select>
          </div>

          <div style="margin-bottom:10px">
            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Bulk Paste CME Codes</label>
            <textarea id="grBulkCodes" placeholder="YYYY-MM-DD, CODE1, CODE2" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:11px;min-height:60px;font-family:monospace"></textarea>
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
          <span style="font-size:13px;color:var(--muted)">
            <span id="grCount">${meetings.length}</span> meetings visible
          </span>
          <input type="text" placeholder="Search..." id="grSearch" oninput="grFilters.search=this.value;renderGrandRounds()" style="background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:4px 8px;font-size:12px;flex:1;min-width:150px" />
        </div>

        <div style="overflow-x:auto;border:1px solid var(--line);border-radius:8px">
          <table style="width:100%;border-collapse:collapse;font-size:12px">
            <thead>
              <tr style="background:#0b1220;border-bottom:1px solid var(--line)">
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
}

// ──────────────────────────────────────────────────────────────
// Parse schedule data into meeting rows
// ──────────────────────────────────────────────────────────────
function parseGrandRoundsData() {
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
    const facBadge = m.isFaculty ? '<span style="background:#3a2e08;border:1px solid #a16207;color:#fbbf24;padding:1px 6px;border-radius:999px;font-size:10px;font-weight:600">FACULTY</span>' : '';
    
    return `
      <tr style="border-bottom:1px solid var(--line-soft);${m.isNoGR ? 'opacity:0.6' : ''} ${m.isFaculty ? 'background:rgba(251,191,36,.04)' : ''}">
        <td style="padding:8px 10px;white-space:nowrap;vertical-align:top">
          <strong>${m.date}</strong>
          <div style="font-size:10px;color:var(--muted)">${getDayOfWeek(m.date)}</div>
        </td>
        <td style="padding:8px 10px;vertical-align:top">
          ${escapeHtml(m.title1)}
          ${m.notes ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">${escapeHtml(m.notes)}</div>` : ''}
          ${facBadge}
        </td>
        <td style="padding:8px 10px;vertical-align:top">
          ${m.title1 !== '—' ? `<input type="text" value="${code1}" data-date="${m.date}" data-slot="hour1" class="gr-code-input" style="width:80px;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:3px 5px;font-size:12px;font-family:monospace" onchange="updateCode('${m.date}','hour1',this.value)" />` : '<span style="color:var(--muted)">—</span>'}
        </td>
        <td style="padding:8px 10px;vertical-align:top">${escapeHtml(m.title2)}</td>
        <td style="padding:8px 10px;vertical-align:top">
          ${m.title2 !== '—' ? `<input type="text" value="${code2}" data-date="${m.date}" data-slot="hour2" class="gr-code-input" style="width:80px;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:3px 5px;font-size:12px;font-family:monospace" onchange="updateCode('${m.date}','hour2',this.value)" />` : '<span style="color:var(--muted)">—</span>'}
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
// Monday Resident Conference Table
// ──────────────────────────────────────────────────────────────
function renderMondayTable() {
  const tbody = document.getElementById('grTableBody');
  if (!tbody) return;
  
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
    tbody.innerHTML = `<tr><td colspan="5" style="padding:30px;text-align:center;color:var(--muted)">No matching Monday conferences</td></tr>`;
    return;
  }
  
  tbody.innerHTML = rows.map(r => `
    <tr style="border-bottom:1px solid var(--line-soft)">
      <td style="padding:8px 10px;white-space:nowrap;vertical-align:top">
        <strong>${r.date}</strong>
        <div style="font-size:10px;color:var(--muted)">${getDayOfWeek(r.date)}</div>
      </td>
      <td style="padding:8px 10px;vertical-align:top">
        <strong>${escapeHtml(r.topic)}</strong>
        ${r.notes ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">${escapeHtml(r.notes)}</div>` : ''}
      </td>
      <td style="padding:8px 10px;vertical-align:top">${escapeHtml(r.resident)}</td>
      <td style="padding:8px 10px;vertical-align:top">${escapeHtml(r.attending)}</td>
      <td style="padding:8px 10px;text-align:center;white-space:nowrap">
        <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="openMondayOutlook('${r.date}','${r.topic.replace(/'/g,"\\'")}','${r.resident.replace(/'/g,"\\'")}','${r.attending.replace(/'/g,"\\'")}')" title="Open in Outlook">📧</button>
        <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="downloadMondayIcs('${r.date}','${r.topic.replace(/'/g,"\\'")}','${r.resident.replace(/'/g,"\\'")}','${r.attending.replace(/'/g,"\\'")}')" title="Download .ics">📥</button>
      </td>
    </tr>
  `).join('');
}

function openMondayOutlook(date, topic, resident, attending) {
  const loc = document.getElementById('grLocation')?.value || '';
  const rList = document.getElementById('grResidentList')?.value || '';
  
  const subj = `Resident AM Conference: ${topic}`;
  const body = `Urology Department — Resident AM Conference\nDate: ${date}\nTime: 7:00-8:00 AM\nResident: ${resident}\nAttending: ${attending}\nLocation: ${loc}`;
  const params = new URLSearchParams({
    subject: subj, body, location: loc,
    startdt: `${date}T07:00:00`, enddt: `${date}T08:00:00`,
    to: rList
  });
  window.open(`https://outlook.office.com/calendar/deeplink/compose?${params}`, '_blank');
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
function openOutlookForDate(date, title1, title2) {
  const codes = grCmeCodes[date] || {};
  const loc = document.getElementById('grLocation')?.value || '';
  const residentList = document.getElementById('grResidentList')?.value || '';
  const facultyList = document.getElementById('grFacultyList')?.value || '';
  
  const isFaculty = /faculty\s*meeting/i.test(title1);
  const attendees = isFaculty ? facultyList : residentList;
  
  // Open 7-8 AM meeting
  if (title1 && title1 !== '—') {
    const subj = codes.hour1 ? `[CME ${codes.hour1}] Grand Rounds: ${title1}` : `Grand Rounds: ${title1}`;
    const body = `Urology Department — Grand Rounds\nDate: ${date}\nTime: 7:00-8:00 AM\n${codes.hour1 ? `CME Code: ${codes.hour1}\n` : ''}Location: ${loc}`;
    const params = new URLSearchParams({
      subject: subj, body, location: loc,
      startdt: `${date}T07:00:00`, enddt: `${date}T08:00:00`,
      to: attendees
    });
    window.open(`https://outlook.office.com/calendar/deeplink/compose?${params}`, '_blank');
  }
  
  // Open 8-9 AM meeting after a delay
  if (title2 && title2 !== '—') {
    setTimeout(() => {
      const subj2 = codes.hour2 ? `[CME ${codes.hour2}] Grand Rounds Conference: ${title2}` : `Grand Rounds Conference: ${title2}`;
      const body2 = `Urology Department — Grand Rounds Conference\nDate: ${date}\nTime: 8:00-9:00 AM\n${codes.hour2 ? `CME Code: ${codes.hour2}\n` : ''}Location: ${loc}`;
      const params2 = new URLSearchParams({
        subject: subj2, body, location: loc,
        startdt: `${date}T08:00:00`, enddt: `${date}T09:00:00`,
        to: attendees
      });
      window.open(`https://outlook.office.com/calendar/deeplink/compose?${params2}`, '_blank');
    }, 500);
  }
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

function openAllOutlook() {
  const inputs = document.querySelectorAll('.gr-code-input');
  inputs.forEach(inp => {
    updateCode(inp.dataset.date, inp.dataset.slot, inp.value);
  });
  showToast('Opening all in Outlook... (pop-ups must be allowed)', 'info');
  
  // Collect unique dates
  const dates = [...new Set(Array.from(document.querySelectorAll('.gr-code-input')).map(i => i.dataset.date))];
  // Use the meetings list
  const meetings = parseGrandRoundsData();
  let idx = 0;
  for (const m of meetings) {
    setTimeout(() => openOutlookForDate(m.date, m.title1, m.title2), idx * 800);
    idx++;
    if (idx > 20) {
      showToast('Opening first 20 meetings to avoid overwhelming your browser', 'warning');
      break;
    }
  }
}

function downloadAllIcs() {
  const meetings = parseGrandRoundsData();
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
