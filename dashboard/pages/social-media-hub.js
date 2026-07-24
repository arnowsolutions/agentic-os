"use strict";

/**
 * Social Media Hub Dashboard
 * Links to all integrated social media skills and tools
 */
async function renderSocialMediaHub() {
  const content = document.getElementById('pageContent');
  content.innerHTML = `
    <div class="page">
      <div class="page-header">
        <h1><span style="filter:none">📱</span> Social Media Hub</h1>
        <p class="page-subtitle">42+ integrated skills for social media management, content creation, and platform automation</p>
      </div>

      <!-- Stats Overview -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px">
        <div class="card"><div class="card-body" style="text-align:center">
          <div style="font-size:28px;font-weight:700;color:#6c5ce7">42</div>
          <div style="font-size:12px;color:#888">SKILL.md Files</div>
        </div></div>
        <div class="card"><div class="card-body" style="text-align:center">
          <div style="font-size:28px;font-weight:700;color:#a29bfe">14</div>
          <div style="font-size:12px;color:#888">Skill Categories</div>
        </div></div>
        <div class="card"><div class="card-body" style="text-align:center">
          <div style="font-size:28px;font-weight:700;color:#fd79a8">4</div>
          <div style="font-size:12px;color:#888">Platform Connectors</div>
        </div></div>
        <div class="card"><div class="card-body" style="text-align:center">
          <div style="font-size:28px;font-weight:700;color:#55efc4">4</div>
          <div style="font-size:12px;color:#888">Platform Connectors</div>
        </div></div>
      </div>

      <!-- Skill Categories Grid -->
      <h2 style="font-size:16px;margin:0 0 12px 0;color:#ccc">Skill Categories</h2>
      <div id="smh-categories" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:24px"></div>

      <!-- Installed Integrations -->
      <h2 style="font-size:16px;margin:0 0 12px 0;color:#ccc">Installed Integrations</h2>
      <div class="card" style="margin-bottom:24px">
        <div class="card-body" id="smh-integrations"></div>
      </div>

      <!-- Related Hermes skills -->
      <h2 style="font-size:16px;margin:0 0 12px 0;color:#ccc">Related Hermes Skills</h2>
      <div class="card">
        <div class="card-body" id="smh-related"></div>
      </div>
    </div>
  `;

  renderCategories();
  renderIntegrations();
  renderRelated();
}

const SMH_CATEGORIES = [
  { name: 'analytics', icon: '📊', count: 3, desc: 'A/B testing, metrics tracking, performance reporting' },
  { name: 'creation', icon: '✍️', count: 4, desc: 'Hook writing, post/thread creation, CTAs' },
  { name: 'engagement', icon: '💬', count: 5, desc: 'Comments, DMs, mentions, influencer outreach' },
  { name: 'strategy', icon: '🎯', count: 4, desc: 'Brand voice, content pillars, CRM-social bridge, positioning' },
  { name: 'publishing', icon: '🚀', count: 4, desc: 'Cross-post, draft review, schedule queue, thread structure' },
  { name: 'repurpose', icon: '♻️', count: 3, desc: 'Blog→thread, newsletter→posts, podcast→clips' },
  { name: 'research', icon: '🔍', count: 3, desc: 'Competitor audit, prospect audit, profile discovery' },
  { name: 'trends', icon: '📈', count: 3, desc: 'Trend monitoring, briefings, news response' },
  { name: 'visual', icon: '🎨', count: 4, desc: 'Visual planning, image prompts, meme creation, asset format' },
  { name: 'crisis', icon: '🛡️', count: 3, desc: 'Crisis response, apology drafting, impersonator monitor' },
  { name: 'captions', icon: '🏷️', count: 1, desc: 'Caption drafting across platforms' },
  { name: 'profile', icon: '👤', count: 2, desc: 'Profile audit, presence refresh' },
  { name: 'planning', icon: '📅', count: 2, desc: 'Content calendar, cadence & timing' },
  { name: 'facebook', icon: '👍', count: 1, desc: 'Facebook Page posting via Meta Graph API' },
  { name: 'clinstagram', icon: '📸', count: 1, desc: 'Instagram CLI — post, DMs, stories, analytics, comments' },
];

