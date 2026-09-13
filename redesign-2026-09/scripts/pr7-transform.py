#!/usr/bin/env python3
"""PR7 transform — AI Builder Suite + Workspace suite prep (2026-09-12).

For each merged page module:
  1. Refactor main render fn → (target) + suitePane fallback chain.
  2. Emoji sweep (approved glyph set; VS16 stripped first).

Assertions: every replacement must hit; leftover scan at end must be empty.
Backups: redesign-2026-09/backup-pre-pr7/
"""
import re
import pathlib
import subprocess
import sys

BASE = pathlib.Path('/workspace/agentic-os/dashboard/pages')

REFACTOR = {
    'ai-builder.js': 'renderAiBuilder',
    'image-gallery.js': 'renderImageGallery',
    'file-browser.js': 'renderFileBrowser',
    'script-runner.js': 'renderScriptRunner',
    'vs-coder.js': 'renderVsCoder',
    'google-studio.js': 'renderGoogleStudio',
}

# (file, old, new, expected_count) — every one asserted.
REPLACES = [
    # ── file-browser.js ──────────────────────────────────────────────
    ('file-browser.js', '>🗂 File Browser</div>', '>File Browser</div>', 1),
    ('file-browser.js', 'renderFileBrowser()">🔄 Reset</button>', 'renderFileBrowser()">↻ Reset</button>', 1),
    ('file-browser.js', 'id="fbUpBtn" disabled>⬆ Up</button>', 'id="fbUpBtn" disabled>↑ Up</button>', 1),
    ('file-browser.js', "'📭 Empty directory'", "'Empty directory'", 1),
    ('file-browser.js', "const icon = isDir ? '📁' : '📄';", "const icon = isDir ? '▣' : '▸';", 1),
    ('file-browser.js', '>⚠ ${escapeHtml(e.message)}', '>! ${escapeHtml(e.message)}', 1),
    # ── script-runner.js ─────────────────────────────────────────────
    ('script-runner.js', '>⚙ Script Runner</div>', '>Script Runner</div>', 1),
    ('script-runner.js', 'renderScriptRunner()">🔄 Reset</button>', 'renderScriptRunner()">↻ Reset</button>', 1),
    ('script-runner.js', '>📜 Scripts</h3>', '>Scripts</h3>', 1),
    ('script-runner.js', '>🔧 Custom Command</h3>', '>Custom Command</h3>', 1),
    ('script-runner.js', 'id="srRunBtn">▶ Run</button>', 'id="srRunBtn">▸ Run</button>', 1),
    ('script-runner.js', 'clearSrOutput()">🗑 Clear</button>', 'clearSrOutput()">✕ Clear</button>', 1),
    ('script-runner.js', 'copySrOutput()">📋 Copy</button>', 'copySrOutput()">Copy</button>', 1),
    ('script-runner.js', '`▶ Running: ${name', '`▸ Running: ${name', 1),
    ('script-runner.js', '">✅ Completed', '">✓ Completed', 1),
    ('script-runner.js', '">❌ Failed', '">✕ Failed', 1),
    ('script-runner.js', '">❌ Error: ', '">✕ Error: ', 1),
    ('script-runner.js', '`✗ ${name', '`✕ ${name', 1),
    # ── vs-coder.js ──────────────────────────────────────────────────
    ('vs-coder.js', 'renderVsCoder()">🔄 Refresh</button>', 'renderVsCoder()">↻ Refresh</button>', 1),
    # ── google-studio.js ─────────────────────────────────────────────
    ('google-studio.js', '>➕ New Project</button>', '>+ New Project</button>', 2),
    ('google-studio.js', 'title="New Project">➕</button>', 'title="New Project">+</button>', 1),
    ('google-studio.js', 'gsRefresh()">🔄 Refresh</button>', 'gsRefresh()">↻ Refresh</button>', 1),
    ('google-studio.js', '"noopener">🚀 Open Script Editor</a>', '"noopener">Open Script Editor</a>', 2),
    ('google-studio.js', '<h3>📁 My Scripts</h3>', '<h3>My Scripts</h3>', 1),
    ('google-studio.js', 'google-studio-empty-icon">📝</div>', 'google-studio-empty-icon">◆</div>', 1),
    ('google-studio.js', 'title="Save to Google Drive">💾 Save</button>', 'title="Save to Google Drive">Save</button>', 1),
    ('google-studio.js', "'💾 Save'", "'Save'", 1),
    ('google-studio.js', '>⚠ ${', '>! ${', 2),
    ('google-studio.js', '`⚠ ${', '`! ${', 4),
    ('google-studio.js', 'project-icon">📜</span>', 'project-icon">◆</span>', 1),
    ('google-studio.js', "const icon = f.type === 'HTML' ? '🌐' : f.type === 'JSON' ? '📋' : '📜';",
                          "const icon = f.type === 'HTML' ? '○' : f.type === 'JSON' ? '◆' : '▸';", 1),
    ('google-studio.js', '>📜 New Apps Script Project</h3>', '>New Apps Script Project</h3>', 1),
    ('google-studio.js', "'✅ Saved to Google Drive!'", "'✓ Saved to Google Drive!'", 1),
    ('google-studio.js', "textContent = '✅ Saved'", "textContent = '✓ Saved'", 1),
    ('google-studio.js', '`✅ Created', '`✓ Created', 1),
    ('google-studio.js', '>▶ Open in Script Editor</a>', '>↗ Open in Script Editor</a>', 1),
    # ── image-gallery.js ─────────────────────────────────────────────
    ('image-gallery.js', '>🎨 Image Gallery</div>', '>Image Gallery</div>', 1),
    ('image-gallery.js', 'igRefresh()">🔄 Refresh</button>', 'igRefresh()">↻ Refresh</button>', 1),
    ('image-gallery.js', '">✨ Create in AI Studio</a>', '>Create in AI Studio</a>', 1),
    ('image-gallery.js', '">🎨 DALL-E</a>', '>DALL-E</a>', 1),
    ('image-gallery.js', '>📁 Folders</div>', '>Folders</div>', 1),
    ('image-gallery.js', '>📂 All Images</div>', '>All Images</div>', 2),
    ('image-gallery.js', '>📁 ${name}</div>', '>${name}</div>', 1),
    ('image-gallery.js', 'igDownloadCurrent()">⬇ Download</button>', 'igDownloadCurrent()">↓ Download</button>', 1),
    ('image-gallery.js', 'igCopyPath()">📋 Copy Path</button>', 'igCopyPath()">Copy Path</button>', 1),
    ('image-gallery.js', 'ig-loading">📂 Scanning workspace...', 'ig-loading">Scanning workspace...', 1),
    ('image-gallery.js', 'ig-error">❌ Failed to load', 'ig-error">✕ Failed to load', 1),
    ('image-gallery.js', 'ig-empty">📭 No images found', 'ig-empty">No images found', 1),
    ('image-gallery.js', '">⬇</button>', '">↓</button>', 1),
    ('image-gallery.js', "'✅ Copied!'", "'✓ Copied!'", 1),
    ('image-gallery.js', 'title="List view">☰</button>', 'title="List view">▤</button>', 1),
    # ── ai-builder.js ────────────────────────────────────────────────
    ('ai-builder.js', 'runBuilderCode()">▶ Run</button>', 'runBuilderCode()">▸ Run</button>', 1),
]

