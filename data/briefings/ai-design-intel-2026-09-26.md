# AI Design Intel — September 26, 2026
Sources scanned: X (available), Reddit (web_search for graphic_design, web_design, UI_Design, midjourney, StableDiffusion, FigmaDesign), HN (available via last30days-pro aggregator), GitHub (available), Google News (available). Candidates considered: 22. Passed the bar: 5.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Resolve | Tool | ✅ Adopt it | Makes your Figma library the agent's rulebook and measures how much the agent invents instead of reusing |
| Slicer.dev | Tool | ✅ Adoptit | AI agent performs research-level UX audits on live sites, pinpointing fixes to actual elements |
| DesignHub | Tool / Workflow | 👀 Watch it | Open-source local-first design & brand toolkit that generates actual design tokens from a single source |
| PixelCrew | Tool / Workflow | 👀 Watch it | Crew of specialized AI agents coordinates on briefs to ship production HTML/Tailwind output |
| Paper + AI Agents (TK Kong) | Technique | ✅ Adopt it | Practical AI-native design workflow using MCP for roundtrip between design canvas and code |

---

### Resolve
**Link:** https://github.com/TANISHQBAFNA/resolve
**Type:** Tool
**What it is:** A small Node tool (pushed Sept 25, MIT) that turns your Figma library into a rulebook the agent must obey. You set the design rules, components and usage scope; Resolve holds a map of your Figma library; the AI calls `recommend` to get ranked library masters for a brief, drafts from those component IDs, and then Resolve's `verify_frame` reports what the agent *invented* instead of reusing. It connects through the standard Figma MCP (no personal access token for normal use), works inside Cursor, Claude Code, Codex, and reads `AGENTS.md`. Its own framing is the correct one: "So Resolve is not 'AI that designs.' It is your rules, made easy for AI to follow — without pasting the whole Figma file into chat."

**What's good about it:** It attacks the single most expensive failure mode in agent-drafted UI: the agent that has your design system in a README, glimpses it once, and then invents a new card radius, a new button variant, and a new spacing rhythm anyway — which is how ten screens become ten unrelated drawings. Resolve's answer is the right shape: rather than dumping the file into context and hoping, it holds a queryable map, hands the agent specific component node IDs, and then *measures reuse* so the invent rate is visible instead of invisible. The measured-invent-rate idea is the part worth stealing regardless of the tool: an agent's design-system compliance should be a number you can watch trend, not a vibe you assess after the fact. Also notable is the boundary discipline — it explicitly refuses to be the taste judge (`verify_frame` checks library reuse only), leaving aesthetic judgment to the human, which is the correct division of labour for an agent tool. Zero-dependency install, MIT, and Node 22.12+ only.

**Pros:**
- Solves the exact problem of agent-invented UI components by handing over real component node IDs from your library rather than prose guidance the agent may ignore
- `verify_frame` makes design-system drift *measurable* (invent rate) — a compliance metric, not a promise
- Works through standard Figma MCP across Cursor, Claude Code, and Codex, and reads `AGENTS.md`, so it fits our harness without a custom bridge
- Explicitly scoped to rules, not taste — it does not pretend to judge design quality, which keeps the human in the right seat

**Cons:**
- One star, days old, single author — the concept is adoptable now, the repo is unproven
- Requires an active Figma library and MCP connection; with no Figma file it does nothing, and Shareef's current design authority lives partly in code (React/Tailwind), not exclusively in Figma
- `verify_frame` measures *reuse of library components*, which is the wrong metric for net-new patterns where the correct answer is a new component — it can flag legitimate first-time designs as "invents"
- Adds another Node project to the toolchain for a job that a stricter `AGENTS.md` plus a token-lint script partly covers already

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** Adopt the *pattern* immediately and the repo as a candidate for the next Figma-based build. The Unified Platform is a production system where unapproved drift is genuinely destructive — every agent-authored component that invents a radius, a hex value, or a spacing step is a small violation of the system that compounds across surfaces. Resolve's contribution is making that violation a reported number. This is the enforcement mechanism under the design-system discipline we have been assembling: Boxy (Sept 22) gave us axioms plus a CSS linter, DESIGN.md Generator gave us a locked, validated token source, and Resolve extends the same idea up the stack to the *component* layer — the agent should be reusing Design Button Variant B, not synthesising what it thinks Button Variant B probably looks like. Two things transfer this week even if we never install it: (1) the map-plus-specific-ID approach beats context-dumping, and we should give agents explicit component identifiers rather than descriptions; (2) track an invent rate as a review metric on any agent-drafted UI, so compliance is visible. For a platform where the design system is the difference between a product and a pile of screens, that measurement is worth having.

