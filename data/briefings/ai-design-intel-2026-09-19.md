# AI Design Intel — September 19, 2026
Sources scanned: X (available), Reddit (subs + method: graphic_design/web_search, web_design/web_search, UI_Design/web_search, midjourney/web_search, StableDiffusion/web_search, FigmaDesign/web_search), HN (available), GitHub (available), Google News. Candidates considered: 18. Passed the bar: 6.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Lattice Prompt: AI-Assisted FPGA Development | Tool | ✅ Adopt it | Shows AI as expert multiplier in high-stakes domain with measurable 10x gains |
| Anthropic Claude One Interface with Docs/Slides/Design | Tool | ✅ Adoptit | Integrates AI into single workflow, reducing tool-switching friction for consistent output |
| Adobe Project Oasis: Figma Users Testing New AI Design Tool | Tool | 👀 Watch it | Major player entry needing craft evaluation beyond announcement phase |
| Smartdesign: Design Authority for Humans & Agents | Idea | ✅ Adopt it | Provides reviewable principles to combat AI-induced sameness in generated interfaces |
| Myli: Multi-Agent Harness for Visual Design | Tool | 👀 Watch it | Technical harness for agent design workflows, early stage but promising architecture |
| Signs of AI Design: Field Guide with Rules File | Tool / Idea | ✅ Adopt it | Evolving catalog of AI tells with false-positive labels, usable as QA gate |

---

### Lattice Prompt: AI-Assisted FPGA Development
**Link:** https://www.latticesemi.com/About/Newsroom/PressReleases/2026/Lattice-Advances-FPGA-Design-with-New-Leadership-AI-Driven-Development-Tool-Lattice-Prompt
**Type:** Tool
**What it is:** Lattice Semiconductor's new AI-powered FPGA development tool for small and mid-range FPGAs that enables natural language interaction across the full design flow (simulation, synthesis, map, place and route, timing analysis, bitstream generation) by orchestrating Lattice Radiant software in the background via open Model Context Protocol (MCP).
**What's good about it:** Demonstrates AI application in a high-precision, high-stakes domain where errors have tangible consequences, positioning AI as a force multiplier for expert designers rather than a replacement. Shows measurable productivity gains (10x or more on common tasks) and integrates with established professional workflows through open standards (MCP).
**Pros:**
- Targets professional hardware design (FPGA) where precision and reliability are critical
- Grounded in vendor's validated knowledge base for more accurate, context-aware responses
- Uses open MCP protocol for interoperability with agentic IDEs (Claude Code, Cursor, VS Code)
**Cons:**
- Currently limited to Lattice's FPGA ecosystem (though MCP suggests future extensibility)
- Focus on FPGA design may not directly translate to UI/UX design challenges
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This announcement validates the pattern we want to see in AI-assisted design: AI as a precision instrument for experts in high-stakes domains, not a slot-machine for novices. For Shareef's design surfaces — particularly the Urology Unified Platform's premium dark UI with Inter typeface and SVG icons, the Big Reef Chapter Player's light theme, and marketing/social creative — this reinforces that we should seek AI tools that assist with specific, constrained tasks where we can define clear boundaries and intent. Examples include generating accessible color variants from our #003da5 navy that meet WCAG contrast, producing motion prototype variations that adhere to our easing curves, or creating localized versions of marketing materials while preserving brand tone. The key is that the designer sets the constraints and intent; AI executes within those bounds, preventing the slot-machine mentality and positioning AI as a craft multiplier rather than a replacement for design judgment. Lattice's approach shows we can trust AI with complex, regulated tasks when it's properly grounded and constrained.

---

### Anthropic Claude One Interface with Docs/Slides/Design
**Link:** https://www.reuters.com/business/media-telecom/anthropic-fold-claude-ai-features-into-one-interface-launches-document-tools-2026-09-16/
**Type:** Tool
**What it is:** Anthropic's update to Claude AI assistant that combines chat, Cowork, and Design features into a single interface, introducing Claude Docs and Claude Slides in beta for creating documents, presentations, and visual designs within conversations, with export to Google Docs/Microsoft Word and PowerPoint/PDF.
**What's good about it:** Reduces cognitive friction and context-switching by integrating related capabilities into a single conversational flow, allowing Claude to automatically determine and deploy the right capabilities for a task without manual tool selection. Creates a more cohesive workflow for generating design artifacts.
**Pros:**
- Eliminates tool-switching friction that breaks creative flow and consistency
- Enables end-to-end design workflow within single conversation (concept → document → presentation)
- Includes export compatibility with standard workplace tools (Google Docs, MS Office, PDF)
**Cons:**
- Still in beta for Docs/Slides features; quality and consistency unknown
- May encourage over-reliance on AI for tasks requiring human judgment
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** For Shareef's design surfaces, particularly workflows involving the Sub-I welcome materials, residency program marketing, and client-style websites, reducing friction between ideation, documentation, and presentation is valuable. The ability to generate a one-page sheet with pertinent information, refine it through conversation, and export it to standard formats streamlines the creation of reimbursement tip sheets, Sub-I packets, and marketing briefs. More importantly, the integrated approach means design decisions stay coherent across artifacts — what works in a Claude Doc will carry through to a Claude Slide without reformatting. This addresses a key pain point in AI-assisted design: the fragmentation that occurs when jumping between specialized tools. For our Urology platform work, this could streamline the creation of design spec documents, interface annotations, and presentation materials for stakeholder reviews while maintaining visual and terminological consistency.

