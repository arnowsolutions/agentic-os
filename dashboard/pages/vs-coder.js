async function renderVsCoder() {
  const content = document.getElementById('pageContent');
  const CODER_URL = 'https://code.srv1738752.hstgr.cloud';
  
  content.innerHTML = `
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-title">VS Coder</div>
        <div class="page-subtitle">Full code editor — edit files, run terminals, manage repos</div>
      </div>
      <div class="btn-group">
        <button class="btn btn-ghost" onclick="renderVsCoder()">🔄 Refresh</button>
        <a href="${CODER_URL}" target="_blank" class="btn btn-primary" rel="noopener noreferrer">↗ Open in new tab</a>
      </div>
    </div>
    <div class="vs-coder-container">
      <iframe
        src="${CODER_URL}"
        class="vs-coder-iframe"
        allow="clipboard-read;clipboard-write;fullscreen;camera;microphone"
        loading="lazy"
        title="VS Coder — Code Editor"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
      ></iframe>
    </div>
    <style>
      .vs-coder-container {
        flex: 1;
        display: flex;
        border-radius: var(--radius-md);
        overflow: hidden;
        border: 1px solid var(--border);
        background: #1a1a2e;
        margin-top: 12px;
        min-height: 0;
      }
      .vs-coder-iframe {
        width: 100%;
        height: calc(100vh - 200px);
        border: none;
        background: #1e1e1e;
      }
    </style>
  `;
}
