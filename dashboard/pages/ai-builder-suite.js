/**
 * AI Builder Suite — merged Builder / Image / Video / Gallery (PR7).
 *
 * Builder and Gallery delegate to their original modules (single-sourced —
 * the suite adds zero duplicated logic). Image and Video embed the standalone
 * prompt-builder pages (/dashboard/prompt-image.html, prompt-video.html)
 * in-place, so they no longer bounce the whole SPA out to a bare page.
 *
 * Legacy hashes (#ai-builder, #prompt-tools-image, #prompt-tools-video,
 * #image-gallery) redirect here via LEGACY_REDIRECTS in app.js and land on
 * the matching tab. Tab state lives in the hash:
 * #ai-builder-suite?tab=builder|image|video|gallery. No emoji.
 */

var AI_BUILDER_SUITE_TABS = [
  { key: 'builder', label: 'Builder', module: 'ai-builder.js',    fn: 'renderAiBuilder' },
  { key: 'image',   label: 'Image',   embed: '/dashboard/prompt-image.html' },
  { key: 'video',   label: 'Video',   embed: '/dashboard/prompt-video.html' },
  { key: 'gallery', label: 'Gallery', module: 'image-gallery.js', fn: 'renderImageGallery' },
];

function aiBuilderSuiteActiveTab() {
  var m = String(window.location.hash || '').match(/[?&]tab=([a-z-]+)/);
  var key = m ? m[1] : '';
  return AI_BUILDER_SUITE_TABS.some(function (t) { return t.key === key; }) ? key : 'builder';
}

/** Switch tab: sync hash without a full route cycle, then re-render in place. */
async function aiBuilderSuiteSetTab(key) {
  var target = 'ai-builder-suite?tab=' + key;
  try {
    history.replaceState(null, '', '#' + target);
  } catch (e) {
    window.location.hash = target;
    return; // hashchange → navigate() re-renders
  }
  await renderAiBuilderSuite();
}

/** Load the tab's source module once; a loaded module keeps its function. */
async function ensureSuiteModule(moduleFile, fnName) {
  if (typeof window[fnName] === 'function') return;
  await loadScript('/dashboard/pages/' + moduleFile + '?v=' + Date.now());
}

async function renderAiBuilderSuite() {
  const content = document.getElementById('pageContent');
  const active = aiBuilderSuiteActiveTab();
  const tab = AI_BUILDER_SUITE_TABS.find(function (t) { return t.key === active; }) || AI_BUILDER_SUITE_TABS[0];

  content.innerHTML = `
    <div class="tabs">
      ${AI_BUILDER_SUITE_TABS.map(function (t) {
        return `<button class="tab${t.key === active ? ' active' : ''}" onclick="aiBuilderSuiteSetTab('${t.key}')">${t.label}</button>`;
      }).join('')}
    </div>
    <div id="suitePane"></div>
  `;

  const pane = document.getElementById('suitePane');
  try {
    if (tab.embed) {
      // Standalone tool page embedded in place (kept single-sourced).
      pane.innerHTML = `<iframe class="suite-embed" src="${tab.embed}" title="${tab.label} — embedded tool" loading="lazy"></iframe>`;
      return;
    }
    await ensureSuiteModule(tab.module, tab.fn);
    const fn = window[tab.fn];
    if (typeof fn !== 'function') throw new Error('Suite module not available: ' + tab.module);
    await fn(pane);
  } catch (err) {
    if (pane) {
      pane.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">!</div>
          <div class="empty-state-title">Could not load ${tab.label}</div>
          <div class="empty-state-desc">${escapeHtml(err.message)}</div>
          <button class="btn btn-primary mt-3" onclick="renderAiBuilderSuite()">Retry</button>
        </div>`;
    }
  }
}