---

### Adobe Project Oasis: Figma Users Testing New AI Design Tool
**Link:** https://finance.yahoo.com/technology/ai/articles/adobe-inviting-figma-users-test-184723278.html
**Type:** Tool
**What it is:** Adobe's invitation to Figma users to test Project Oasis, a web-based graphic-design tool with brand-aware AI, seeking feedback under NDA before public launch as reported September 9, 2026.
**What's good about it:** Major design-tool player (Adobe) entering the AI space with direct relevance to Figma users, suggesting potential for professional-grade AI assistance within established design workflows that many designers already use.
**Pros:**
- Direct relevance to Figma workflows already used by many designers
- Backed by Adobe's substantial design-tool expertise and resources
- Focus on brand-aware AI suggests attention to brand consistency and guidelines
**Cons:**
- Early invitation stage; actual capabilities and quality unknown
- Risk of Adobe's typical bloat or over-engineering in AI implementation
- NDA-restricted testing limits public evaluation of output quality
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** For Shareef's design surfaces, particularly the Urology Unified Platform which likely uses Figma-adjacent workflows (given its Inter typeface, SVG icons, and premium dark UI), a Figma-relevant AI tool from Adobe could be valuable if it respects established design systems. However, we must judge it by its output, not its invitation. The key test will be whether it can generate components that adhere to our specific grid, use our accent color (#003da5) with proper contrast, and produce SVG icons that maintain our line-weight consistency — not just create visually pleasing but system-violating designs. Until we see it in action with our actual design tokens and constraints (or at least see public demonstrations of its output quality), it remains a watch item. The precedent of Figma disabling its own AI app design tool for copying Apple's weather app shows even major players can miss the mark on art direction, so verification through actual output is essential before adoption.

---

### Smartdesign: Design Authority for Humans & Agents
**Link:** https://foragents.pages.dev/
**Type:** Idea
**What it is:** A practical design language for people and agents building products together, framed as "the shared standard." It provides principles to keep interfaces clear, consistent, accessible, and appropriate to the work, addressing how AI can produce polished interfaces before understanding the user.
**What's good about it:** Provides specific, actionable principles rather than vague guidelines, particularly the final check questions that serve as a review tool: "Does this solve the user's actual problem?", "Can every interaction be completed with a keyboard?", "Are loading, empty, error, success, and disabled states handled?", "Did we reuse the existing system instead of inventing another one?", "Can anything visible be removed without reducing usability?"
**Pros:**
- Principles are specific and checkable rather than aspirational
- "Errors stay visible" principle names a specific failure mode generated UI hits constantly
- Final-check questions are usable as a pre-ship gate for design review
- Written explicitly for agents and humans building products together
**Cons:**
- It's a manifesto/page of principles, not a verifiable system or tool
- Most principles overlap with standards we likely already hold (accessibility, restraint, reuse)
- "Minimal chrome" and "visual restraint" can be fulfilled by producing generic minimalism
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This is immediately applicable to Shareef's work as a review and guidance framework rather than a generation tool. For the Urology Unified Platform, the residency program's marketing site, Sub-I materials, and client-style websites, these principles provide a concrete framework for evaluating AI-generated work. The "Errors stay visible" principle is particularly valuable for preventing silent failures in critical flows (like call-out systems or reimbursement submissions). The final-check questions — especially keyboard accessibility and removal-based usability — provide sharper review instruments than generic "is it clean?" checks. Smartdesign doesn't generate design; it helps us judge whether generated work meets our standards, which is exactly what we need to prevent AI slop from creeping in through technically correct but user-hostile outputs. We can adopt these principles as part of our design review process without needing to install anything.

---

