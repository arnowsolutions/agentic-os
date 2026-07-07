async function renderClaudeCode() {
  const content = document.getElementById('pageContent');
  const TERMINAL_URL = 'https://claude.srv1738752.hstgr.cloud';

  content.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
      <div>
        <div class="page-title" style="font-size:20px;font-weight:700">🤖 Claude Code</div>
        <div style="font-size:12px;color:var(--text-muted);margin-top:2px">Free LLM terminal · OmniRoute · $0.00 · 4 free models</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderClaudeCode()">🔄 Refresh</button>
        <a href="${TERMINAL_URL}" target="_blank" class="btn btn-primary">↗ Open in new tab</a>
      </div>
    </div>

    <!-- Model picker guide -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:12px">
      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);padding:12px">
        <div style="font-size:11px;color:#f59e0b;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Pick "Opus" or "Default"</div>
        <div style="font-size:14px;font-weight:600">Llama 3.3 70B</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Best reasoning · biggest free model</div>
      </div>
      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);padding:12px">
        <div style="font-size:11px;color:#3b82f6;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Pick "Sonnet"</div>
        <div style="font-size:14px;font-weight:600">Llama 4 Scout 17B</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Best coding · balanced quality</div>
      </div>
      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);padding:12px">
        <div style="font-size:11px;color:#22c55e;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Pick "Sonnet 5"</div>
        <div style="font-size:14px;font-weight:600">Qwen 3.6 27B</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Alibaba coding model · newer</div>
      </div>
      <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);padding:12px">
        <div style="font-size:11px;color:#a78bfa;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px">Pick "Haiku"</div>
        <div style="font-size:14px;font-weight:600">Llama 3.1 8B</div>
        <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Fastest · sub-second</div>
      </div>
    </div>

    <!-- Terminal iframe — fills remaining viewport -->
    <div style="height:calc(100vh - 250px);display:flex;flex-direction:column;border-radius:var(--radius-md);overflow:hidden;border:1px solid var(--border);background:#1a1a2e">
      <div style="display:flex;align-items:center;gap:8px;padding:8px 14px;background:#0f0f1e;border-bottom:1px solid var(--border);flex-shrink:0">
        <span style="width:12px;height:12px;border-radius:50%;background:#ff5f56;display:inline-block"></span>
        <span style="width:12px;height:12px;border-radius:50%;background:#ffbd2e;display:inline-block"></span>
        <span style="width:12px;height:12px;border-radius:50%;background:#27c93f;display:inline-block"></span>
        <span style="margin-left:8px;font-size:12px;color:var(--text-muted);font-family:monospace">claude-code — /workspace</span>
      </div>
      <iframe
        src="${TERMINAL_URL}"
        style="width:100%;flex:1;border:none;background:#1a1a2e;min-height:0"
        allow="clipboard-read;clipboard-write;fullscreen;autoplay"
        loading="lazy"
        title="Claude Code Terminal"
      ></iframe>
    </div>
  `;
}