const SMH_INTEGRATIONS = [
  { name: 'Instagram (clinstagram)', url: 'https://github.com/paperfoot/clinstagram', desc: 'Instagram CLI — post, DMs, stories, analytics, comments, hashtags. Meta API + private API.', binary: 'clinstagram', status: '✅ v0.3.2 installed' },
  { name: 'Growth OS', url: 'https://github.com/nocodework/growth-os', desc: 'Business URL → ICP audit → GA4/GSC integration → marketing delegation', dir: '/workspace/integrations/growth-os', status: '📦 Installed' },
  { name: 'X/Twitter (xurl)', url: 'https://github.com/xdevplatform/xurl', desc: 'Official X API CLI — post, search, DM, media upload', skill: 'xurl', status: '✅ Configured' },
  { name: 'Facebook Page', url: 'https://github.com/mustfaaa/hermes-facebook-skill', desc: 'Meta Graph API — post, comment, like, fetch', skill: 'facebook', status: '⚠️ Needs FB_PAGE_TOKEN' },
  { name: 'Crewm8 Social Graph', url: 'https://github.com/gokulb20/Crewm8-Social-Media-Manager-Skill-Graph', desc: '37 agent-agnostic social media skills (upstream)', dir: '/workspace/integrations/crewm8-social', status: '📦 Installed' },
];

const SMH_RELATED = [
  { name: 'social-media-agent-orchestrator', desc: '10-agent chain: Trend Monitor → Brand Strategist → Copywriter → ... → QC' },
  { name: 'content-repurposing-engine', desc: 'Long-form → 5 insights → platform-native posts + reel ideas' },
  { name: 'claude-code-marketing-stack', desc: 'Campaign brief → plan → carousel → video script → email' },
  { name: 'ai-employees', desc: 'Named AI Employee roles — includes Social Media Manager' },
  { name: 'xurl', desc: 'X/Twitter API via official CLI — post, search, DM, media' },
];

function renderCategories() {
  const el = document.getElementById('smh-categories');
  el.innerHTML = SMH_CATEGORIES.map(c => `
    <div class="card" style="cursor:pointer" onclick="navigate('skill-${c.name}')">
      <div class="card-body">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
          <span style="font-size:20px">${c.icon}</span>
          <strong style="font-size:14px;color:#eee">${c.name.charAt(0).toUpperCase() + c.name.slice(1)}</strong>
          <span style="margin-left:auto;font-size:11px;color:#888;background:#1a1a2e;padding:2px 8px;border-radius:4px">${c.count} skills</span>
        </div>
        <div style="font-size:12px;color:#888;line-height:1.5">${c.desc}</div>
      </div>
    </div>
  `).join('');
}

function renderIntegrations() {
  const el = document.getElementById('smh-integrations');
  el.innerHTML = SMH_INTEGRATIONS.map(i => `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #1a1a2e">
      <span>${i.status.split(' ')[0]}</span>
      <div style="flex:1">
        <a href="${i.url}" target="_blank" style="color:#a29bfe;text-decoration:none;font-weight:500">${i.name}</a>
        <div style="font-size:12px;color:#666;margin-top:2px">${i.desc}</div>
      </div>
      <span style="font-size:11px;color:#888">${i.status}</span>
    </div>
  `).join('');
}

function renderRelated() {
  const el = document.getElementById('smh-related');
  el.innerHTML = SMH_RELATED.map(r => `
    <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #1a1a2e">
      <span>🔗</span>
      <div style="flex:1">
        <div style="color:#a29bfe;font-weight:500;font-size:13px">${r.name}</div>
        <div style="font-size:12px;color:#666;margin-top:2px">${r.desc}</div>
      </div>
    </div>
  `).join('');
}