### Myli: Multi-Agent Harness for Visual Design
**Link:** https://github.com/EightPotions/Myli
**Type:** Tool
**What it is:** A provider-neutral, pre-alpha Python harness for agents that propose RFC 6902 changes to application-owned JSON design documents. It validates design changes against schemas and supports vision/model integration without persisting or applying changes to application state.
**What's good about it:** Provides technical infrastructure for agent-driven design workflows with proper validation, version control (via RFC 6902 patches), and vision capabilities — treating design as code that can be reviewed, tested, and evolved through agent collaboration.
**Pros:**
- Treat visual design as version-controlled code (RFC 6902 patches)
- Provider-neutral architecture allows swapping LLM/vision backends
- Includes vision capabilities for reviewing visual output before proposing changes
- Open source (MIT license) with active development (updated Sept 18, 2026)
**Cons:**
- Pre-alpha stage; limited adoption and community
- Technical focus may be overkill for simple design tasks
- Requires treating design as JSON documents, which may not fit all workflows
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Myli represents an interesting technical approach to agent-driven design workflows that could be valuable for Shareef's more complex design surfaces. For the Urology Unified Platform, where we have committed design systems (navy #003da5, single accent, Inter typeface, SVG icons), Myli's approach of treating design documents as version-controlled JSON patches could help ensure that AI-generated changes respect our established systems through schema validation. The vision capability is particularly valuable — it means an agent could look at rendered output (like a mockup of a new platform feature) before proposing JSON changes, similar to the contact-sheet verification we valued in motion graphics skills. However, as a pre-alpha tool with minimal adoption, it's more of a pattern to watch than a dependency to install today. If Shareef wants to explore agent-driven design workflows for complex, iterative design work (like refining the platform's information architecture over multiple cycles), Myli's architecture is worth monitoring. For simpler, more direct design tasks, lighter-weight approaches may be more appropriate.

---

### Signs of AI Design: Field Guide with Rules File
**Link:** https://github.com/febbhav/signs-of-ai-design
**Type:** Tool / Idea
**What it is:** A field guide to the visual tells of AI-generated design across 7 categories (websites/app interfaces, AI-generated images, video, logos/branding, slide decks/documents, marketing/social/print, copy embedded in design), modeled on Wikipedia's Signs of AI writing. Includes a `design-rules.md` file usable as `CLAUDE.md`, `.cursorrules`, or `AGENTS.md` to tell coding agents what to design against.
**What's good about it:** Evolving catalog that pairs each AI tell with why models produce it and false positives, carrying reliability and status labels to help users judge significance. The `design-rules.md` provides actionable constraints for agents rather than just detection patterns.
**Pros:**
- Two-way resource: detector for reviewing work AND rules file for generation
- Reliability and status labels honestly address decay as models patch their tells
- Covers surfaces our other sources ignore — logos, branding, decks, print, embedded copy
- CC BY-SA 4.0 license allows free use, adaptation, and internal tooling
**Cons:**
- Not a fresh find (repository created July 22, 2026, last pushed July 31, 2026)
- 21 stars, single maintainer, prose-heavy with no CLI or automated scoring
- Its own false-positive discipline means it's only diagnostic in combination
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This is the closest thing we have to a formalized QA gate for AI-assisted design work. For Shareef's design surfaces, the practical value is two-fold: First, as a detection tool, it helps us identify the visual tells of AI slop in our own work (Urology platform interfaces, marketing creative, Sub-I materials, etc.). Second, and more importantly, the `design-rules.md` file can be dropped into our agent skills as a constraint — telling our coding agents what to design against rather than hoping they'll avoid slop through prompting alone. The guide's honesty about false positives and status labels means we can apply it intelligently: for example, we know that "dark hero with glow" is weak alone because it's also Linear's and Raycast's deliberate house style, so for our premium dark UI with single accent, the question becomes "is our dark a decision with a system behind it?" rather than "is dark slop?" This pairs exceptionally well with the Anthropic Claude One Interface work — the guide tells us what to avoid, the integrated Claude interface helps us avoid tool-switching fractures, and together they help us maintain craft discipline in AI-assisted workflows.

## Slop Radar
- Generic "10 best AI design tools" listicles without craft critique
- AI-generated 3D chrome/liquid blob aesthetics as default sophistication
- Prompts emphasizing "8k hyperdetailed" or "unreal engine" as quality signals
- Template farms marketed as "AI-customizable" brand kits

## Overall Assessment
AI-assisted design craft is maturing beyond the initial hype wave, with promising developments in two directions: professional tools showing AI as a force multiplier for experts in high-stakes domains (exemplified by Lattice's FPGA tool), and workflow integration efforts reducing friction between AI capabilities (shown by Anthropic's unified Claude interface). The single highest-leverage move for Shareef this week is to adopt the Signs of AI Design field guide's `design-rules.md` as a constraint in our agent skills — this creates a machine-enforced baseline that prevents the most common visual tells of AI slop from entering our work, immediately raising the quality floor for AI-assisted design across our Urology UI, marketing materials, and client-facing content.
-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-19.md — verified written
Email: Email sent: AI Design Intel — September 19, 2026
Vault: Vault: added 1 item(s) → 1394 total (2026-09-19).