---

### Slicer.dev
**Link:** https://slicer.dev/
**Type:** Tool
**What it is:** AI agent performs research-level UX audits on live websites, capturing real pages (not screenshots) and scoring them across copy, UI, usability, flow, and accessibility. Each finding is tied to the exact element on the exact page, ready to hand to a designer or agent. It walks your site like a visitor and hands back the pages, the score, and the fixes — all pinned to what actually shipped. Trusted by designers at companies like Vinted, Hostinger, Airtable, and Clay.

**What's good about it:** Unlike superficial checklist tools, Slicer provides genuine research-level scrutiny that matches what a senior UX designer would deliver. The tool captures live pages (not static screenshots), so the state you saw is the state you keep even after site changes. Findings are pinned to specific elements with clear remediation steps, making it actionable for both designers and developers. The transparency of showing real client logos builds credibility, and the browser extension for auditing signed-in pages addresses a critical gap in most audit tools. Most importantly, it shifts the paradigm from subjective opinions to objective, evidence-based findings that can drive concrete improvements.

**Pros:**
- Research-level scrutiny that goes beyond basic accessibility checks to evaluate copy, UI, usability, flow, and accessibility holistically
- Live page capture (not screenshots) ensures findings reflect actual user experience, not outdated versions
- Each issue points to the exact element on the exact page, tagged by journey step — ready to hand to a designer or agent
- Transparent pricing with clear tiers and 14-day money-back guarantee reduces adoption risk
- Trusted by real designers at recognizable companies (Vinted, Hostinger, Airtable, Clay) provides social proof

**Cons:**
- Currently focuses on web applications; may not cover native mobile or desktop applications relevant to some Shareef surfaces
- Browser extension required for signed-in page audits adds slight friction to the workflow
- Pricing model, while transparent, represents an ongoing cost that needs justification against internal alternatives
- As a specialized tool, it excels at audits but doesn't provide design generation or implementation capabilities

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's need to maintain premium, professional design across the Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites, Slicer.dev provides the missing piece: objective, research-level evaluation of whether AI-assisted designs actually work for real users. While we've been building enforcement mechanisms (Resolve for component reuse, DesignHub for token consistency), we lacked a way to measure whether the resulting designs actually achieve their intended user experience goals. Slicer.dev fills this gap by providing the kind of detailed, element-level feedback that separates tactical compliance from strategic design excellence. For the Unified Platform specifically, auditing key screens like the on-call schedule, reimbursement views, and evaluation forms would reveal whether AI-generated interfaces maintain the cognitive clarity and accessibility required for clinical use. The tool's ability to audit signed-in pages via extension makes it particularly valuable for evaluating authenticated experiences like the provider dashboard.

---

### DesignHub
**Link:** https://github.com/yakew7/DesignHub
**Type:** Tool / Workflow
**What it is:** Open-source, local-first design & brand toolkit. Build a brand once, then get logo variants, mockups, social assets, a brand book PDF and design tokens. Plus fonts, colors, icons, SVG & accessibility tools. No login, no backend. Designed for designers who want to own their stack.

**What's good about it:** DesignHub attacks the core problem of brand fragmentation by letting you build a brand once and derive all assets from that single source. It outputs actual design tokens (CSS variables, JSON, etc.) rather than just static assets, making the system machine-readable and enforceable. The local-first approach means no login or backend — everything runs on your machine, addressing privacy and dependency concerns. It includes SVG and accessibility tools out of the box, showing awareness that real brand systems need more than just pretty pictures. The toolchain approach (typography → colors → icons → export → background studio → effects lab → accessibility lab → SVG playground → brand studio → logo studio → mockups → social media → brand guidelines → brand projects → brand DNA) provides a logical progression for building a complete brand system.

**Pros:**
- Local-first, no login or backend — everything runs on your machine, enhancing privacy and reducing points of failure
- Generates actual design tokens (CSS variables, JSON, etc.) from a single brand source, making the system machine-readable and enforceable
- Includes comprehensive asset generation: logo variants, mockups, social assets, brand book PDF, plus fonts, colors, icons, SVG & accessibility tools
- Open-source MIT license with active development (daily commits) and growing community (11 stars in 2 days)
- Logical progression from fundamentals (typography, colors) to advanced features (brand DNA, social assets)

