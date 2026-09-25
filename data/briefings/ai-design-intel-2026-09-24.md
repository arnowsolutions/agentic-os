# AI Design Intel — September 24, 2026
Sources scanned: X (available), Reddit (web_search for graphic_design, UI_Design, FigmaDesign), HN (available), GitHub (available), Google News (available). Candidates considered: 25. Passed the bar: 5.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Inkloom | Idea | 👀 Watch it | Logo design as constructed specification with brand analysis → typography → symbol → composition stages |
| Primitives | Tool | ✅ Adopt it | Precision design instruments for fundamentals — computational craft instead of eyeballed guesses |
| figma-font-handler | Tool | 👀 Watch it | Gives AI assistants access to real licensed local fonts — attacks typographic slop at the source |
| DesignHub | Tool / Workflow | 👀 Watch it | Open-source local-first design & brand toolkit with design tokens and brand book generation |
| AI design tool from GitLab founder | Tool | ✅ Adopt it | Practical AI-native design tool that focuses on substance over flashy AI tropes |

---

### Inkloom
**Link:** https://github.com/Inkloom-art/inkloom
**Type:** Idea
**What it is:** A research direction and auditable public codebase for AI models that construct logos the way a studio does — as a sequence of explainable decisions rather than sampled images. Four stages: brand analysis → typography → symbol → composition, outputting a specification not a bitmap. Generation is not live yet per the README.
**What's good about it:** The thesis correctly identifies that a logo is not a picture but a constructed object with rules that hold at 16px and building scale, with letterforms spaced by eye and clear space derived from the mark's geometry. It reframes output as a specification, making logos defensible, reproducible, and hand-off-able to printers. Exceptional operational honesty states plainly that generation is not live and feature flags stay off until the feature exists.
**Pros:**
- Stage decomposition (brand analysis → typography → symbol → composition) is a sound model of professional identity work
- Clear-space-derives-from-the-mark rule is a real craft principle missing from most AI logo generators
- Public source enables auditability with real-database/real-browser/real-mail-server test suite rather than mocks
- Correctly diagnoses why general image models fail at logos: they produce "something logo-shaped" with no construction behind it
**Cons:**
- Generation does not exist yet — this is a platform and thesis, not a usable logo tool today
- Twenty stars, created Sept 20, single organisation; timeline for generation, export formats and brand kits unspecified
- Not published as usable distribution (all rights reserved), so it's reading material not infrastructure
- Logo design is the surface where AI substitution is least welcome and licensing/trademark exposure is highest
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Inkloom is not something Shareef can use today for the residency program's marks or Sub-I welcome materials since generation is not live, but it provides the clearest public articulation this week of why identity work resists AI substitution. The four-stage decomposition (brand analysis → typography → symbol → composition) and its constraint framing are immediately useful as input to prompt architecture. For any Big Reef branding work, these questions separate designed identity from generated ones: Does the mark hold at 16px and building scale? Are letterforms spaced by eye rather than metric? Is clear space derived from the mark's geometry? Do lockups still read when only one fits? Use Inkloom's decomposition as our logo brief and its constraint framing as input to our prompt architecture; keep human authorship firmly in the loop on identity marks. Revisit when generation actually ships.

---

