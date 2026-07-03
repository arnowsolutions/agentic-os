// ──────────────────────────────────────────────────────────────
// Grand Rounds Schedule Manager — Full interactive editor
// Embedded into Agentic OS dashboard
// ──────────────────────────────────────────────────────────────

// Embedded schedule data (2026-2027 Grand Rounds)
// Columns: 0=Month, 1=Monday Date, 2=Mon AM Conference, 3=Resident, 4=Attending,
//          5=CME7-8, 6=CME8-9, 7=Friday Date, 8=GR 7-8, 9=GR 8-9, 10=Other
const GR_DATA = [
  ["July", "2026-07-06", "SASP - UTI/STD/Infections", "Nate", "Edelblute", "", "", "2026-07-03", "NO GRAND ROUNDS", "", "7/4 - Independence Day"],
  ["", "2026-07-13", "SASP - Nephrolithiasis", "Jasmin", "Raskolnikov", "", "", "2026-07-10", "Peds", "Peds Multidisciplinary", "confirmed"],
  ["", "2026-07-20", "SASP - Trauma", "Dinora", "Donnelly", "", "", "2026-07-17", "Sankin expectations overview (1hr)", "Sub-I talks - 0.75 hr (3)", "TB"],
  ["", "2026-07-27", "SASP - Embryology", "Val", "Ohmann", "", "", "2026-07-24", "", "", ""],
  ["August", "2026-08-03", "SASP - ED", "Sam", "Maria", "", "", "2026-07-31", "Quality Improvement: Stats/M&Ms/Indications June/ July", "", "TB"],
  ["", "2026-08-10", "SASP - UDS", "N/A", "Abraham", "", "", "2026-08-07", "SASP Review with Dr. Lipsky", "", ""],
  ["", "2026-08-17", "SASP - BPH/Obstructive Uropathy", "Jake", "Theofanides", "", "", "2026-08-14", "", "Sub-I talks - 0.5 hr (2)", "TB; No PEDS GR"],
  ["", "2026-08-24", "SASP - Neurogenic Bladder/Voiding Dysfunction", "Kelli", "Clearwater", "", "", "2026-08-21", "NO GRAND ROUNDS", "", ""],
  ["", "2026-08-31", "SASP - Urethral Reconstruction", "Rutul", "Cedars", "", "", "2026-08-28", "PGY-4 Subspeciality Presentations", "Sub-I talks - 0.75 hr (3)", "TB?"],
  ["September", "2026-09-07", "Holiday", "", "", "", "", "2026-09-04", "NO GRAND ROUNDS vs QPS", "", "9/7 - Labor Day"],
  ["", "2026-09-14", "SASP - Infertility", "Joe", "Lipsky", "", "", "2026-09-11", "Peds", "Peds Multidisciplinary", "Rosh Hashana Sept 12-13"],
  ["", "2026-09-21", "SASP - Adrenal Tumors", "Jen", "?", "", "", "2026-09-18", "FACULTY MEETING", "", ""],
  ["", "2026-09-28", "SASP - UTUC", "Hordines", "Small", "", "", "2026-09-25", "", "Sub-I talks - 0.75 hr (3)", "Yom Kipur 9/21; Sukkot 9/26-27"],
  ["October", "2026-10-05", "SASP - NMIBC/MIBC", "Hill", "Sankin", "", "", "2026-10-02", "Quality Improvement: Stats/M&Ms/Indications Aug/ Sept", "", "Sukkot 10/3-4"],
  ["", "2026-10-12", "SASP - Renal Tumors", "Jasmin", "Aboumohamed", "", "", "2026-10-09", "Peds", "Peds Multidisciplinary", ""],
  ["", "2026-10-19", "SASP - Penile Cancer", "Dinora", "Lowe", "", "", "2026-10-16", "", "", ""],
  ["", "2026-10-26", "SASP - Testicular Tumors", "Nate", "Mallahan", "", "", "2026-10-23", "Sub-Intern Presentations - 1 hr (4)", "", ""],
  ["November", "2026-11-02", "SASP - Prostate Cancer Workup/Treatment", "Sam", "Watts", "", "", "2026-10-30", "", "PGY-4 Subspeciality Presentations", ""],
  ["", "2026-11-09", "pre-ISE crash review", "", "Lipsky", "", "", "2026-11-06", "FACULTY MEETING", "", "Diwali 11/8"],
  ["", "2026-11-16", "pre-ISE crash review", "", "Lowe", "", "", "2026-11-13", "Peds", "Peds Multidisciplinary", "11/15 - ISE"],
  ["", "2026-11-23", "post ise mental rest day", "", "", "", "", "2026-11-20", "", "", ""],
  ["December", "2026-11-30", "SASP - Urinary Fistulae / Diversions", "Val", "Waldschmidtt", "", "", "2026-11-27", "NO GRAND ROUNDS", "", "11/27 - Thanksgiving"],
  ["", "2026-12-07", "SASP - Incontinence/OAB/POP", "Jake", "Laudano", "", "", "2026-12-04", "Quality Improvement: Stats/M&Ms/Indications Oct-Nov", "", ""],
  ["", "2026-12-14", "SASP - Lap/Robotic Surgery", "Joe", "Edelblute", "", "", "2026-12-11", "Peds", "Peds Multidisciplinary", ""],
  ["", "2026-12-21", "SASP - Physiology (fluids, electrolytes, HTN/vascular disease, endocrinopathy)", "Kelli", "Donnelly", "", "", "2026-12-18", "Valentine Essay Submission Presentations", "Resident QI Updates", ""],
  ["", "2026-12-28", "Holiday", "", "", "", "", "2026-12-25", "NO GRAND ROUNDS", "", "12/25 - Christmas"],
  ["January", "2027-01-04", "SASP - Pediatric GU Onc", "Rutul", "Ohmann", "", "", "2027-01-01", "NO GRAND ROUNDS", "", "1/1 - New Year"],
  ["", "2027-01-11", "SASP - Congenital Anomalies", "Hordines", "Raskolnikov", "", "", "2027-01-08", "Peds", "Peds Multidisciplinary", ""],
  ["", "2027-01-18", "Holiday", "", "", "", "", "2027-01-15", "FACULTY MEETING", "", "1/19 - MLK Day"],
  ["", "2027-01-25", "SASP -", "Hill", "", "", "", "2027-01-22", "Journal Club", "", ""],
  ["February", "2027-02-01", "SASP", "Pak", "", "", "", "2027-01-29", "", "", ""],
  ["", "2027-02-08", "SASP", "", "", "", "", "2027-02-05", "Quality Improvement: Stats/M&Ms/Indications - Dec/Jan", "", ""],
  ["", "2027-02-15", "SASP", "", "", "", "", "2027-02-12", "Peds", "Peds Multidisciplinary", ""],
  ["", "2027-02-22", "Holiday", "", "", "", "", "2027-02-19", "PGY-4 Subspeciality Presentations (1 hr)", "Visiting Lecture: Fed Ghali (Yale) - Uro-oncology", "2/16 - President's Day"],
  ["March", "2027-03-01", "SASP", "", "", "", "", "2027-02-26", "Prisoner Ethics - Ari", "Prisoner Ethics - Small", ""],
  ["", "2027-03-08", "SASP", "", "", "", "", "2027-03-05", "FACULTY MEETING", "", "Inlexzo Mobile Lab 8-12"],
  ["", "2027-03-15", "SASP", "", "", "", "", "2027-03-12", "Peds", "Peds Multidisciplinary", ""],
  ["", "2027-03-22", "SASP", "", "", "", "", "2027-03-19", "Journal Club", "", "Eid al-Fitr 3-20"],
  ["", "2027-03-29", "SASP", "", "", "", "", "2027-03-26", "Quality Improvement: Stats/M&Ms/Indications - Feb/ March", "Sub-I Presentation (1 - 15 min)", ""],
  ["April", "2027-04-05", "SASP", "", "", "", "", "2027-04-02", "NO GRAND ROUNDS - Good Friday/ Passover", "", "GoodFriday 4/3; Passover 4/3-4/4"],
  ["", "2027-04-12", "SASP", "", "", "", "", "2027-04-09", "Peds", "Peds Multidisciplinary", "Easter 4/5; 4/8-4/9 Passover"],
  ["", "2027-04-19", "SASP", "", "", "", "", "2027-04-16", "Guest Speaker - Contract Negotiations", "Prosthetics Talk - Dr. Pedro Maria", ""],
  ["", "2027-04-26", "SASP", "", "", "", "", "2027-04-23", "Sub-I Presentation (15 min)/PGY 4 Subspecialty", "Dr Kelvin Davies - Testing a Paradigm Shift: Erectile Dysfunction as a Causal Driver of Cardiovascular Disease.", ""],
  ["May", "2027-05-03", "SASP -", "", "", "", "", "2027-04-30", "Quality Improvement: Stats/M&Ms/Indications - March/April", "", "Resident Anatomy Simulation - Ileal Ureter"],
  ["", "2027-05-10", "SASP -", "", "", "", "", "2027-05-07", "Peds", "Peds Multidisciplinary", ""],
  ["", "2027-05-17", "SASP -", "", "", "", "", "2027-05-14", "NO GRAND ROUNDS - AUA", "", "AUA 5/15-18"],
  ["", "2027-05-24", "SASP -", "", "", "", "", "2027-05-21", "", "", ""],
  ["", "2027-05-31", "Holiday", "", "", "", "", "2027-05-28", "Journal Club/ STATs with Dr. Aggaliu", "", "Eid al-adha 5/27 - Memorial Day - 5/25"],
  ["June", "2027-06-07", "SKIT", "", "", "", "", "2027-06-04", "Quality Improvement: Stats/M&Ms/Indications - May", "", ""],
  ["", "2027-06-14", "SKIT", "", "", "", "", "2027-06-11", "Dr. Kryger VP", "Peds Multidisciplinary", ""],
  ["", "2027-06-21", "End of year debrief", ":(", "", "", "", "2027-06-18", "", "", "6/19 - Juneteenth, 6/17 - Graduation!"],
  ["", "2027-06-28", "Expectations Meeting", "", "", "", "", "2027-06-25", "FACULTY MEETING", "", ""],
  ["July", "2027-07-05", "[see next yr calendar]", "", "", "", "", "2027-07-02", "", "", "7/4 - July 4th"]
];
64|
65|let grFilters = { skipNoGR: true, skipFaculty: false, skipHoliday: true, search: '', month: '' };
66|let grCmeCodes = {};  // { "YYYY-MM-DD": { hour1: "code", hour2: "code" } }
67|
68|// ──────────────────────────────────────────────────────────────
69|// Main render function
70|// ──────────────────────────────────────────────────────────────
71|async function renderGrandRounds() {
72|  const content = document.getElementById('pageContent');
73|  
74|  // Build the parsed meeting list from embedded data
75|  const meetings = parseGrandRoundsData();
76|  
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
89|      <!-- Sidebar Controls -->
90|      <div class="card" style="position:sticky;top:70px">
91|        <div class="card-header"><span class="card-title">⚙ Controls</span></div>
92|        <div class="card-body" style="font-size:13px">
93|          
94|          <div style="margin-bottom:10px">
95|            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Distribution Lists</label>
96|            <input type="text" id="grResidentList" placeholder="Residents email" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px;margin-bottom:4px" value="residents@x.org" />
97|            <input type="text" id="grFacultyList" placeholder="Faculty email" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px" value="faculty@x.org" />
98|          </div>
99|
100|          <div style="margin-bottom:10px">
101|            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Location / Zoom</label>
102|            <input type="text" id="grLocation" placeholder="Room or Zoom link" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px" />
103|          </div>
104|
105|          <div style="margin-bottom:10px">
106|            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Filters</label>
107|            <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin:3px 0;cursor:pointer">
108|              <input type="checkbox" id="grFilterNoGR" ${grFilters.skipNoGR?'checked':''} onchange="grFilters.skipNoGR=this.checked;renderGrandRounds()" /> Hide "NO GRAND ROUNDS"
109|            </label>
110|            <label style="display:flex;align-items:center;gap:6px;font-size:12px;margin:3px 0;cursor:pointer">
111|              <input type="checkbox" id="grFilterFaculty" ${grFilters.skipFaculty?'checked':''} onchange="grFilters.skipFaculty=this.checked;renderGrandRounds()" /> Hide FACULTY MEETING
112|            </label>
113|          </div>
114|
115|          <div style="margin-bottom:10px">
116|            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Month Jump</label>
117|            <select id="grMonthJump" onchange="grFilters.month=this.value;renderGrandRounds()" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:12px">
118|              <option value="">All months</option>
119|              ${['July','August','September','October','November','December','January','February','March','April','May','June','July 2027'].map(m => 
120|                `<option value="${m}" ${grFilters.month===m?'selected':''}>${m}</option>`
121|              ).join('')}
122|            </select>
123|          </div>
124|
125|          <div style="margin-bottom:10px">
126|            <label style="display:block;color:var(--muted);margin-bottom:4px;font-size:12px">Bulk Paste CME Codes</label>
127|            <textarea id="grBulkCodes" placeholder="YYYY-MM-DD, CODE1, CODE2" style="width:100%;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:5px 7px;font-size:11px;min-height:60px;font-family:monospace"></textarea>
128|            <button class="btn btn-sm" style="margin-top:4px;width:100%;font-size:11px" onclick="applyBulkCodes()">Apply Codes</button>
129|          </div>
130|
131|          <div style="display:flex;flex-direction:column;gap:4px;margin-top:8px">
132|            <button class="btn btn-sm" style="font-size:11px" onclick="openAllOutlook()">📧 Open All in Outlook</button>
133|            <button class="btn btn-sm" style="font-size:11px" onclick="downloadAllIcs()">📥 Download All .ics</button>
134|            <button class="btn btn-sm" style="font-size:11px" onclick="saveCodesLocally()">💾 Save Codes</button>
135|          </div>
136|        </div>
137|      </div>
138|
139|      <!-- Main Table -->
140|      <div>
141|        <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;flex-wrap:wrap">
142|          <span style="font-size:13px;color:var(--muted)">
143|            <span id="grCount">${meetings.length}</span> meetings visible
144|          </span>
145|          <input type="text" placeholder="Search..." id="grSearch" oninput="grFilters.search=this.value;renderGrandRounds()" style="background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:4px 8px;font-size:12px;flex:1;min-width:150px" />
146|        </div>
147|
148|        <div style="overflow-x:auto;border:1px solid var(--line);border-radius:8px">
149|          <table style="width:100%;border-collapse:collapse;font-size:12px">
150|            <thead>
151|              <tr style="background:#0b1220;border-bottom:1px solid var(--line)">
152|                <th style="padding:8px 10px;text-align:left;white-space:nowrap">Date</th>
153|                <th style="padding:8px 10px;text-align:left">Meeting (7-8 AM)</th>
154|                <th style="padding:8px 10px;text-align:left;width:85px">CME Code 1</th>
155|                <th style="padding:8px 10px;text-align:left">Conference (8-9 AM)</th>
156|                <th style="padding:8px 10px;text-align:left;width:85px">CME Code 2</th>
157|                <th style="padding:8px 10px;text-align:center;width:130px">Actions</th>
158|              </tr>
159|            </thead>
160|            <tbody id="grTableBody">
161|              ${renderTableRows(meetings)}
162|            </tbody>
163|          </table>
164|        </div>
165|      </div>
166|    </div>
167|  `;
168|
169|  // Load saved codes from localStorage
170|  loadCodes();
171|}
172|
173|// ──────────────────────────────────────────────────────────────
174|// Parse schedule data into meeting rows
175|// ──────────────────────────────────────────────────────────────
176|function parseGrandRoundsData() {
177|  const results = [];
178|  
179|  for (const row of GR_DATA) {
180|    const fri = row[7];
181|    const gr1 = (row[8] || '').trim();
182|    const gr2 = (row[9] || '').trim();
183|    const other = (row[10] || '').trim();
184|    const monAM = (row[2] || '').trim();
185|    const resident = (row[3] || '').trim();
186|    const attending = (row[4] || '').trim();
187|    const month = row[0] || '';
188|    
189|    if (!fri) continue;
190|    const isFaculty = /faculty\s*meeting/i.test(gr1);
191|    const isNoGR = /no\s*grand\s*rounds/i.test(gr1);
192|    
193|    // Apply filters
194|    if (grFilters.skipNoGR && isNoGR) continue;
195|    if (grFilters.skipFaculty && isFaculty) continue;
196|    if (grFilters.month && !fri.startsWith(grFilters.month.substring(0,4))) continue;
197|    if (grFilters.search) {
198|      const q = grFilters.search.toLowerCase();
199|      if (!gr1.toLowerCase().includes(q) && !gr2.toLowerCase().includes(q) && !other.toLowerCase().includes(q) &&
200|          !monAM.toLowerCase().includes(q) && !resident.toLowerCase().includes(q)) continue;
201|    }
202|    
203|    results.push({
204|      date: fri,
205|      month,
206|      title1: gr1 || '—',
207|      title2: gr2 || '—',
208|      notes: other,
209|      monAM,
210|      resident,
211|      attending,
212|      isFaculty,
213|      isNoGR,
214|      row
215|    });
216|  }
217|  
218|  return results;
219|}
220|
221|// ──────────────────────────────────────────────────────────────
222|// Render table rows
223|// ──────────────────────────────────────────────────────────────
224|function renderTableRows(meetings) {
225|  return meetings.map((m, i) => {
226|    const codes = grCmeCodes[m.date] || {};
227|    const code1 = codes.hour1 || '';
228|    const code2 = codes.hour2 || '';
229|    const facBadge = m.isFaculty ? '<span style="background:#3a2e08;border:1px solid #a16207;color:#fbbf24;padding:1px 6px;border-radius:999px;font-size:10px;font-weight:600">FACULTY</span>' : '';
230|    
231|    return `
232|      <tr style="border-bottom:1px solid var(--line-soft);${m.isNoGR ? 'opacity:0.6' : ''} ${m.isFaculty ? 'background:rgba(251,191,36,.04)' : ''}">
233|        <td style="padding:8px 10px;white-space:nowrap;vertical-align:top">
234|          <strong>${m.date}</strong>
235|          <div style="font-size:10px;color:var(--muted)">${getDayOfWeek(m.date)}</div>
236|        </td>
237|        <td style="padding:8px 10px;vertical-align:top">
238|          ${escapeHtml(m.title1)}
239|          ${m.notes ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">${escapeHtml(m.notes)}</div>` : ''}
240|          ${facBadge}
241|        </td>
242|        <td style="padding:8px 10px;vertical-align:top">
243|          ${m.title1 !== '—' ? `<input type="text" value="${code1}" data-date="${m.date}" data-slot="hour1" class="gr-code-input" style="width:80px;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:3px 5px;font-size:12px;font-family:monospace" onchange="updateCode('${m.date}','hour1',this.value)" />` : '<span style="color:var(--muted)">—</span>'}
244|        </td>
245|        <td style="padding:8px 10px;vertical-align:top">${escapeHtml(m.title2)}</td>
246|        <td style="padding:8px 10px;vertical-align:top">
247|          ${m.title2 !== '—' ? `<input type="text" value="${code2}" data-date="${m.date}" data-slot="hour2" class="gr-code-input" style="width:80px;background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:3px 5px;font-size:12px;font-family:monospace" onchange="updateCode('${m.date}','hour2',this.value)" />` : '<span style="color:var(--muted)">—</span>'}
248|        </td>
249|        <td style="padding:8px 10px;text-align:center;white-space:nowrap">
250|          <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="openOutlookForDate('${m.date}','${m.title1}','${m.title2}')" title="Open in Outlook">📧</button>
251|          <button class="btn btn-sm" style="font-size:10px;padding:3px 7px" onclick="downloadIcsForDate('${m.date}','${m.title1}','${m.title2}')" title="Download .ics">📥</button>
252|        </td>
253|      </tr>
254|    `;
255|  }).join('');
256|}
257|
258|function getDayOfWeek(dateStr) {
259|  const d = new Date(dateStr + 'T12:00:00');
260|  return ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][d.getDay()];
261|}
262|
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
  if (!monIcsProgress) return '<span style="color:var(--muted);font-size:11px">⋯</span>';
  const sent = monIcsProgress.monday_sasp?.ics_sent_dates || [];
  return sent.includes(date)
    ? '<span style="color:var(--green);font-weight:600;font-size:13px">✅ Sent</span>'
    : '<span style="color:var(--muted);font-size:11px">—</span>';
}

async function renderMondayTable() {
  const tbody = document.getElementById('grTableBody');
  if (!tbody) return;
  
  await loadMonIcsProgress();
  
  const rows = [];
271|  
272|  for (const row of GR_DATA) {
273|    const monDate = row[1];
274|    const topic = (row[2] || '').trim();
275|    const resident = (row[3] || '').trim();
276|    const attending = (row[4] || '').trim();
277|    const other = (row[10] || '').trim();
278|    
279|    if (!monDate) continue;
280|    
281|    // Skip empty/holiday rows if filter is on
282|    if (grFilters.skipHoliday && (!topic || /holiday/i.test(topic))) continue;
283|    
284|    // Search filter
285|    if (grFilters.search) {
286|      const q = grFilters.search.toLowerCase();
287|      if (!topic.toLowerCase().includes(q) && !resident.toLowerCase().includes(q) && 
288|          !attending.toLowerCase().includes(q)) continue;
289|    }
290|    
291|    rows.push({
292|      date: monDate,
293|      topic: topic || '—',
294|      resident: resident || '—',
295|      attending: attending || '—',
296|      notes: other
297|    });
298|  }
299|  
300|  // Update count
301|  const countEl = document.getElementById('grCount');
302|  if (countEl) countEl.textContent = rows.length;
303|  
if (rows.length === 0) {
  tbody.innerHTML = `<tr><td colspan="6" style="padding:30px;text-align:center;color:var(--muted)">No matching Monday conferences</td></tr>`;
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
  const content = document.getElementById('pageContent');
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
        <span style="font-size:13px;color:var(--muted)">
          <span id="grCount">0</span> Monday meetings
        </span>
        <input type="text" placeholder="Search..." id="grSearch" oninput="grFilters.search=this.value;renderMondayTable()" style="background:#0b1220;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:4px 8px;font-size:12px;flex:1;min-width:150px" />
      </div>

      <div style="overflow-x:auto;border:1px solid var(--line);border-radius:8px">
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:#0b1220;border-bottom:1px solid var(--line)">
              <th style="padding:8px 10px;text-align:left;white-space:nowrap">Date</th>
              <th style="padding:8px 10px;text-align:left">Topic</th>
              <th style="padding:8px 10px;text-align:left">Resident</th>
              <th style="padding:8px 10px;text-align:left">Attending</th>
              <th style="padding:8px 10px;text-align:center">ICS Sent</th>
              <th style="padding:8px 10px;text-align:center;width:90px">Actions</th>
            </tr>
          </thead>
          <tbody id="grTableBody">
            <tr><td colspan="6" style="padding:30px;text-align:center;color:var(--muted)">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
  await renderMondayTable();
}

function openMondayOutlook(date, topic, resident, attending) {
330|  const loc = document.getElementById('grLocation')?.value || '';
331|  const rList = document.getElementById('grResidentList')?.value || '';
332|  
333|  const subj = `Resident AM Conference: ${topic}`;
334|  const body = `Urology Department — Resident AM Conference\nDate: ${date}\nTime: 7:00-8:00 AM\nResident: ${resident}\nAttending: ${attending}\nLocation: ${loc}`;
335|  const params = new URLSearchParams({
336|    subject: subj, body, location: loc,
337|    startdt: `${date}T07:00:00`, enddt: `${date}T08:00:00`,
338|    to: rList
339|  });
340|  window.open(`https://outlook.office.com/calendar/deeplink/compose?${params}`, '_blank');
341|}
342|
343|function downloadMondayIcs(date, topic, resident, attending) {
344|  const loc = document.getElementById('grLocation')?.value || '';
345|  const subj = `Resident AM Conference: ${topic}`;
346|  
347|  let ics = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Resident Conference//EN\r\n';
348|  ics += `BEGIN:VEVENT\r\nUID:mon-${date}@resident-conf\r\nDTSTART:${date.replace(/-/g,'')}T070000\r\nDTEND:${date.replace(/-/g,'')}T080000\r\nSUMMARY:${subj}\r\nLOCATION:${loc}\r\nDESCRIPTION:Resident: ${resident}\\nAttending: ${attending}\r\nEND:VEVENT\r\n`;
349|  ics += 'END:VCALENDAR';
350|  
351|  const blob = new Blob([ics], {type: 'text/calendar'});
352|  const url = URL.createObjectURL(blob);
353|  const a = document.createElement('a');
354|  a.href = url; a.download = `resident-conf-${date}.ics`;
355|  a.click();
356|  URL.revokeObjectURL(url);
357|}
358|
359|function escapeHtml(s) {
360|  if (!s) return '';
361|  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
362|}
363|
364|// ──────────────────────────────────────────────────────────────
365|// CME Code Management
366|// ──────────────────────────────────────────────────────────────
367|function updateCode(date, slot, value) {
368|  if (!grCmeCodes[date]) grCmeCodes[date] = {};
369|  grCmeCodes[date][slot] = value.trim();
370|  saveCodesLocally();
371|}
372|
373|function loadCodes() {
374|  try {
375|    const saved = localStorage.getItem('grCmeCodes');
376|    if (saved) grCmeCodes = JSON.parse(saved);
377|  } catch {}
378|}
379|
380|function saveCodesLocally() {
381|  try {
382|    localStorage.setItem('grCmeCodes', JSON.stringify(grCmeCodes));
383|    showToast('💾 Codes saved locally', 'success');
384|  } catch {}
385|}
386|
387|function applyBulkCodes() {
388|  const text = document.getElementById('grBulkCodes').value;
389|  if (!text.trim()) { showToast('Paste codes first', 'warning'); return; }
390|  
391|  const lines = text.split('\n').filter(l => l.trim() && !l.startsWith('#'));
392|  let count = 0;
393|  
394|  for (const line of lines) {
395|    const parts = line.split(/[,\t;]+/).map(s => s.trim());
396|    if (parts.length < 2) continue;
397|    const date = parts[0];
398|    if (!grCmeCodes[date]) grCmeCodes[date] = {};
399|    grCmeCodes[date].hour1 = parts[1] || '';
400|    if (parts.length >= 3) grCmeCodes[date].hour2 = parts[2] || '';
401|    count++;
402|  }
403|  
404|  saveCodesLocally();
405|  renderGrandRounds();
406|  showToast(`✅ Applied ${count} code entries`, 'success');
407|}
408|
409|// ──────────────────────────────────────────────────────────────
410|// Outlook & ICS Actions
411|// ──────────────────────────────────────────────────────────────
412|function openOutlookForDate(date, title1, title2) {
413|  const codes = grCmeCodes[date] || {};
414|  const loc = document.getElementById('grLocation')?.value || '';
415|  const residentList = document.getElementById('grResidentList')?.value || '';
416|  const facultyList = document.getElementById('grFacultyList')?.value || '';
417|  
418|  const isFaculty = /faculty\s*meeting/i.test(title1);
419|  const attendees = isFaculty ? facultyList : residentList;
420|  
421|  // Open 7-8 AM meeting
422|  if (title1 && title1 !== '—') {
423|    const subj = codes.hour1 ? `[CME ${codes.hour1}] Grand Rounds: ${title1}` : `Grand Rounds: ${title1}`;
424|    const body = `Urology Department — Grand Rounds\nDate: ${date}\nTime: 7:00-8:00 AM\n${codes.hour1 ? `CME Code: ${codes.hour1}\n` : ''}Location: ${loc}`;
425|    const params = new URLSearchParams({
426|      subject: subj, body, location: loc,
427|      startdt: `${date}T07:00:00`, enddt: `${date}T08:00:00`,
428|      to: attendees
429|    });
430|    window.open(`https://outlook.office.com/calendar/deeplink/compose?${params}`, '_blank');
431|  }
432|  
433|  // Open 8-9 AM meeting after a delay
434|  if (title2 && title2 !== '—') {
435|    setTimeout(() => {
436|      const subj2 = codes.hour2 ? `[CME ${codes.hour2}] Grand Rounds Conference: ${title2}` : `Grand Rounds Conference: ${title2}`;
437|      const body2 = `Urology Department — Grand Rounds Conference\nDate: ${date}\nTime: 8:00-9:00 AM\n${codes.hour2 ? `CME Code: ${codes.hour2}\n` : ''}Location: ${loc}`;
438|      const params2 = new URLSearchParams({
439|        subject: subj2, body, location: loc,
440|        startdt: `${date}T08:00:00`, enddt: `${date}T09:00:00`,
441|        to: attendees
442|      });
443|      window.open(`https://outlook.office.com/calendar/deeplink/compose?${params2}`, '_blank');
444|    }, 500);
445|  }
446|}
447|
448|function downloadIcsForDate(date, title1, title2) {
449|  const codes = grCmeCodes[date] || {};
450|  const loc = document.getElementById('grLocation')?.value || '';
451|  let ics = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Grand Rounds Scheduler//EN\r\n';
452|  
453|  if (title1 && title1 !== '—') {
454|    const subj = codes.hour1 ? `[CME ${codes.hour1}] Grand Rounds: ${title1}` : `Grand Rounds: ${title1}`;
455|    ics += `BEGIN:VEVENT\r\nUID:${date}-1@grand-rounds\r\nDTSTART:${date.replace(/-/g,'')}T070000\r\nDTEND:${date.replace(/-/g,'')}T080000\r\nSUMMARY:${subj}\r\nLOCATION:${loc}\r\nDESCRIPTION:CME Code: ${codes.hour1||'N/A'}\\nUrology Grand Rounds\r\nEND:VEVENT\r\n`;
456|  }
457|  if (title2 && title2 !== '—') {
458|    const subj2 = codes.hour2 ? `[CME ${codes.hour2}] Grand Rounds Conference: ${title2}` : `Grand Rounds Conference: ${title2}`;
459|    ics += `BEGIN:VEVENT\r\nUID:${date}-2@grand-rounds\r\nDTSTART:${date.replace(/-/g,'')}T080000\r\nDTEND:${date.replace(/-/g,'')}T090000\r\nSUMMARY:${subj2}\r\nLOCATION:${loc}\r\nDESCRIPTION:CME Code: ${codes.hour2||'N/A'}\\nUrology Grand Rounds Conference\r\nEND:VEVENT\r\n`;
460|  }
461|  ics += 'END:VCALENDAR';
462|  
463|  const blob = new Blob([ics], {type: 'text/calendar'});
464|  const url = URL.createObjectURL(blob);
465|  const a = document.createElement('a');
466|  a.href = url; a.download = `grand-rounds-${date}.ics`;
467|  a.click();
468|  URL.revokeObjectURL(url);
469|}
470|
471|function openAllOutlook() {
472|  const inputs = document.querySelectorAll('.gr-code-input');
473|  inputs.forEach(inp => {
474|    updateCode(inp.dataset.date, inp.dataset.slot, inp.value);
475|  });
476|  showToast('Opening all in Outlook... (pop-ups must be allowed)', 'info');
477|  
478|  // Collect unique dates
479|  const dates = [...new Set(Array.from(document.querySelectorAll('.gr-code-input')).map(i => i.dataset.date))];
480|  // Use the meetings list
481|  const meetings = parseGrandRoundsData();
482|  let idx = 0;
483|  for (const m of meetings) {
484|    setTimeout(() => openOutlookForDate(m.date, m.title1, m.title2), idx * 800);
485|    idx++;
486|    if (idx > 20) {
487|      showToast('Opening first 20 meetings to avoid overwhelming your browser', 'warning');
488|      break;
489|    }
490|  }
491|}
492|
493|function downloadAllIcs() {
494|  const meetings = parseGrandRoundsData();
495|  if (meetings.length === 0) { showToast('No meetings to download', 'warning'); return; }
496|  
497|  // Download one combined .ics file
498|  let combinedIcs = 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Grand Rounds Scheduler//EN\r\n';
499|  const loc = document.getElementById('grLocation')?.value || '';
500|  
501|