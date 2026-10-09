# AI Design Intel — October 8, 2026
Sources scanned: X (available), Reddit (web_search for graphic_design, web_design, UI_Design, midjourney, StableDiffusion, FigmaDesign), HN (unavailable - 502 errors), GitHub (available), Google News (available). Candidates considered: 12. Passed the bar: 7.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Broom Design | Tool | ✅ Adopt it | Consolidates top anti-slop skills with checker and design system generator |
| Brand Identity Skill | Tool | ✅ Adopt it | Creates unified brand identity system from one brief with measurement |
| Persian Motion Director | Tool | 👀 Watch it | Claude skill for pro motion design with correct Persian/Farsi typography |
| Qiaomu Codex ImageGen | Tool | 👀 Watch it | Enables any agent to use Codex's built-in image generation via MCP |
| Anthropic Claude Design | Idea | 👀 Watch it | Experimental AI design tool for creating quick visuals (needs evaluation) |
| Google Pics | Idea | ❌ Skip it | Prompt-based AI design tool - likely generates generic slop aesthetics |
| Figma AI Plugins | Trend | 👀 Watch it | 100+ AI Figma plugins released - need quality filtering for premium work |

---

### Broom Design
**Link:** https://github.com/boburxd/broom-design
**Type:** Tool
**What it is:** Broom Design: the design skill for AI coding agents. The most popular design skills in one, with a checker and a design system generator. Removes AI slop from UI in Claude Code, Codex, Cursor, Copilot and Gemini CLI, and respects your design system. Includes six commands for audit, fix, check, design from brief, redesign existing products, and handoff from Figma files.
**What's good about it:** This skill consolidates the most effective anti-slop techniques from leading design skills into one comprehensive package. Unlike single-focus tools, it brings together separation, color/contrast, spacing/type, states/motion, copy/accessibility, and stack compatibility into one unified system. The built-in checker provides immediate feedback on slop violations, while the design system generator allows creating systems from briefs or existing Figma files. Most significantly, it respects existing design systems rather than overriding them - crucial for maintaining brand consistency in established products like Shareef's Unified Platform. The six-command approach provides a complete workflow from initial design through refinement and handoff.
**Pros:**
- Consolidates multiple anti-slop techniques into one unified skill
- Includes automated checker for immediate slop detection and feedback
- Features design system generator for creating systems from briefs or Figma
- Respects existing design systems rather than imposing new ones
**Cons:**
- Consolidated approach may not go as deep as specialized skills in specific areas
- Requires agents to be configured to use the skill consistently
- May overlap with existing skills causing configuration complexity
- Generator quality depends on the brief or source Figma file provided
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's actual design surfaces, this provides the most immediate and comprehensive path to eliminating AI slop from agent-generated work. The Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites all suffer when AI generates work that drifts from the intended design system toward generic defaults. Broom Design directly addresses this by providing both prevention (through comprehensive rules) and correction (through the audit/fix commands) in one package. For the Unified Platform specifically, teams could use the `/broom design` command to generate or refine design system tokens from briefs, then use `/broom audit` and `/broom fix` to ensure AI-generated components maintain the platform's premium dark theme, single accent (#003da5), Inter typography, and SVG icon standards. The `/broom handoff` command is particularly valuable for ensuring that AI-generated Figma files can be confidently handed off to developers without introducing inconsistencies. This creates a complete workflow that keeps AI agents within the design system while providing the tools to correct any drift that occurs.

---

### Brand Identity Skill
**Link:** https://github.com/fatihaydost/brand-identity-skill
**Type:** Tool
**What it is:** A Claude Code skill that designs a brand identity as one system: logo, typography and colour palette built together from one brief, measured, compared as identity cards, and delivered as a brand guidelines kit. Includes 24 example brand identities and tools for packaging, installation, and measurement.
**What's good about it:** This skill solves the fundamental problem of fragmented brand asset generation by creating all identity elements (logo, typography, color) from a single brief in a cohesive system. Unlike tools that generate disjointed assets, it ensures complete consistency across all brand touchpoints. The skill includes measurement and comparison features that allow objective evaluation of generated identities against the original brief, preventing the generic AI look through structured, measurable outputs. Most significantly, it treats brand identity as a systematic process rather than a collection of independent generations, aligning with premium design agency practices.
**Pros:**
- Creates logo, typography, and color palette as a unified system from one brief
- Includes measurement and comparison tools for objective quality assessment
- Provides 24 pre-built brand identity examples for immediate reference and learning
- Comes with packaging tools for easy distribution and installation across teams
**Cons:**
- Currently limited to Claude Code agents only
- Focuses specifically on brand identity rather than broader UI/UX design
- Requires understanding of the skill's specific workflow and conventions
- Measurement system may need customization for specific industry standards (healthcare)
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's need to maintain premium, professional design across the Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites, this skill provides the critical missing piece: a systematic approach to brand identity generation that ensures consistency and quality. Unlike AI tools that generate logos, typography, and colors in isolation (leading to inconsistent brand expressions), this skill builds all elements together from one brief, ensuring they work as a cohesive system. For the Unified Platform specifically, teams could use this skill to generate or refine the Montefiore Urology brand system (ensuring the navy #003da5 accent, Inter typeface, and SVG icon standards are applied consistently) and then export those tokens for use in development workflows. The measurement and comparison features allow objective evaluation of whether AI-generated brand elements actually meet the brief requirements, preventing the drift toward generic AI aesthetics. This creates the foundation needed for other AI design tools to work effectively: when brand identity is established as a measurable system, agents have a clear target to hit rather than generating in a vacuum.

---

### Persian Motion Director
**Link:** https://github.com/atmirrr/persian-motion-director
**Type:** Tool
**What it is:** A Claude skill for pro motion design with correct Persian (Farsi) typography: no slideshows, no broken letters. 8 techniques, HarfBuzz tooling, Remotion examples.
**What's good about it:** This skill addresses a critical gap in AI-assisted design: proper typographic handling for non-Latin scripts, particularly Persian/Farsi. Most AI tools either ignore proper typographic rules or apply Latin-centric assumptions that break with complex scripts. The skill provides 8 specific techniques for motion design, integrates HarfBuzz for proper text shaping, and includes Remotion examples for practical application. What makes this premium is the focus on linguistic and typographic correctness rather than just visual appeal - ensuring that motion graphics maintain readability and cultural appropriateness.
**Pros:**
- Solves Persian/Farsi typography issues in motion design (broken letters, incorrect shaping)
- Provides 8 specific motion design techniques for professional results
- Integrates HarfBuzz tooling for proper complex script handling
- Includes Remotion examples for immediate practical application
**Cons:**
- Specifically focused on Persian/Farsi - limited immediate utility for Shareef's team
- Requires Claude Code agent setup to use the skill
- Motion design focus may not address all UI/UX needs for Shareef's surfaces
- Remotion dependency adds complexity for teams not already using it
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** While this skill solves a genuine problem in AI-assisted design (typographic correctness for complex scripts), its immediate applicability to Shareef's design surfaces is limited. The Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites primarily use Latin script (English) with the Inter typeface and Montefiore's established branding. However, the principles behind this skill - linguistic correctness in AI-generated motion design and proper typographic handling - are valuable for future consideration. If Shareef's team ever needs to create multilingual content or motion graphics for Persian/Farsi speaking audiences, this would be invaluable. For now, it represents the kind of specialized, craft-focused tool that prevents the generic "AI look" by addressing real typographic challenges rather than just generating visuals. Worth watching as AI design tools mature to handle global typographic challenges properly.

---

### Qiaomu Codex ImageGen
**Link:** https://github.com/joeseesun/qiaomu-codex-imagegen
**Type:** Tool
**What it is:** 让任何 Agent 调用 Codex 内置生图（MCP + CLI + Skill），内置小红书、视频封面、Mondo 海报技巧 · Codex image generation for any agent
**What's good about it:** This tool enables any AI agent to access Codex's built-in image generation capabilities through MCP (Model Context Protocol), CLI, or skill interfaces. What makes it premium is that it leverages Codex's actual image generation model (rather than relying on external APIs like Midjourney or Stable Diffusion), providing more consistent and controllable results. The built-in templates for Xiaohongshu (Little Red Book), video covers, and Mondo posters show practical, production-ready applications rather than generic experimentation. Most significantly, it treats image generation as a tool that agents can use purposefully within their workflow, rather than as a magical prompt-based solution that produces unpredictable results.
**Pros:**
- Enables any agent to use Codex's built-in image generation via MCP/CLI/skill
- Includes production-ready templates for social media, video, and poster design
- Leverages Codex's native image model for more consistent results than external APIs
- Provides practical, application-focused templates rather than generic generation
**Cons:**
- Requires access to Codex (may involve cost or access restrictions)
- Focuses on specific use cases (Xiaohongshu, video covers, Mondo posters) 
- May have learning curve for MCP setup and configuration
- Template quality may vary for different design needs
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** This represents a step toward more professional, controllable AI-assisted image generation - moving away from the slot-machine unpredictability of prompt-only approaches toward structured, tool-based generation that agents can use purposefully. For Shareef's design surfaces, the ability to generate consistent, on-brand visuals for marketing/social creative, Sub-I welcome materials, and client-style websites is valuable. However, the current focus on specific platforms (Xiaohongshu) and formats (video covers, Mondo posters) may not directly align with immediate needs. The MCP integration approach is promising as it allows agents to use image generation as a controlled tool within their workflow rather than relying on unpredictable prompt engineering. If the templates could be adapted or extended for healthcare/urology-specific contexts (patient education materials, procedural illustrations, etc.), this would become much more relevant. Worth watching as the ecosystem develops more healthcare-focused applications.

---

### Anthropic Claude Design
**Link:** https://news.google.com/rss/articles/CBMiiwFBVV95cUxNRGdTQlVfUjFBMXNtcXRnQVAtUG9VeFdZQ256dTBuXzVKNDBoWEs3X09lY1d3a3dPazFuTWxIN0N2WGFhdEwwN3gyd1R1YThRcE5Cc3Nicms1djBUcnpaUTZublp5SWZORF9fVzl0VjFreHVTN1N4SjdGLTVtY0pqM2Y5ajM4eHl2SHFj?oc=5
**Type:** Idea
**What it is:** Experimental AI design tool from Anthropic for creating quick visuals, unveiled in April 2026 with recent coverage in September 2026.
**What's good about it:** Represents Anthropic's entry into the AI design tool space, building on their Claude AI foundation. Early indications suggest it focuses on creating production-ready visuals rather than just experimental generations. The tool appears to integrate with Claude's existing capabilities, potentially offering a more cohesive workflow for teams already using Claude Code.
**Pros:**
- Comes from Anthropic, creators of Claude AI used in many design workflows
- Focuses on creating quick visuals for practical applications
- Likely integrates well with existing Claude-based development workflows
- Represents a major AI lab's commitment to practical design tools
**Cons:**
- Limited public information available - needs hands-on evaluation
- May still suffer from generic AI aesthetics without proper constraints
- Unclear how it handles brand consistency and design systems
- Recent coverage suggests ongoing development rather than mature product
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** As Shareef seeks to move beyond AI slop toward premium, art-directed design, tools from established AI labs like Anthropic warrant attention. However, the history of AI design tools shows that many initial releases produce impressive demos but fail to deliver consistent, production-ready results that avoid the generic AI aesthetic. For Shareef's actual design surfaces (Unified Platform UI, marketing/social creative, Sub-I welcome materials, client-style websites), any new tool would need to demonstrate clear advantages over existing enforcement-based approaches like Broom Design and Brand Identity Skill. The tool's ability to create visuals that maintain the Montefiore Urology brand system (navy #003da5, Inter typeface, SVG standards) while avoiding slop would be the key test. Worth watching for updates and hands-on evaluations, but premature to adopt without seeing concrete evidence of premium, consistent output.

---

### Google Pics
**Link:** https://news.google.com/rss/articles/CBMiuAFBVV95cUxPbmM4c1Q1eDVrSGR1RmVfRGN4dnB5UU9tT1FlV1F2d1RiamVTUC13UURoLWg5dVpQQVlCX3Z2ZFNhX25KVzh0Zy1TWUFKOWtiQTJkMm9YV2M4MURjUmlHeTZGMVdMUjFNV1dRbzRmSDlqUFhRd2FMX21lZVhTaU5iXzQteXJBai1NUTRnYmhHeGx6aU1NakNqbjl6OUtwRk9QbjIxRlB5ZlFlTDJOVHk2Tm9KTTdlbWg20gHAAUFVX3lxTE1WQjlKM3l3Nm91SkFuNVFvT0lSc0E1dTRpMV9EZzRhQjZMd1ZheFhxbEl4elBiNmRzd2tFMG1feFFhSzUtOEJDSEM1OWotalRKNHlhOS1jNURWM1duWDZYZHRjbDZqQWx5UDh6d3IwTzZRMHk1eXZBTVdZQkN3M1JrZTdsZ1VHUEhNWVlTcEZ2U1owa1FCZkN6VFdENElTSkpydEhwV1k5VDdiRWlqdFYwNVlyLXVkSHhYbjZOM0szTQ?oc=5
**Type:** Idea
**What it is:** Google's AI design tool that lets users create designs with prompts, launched September 2026.
**What's good about it:** Represents Google's entry into accessible AI design tools, leveraging their AI research capabilities. The prompt-based approach aims to make design creation accessible to non-designers.
**Pros:**
- From Google, leveraging their extensive AI research and infrastructure
- Prompt-based interface lowers barrier to entry for design creation
- Likely integrates with Google's broader ecosystem of products
- Represents a major tech company's investment in democratizing design
**Cons:**
- Prompt-based approach likely produces generic AI aesthetics (slop)
- Limited control over typography, layout, and brand consistency
- History shows prompt-only tools struggle with professional-grade output
- Unclear how it handles healthcare-specific design requirements
**Should we...**
- ❌ **Skip it** — slop-adjacent, hype, or redundant
**Why:** This tool exemplifies the exact "AI slop" aesthetic that Shareef is trying to avoid. Prompt-based AI design tools without strong constraints inevitably produce the telltale signs of AI-generated work: generic gradients, inconsistent spacing, questionable typography choices, and lack of intentional design hierarchy. For Shareef's design surfaces - which require premium, professional quality matching top agency standards - this approach would undermine rather than elevate the work. The Unified Platform UI needs precise adherence to the dark theme, single accent (#003da5), Inter typography, and SVG icon standards. Marketing/social creative requires intentional, brand-aligned visuals that avoid the generic AI look. Sub-I welcome materials and client-style websites need to convey professionalism and trustworthiness, which prompt-generated slop cannot achieve. Real design requires human judgment at key decision points, structured workflows, and enforceable design systems - not magic prompts that produce unpredictable results. This tool represents the hype cycle rather than substantive progress toward premium AI-assisted design.

---

### Figma AI Plugins
**Link:** https://x.com/felixleezd/status/1646190337164214273?t=NFk2k09RYr5h9CKQMEkHbQ&s=03
**Type:** Trend
**What it reports:** Over 100+ AI Figma plugins were released in March 2026, with ongoing discussion about their value and quality.
**What's good about it:** The surge in AI Figma plugins shows active experimentation in integrating AI capabilities directly into the primary design tool used by many professionals. Some plugins focus on specific, valuable functions like design system maintenance, accessibility checking, or asset generation rather than trying to replace designers entirely.
**Pros:**
- Shows active innovation in the AI-design tool space
- Some plugins provide valuable, focused functionality (not just generation)
- Integrates AI capabilities where designers already work (Figma)
- Enables experimentation with different AI-assisted workflows
**Cons:**
- Majority likely produce generic AI aesthetics without proper constraints
- Quality varies widely - requires careful evaluation of each plugin
- Risk of fragmenting design workflows across too many specialized tools
- Many focus on generation rather than enforcement or improvement
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The Figma ecosystem represents a critical battleground in the fight against AI slop. For Shareef's design surfaces, Figma is likely the primary design tool used for Unified Platform UI work, marketing/social creative, and client-style websites. The challenge is distinguishing between plugins that merely generate slop (AI-generated designs that look artificially perfect but lack intentionality) versus those that genuinely enhance the design process. Premium signals to watch for: plugins that enforce design systems, check accessibility, maintain brand consistency, or provide controlled generation within existing frameworks. Slop signals to avoid: plugins that promise "one-click" complete designs, generate unpredictable results, or ignore established design systems. Worth watching as the ecosystem matures, with focus on plugins that act as design assistants rather than replacements - tools that help designers work better rather than trying to automate away design judgment entirely.

---

## Slop Radar
- **Prompt-only AI design tools that promise complete designs from text descriptions** — These produce the generic purple/blue gradients, rounded corners, and telltale AI aesthetics we're trying to avoid. Real design requires constraints, systems thinking, and human judgment at key decision points.
- **Tools that generate visuals without outputting design tokens or machine-readable specifications** — Without tokens, there's no way to enforce consistency across surfaces or prevent drift that leads to slop over time.
- **AI tools that ignore or override existing design systems instead of respecting and enhancing them** — This creates inconsistency and undermines the intentional, crafted quality of professional design work.
- **Plugins and tools that focus on generation speed over design quality and intentionality** — Premium design comes from research→strategy→execution, not from maximizing outputs per minute.

## Overall Assessment
The current state of AI-assisted design shows a maturing landscape where the most valuable contributions aren't flashy generation tools, but rather workflow enforcers and system maintainers that bring discipline to the process. We're seeing a clear shift toward tools that prevent AI slop at the source (like Broom Design and Brand Identity Skill) rather than trying to correct it after generation. The single highest-leverage move for Shareef this week is to adopt Broom Design as the foundation - creating the enforcement mechanism that keeps AI agents within professional design boundaries while providing tools to correct any drift. Pair this with the Brand Identity Skill for systematic brand creation, and Shareef's surfaces will move from AI-generated slop to AI-assisted excellence. This approach directly addresses Shareef's actual design surfaces: ensuring the Unified Platform UI maintains its premium dark theme and single accent, marketing/social creative avoids generic AI aesthetics, Sub-I welcome materials feel intentionally crafted rather than templated, and client-style websites reflect the same professional-grade quality as top agency work. The watch-list items (Persian Motion Director, Qiaomu Codex ImageGen) represent promising developments in specific areas worth monitoring for future adoption as they mature and demonstrate consistent, premium output.
-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-10-08.md — verified written