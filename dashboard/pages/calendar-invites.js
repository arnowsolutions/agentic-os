// ──────────────────────────────────────────────────────────────
// Calendar Invites — Outlook deeplink generator with DB-backed schedule editor
// ──────────────────────────────────────────────────────────────

async function renderCalendarInvites() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">📧 Calendar Invites</h1>
        <p class="page-breadcrumb">One-click Outlook calendar invites with editable schedule</p>
      </div>
    </div>
    <div style="position:relative;width:100%;height:calc(100vh - 180px);min-height:600px;border:1px solid var(--border-color,#334155);border-radius:12px;overflow:hidden;background:#0f172a">
      <iframe src="/api/calendar-invites?test=false" style="width:100%;height:100%;border:none" title="Calendar Invites"></iframe>
    </div>
  `;
}
