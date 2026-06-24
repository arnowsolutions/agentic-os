/**
 * On-Call Schedule Page — 3-Location Tab View
 * 
 * Tabs: Moses | Wakefield | Weiler
 * Each tab has its own weekly schedule table.
 */

async function renderOncall() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📅 Montefiore Urology On-Call Schedule</h1>
        <p class="page-subtitle">3 locations — Moses · Wakefield · Weiler. Switch tabs to view each hospital's schedule.</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="renderOncall()">🔄 Refresh</button>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
      <div id="oncallNowCard"></div>
      <div id="oncallSearchCard">
        <div class="card" style="padding:20px">
          <h3 style="margin:0 0 12px 0;font-size:15px">🔍 Look Up a Date</h3>
          <div style="display:flex;gap:8px">
            <input type="date" id="oncallSearchDate" value="${new Date().toISOString().split('T')[0]}"
                   style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:6px;
                          background:var(--surface);color:var(--text);font-size:14px">
            <button class="btn btn-primary" onclick="searchOncall()">Search</button>
          </div>
          <div id="oncallSearchResult" style="margin-top:12px;font-size:14px"></div>
        </div>
      </div>
    </div>

    <!-- Hospital Tabs -->
    <div style="display:flex;gap:4px;margin-bottom:12px;border-bottom:2px solid var(--border);padding-bottom:0">
      <button class="oncall-tab active" data-tab="Moses" onclick="switchHospitalTab('Moses')" 
              style="padding:10px 20px;border:none;background:none;cursor:pointer;font-size:14px;font-weight:600;
                     border-bottom:3px solid #6c5ce7;color:var(--text);border-radius:6px 6px 0 0">
        🏥 Moses
      </button>
      <button class="oncall-tab" data-tab="Wakefield" onclick="switchHospitalTab('Wakefield')"
              style="padding:10px 20px;border:none;background:none;cursor:pointer;font-size:14px;font-weight:600;
                     border-bottom:3px solid transparent;color:var(--text-muted);border-radius:6px 6px 0 0">
        🏥 Wakefield
      </button>
      <button class="oncall-tab" data-tab="Weiler" onclick="switchHospitalTab('Weiler')"
              style="padding:10px 20px;border:none;background:none;cursor:pointer;font-size:14px;font-weight:600;
                     border-bottom:3px solid transparent;color:var(--text-muted);border-radius:6px 6px 0 0">
        🏥 Weiler
      </button>
    </div>

    <div class="card" style="padding:20px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h3 style="margin:0;font-size:15px" id="oncallScheduleTitle">📅 Moses — Weekly Schedule</h3>
        <div style="display:flex;gap:6px;align-items:center">
          <button class="btn" onclick="navigateWeek(-1)">◀ Prev Week</button>
          <span id="oncallWeekLabel" style="font-weight:600;font-size:14px;min-width:220px;text-align:center"></span>
          <button class="btn" onclick="navigateWeek(1)">Next Week ▶</button>
          <button class="btn" style="margin-left:4px" onclick="goToThisWeek()">📅 This Week</button>
        </div>
      </div>
      <div style="overflow-x:auto">
        <table id="oncallScheduleTable" style="width:100%;border-collapse:collapse;font-size:13px">
          <thead>
            <tr style="background:var(--surface);border-bottom:2px solid var(--border)">
              <th style="padding:10px 12px;text-align:left;font-weight:600">Date</th>
              <th style="padding:10px 12px;text-align:left;font-weight:600">On-Call Attending</th>
              <th style="padding:10px 12px;text-align:left;font-weight:600">Backup</th>
              <th style="padding:10px 12px;text-align:left;font-weight:600">PEDS</th>
              <th style="padding:10px 12px;text-align:left;font-weight:600">On-Call Resident</th>
              <th style="padding:10px 12px;text-align:left;font-weight:600">2nd On-Call</th>
              <th style="padding:10px 12px;text-align:left;font-weight:600">Chief Resident</th>
              <th style="padding:10px 12px;text-align:center;font-weight:600">Type</th>
            </tr>
          </thead>
          <tbody id="oncallTableBody"></tbody>
        </table>
      </div>
      <div id="oncallEmptyMsg" style="display:none;padding:20px;text-align:center;color:var(--text-muted)">
        No schedule data for this week. Schedule runs Jul 1 – Dec 31, 2026.
      </div>
    </div>

    <div style="margin-top:16px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px" id="hospitalSummaryCards"></div>
  `;

  currentMonday = getMonday(new Date());
  activeHospital = 'Moses';
  await Promise.all([
    loadOncallNow(),
    renderWeekView(),
    loadHospitalSummary()
  ]);
}

let currentMonday = null;
let activeHospital = 'Moses';
let weekCache = {};

function getMonday(d) {
  const date = new Date(d);
  const day = date.getDay();
  const diff = date.getDate() - day + (day === 0 ? -6 : 1);
  date.setDate(diff);
  date.setHours(0, 0, 0, 0);
  return date;
}

function fmtDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function fmtDateShort(iso) {
  if (!iso) return '-';
  const d = new Date(iso + 'T00:00:00');
  const mon = d.toLocaleDateString('en-US', { month: 'short' });
  return `${mon} ${d.getDate()}`;
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

const HOSPITAL_COLORS = { Moses: '#6c5ce7', Wakefield: '#0984e3', Weiler: '#00b894' };
const HOSPITAL_EMOJIS = { Moses: '🏥', Wakefield: '🏥', Weiler: '🏥' };

function switchHospitalTab(hospital) {
  activeHospital = hospital;
  
  // Update tab styles
  document.querySelectorAll('.oncall-tab').forEach(tab => {
    const isActive = tab.dataset.tab === hospital;
    tab.style.borderBottomColor = isActive ? HOSPITAL_COLORS[hospital] : 'transparent';
    tab.style.color = isActive ? 'var(--text)' : 'var(--text-muted)';
  });
  
  // Update title
  document.getElementById('oncallScheduleTitle').textContent = `📅 ${hospital} — Weekly Schedule`;
  
  // Re-render week view with selected hospital
  renderWeekView();
}

// ─── Attending Cell with split-shift tooltips ───────────────────

function attendingCell(name) {
  if (!name || name === 'None') return '<span style="color:var(--text-muted)">—</span>';
  const parenIdx = name.indexOf(' (');
  if (parenIdx === -1) return esc(name);
  
  const doctor = name.substring(0, parenIdx);
  let note = name.substring(parenIdx + 2, name.length - 1);
  
  if (note.includes(' / ')) {
    const parts = note.split(' / ');
    let part1 = parts[0];
    let part2 = parts[1];
    
    let doc1 = part1;
    let time1 = '';
    const tIdx = part1.indexOf(' (');
    if (tIdx !== -1) {
      doc1 = part1.substring(0, tIdx);
      time1 = part1.substring(tIdx + 2, part1.length - 1);
    }
    
    let doc2 = part2;
    let location2 = '';
    const lIdx = part2.indexOf(' (');
    if (lIdx !== -1) {
      doc2 = part2.substring(0, lIdx);
      location2 = part2.substring(lIdx + 2, part2.length - 1);
    }
    
    const tooltip = `${esc(doc1)}: ${time1 || 'all day'}<br>${esc(doc2)}: ${location2}`;
    
    return `<span style="cursor:help;border-bottom:1px dashed var(--text-muted)" 
              title="${esc(tooltip).replace(/"/g, '&quot;')}">
      ${esc(doc1)} / ${esc(doc2)}
      <span style="display:inline-flex;align-items:center;justify-content:center;
                   width:16px;height:16px;border-radius:50%;background:${HOSPITAL_COLORS[activeHospital] || '#6c5ce7'};
                   color:#fff;font-size:10px;font-weight:700;margin-left:4px;
                   cursor:help;vertical-align:middle">i</span>
    </span>`;
  }
  
  return `<span style="cursor:help;border-bottom:1px dashed var(--text-muted)"
              title="${esc(note).replace(/"/g, '&quot;')}">
    ${esc(doctor)}
    <span style="display:inline-flex;align-items:center;justify-content:center;
                 width:16px;height:16px;border-radius:50%;background:rgba(108,92,231,0.2);
                 color:#6c5ce7;font-size:10px;font-weight:700;margin-left:4px;
                 cursor:help;vertical-align:middle">i</span>
  </span>`;
}

// ─── Who's On Call Now ──────────────────────────────────────────

async function loadOncallNow() {
  try {
    const data = await api.get('/api/oncall/now');
    const card = document.getElementById('oncallNowCard');
    const entries = data.oncall || [];

    if (entries.length > 0) {
      const moses = entries.find(e => e.hospital === 'Moses');
      const wakefield = entries.find(e => e.hospital === 'Wakefield');
      const weiler = entries.find(e => e.hospital === 'Weiler');

      let html = `<div class="card" style="padding:20px;border-left:4px solid #00b894">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">🟢 ON CALL NOW — ${data.date}</div>`;

      if (moses) {
        html += `<div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--border)">
          <div style="font-weight:600;font-size:14px;color:${HOSPITAL_COLORS.Moses}">🏥 Moses</div>
          <div style="margin-top:2px"><strong>Attending:</strong> ${attendingCell(moses.primary_attending)}</div>
          ${moses.backup_attending && moses.backup_attending !== 'None' ? `<div><strong>Backup:</strong> ${attendingCell(moses.backup_attending)}</div>` : ''}
          ${moses.peds_attending && moses.peds_attending !== 'None' ? `<div><strong>PEDS:</strong> ${attendingCell(moses.peds_attending)}</div>` : ''}
        </div>`;
      }
      if (wakefield) {
        html += `<div style="margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid var(--border)">
          <div style="font-weight:600;font-size:14px;color:${HOSPITAL_COLORS.Wakefield}">🏥 Wakefield</div>
          <div style="margin-top:2px"><strong>Attending:</strong> ${attendingCell(wakefield.primary_attending)}</div>
          ${wakefield.backup_attending && wakefield.backup_attending !== 'None' ? `<div><strong>Backup:</strong> ${attendingCell(wakefield.backup_attending)}</div>` : ''}
          ${wakefield.peds_attending && wakefield.peds_attending !== 'None' ? `<div><strong>PEDS:</strong> ${attendingCell(wakefield.peds_attending)}</div>` : ''}
        </div>`;
      }
      if (weiler) {
        html += `<div style="margin-bottom:4px">
          <div style="font-weight:600;font-size:14px;color:${HOSPITAL_COLORS.Weiler}">🏥 Weiler</div>
          <div style="margin-top:2px"><strong>Attending:</strong> ${attendingCell(weiler.primary_attending)}</div>
          ${weiler.backup_attending && weiler.backup_attending !== 'None' ? `<div><strong>Backup:</strong> ${attendingCell(weiler.backup_attending)}</div>` : ''}
          ${weiler.peds_attending && weiler.peds_attending !== 'None' ? `<div><strong>PEDS:</strong> ${attendingCell(weiler.peds_attending)}</div>` : ''}
        </div>`;
      }
      html += `<div style="font-size:11px;color:var(--text-muted);margin-top:4px">${esc(data.date)}</div></div>`;
      card.innerHTML = html;
    } else {
      card.innerHTML = `<div class="card" style="padding:20px">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">🔴 ON CALL</div>
        <div style="font-size:14px;color:var(--text-muted)">${esc(data.message || 'No data for today')}</div>
      </div>`;
    }
  } catch (err) {
    document.getElementById('oncallNowCard').innerHTML =
      `<div class="card" style="padding:20px"><div style="color:var(--red)">⚠ ${esc(err.message)}</div></div>`;
  }
}

