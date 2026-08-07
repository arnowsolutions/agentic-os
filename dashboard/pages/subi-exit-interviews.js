// ──────────────────────────────────────────────────────────────
// Sub-I Exit Interviews — Outlook deeplink generator
// Mirrors calendar-invites.js exactly: iframe embed of the
// server-generated deeplink page. Works the same way as the
// Grand Rounds / Monday Conference Calendar Invites page.
// ──────────────────────────────────────────────────────────────

async function renderSubiExitInterviews() {
  const content = document.getElementById('pageContent');

  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">🎓 Sub-I Exit Interviews</h1>
        <p class="page-breadcrumb">One-click Outlook compose — interviewee and time per row</p>
      </div>
    </div>
    <div style="position:relative;width:100%;height:calc(100vh - 180px);min-height:600px;border:1px solid var(--border-color,#334155);border-radius:12px;overflow:hidden;background:#0f172a">
      <iframe src="/api/subi-exit-invites?test=false" style="width:100%;height:100%;border:none" title="Sub-I Exit Interviews"></iframe>
    </div>
  `;
}