**Cons:**
- Very early stage — 11 stars, created Sept 23, single author; treat as promising prototype, not infrastructure to depend on
- Next.js/TypeScript stack may not align with Shareef's current React/Tailwind Unified Platform
- Brand generation approach may produce coherent but generic output without strong human art direction
- Accessibility tools included but depth unknown — may be basic contrast checks rather than comprehensive auditing

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** DesignHub's local-first, token-generating approach aligns well with the need for machine-enforceable design systems on Shareef's surfaces. For the Unified Platform, the ability to generate consistent design tokens from a single source could prevent the drift that leads to AI slop. However, it's too early to depend on for production systems. What's valuable to adopt this week is the mindset: build the brand once as a single source of truth, then derive all assets from it. This could be implemented today by creating a canonical brand specification for Montefiore Urology (navy #003da5 as single accent, Inter typeface, SVG icon stroke weight) and using it to generate tokens, component variants, and asset guidelines. Watch the repo; if it maintains momentum and adds verifiable outputs (like automated token validation), re-evaluate for adoption.

---

### PixelCrew
**Link:** https://pixelcrew.ai/
**Type:** Tool / Workflow
**What it is:** A crew of specialized AI agents coordinates on your design brief and ships production-quality design. Each agent has a named specialization (Researcher/Strategy, Director/Art Direction, Designer/UX Architecture) and a defined scope, working sequentially with context the way a real team does. The process follows: Brief → Research → Strategy → Creative Direction → Wireframes → Copy and Design System → QA Audit → Production Output (HTML/Tailwind). Average delivery: 25–45 minutes. No subscription fees — users bring their own API keys and pay model costs directly to providers.

**What's good about it:** PixelCrew implements a genuine agency workflow with AI agents, moving beyond the "one prompt, one output" paradigm that produces generic results. By structuring the process as research → strategy → creative direction → implementation, it forces the kind of disciplined thinking that separates bespoke design from template work. The specialization of agents (researcher, director, designer) mirrors real agency roles and prevents the confusion that happens when one agent tries to do everything. The focus on production-ready HTML/Tailwind output (not just mockups or concepts) means the work can actually ship to engineering. The bring-your-own-key model aligns with ethical AI use by avoiding markup on model costs. Most importantly, it treats AI as a coordinated team rather than a magic genie, which is the only way to get consistently high-quality results.

**Pros:**
- Implements real agency workflow with specialized agents (research, strategy, art direction, UX)
- Focuses on production-ready output (HTML/Tailwind) that can ship directly to engineering
- Clear, sequential process with defined handoffs prevents agent confusion and overlap
- Bring-your-own-key model avoids markup and aligns with transparent AI usage
- Demonstrated case studies show actual production work (coffee shop, automotive landing page, task manager, roastery)

**Cons:**
- Currently in alpha; long-term reliability and support model unproven
- Requires users to manage their own API keys and monitor model costs
- Output limited to HTML/Tailwind; may not cover all Shareef surfaces (native apps, complex enterprise systems)
- As a workflow tool, it depends on the quality of underlying models rather than introducing novel design techniques
- Single creator project (per GitHub links) presents bus-factor risk despite credible background

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** PixelCrew represents the most promising attempt to structure AI-assisted design as a genuine collaborative process rather than a prompt-engineering exercise. For Shareef's need to move away from generic "AI slop" aesthetics toward premium, professional design, the sequential agent workflow addresses the root cause of slop: undisciplined, one-shot generation. The researcher→director→designer progression ensures that creative decisions are informed by strategy rather than made in isolation. The focus on production HTML/Tailwind output means work can actually engineering-handoff rather than remaining as beautiful-but-useless mockups. For the Unified Platform specifically, having an agent crew that understands UI/UX architecture (Mira's role) could help generate screens that maintain the platform's cognitive clarity and accessibility requirements. The model-cost-transparency is particularly valuable for healthcare contexts where budget predictability matters. However, as an alpha product with unproven long-term viability, it warrants watching rather than adoption — but the workflow principles it embodies are immediately applicable to how we structure our own AI-assisted design processes.

---

### Paper + AI Agents (TK Kong)
**Link:** https://x.com/tkkong/status/2034368184036561160
**Type:** Technique
**What it is:** A practical guide to designing products that are built around AI from the start — not retrofitted. TK Kong (ex-Ramp) shares his workflow using Paper (the design tool built on native HTML/CSS rather than a WebGL canvas) and AI agents to design and build products. The core technique involves roundtrip workflows: using AI agents to generate/modify designs in Paper via MCP, then using Paper Snapshot to bring real app versions from QA or deploy branches into the canvas for comparison, creating a closed loop between AI-generated design and actual code implementation.

