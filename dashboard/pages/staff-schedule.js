async function renderStaffSchedule() {
  const content = document.getElementById('pageContent');
  const hospitals = ['Moses', 'Wakefield', 'Weiler'];
  const roles = ['NP', 'PA', 'Coordinator', 'Nurse'];

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">👥 Staff Schedule</div>
        <div class="page-subtitle">NP, PA, coordinator & nurse schedules across all hospitals</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderStaffSchedule()">🔄 Refresh</button>
      </div>
    </div>
    <div class="ss-tabs" id="ssTabs">
      ${hospitals.map(h => `<button class="ss-tab ${h==='Moses'?'active':''}" onclick="switchSSTab('${h}')">🏥 ${h}</button>`).join('')}
    </div>
    <div id="ssContent" class="ss-content"><div class="loading"><div class="loading-spinner"></div></div></div>
    <style>
      .ss-tabs { display:flex; gap:4px; margin-top:12px; border-bottom:2px solid var(--border); }
      .ss-tab { padding:8px 16px; border:none; background:none; cursor:pointer; font-size:13px; font-weight:600; color:var(--text-muted); border-bottom:3px solid transparent; margin-bottom:-2px; }
      .ss-tab.active { color:var(--text); border-bottom-color:#6c5ce7; }
      .ss-content { margin-top:12px; }
      .ss-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:10px; }
      .ss-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:14px; }
      .ss-card .name { font-size:13px; font-weight:600; }
      .ss-card .role { font-size:11px; color:var(--text-muted); display:inline-block; padding:1px 6px; border-radius:4px; background:rgba(255,255,255,0.06); margin-top:4px; }
      .ss-card .detail { font-size:11px; color:var(--text-muted); margin-top:6px; }
      .ss-card .detail span { display:block; padding:2px 0; }
    </style>
  `;
  window._ssHospital = 'Moses';
  loadStaffSchedule('Moses');
}

async function loadStaffSchedule(hospital) {
  try {
    const res = await fetch(`/api/staff-schedule?hospital=${hospital}`).then(r => r.json()).catch(() => ({}));
    const staff = res.staff || [];

    // Demo data if empty
    const demo = {
      Moses: [
        {name:'Jane Smith', role:'NP', detail:'Mon-Fri, Urology Clinic'},
        {name:'John Davis', role:'PA', detail:'Mon-Thu, OR & Clinic'},
        {name:'Maria Garcia', role:'Coordinator', detail:'Mon-Fri, Admin Office'},
        {name:'Linda Brown', role:'Nurse', detail:'Tue-Sat, Inpatient'},
        {name:'Robert Wilson', role:'NP', detail:'Wed-Sun, Float'},
      ],
      Wakefield: [
        {name:'Sarah Lee', role:'NP', detail:'Mon-Fri, Clinic'},
        {name:'David Kim', role:'PA', detail:'Mon, Wed, Fri'},
        {name:'Amanda Taylor', role:'Coordinator', detail:'Mon-Thu'},
      ],
      Weiler: [
        {name:'Michael Chen', role:'NP', detail:'Mon-Fri, Pediatric Urology'},
        {name:'Emily White', role:'Nurse', detail:'Weekdays, Inpatient'},
        {name:'James Miller', role:'PA', detail:'Tue, Thu, Sat'},
      ],
    };

    const data = staff.length > 0 ? staff : (demo[hospital] || []);
    const container = document.getElementById('ssContent');
    container.innerHTML = `<div class="ss-grid">${data.map(s => `
      <div class="ss-card">
        <div class="name">${escapeHtml(s.name)}</div>
        <div class="role">${s.role || 'Staff'}</div>
        <div class="detail"><span>${escapeHtml(s.detail || s.schedule || '')}</span></div>
      </div>
    `).join('')}</div>`;
  } catch(e) {
    document.getElementById('ssContent').innerHTML = `<div style="padding:24px;text-align:center;color:var(--text-muted)">⚠️ ${escapeHtml(e.message)}</div>`;
  }
}

function switchSSTab(hospital) {
  window._ssHospital = hospital;
  document.querySelectorAll('.ss-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.ss-tab[onclick*="${hospital}"]`).classList.add('active');
  loadStaffSchedule(hospital);
}