WHITELIST = set('✓✕↻⌕●◐▸▣◆○▤▦↗↑↓→✎↩—‹›')
EMOJI_RE = re.compile(r'[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\u2B00-\u2BFF\u25B6]')


def main():
    failures = []
    for fn in REFACTOR:
        p = BASE / fn
        t = p.read_text()
        t = t.replace('\uFE0F', '')  # strip VS16 — every such char is emoji-ish in these files

        fname = REFACTOR[fn]
        old = f"async function {fname}() {{\n  const content = document.getElementById('pageContent');"
        new = (f"async function {fname}(target) {{\n"
               f"  const content = target || document.getElementById('suitePane') || document.getElementById('pageContent');")
        if old not in t:
            failures.append(f"{fn}: refactor pattern not found for {fname}")
        else:
            t = t.replace(old, new, 1)

        for rfn, rold, rnew, n in REPLACES:
            if rfn != fn:
                continue
            c = t.count(rold)
            if c != n:
                failures.append(f"{fn}: '{rold[:44]}…' expected {n}x, found {c}")
                continue
            t = t.replace(rold, rnew)

        if fn == 'script-runner.js':
            t2, k = re.subn(r"icon: '[^']*',", "icon: '▸',", t)
            if k != 8:
                failures.append(f"script-runner.js: icon: rows expected 8, found {k}")
            t = t2

        # emoji leftovers
        left = sorted({c for c in EMOJI_RE.findall(t) if c not in WHITELIST})
        p.write_text(t)
        r = subprocess.run(['node', '--check', str(p)], capture_output=True, text=True)
        status = 'OK ' if r.returncode == 0 else f'FAIL({r.stderr.strip()[:80]})'
        print(f"{fn:22s} {status}  leftover={left if left else 'none'}")
        if left:
            failures.append(f"{fn}: leftover {left}")

    print()
    if failures:
        print('FAILURES:')
        for f in failures:
            print('  -', f)
        return 1
    print('ALL TRANSFORMS PASS — 6 files, emoji clean')
    return 0


if __name__ == '__main__':
    sys.exit(main())