function navigateWeek(delta) {
  if (!currentMonday) currentMonday = getMonday(new Date());
  currentMonday.setDate(currentMonday.getDate() + (delta * 7));
  renderWeekView();
}

function goToThisWeek() {
  currentMonday = getMonday(new Date());
  renderWeekView();
}

// ─── Weekly Schedule View (per active hospital) ─────────────────

async function renderWeekView() {
  const label = document.getElementById('oncallWeekLabel');
  const tbody = document.getElementById('oncallTableBody');
  const emptyMsg = document.getElementById('oncallEmptyMsg');
  if (!label || !tbody) return;

  if (!currentMonday) currentMonday = getMonday(new Date());
  const mondayStr = currentMonday.toISOString().split('T')[0];
  const nextMon = new Date(currentMonday);
  nextMon.setDate(nextMon.getDate() + 6);
  const sundayStr = nextMon.toISOString().split('T')[0];
  label.textContent = `${fmtDate(mondayStr)} — ${fmtDate(sundayStr)}`;

  try {
    const data = await api.get(`/api/oncall/week?start=${mondayStr}`);
    const entries = data.oncall || [];

    if (entries.length === 0) {
      tbody.innerHTML = '';
      emptyMsg.style.display = 'block';
      return;
    }
    emptyMsg.style.display = 'none';

    const todayStr = new Date().toISOString().split('T')[0];
    const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    // Filter to active hospital only
    const filtered = entries.filter(e => e.hospital === activeHospital);

    let html = '';
    for (let i = 0; i < 7; i++) {
      const day = new Date(currentMonday);
      day.setDate(day.getDate() + i);
      const dateStr = day.toISOString().split('T')[0];
      const dayName = daysOfWeek[i];
      const isToday = dateStr === todayStr;

      const entry = filtered.find(e => e.date === dateStr);
      const isWeekend = i >= 5;

      const rowStyle = isToday ? 'background:rgba(0,184,148,0.08);font-weight:500' :
                       isWeekend ? 'background:rgba(108,92,231,0.04)' : '';

      const attendingDisplay = entry ? attendingCell(entry.primary_attending) : '<span style="color:var(--text-muted)">—</span>';
      const backupDisplay = entry && entry.backup_attending && entry.backup_attending !== 'None' ? attendingCell(entry.backup_attending) : '<span style="color:var(--text-muted)">—</span>';
      const pedsDisplay = entry && entry.peds_attending && entry.peds_attending !== 'None' ? attendingCell(entry.peds_attending) : '<span style="color:var(--text-muted)">—</span>';

      html += `<tr style="${rowStyle};border-bottom:1px solid var(--border)">
        <td style="padding:8px 12px;white-space:nowrap"><strong>${isToday ? '🟢 ' : ''}${fmtDateShort(dateStr)}</strong><br><span style="font-size:11px;color:var(--text-muted)">${dayName}</span></td>
        <td style="padding:8px 12px">${attendingDisplay}</td>
        <td style="padding:8px 12px">${backupDisplay}</td>
        <td style="padding:8px 12px">${pedsDisplay}</td>
        <td style="padding:8px 12px;color:var(--text-muted)">—</td>
        <td style="padding:8px 12px;color:var(--text-muted)">—</td>
        <td style="padding:8px 12px;color:var(--text-muted)">—</td>
        <td style="padding:8px 12px;text-align:center"><span class="tag" style="background:${isWeekend ? 'rgba(108,92,231,0.15)' : 'rgba(0,184,148,0.15)'};color:${isWeekend ? '#6c5ce7' : '#00b894'};border:none">${isWeekend ? 'WE' : 'WD'}</span></td>
      </tr>`;
    }

    tbody.innerHTML = html;
  } catch (err) {
    document.getElementById('oncallTableBody').innerHTML =
      `<tr><td colspan="8" style="padding:20px;color:var(--red);text-align:center">⚠ ${esc(err.message)}</td></tr>`;
  }
}

