/* Pac-Man 3D — a simple browser canvas maze game */
async function renderPacMan(target) {
  const content = target || document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <h1>Pac-Man 3D</h1>
      <p class="page-subtitle">3D variation of the classic maze chase</p>
    </div>
    <div class="game-wrapper">
      <canvas id="gameCanvas" width="800" height="600"></canvas>
      <div class="game-controls">
        <kbd>Arrow keys</kbd> — move
        <kbd>P</kbd> / <kbd>Esc</kbd> — pause
        <kbd>M</kbd> — mute
      </div>
    </div>
  `;
  // Minimal canvas setup — just a placeholder; real Three.js port lives in /workspace/games/pac3d
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#05060a';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ffd43b';
  ctx.beginPath();
  ctx.arc(400, 300, 12, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#ff6b6b';
  ctx.beginPath();
  ctx.arc(420, 300, 12, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#1dd1a1';
  ctx.beginPath();
  ctx.arc(440, 300, 12, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#ffa322';
  ctx.beginPath();
  ctx.arc(460, 300, 12, 0, Math.PI * 2);
  ctx.fill();
}