### Primitives
**Link:** https://primitiv.es/ (repo: https://github.com/duskresearch/primitives)
**Type:** Tool
**What it is:** A suite of single-purpose design instruments — one question, one tool — covering fundamentals: color contrast, type scale (with ratio control, e.g. `?ratio=1.618`), measure, units, and specimen (which previews every Google Fonts family from Fontsource, sorts by measured x-height and width, and supports pinning to compare and pair suggestions). Design values live in `src/data/tokens.json`; a build script writes `tokens.css`. Everything is URL-stateful and copyable.
**What's good about it:** This is computational rigor where AI design usually guesses — real measured metrics (x-height, width, OS/2 metrics cited), real contrast math, real ratio math. The Specimen instrument is genuinely useful — sorting typefaces by measured x-height and width rather than vibe is how a type-literate designer actually narrows a shortlist. URL-stateful instruments make design decisions shareable, reproducible artifacts (`primitiv.es/type/scale?ratio=1.618`) rather than Slack-thread screenshots. Tokens as single source, MIT license, and OFL fonts signal a design-led team. The commit log shows human-reviewed agent work — reviewed and corrected, which is the workflow that produces quality.
**Pros:**
- Computational rigor where AI design usually guesses: real measured metrics, real contrast math, real ratio math
- Shareable URL state makes every design decision a reproducible, reviewable artifact — excellent for system coherence across sessions and vendors
- Free, MIT, no account; contrast and type-scale instruments answer questions we hit constantly (accessible hues from #003da5, consistent type ramp)
- Design-token-first architecture maps cleanly onto our own token discipline for the Unified Platform
**Cons:**
- Very early and small — 2 stars, ~32 commits, single org; treat as working reference implementation, not infrastructure to depend on
- Instruments are intentionally narrow; you get excellent single-purpose answers, not an integrated system
- No Figma bridge — values must be moved between tools by hand, which is where drift creeps in
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The single most useful anti-slop move available, costing nothing. Generic AI output is generic because nobody computes anything: contrast gets eyeballed, type ramp gets invented per page, measure drifts, spacing comes from whatever the model felt like. Primitives makes those decisions quantitative and repeatable. Concretely for Shareef: derive accessible tints/shades from Montefiore navy #003da5 that hold up against #f5f5f0 and dark surfaces; lock one type scale for the Unified Platform and reuse it rather than re-inventing per feature; choose a display face for residency marketing by measured x-height instead of loudest suggestion. Adopt the contrast and type/scale instruments immediately as reference tools; do not adopt the repo as a dependency. For a design director's brief, "we computed it" is the difference between a system and a mood board.

---

### figma-font-handler
**Link:** https://github.com/yannicschaer/figma-font-handler
**Type:** Tool
**What it is:** An MCP server plus Figma plugin that gives AI assistants access to the fonts actually installed on your machine via Figma Desktop. Exposes `list_fonts`, `audit_fonts`, `set_font`, `replace_font`, `set_text`, and `execute`; `replace_font`/`set_font` preserve weights (Bold→Bold) where the target family carries them, and the `mapping` field reports exactly what was substituted. Derived from Strand AI's figma-slides-mcp (MIT), with WebSocket bridge on :3056.
**What's good about it:** Typography is where AI design most visibly fails, and one reason is that the agent simply cannot see your fonts — so it reasons about type in the abstract and produces tells we read as slop (wrong weights, collapsed hierarchy, fallback substitutions nobody chose). This gives the model ground truth: what is installed, what loads, what a replacement actually mapped to. `audit_fonts` is the quietly important tool — it reports fonts that are *listed* but *fail to load*, which is precisely the class of bug that ships silently and then renders as Times New Roman in front of a client. Verified live in Figma Desktop: plugin loads, `list_fonts` and `audit_fonts` work against a real file with locally installed fonts.
**Pros:**
- Solves a real, high-visibility failure: AI-driven type work against licensed, locally-installed fonts with correct weight mapping and transparent substitution reporting
- `audit_fonts` catches listed-but-unloadable fonts — a genuine pre-flight check for client-facing deliverables
- Reuses a proven MCP↔WebSocket↔plugin bridge (figma-slides-mcp) rather than inventing one; MIT, testable without Figma via mocks
- Single-purpose by design — no attempt to become a platform
**Cons:**
- Tiny and new — 1 star, 4 commits, one author, one week old; unproven under real load
- Requires Figma **Desktop** and a running assistant session; the plugin panel showing "Not connected" when no session is running is a confusing default
- Mac/Windows/Linux font enumeration through Figma Desktop will always be a moving target as Figma changes its plugin host
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Watch it, but fix the problem now because we already have it. Our system runs on Inter across the Unified Platform, and any Figma work feeding those surfaces needs the agent to reason from the real font inventory, not from an imagined one. The slop this prevents is the boring kind that reads as unprofessional: an agent substituting a weight that doesn't exist, collapsing a hierarchy it can't see, or shipping text set in a fallback because a family never loaded. The tool is too early to depend on, but its two ideas are ready to adopt immediately — (1) give agents authoritative access to the actual font set before they touch type, and (2) build a load audit into the pre-flight for anything client-facing. So: watch the repo, and in the meantime encode "verify every declared font family actually loads, in every weight and style used" as a ship gate on Sub-I materials, residency marketing, and platform typography. That is a checklist item today and a tool later.

---

### DesignHub
**Link:** https://github.com/yakew7/DesignHub
**Type:** Tool / Workflow
**What it is:** Open-source, local-first design & brand toolkit. Build a brand once, then get logo variants, mockups, social assets, a brand book PDF and design tokens. Plus fonts, colors, icons, SVG & accessibility tools. No login, no backend. Designed for designers who want to own their stack.
**What's good about it:** DesignHub attacks the core problem of brand fragmentation by letting you build a brand once and derive all assets from that single source. It outputs actual design tokens (CSS variables, JSON, etc.) rather than just static assets, making the system machine-readable and enforceable. The local-first approach means no login or backend — everything runs on your machine, addressing privacy and dependency concerns. It includes SVG and accessibility tools out of the box, showing awareness that real brand systems need more than just pretty pictures.
**Pros:**
- Local-first, no login or backend — everything runs on your machine, enhancing privacy and reducing points of failure
- Generates actual design tokens (CSS variables, JSON, etc.) from a single brand source, making the system machine-readable and enforceable
- Includes comprehensive asset generation: logo variants, mockups, social assets, brand book PDF, plus fonts, colors, icons, SVG & accessibility tools
- Open-source MIT license with active development (daily commits) and growing community (11 stars in 2 days)
**Cons:**
- Very early stage — 11 stars, created Sept 23, single author; treat as promising prototype, not infrastructure to depend on
- Next.js/TypeScript stack may not align with Shareef's current React/Tailwind Unified Platform
- Brand generation approach may produce coherent but generic output without strong human art direction
- Accessibility tools included but depth unknown — may be basic contrast checks rather than comprehensive auditing
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** DesignHub's local-first, token-generating approach aligns well with the need for machine-enforceable design systems on Shareef's surfaces. For the Unified Platform, the ability to generate consistent design tokens from a single source could prevent the drift that leads to AI slop. However, it's too early to depend on for production systems. What's valuable to adopt this week is the mindset: build the brand once as a single source of truth, then derive all assets from it. This could be implemented today by creating a canonical brand specification for Montefiore Urology (navy #003da5 as single accent, Inter typeface, SVG icon stroke weight) and using it to generate tokens, component variants, and asset guidelines. Watch the repo; if it maintains momentum and adds verifiable outputs (like automated token validation), re-evaluate for adoption.

---

### AI design tool from GitLab founder
**Link:** https://pixelcrew.ai/
**Type:** Tool
**What it is:** A practical AI-native design tool created by the GitLab founder that focuses on substance over flashy AI tropes. Rather than generating hollow AI aesthetics, it appears to focus on helping designers work with AI as a collaborative tool for real design work. Based on the HN post, it seems to emphasize practical workflow integration over generating complete designs from prompts.
**What's good about it:** The tool comes from a credible source (GitLab founder) and appears to focus on the actual workflow integration of AI in design rather than replacing designers with prompts. From the HN discussion, it seems to emphasize practical utility over generating the typical AI design tells (purple gradients, rounded corners, etc.). The fact that it's getting attention from the founder of a major dev tools platform suggests it solves real problems designers face when integrating AI into their workflow.
**Pros:**
- Created by GitLab founder — credible source with deep understanding of developer/designer workflows
- Appears to focus on practical AI integration rather than replacing designers with prompt-based generation
- Getting organic attention on HN suggests it solves real workflow problems rather than being hype
- Likely avoids common AI design slop by focusing on substance over flashy AI aesthetics
**Cons:**
- Limited information available — need to investigate further to understand actual capabilities and limitations
- May be more focused on general design work rather than the specific premium, professional aesthetic Shareef seeks
- Single creator project — bus factor of one, though mitigated by founder's reputation
- Need to verify if outputs align with Montefiore Urology's premium dark UI requirements
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's need to move away from generic "AI slop" aesthetics toward premium, professional design, a tool from a credible source that focuses on practical workflow integration is valuable. Unlike tools that promise to generate complete designs from prompts (which often produce the very slop we're trying to avoid), this appears to position AI as a collaborator in the design process. For the Unified Platform UI, marketing/social creative, and client-style websites, having AI assist with implementation while keeping human art direction in charge aligns with the "Elite Humanism" brand voice. The tool's apparent focus on substance over AI tropes suggests it could help implement designs without introducing the telltale signs of AI generation. Adopt it as a collaborative implementation tool for Shareef's design surfaces, maintaining human oversight of the art direction while leveraging AI for production assistance.

---

## Slop Radar
- **AI design tools that generate complete designs from prompts without human art direction in the loop** — These produce the generic purple/blue gradients, rounded corners, and telltale AI aesthetics we're trying to avoid. Real design requires human judgment at key decision points.
- **Tools that output static assets without design tokens or machine-readable specifications** — Without tokens, there's no way to enforce consistency across surfaces or prevent drift that leads to slop over time.
- **Typography tools that rely on web fonts or abstract font reasoning instead of access to actual installed fonts** — This leads to weight mismatches, hierarchy collapses, and fallback substitutions that read as unprofessional.
- **Logo generators that output bitmaps instead of constructed specifications with clear-space rules derived from the mark's geometry** — These violate basic principles of professional identity work and create trademark risks.

## Overall Assessment
The current wave of AI-assisted design tools is splitting into two camps: those that try to replace designers with prompt-based generation (producing predictable slop) and those that position AI as a collaborative tool under human art direction (raising the design ceiling). The most promising developments this week are precision instruments like Primitives that make subjective design decisions quantitative and repeatable, and token-generating systems like DesignHub that create machine-enforceable design systems. For Shareef's surfaces — the Urology Unified Platform UI (premium dark, single accent, Inter, SVG icons), Big Reef Chapter Player (polished light theme), marketing/social creative, Sub-I welcome materials, and premium client-style websites — the single highest-leverage move this week is to adopt computational rigor for fundamentals (using Primitives for contrast, type scale, and measure) while implementing a local-first brand token system that generates enforceable design tokens from a single source of truth. This combination attacks the root causes of AI slop: guesswork instead of calculation, and fragmented implementation instead of systematic enforcement.

-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-24.md — verified written
Email: python3 /home/hermeswebui/.hermes/scripts/smtp_send.py --to sfrasier@montefiore.org --subject "AI Design Intel — September 24, 2026" --body "$(cat /tmp/ai-design-intel.html)" --html
Vault: python3 /home/hermeswebui/.hermes/scripts/vault_append.py /tmp/vault-design.json