// ─── Hospital Summary Cards ─────────────────────────────────────

async function loadHospitalSummary() {
  try {
    const data = await api.get('/api/oncall/schedule');
    const hospitals = data.hospitals || [];
    const container = document.getElementById('hospitalSummaryCards');

    let html = '';
    hospitals.forEach(h => {
      const color = HOSPITAL_COLORS[h.name] || '#636e72';
      html += `<div class="card" style="padding:16px;border-left:3px solid ${color}">
        <div style="font-size:14px;font-weight:600;margin-bottom:6px;color:${color}">🏥 ${esc(h.name)}</div>
        <div style="font-size:12px;color:var(--text-muted)">
          ${h.total_dates} days · ${h.start_date} to ${h.end_date}<br>
          ${h.unique_primary_attendings.length} attendings on rotation
        </div>
      </div>`;
    });
    container.innerHTML = html;
  } catch (err) {
    // Silently handle
  }
}

// ─── Search by Date ──────────────────────────────────────────────

async function searchOncall() {
  const dateInput = document.getElementById('oncallSearchDate');
  const resultDiv = document.getElementById('oncallSearchResult');
  if (!dateInput || !resultDiv) return;

  const date = dateInput.value;
  if (!date) { resultDiv.innerHTML = '<div style="color:var(--text-muted)">Select a date</div>'; return; }

  try {
    const data = await api.get(`/api/oncall/date?date=${date}`);
    const entries = data.oncall || [];

    if (entries.length === 0) {
      resultDiv.innerHTML = `<div style="color:var(--text-muted)">No schedule data for ${date}. Runs Jul 1 – Dec 31, 2026.</div>`;
      return;
    }

    let html = '';
    entries.forEach(e => {
      const color = HOSPITAL_COLORS[e.hospital] || '#636e72';
      html += `<div style="margin-bottom:8px;padding:10px;background:var(--surface);border-radius:6px;border:1px solid var(--border);border-left:3px solid ${color}">
        <div style="font-weight:600;font-size:14px;margin-bottom:4px;color:${color}">🏥 ${esc(e.hospital)}</div>
        <table style="font-size:13px;width:100%">
          <tr><td style="color:var(--text-muted);width:80px">On-Call:</td><td style="font-weight:500">${attendingCell(e.primary_attending)}</td></tr>
          ${e.backup_attending && e.backup_attending !== 'None' ? `<tr><td style="color:var(--text-muted)">Backup:</td><td>${attendingCell(e.backup_attending)}</td></tr>` : ''}
          ${e.peds_attending && e.peds_attending !== 'None' ? `<tr><td style="color:var(--text-muted)">PEDS:</td><td>${attendingCell(e.peds_attending)}</td></tr>` : ''}
          <tr><td style="color:var(--text-muted)">Resident:</td><td style="color:var(--text-muted)">— (add schedule)</td></tr>
        </table>
      </div>`;
    });
    resultDiv.innerHTML = html;
  } catch (err) {
    resultDiv.innerHTML = `<div style="color:var(--red)">⚠ ${esc(err.message)}</div>`;
  }
}
