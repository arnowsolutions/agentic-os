async function renderStaffSchedule(target) {
  const content = target || document.getElementById('suitePane') || document.getElementById('pageContent');
  const hospitals = ['Moses', 'Wakefield', 'Weiler'];
  const roles = ['NP', 'PA', 'Coordinator', 'Nurse'];

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">Staff Schedule</div>
        <div class="page-subtitle">NP, PA, coordinator & nurse schedules across all hospitals</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderStaffSchedule()">↻ Refresh</button>
      </div>
    </div>
    <div class="ss-tabs" id="ssTabs">
      ${hospitals.map(h => `<button class="ss-tab ${h==='Moses'?'active':''}" onclick="switchSSTab('${h}')">${h}</button>`).join('')}
    </div>
    <div id="ssContent" class="ss-content"><div class="loading"><div class="loading-spinner"></div></div></div>
    <style>
      .ss-tabs { display:flex; gap:4px; margin-top:12px; border-bottom:2px solid var(--border); }
      .ss-tab { padding:8px 16px; border:none; background:none; cursor:pointer; font-size:13px; font-weight:600; color:var(--text-muted); border-bottom:3px solid transparent; margin-bottom:-2px; }
      .ss-tab.active { color:var(--text); border-bottom-color:var(--accent); }
      .ss-content { margin-top:12px; }
      .ss-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:10px; }
      .ss-card { background:var(--bg-card); border-radius:var(--radius-md); border:1px solid var(--border); padding:14px; }
      .ss-card .name { font-size:13px; font-weight:600; }
      .ss-card .role { font-size:11px; color:var(--text-muted); display:inline-block; padding:1px 6px; border-radius:4px; background:var(--fill-muted); margin-top:4px; }
      .ss-card .detail { font-size:11px; color:var(--text-muted); margin-top:6px; }
      .ss-card .detail span { display:block; padding:2px 0; }
    </style>
  `;
  window._ssHospital = 'Moses';
  loadStaffSchedule('Moses');
}

async function loadStaffSchedule(hospital) {
  const container = document.getElementById('ssContent');
  try {
    const res = await fetch(`/api/staff-schedule?hospital=${encodeURIComponent(hospital)}`).then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
    const staff = res.staff || [];
    stampPage(res);
    if (!staff.length) {
      container.innerHTML = `<div style="padding:24px;text-align:center;color:var(--text-muted)">No staff listed for ${escapeHtml(hospital)} yet.</div>`;
      return;
    }
    container.innerHTML = `<div class="ss-grid">${staff.map(s => `
      <div class="ss-card">
        <div class="name">${escapeHtml(s.name)}</div>
        <div class="role">${s.role || 'Staff'}</div>
        <div class="detail"><span>${escapeHtml(s.detail || s.schedule || '')}</span></div>
      </div>
    `).join('')}</div>`;
  } catch (e) {
    container.innerHTML = `<div style="padding:24px;text-align:center;color:var(--text-muted)">! Could not load staff schedule — ${escapeHtml(e.message)}</div>`;
  }
}

function switchSSTab(hospital) {
  window._ssHospital = hospital;
  document.querySelectorAll('.ss-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.ss-tab[onclick*="${hospital}"]`).classList.add('active');
  loadStaffSchedule(hospital);
}
