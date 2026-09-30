# AI Design Intel — September 29, 2026
Sources scanned: X (available), Reddit (web_search for graphic_design, web_design, UI_Design, midjourney, StableDiffusion, FigmaDesign), HN (available via last30days-pro aggregator), GitHub (available), Google News (available). Candidates considered: 10. Passed the bar: 4.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Open Design | Tool | ✅ Adopt it | Local-first, open-source Claude Design alternative with agent skills and design systems |
| DESIGN.md Protocol | Tool / Workflow | ✅ Adopt it | Persistent design system contract that prevents AI drift and enables agent consistency |
| Slicer.dev | Tool | ✅ Adopt it | Research-level UX audits that pinpoint issues to exact elements on live pages |
| Paper + AI Agents (TK Kong) | Technique | 👀 Watch it | Practical AI-native design workflow using MCP for roundtrip between design canvas and code |

---

### Open Design
**Link:** https://github.com/Decentralised-AI/open-design
**Type:** Tool
**What it is:** Open-source alternative to Anthropic's Claude Design that transforms coding agents into design engines through 31 composable Skills and 72 brand-grade Design Systems. Runs locally with full BYOK (Bring Your Own Key) support across 16 coding-agent CLIs including Claude Code, Cursor, Gemini, Hermes, and more. Generates web, desktop, mobile prototypes, slides, images, videos, and HyperFrames with sandboxed preview and multiple export formats.
**What's good about it:** Open Design solves the core problem of vendor lock-in while maintaining the artifact-first mental model that makes Claude Design effective. Unlike closed-source tools, it wires existing coding agents into a skill-driven design workflow that runs locally, giving teams full control over their design process. The 31 composable Skills (like MCP connector, file attachment handler, web search, and Figma integration) and 72 brand-grade Design Systems provide immediate, production-ready capabilities without requiring teams to build from scratch. Most importantly, it treats AI agents as collaborative partners rather than black-box generators, aligning with Shareef's need for premium, art-directed design output.
**Pros:**
- Local-first, web-deployable, BYOK at every layer — eliminates dependency on closed-source, cloud-only tools
- 31 composable Skills and 72 brand-grade Design Systems provide immediate, production-ready capabilities
- Supports 16 coding-agent CLIs including Claude Code, Cursor, Gemini, Hermes, and more for flexibility
- Generates multiple artifact types (web/desktop/mobile prototypes, slides, images, videos, HyperFrames) with sandboxed preview
**Cons:**
- Still early stage — requires evaluation of skill quality and design system relevance to healthcare UX
- Local-first approach may need adaptation for team collaboration compared to cloud-native alternatives
- Learning curve for skill composition and design system customization
- Verification needed on whether 72 design systems include healthcare/medical domain examples
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's need to maintain premium, professional design across the Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites, Open Design provides the critical missing piece: a local-first, agent-controlled design workflow that prevents the generic AI slop aesthetic. Unlike tools that generate designs in isolation, Open Design treats coding agents as collaborative partners that operate within structured skills and design systems. This directly addresses Shareef's concern about AI-assisted design looking like it came from a template rather than a top agency. For the Unified Platform specifically, teams could use Open Design's Figma MCP skill and healthcare-relevant design systems to generate components that maintain the platform's premium dark theme, single accent color (#003da5), Inter typography, and SVG icon consistency. The BYOK approach ensures no vendor lock-in while the local-first model addresses privacy concerns for healthcare-related design work. Most valuable is the shift from "AI that designs" to "your rules, made easy for AI to follow" — exactly the enforcement mechanism needed to prevent agent-invented UI components from breaking design system consistency.
---

### DESIGN.md Protocol
**Link:** https://designmd.cc/benchmarks/github
**Type:** Tool / Workflow
**What it is:** A persistent, repo-resident design system specification in markdown format that gives AI coding agents a structured understanding of visual identity. Created by Google Stitch and now an open standard, DESIGN.md uses YAML front-matter for machine-readable tokens (colors, typography, spacing) and Markdown prose for human-readable rationale. The format includes 9 canonical sections: Overview, Colors, Typography, Layout, Elevation & Depth, Shapes, Components, Do's and Don'ts, and Agent Prompt Guide, with community extensions adding Visual Theme & Atmosphere and other sections.
**What's good about it:** DESIGN.md solves the fundamental problem of AI-generated design inconsistency by providing agents with a persistent, version-controlled contract they can read once at session start rather than requiring re-explanation with every prompt. Unlike JSON schemas or proprietary formats, markdown is natively understood by LLMs, human-editable, and Git-versionable. The two-layer architecture (normative tokens + explanatory prose) ensures agents get both the "what" and the "why" behind design decisions. Most significantly, it prevents the context failure where identical prompts produce different design systems — a critical issue for maintaining brand consistency across AI-assisted workflows. The Agent Prompt Guide section innovation treats AI as a teammate with explicit meta-instructions for UI generation.
**Pros:**
- Persistent, repo-resident contract eliminates context failure and design drift between sessions
- Markdown format is LLM-native, human-readable, editable, and Git-versionable
- Two-layer architecture provides both machine-readable tokens and human-readable rationale
- Prevents identical prompts from generating different design systems (context failure)
- Agent Prompt Guide treats AI as teammate with explicit UI generation meta-instructions
**Cons:**
- Requires discipline to maintain and update as design systems evolve
- Adoption depends on team consistency in using the file as the single source of truth
- May need extension for complex motion design or interaction specifications
- Verification needed on tool support across all agents Shareef uses (Hermes, Cursor, etc.)
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** DESIGN.md is the single highest-leverage adoption for Shareef's design surfaces this week because it directly prevents the AI slop aesthetic that plagues agent-generated interfaces. For the Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites, consistent application of DESIGN.md would ensure that AI agents generate work that adheres to Montefiore Urology's brand system (navy #003da5 accent, Inter typeface, SVG icon standards) rather than defaulting to generic gradients and rounded corners. Unlike temporary prompts or contextual explanations, DESIGN.md provides a permanent, version-controlled reference that agents can rely on — eliminating the guesswork that leads to inconsistent spacing, typography, and color usage. This creates the foundation needed for other AI design tools to work effectively: when agents understand the design system deeply, their outputs require less art-direction correction and maintain the premium, intentional quality Shareef seeks. The format's simplicity (plain markdown) means it can be implemented immediately across all current workflows with zero tooling cost.
---

### Slicer.dev
**Link:** https://slicer.dev/
**Type:** Tool
**What it is:** AI agent that performs research-level UX audits on live websites, capturing real pages (not screenshots) and scoring them across copy, UI, usability, flow, and accessibility. Each finding is tied to the exact element on the exact page, ready to hand to a designer or agent. Trusted by designers at companies like Vinted, Hostinger, Airtable, and Clay. The tool walks sites like a visitor and hands back pages, scores, and fixes — all pinned to what actually shipped.
**What's good about it:** Unlike superficial checklist tools, Slicer provides genuine research-level scrutiny that matches what a senior UX designer would deliver. The tool captures live pages (not static screenshots), so the state you saw is the state you keep even after site changes. Findings are pinned to specific elements with clear remediation steps, making it actionable for both designers and developers. Most importantly, it shifts the paradigm from subjective opinions to objective, evidence-based findings that can drive concrete improvements. For healthcare contexts like Shareef's surfaces, this provides the critical missing piece: objective evaluation of whether AI-assisted designs actually work for real users in clinical settings.
**Pros:**
- Research-level scrutiny evaluating copy, UI, usability, flow, and accessibility holistically
- Live page capture (not screenshots) ensures findings reflect actual user experience
- Each issue points to the exact element on the exact page, tagged by journey step
- Transparent pricing with clear tiers and 14-day money-back guarantee reduces adoption risk
- Browser extension for auditing signed-in pages addresses critical gap in most audit tools
**Cons:**
- Currently focuses on web applications; may not cover native mobile or desktop applications
- Browser extension required for signed-in page audits adds slight workflow friction
- Pricing model represents ongoing cost needing justification against internal alternatives
- As specialized audit tool, it doesn't provide design generation or implementation capabilities
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's need to maintain premium, professional design across the Unified Platform UI, marketing/social creative, Sub-I welcome materials, and client-style websites, Slicer.dev provides the essential evaluation layer missing from current AI-assisted design workflows. While enforcement mechanisms (like Open Design's skills and DESIGN.md's tokens) keep agents within the design system, Slicer.dev answers the crucial question: do the resulting designs actually achieve their intended user experience goals? For the Unified Platform specifically, auditing key screens like the on-call schedule, reimbursement views, and evaluation forms would reveal whether AI-generated interfaces maintain the cognitive clarity and accessibility required for clinical use — moving beyond tactical compliance to strategic design excellence. The tool's ability to audit signed-in pages via extension makes it particularly valuable for evaluating authenticated experiences like the provider dashboard. This creates the closed loop missing from current AI-assisted design: agents that are both constrained by the system (via Open Design + DESIGN.md) AND accountable to real-user outcomes (via Slicer.dev). Without this evaluation step, teams risk optimizing for system consistency while producing designs that fail real users — the opposite of premium, art-directed work.
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
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** This is the highest-leverage technique for Shareef's actual design surfaces because it directly addresses the gap between AI-generated designs and implementable code — but requires Paper adoption which may not align with current tooling. The Unified Platform UI (React/Tailwind), marketing/social creative, Sub-I welcome materials, and client-style websites all suffer when AI generates designs that look good but can't be built, or when developers implement designs that drift from the intended visual language. The Paper + AI Agents roundtrip workflow solves this by making the design tool and development environment collaborators rather than separate silos. For the Unified Platform specifically, this could mean using AI agents to generate/modify components in a Paper canvas that mirrors the actual React/Tailwind implementation, then using Paper Snapshots of the deployed Unified Platform to validate that AI-generated changes maintain visual and functional consistency. However, since Shareef's team likely uses Figma rather than Paper, this technique warrants watching rather than immediate adoption. The core principle — grounding AI work in reality through roundtrip validation — is immediately applicable by establishing similar workflows between existing design tools (Figma) and development environment using available MCP integrations. Revisit if Shareef's team adopts Paper or if equivalent Figma-based roundtrip workflows emerge.

---

## Slop Radar
- **AI design tools that generate complete designs from prompts without human art direction in the loop** — These produce the generic purple/blue gradients, rounded corners, and telltale AI aesthetics we're trying to avoid. Real design requires human judgment at key decision points.
- **Tools that output static assets without design tokens or machine-readable specifications** — Without tokens, there's no way to enforce consistency across surfaces or prevent drift that leads to slop over time.
- **Workflow tools that promise "one-click" design generation instead of structured agency processes** — Real quality comes from research→strategy→execution, not magic prompts.
- **Typography tools that rely on web fonts or abstract font reasoning instead of access to actual installed fonts** — This leads to weight mismatches, hierarchy collapses, and fallback substitutions that read as unprofessional.

## Overall Assessment
The current state of AI-assisted design reveals a maturing landscape where the most valuable contributions aren't flashy generation tools, but rather workflow enablers that bring discipline to the process. We're seeing three converging trends that together offer a path beyond AI slop: (1) local-first agent orchestration tools like Open Design that put coding agents under structured control, (2) persistent design system contracts like DESIGN.md that prevent context failure and drift, and (3) research-level evaluation tools like Slicer.dev that measure whether AI-assisted designs actually work for real users. The single highest-leverage move for Shareef this week is to adopt Open Design and DESIGN.md as the foundation — creating the enforcement mechanism that keeps AI agents within the design system while eliminating vendor lock-in. Pair this with Slicer.dev for evaluation, and Shareef's surfaces will move from AI-generated slop to AI-assisted excellence — where the technology serves the design intent rather than undermining it. This approach directly addresses Shareef's actual design surfaces: ensuring the Unified Platform UI maintains its premium dark theme and single accent, marketing/social creative avoids generic AI aesthetics, Sub-I welcome materials feel intentionally crafted rather than templated, and client-style websites reflect the same professional-grade quality as top agency work.
-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-29.md — verified written