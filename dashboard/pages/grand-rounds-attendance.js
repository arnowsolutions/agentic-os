// ──────────────────────────────────────────────────────────────
// Grand Rounds Attendance Tracker — 2025-2026
// Shows: Both, Only 7AM, Only 8AM, Any 1 = compliant
// ──────────────────────────────────────────────────────────────

let attendanceData = null;
let useNoPeds = false;

async function renderGrandRoundsAttendance() {
  const content = document.getElementById('pageContent');
  content.innerHTML = '<div class="loading"><div class="loading-spinner"></div><span>Loading attendance data...</span></div>';

  try {
    const resp = await fetch('/dashboard/data/attendance-data.json?_=' + Date.now());
    attendanceData = await resp.json();
  } catch {
    content.innerHTML = `<div class="card" style="padding:30px;text-align:center;color:var(--muted)">
      <div style="font-size:40px;margin-bottom:12px">📊</div>
      <h3>No Attendance Data Yet</h3>
      <p style="color:var(--muted);font-size:13px">Run the data builder first.</p>
    </div>`;
    return;
  }

  renderTable();
}

function renderTable() {
  const d = attendanceData;
  const view = useNoPeds ? 'noPeds' : 'all';
  const totalWeeks = useNoPeds ? d.activeNoPeds : d.activeWeeks;
  const needAny = Math.ceil(totalWeeks * 70 / 100);
  const needBoth = Math.ceil(totalWeeks * 70 / 100);

  const faculty = [...d.people];
  faculty.sort((a, b) => {
    const aPct = useNoPeds ? a.noPeds.pctAny : a.all.pctAny;
    const bPct = useNoPeds ? b.noPeds.pctAny : b.all.pctAny;
    return bPct - aPct || a.last.localeCompare(b.last);
  });

  // Summary stats
  const passAny = faculty.filter(p => useNoPeds ? p.noPeds.passAny : p.all.passAny);
  const passBoth = faculty.filter(p => useNoPeds ? p.noPeds.passBoth : p.all.passBoth);
  const passAnyPct = faculty.length ? Math.round((passAny.length / faculty.length) * 100) : 0;
  const passBothPct = faculty.length ? Math.round((passBoth.length / faculty.length) * 100) : 0;

  const pedsCount = d.activeWeeks - d.activeNoPeds;

  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📊 Grand Rounds Attendance</h1>
        <p class="page-subtitle">Academic Year 2025-2026 — Attend ≥1 of 2 Friday meetings = compliant</p>
      </div>
      <div class="btn-group">
        <button class="btn" onclick="exportAttendanceCSV()">📥 Export CSV</button>
        <button class="btn" onclick="renderGrandRoundsAttendance()">🔄 Refresh</button>
      </div>
    </div>

    <!-- Toggle -->
    <div class="card" style="margin-bottom:14px">
      <div class="card-body" style="padding:10px 14px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
        <span style="font-size:13px;font-weight:600">View:</span>
        <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer">
          <input type="radio" name="attView" ${useNoPeds ? '' : 'checked'} onchange="useNoPeds=false;renderTable()" />
          All Weeks <span style="color:var(--muted)">(${d.activeWeeks} active)</span>
        </label>
        <label style="display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer">
          <input type="radio" name="attView" ${useNoPeds ? 'checked' : ''} onchange="useNoPeds=true;renderTable()" />
          Exclude Peds <span style="color:var(--muted)">(${d.activeNoPeds} active)</span>
        </label>
        <span style="font-size:11px;color:var(--muted)">Excluded: 3 Faculty Meetings + ${pedsCount} Peds weeks</span>
      </div>
    </div>

    <!-- Summary Cards -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px">
      <div class="card" style="text-align:center;padding:12px 8px">
        <div style="font-size:24px;font-weight:700;color:var(--accent)">${totalWeeks}</div>
        <div style="font-size:10px;color:var(--muted)">Active Fridays</div>
      </div>
      <div class="card" style="text-align:center;padding:12px 8px">
        <div style="font-size:24px;font-weight:700;color:var(--green)">${passAny.length}</div>
        <div style="font-size:10px;color:var(--muted)">Pass Any 1 ≥70%</div>
      </div>
      <div class="card" style="text-align:center;padding:12px 8px">
        <div style="font-size:24px;font-weight:700;color:var(--yellow)">${passBoth.length}</div>
        <div style="font-size:10px;color:var(--muted)">Pass Both ≥70%</div>
      </div>
      <div class="card" style="text-align:center;padding:12px 8px">
        <div style="font-size:24px;font-weight:700;color:${passAnyPct >= 70 ? 'var(--green)' : 'var(--red)'}">${passAnyPct}%</div>
        <div style="font-size:10px;color:var(--muted)">Dept Any-1</div>
      </div>
      <div class="card" style="text-align:center;padding:12px 8px">
        <div style="font-size:24px;font-weight:700;color:${passBothPct >= 70 ? 'var(--green)' : 'var(--red)'}">${passBothPct}%</div>
        <div style="font-size:10px;color:var(--muted)">Dept Both</div>
      </div>
    </div>

    <!-- Legend -->
    <div style="display:flex;gap:16px;font-size:11px;color:var(--muted);margin-bottom:12px;flex-wrap:wrap">
      <span>🟢 <b>Both</b> = signed in for both meetings</span>
      <span>🟡 <b>7AM</b> = signed in for Grand Rounds only</span>
      <span>🔵 <b>8AM</b> = signed in for Conference only</span>
      <span>🎯 <b>Compliance = Any 1</b> (separate sign-in codes per meeting)</span>
      <span>Target: <b>70%</b></span>
    </div>

    <!-- Main Table -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">📋 Faculty Compliance</span>
        <div style="margin-left:auto;font-size:11px;color:var(--muted)">
          Need ≥${needAny} weeks for any-1 pass
        </div>
      </div>
      <div style="overflow-x:auto">
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:var(--bg);border-bottom:1px solid var(--line)">
              <th style="padding:7px 10px;text-align:left">Faculty</th>
              <th style="padding:7px 10px;text-align:left">EZ ID</th>
              <th style="padding:7px 10px;text-align:center" colspan="2">🟢 Both</th>
              <th style="padding:7px 10px;text-align:center">🟡 7AM</th>
              <th style="padding:7px 10px;text-align:center">🔵 8AM</th>
              <th style="padding:7px 10px;text-align:center" colspan="2">Attend Any 1</th>
              <th style="padding:7px 10px;text-align:center">Bar</th>
              <th style="padding:7px 10px;text-align:center">Status</th>
            </tr>
          </thead>
          <tbody>
            ${faculty.map(p => {
              const s = useNoPeds ? p.noPeds : p.all;
              const barAny = Math.min(s.pctAny, 100);
              const barBoth = Math.min(s.pctBoth, 100);
              const anyColor = s.passAny ? 'var(--green)' : (s.pctAny >= 60 ? 'var(--yellow)' : 'var(--red)');
              const bothColor = s.passBoth ? 'var(--green)' : (s.pctBoth >= 60 ? 'var(--yellow)' : 'var(--red)');
              const statusAny = s.passAny ? '✅' : (s.pctAny >= 60 ? '⚠️' : '🔴');
              const statusBoth = s.passBoth ? '✅' : (s.pctBoth >= 60 ? '⚠️' : '🔴');
              return `
                <tr style="border-bottom:1px solid var(--line-soft)">
                  <td style="padding:6px 10px"><strong>${escapeHtml(p.first)} ${escapeHtml(p.last)}</strong></td>
                  <td style="padding:6px 10px;color:var(--muted);font-family:monospace;font-size:10px">${p.ezId || '—'}</td>
                  <td style="padding:6px 10px;text-align:right;font-weight:700">${s.both}</td>
                  <td style="padding:6px 10px;text-align:left;font-size:10px;color:${bothColor}">${s.pctBoth}%</td>
                  <td style="padding:6px 10px;text-align:center">${s.only7}</td>
                  <td style="padding:6px 10px;text-align:center">${s.only8}</td>
                  <td style="padding:6px 10px;text-align:right;font-weight:700">${s.any}</td>
                  <td style="padding:6px 10px;text-align:left;font-size:11px;color:${anyColor}">/${s.total}</td>
                  <td style="padding:6px 10px">
                    <div style="width:70px;height:6px;background:var(--bg);border-radius:3px;overflow:hidden">
                      <div style="height:100%;width:${barAny}%;background:${anyColor};border-radius:3px"></div>
                    </div>
                  </td>
                  <td style="padding:6px 10px;text-align:center;font-size:13px" title="Any: ${s.pctAny}% | Both: ${s.pctBoth}%">
                    ${statusAny}
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Bottom summary -->
    <div class="card" style="margin-top:16px">
      <div class="card-body" style="padding:12px 16px;font-size:12px;color:var(--muted)">
        <div style="display:flex;gap:20px;flex-wrap:wrap">
          <span><b style="color:var(--green)">${passAny.length}/${faculty.length}</b> faculty pass <b>Any 1 meeting</b> ≥70%</span>
          <span><b style="color:var(--yellow)">${passBoth.length}/${faculty.length}</b> faculty pass <b>Both meetings</b> ≥70%</span>
          <span><b>${totalWeeks}</b> active weeks tracked</span>
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function exportAttendanceCSV() {
  if (!attendanceData) return;
  const view = useNoPeds ? 'Exclude Peds' : 'All Weeks';
  const headers = ['First Name','Last Name','EZ ID','View','Both Weeks','Both %','Only 7AM','Only 8AM','Any 1 Week','Total Weeks','Any 1 %','Pass Any 1','Pass Both'];
  const rows = attendanceData.people.map(p => {
    const s = useNoPeds ? p.noPeds : p.all;
    return [p.first, p.last, p.ezId, view, s.both, s.pctBoth + '%', s.only7, s.only8, s.any, s.total, s.pctAny + '%', s.passAny ? 'Yes' : 'No', s.passBoth ? 'Yes' : 'No'];
  });
  
  let csv = headers.join(',') + '\n' + rows.map(r => r.map(c => '"' + String(c).replace(/"/g,'""') + '"').join(',')).join('\n');
  const blob = new Blob([csv], {type: 'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'Grand_Rounds_Compliance_2025-2026.csv';
  a.click();
  URL.revokeObjectURL(url);
  showToast('📥 CSV exported', 'success');
}
