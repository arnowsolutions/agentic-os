/* Tetris Swap — a block-swapping puzzle game */
async function renderTetrisSwap(target) {
  const content = target || document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page-header">
      <h1>Tetris Swap</h1>
      <p class="page-subtitle">Swap adjacent blocks to create matching groups</p>
    </div>
    <div class="game-wrapper">
      <div class="swap-board" id="swapBoard">
        <!-- Board rendered by JS -->
      </div>
      <div class="game-controls">
        <kbd>Arrow keys</kbd> — select block
        <kbd>Space</kbd> — swap
        <kbd>R</kbd> — restart
      </div>
    </div>
  `;
  // Minimal board placeholder — 4x4 grid of colored squares
  const board = document.getElementById('swapBoard');
  board.innerHTML = '';
  const colors = ['#ff6b6b', '#ffa322', '#1dd1a1', '#44a0ff'];
  for (let i = 0; i < 16; i++) {
    const square = document.createElement('div');
    square.className = 'swap-square';
    square.style.backgroundColor = colors[i % 4];
    square.dataset.index = i;
    square.addEventListener('click', () => alert(`Block ${i + 1} selected`));
    board.appendChild(square);
  }
  const style = document.createElement('style');
  style.textContent = `
    .swap-board { display:grid; grid-template-columns:repeat(4, 1fr); gap:4px; padding:8px; }
    .swap-square { width:40px; height:40px; background:var(--color); border:1px solid var(--border); }
  `;
  document.head.appendChild(style);
}