**What's good about it:** This isn't another "here are 10 AI design tools" listicle — it's a hard-won workflow from someone who's actually shipping products using this approach. The roundtrip nature (AI → Paper → code → back to Paper) creates the kind of feedback loop that prevents the two fatal flaws of AI-assisted design: generating beautiful mockups that can't be built, and generating code that violates design systems. By using Paper's native HTML/CSS foundation (rather than WebGL), the designs live in the same medium as the final product, eliminating the translation loss that occurs when moving between design tools and code. The MCP integration allows AI agents to directly manipulate the design canvas, making the collaboration feel native rather than bolted-on. Most valuable is the emphasis on bringing real QA/deploy branches into the canvas for comparison — this grounds the AI work in reality rather than letting it float in a purely generative space.

**Pros:**
- Roundtrip workflow prevents the "beautiful mockup, unbuildable reality" failure mode
- Paper's native HTML/CSS foundation eliminates translation loss between design and code
- MCP integration makes AI-agent collaboration feel native to the design tool
- Grounding AI work in real QA/deploy branches prevents generative drift
- Comes from proven product-builder (TK Kong, ex-Ramp) rather than theoretical advocate

**Cons:**
- Requires Paper specifically; workflow may not transfer directly to Figma/Sketch/etc.
- MCP setup and configuration adds initial complexity
- Workflow assumes access to QA/deploy branches for comparison (may not exist for all projects)
- Technique-focused rather than tool-focused; requires implementation rather than installation
- Limited to design tools that support similar MCP roundtrip capabilities

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This is the highest-leverage technique for Shareef's actual design surfaces because it directly addresses the gap between AI-generated designs and implementable code. The Unified Platform UI (React/Tailwind), marketing/social creative, Sub-I welcome materials, and client-style websites all suffer when AI generates designs that look good but can't be built, or when developers implement designs that drift from the intended visual language. The Paper + AI Agents roundtrip workflow solves this by making the design tool and the development environment collaborators rather than separate silos. For the Unified Platform specifically, this could mean using AI agents to generate/modify components in a Paper canvas that mirrors the actual React/Tailwind implementation, then using Paper Snapshots of the deployed Unified Platform to validate that AI-generated changes maintain visual and functional consistency. The technique's emphasis on grounding AI work in reality (via real QA/deploy branch snapshots) is exactly what's needed to prevent the Unified Platform from accumulating AI-driven visual debt. Unlike tool-dependent finds, this technique can be implemented immediately with existing resources by establishing a roundtrip workflow between our current design tools and development environment.

## Slop Radar
- **AI design tools that generate complete designs from prompts without human art direction in the loop** — These produce the generic purple/blue gradients, rounded corners, and telltale AI aesthetics we're trying to avoid. Real design requires human judgment at key decision points.
- **Tools that output static assets without design tokens or machine-readable specifications** — Without tokens, there's no way to enforce consistency across surfaces or prevent drift that leads to slop over time.
- **Typography tools that rely on web fonts or abstract font reasoning instead of access to actual installed fonts** — This leads to weight mismatches, hierarchy collapses, and fallback substitutions that read as unprofessional.
- **Workflow tools that promise "one-click" design generation instead of structured agency processes** — Real quality comes from research→strategy→execution, not magic prompts.

## Overall Assessment
The current state of AI-assisted design reveals a maturing landscape where the most valuable contributions aren't flashy generation tools, but rather workflow enablers that bring discipline to the process. We're seeing three converging trends that together offer a path beyond AI slop: (1) enforcement mechanisms that make AI agents obey design systems (Resolve measuring component reuse), (2) evaluation tools that provide research-level assessment of whether designs actually work for users (Slicer.dev's element-level UX audits), and (3) structured workflows that treat AI as a coordinated team rather than a prompt-engineering exercise (PixelCrew's specialist agents, TK Kong's Paper roundtrip). The single highest-leverage move for Shareef this week is to implement the enforcement + evaluation combo: adopt Resolve to make AI agents measurable citizens of the Unified Platform design system, and adopt Slicer.dev to audit whether the resulting designs actually achieve their clinical and usability goals. This creates the closed loop missing from current AI-assisted design: agents that are both constrained by the system *and* accountable to real-user outcomes. Pair this with the workflow discipline of structuring AI assistance as research→strategy→execution (rather than one-shot prompts), and Shareef's surfaces will move from AI-generated slop to AI-assisted excellence — where the technology serves the design intent rather than undermining it.