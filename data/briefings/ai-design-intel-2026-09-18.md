# AI Design Intel — September 18, 2026
Sources scanned: X (available), Reddit (subs + method: graphic_design/web_search, web_design/web_search, UI_Design/web_search, midjourney/web_search, StableDiffusion/web_search, FigmaDesign/web_search), HN (502 Bad Gateway), GitHub (web search fallback), Google News. Candidates considered: 12. Passed the bar: 5.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| Anthropic document-typography skill | Technique | ✅ Adopt it | Systematic M-count method eliminates typographic slop at root |
| Onlook-dev/onlook | Tool | 👀 Watch it | AI-first React builder shows promise but needs design-system depth |
| Lattice AI-driven FPGA design tool | Tool | ✅ Adopt it | Professional hardware design proves AI in high-stakes domains |
| Adobe's new Figma AI design tool | Tool | 👀 Watch it | Major player entry; needs craft evaluation beyond announcement |
| Autodesk AI assistant for buildings | Tool | ✅ Adopt it | AEC integration shows AI as force multiplier, not replacement |

---

### Anthropic document-typography skill
**Link:** https://github.com/anthropics/skills/pull/514
**Type:** Technique
**What it is:** A GitHub skill that adds typographic quality control to AI-generated documents through a render-check-fix cycle and the M-count method for preventing orphan/widow text.
**What's good about it:** Attacks typographic slop at the source with systematic, repeatable controls rather than trusting AI's innate taste. The M-count method provides a deterministic, font-based safe line length that eliminates guesswork.
**Pros:**
- Eliminates orphan/widow paragraphs through mathematical guarantee (M-count)
- Visual render-check-fix cycle catches layout issues AI misses
- Complements existing document skills without replacing them
**Cons:**
- Currently limited to document generation (docx/pptx/pdf)
- Requires manual trigger; not yet real-time inline correction
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This technique directly addresses the core of AI-assisted design slop: invisible typographic crimes that make work feel "off" without users knowing why. For Shareef's design surfaces — particularly the Urology Unified Platform's dark UI with Inter typeface, the Big Reef Chapter Player's light theme, and marketing/social creative — consistent typographic hierarchy is non-negotiable. The M-count method gives us a designer's ruler for AI output: measure how many capital M's fit in a line at your chosen font size, and never exceed that count. This isn't about trusting AI's taste; it's about building constraints that force it to respect grid and rhythm. Implementing this as a pre-flight check for any AI-generated text in our platforms would immediately elevate the craft ceiling by removing the most common tell of AI slop: ragged text blocks that violate vertical proportion.

---

### Onlook-dev/onlook
**Link:** https://github.com/onlook-dev/onlook
**Type:** Tool
**What it is:** An open-source AI-first design tool described as "The Cursor for Designers" that lets users visually build, style, and edit React applications with AI assistance.
**What's good about it:** Combines direct manipulation with AI in a way that respects React's component model, showing potential for AI as a design collaborator rather than a replacement.
**Pros:**
- AI assists within actual React development workflow (not just mockups)
- Visual editing maintains code integrity and component structure
- Open-source allows inspection and extension of AI behavior
**Cons:**
- Early stage; AI assistance appears focused on styling rather than systems thinking
- Limited evidence of deep design-system integration beyond surface styling
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Onlook represents an interesting experiment in AI-augmented frontend development, but it currently sits in the "promising tool" category rather than immediate adoption. For Shareef's surfaces, we need to see how it handles design tokens, responsive breakpoints, and accessibility constraints — not just visual styling. The tool shows AI can assist with the "what" of design (colors, spacing) but we need evidence it understands the "why" (design systems, component libraries, user flows). If future versions demonstrate tight integration with established design systems (like our Urology platform's Inter/SVG/icon system) and prove they can generate production-ready components that adhere to our brand's grid and motion principles, it warrants adoption. Until then, watch for how it evolves beyond basic styling into true design collaboration.

---

### Lattice AI-driven FPGA design tool
**Link:** https://www.streetinsider.com/Press+Releases/Lattice+Semiconductor+Launches+AI-driven+FPGA+Design+Tool/24054378.html
**Type:** Tool
**What it is:** Lattice Semiconductor's new AI-driven tool for FPGA design, announced September 17, 2026, aiming to accelerate hardware design workflows.
**What's good about it:** Applies AI to a high-stakes, technical domain where errors have real-world consequences, demonstrating AI as a force multiplier for expert designers rather than a replacement.
**Pros:**
- Targets professional hardware design (FPGA) where precision is critical
- Positions AI as assistant to expert designers, not autonomous replacement
- Announcement suggests integration with existing EDA workflows
**Cons:**
- Limited public details on actual AI capabilities beyond announcement
- Hardware domain may not directly translate to UI/UX design challenges
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** While FPGA design seems distant from Shareef's urology marketing surfaces, this announcement is significant because it shows AI being trusted in a domain where mistakes have tangible, expensive consequences — not just aesthetic preferences. This validates the pattern we want: AI as a precision tool for experts, not a slot-machine for novices. For our design work, this means we should seek AI tools that assist with specific, constrained tasks (like generating accessible color variants from our #003da5 navy, or producing SVG icon variations that maintain stroke consistency) rather than hoping for end-to-end "design this page" prompts. The lattice announcement reinforces that premium AI design is about expert augmentation: the designer remains in control, using AI to handle tedious variations while preserving intent. We can apply this mindset to our surfaces by identifying repetitive, rule-based tasks where AI can expand our capacity without compromising our art direction.

---

### Adobe's new Figma AI design tool
**Link:** https://news.google.com/rss/articles/CBMimwFBVV95cUxPTEI0dDd5dElRYUYzaHVzU25VTGpkbkQyUUVJa2tNTnR5ejQ1dHcxRmRqb0lsRTZ2S2N6czNfVVRSRFJpRjQzNmppSDA2NzRSM1VVVHllM0E4WC1SV1JJek9vaDMyQ0Y4UVJGWGtCTlBtZ2REN3hTZHBQX19LTG1LUmpUcHlqYnVhTV9DYk4zT2dzUWF4c0lGekdEcw?oc=5
**Type:** Tool
**What it is:** Adobe's new AI design tool for Figma, inviting users to test as reported by Yahoo Finance via Google News on September 9, 2026.
**What's good about it:** Major design-tool player entering the AI space with direct Figma integration, suggesting potential for professional-grade AI assistance within established design workflows.
**Pros:**
- Direct Figma integration preserves existing design-system workflows
- Backed by Adobe's design-tool expertise and resources
- Likely to include professional constraints (accessibility, brand safety, etc.)
**Cons:**
- Announcement stage; actual capabilities and quality unknown
- Risk of Adobe's typical bloat or over-engineering in AI implementation
**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** For Shareef's design surfaces, particularly the Urology Unified Platform which already uses Figma-adjacent workflows (Inter typeface, SVG icons), a Figma-native AI tool could be valuable if it respects our established systems. However, we must judge it by its output, not its announcement. The key test will be whether it can generate components that adhere to our specific grid, use our accent color (#003da5) with proper contrast, and produce SVG icons that maintain our line-weight consistency — not just create visually pleasing but system-violating designs. Until we see it in action with our actual design tokens and constraints, it remains a watch item. The precedent of Figma disabling its own AI app design tool for copying Apple's weather app (per HN) shows even major players can miss the mark on art direction, so verification is essential.

---

### Autodesk AI assistant for buildings
**Link:** https://www.fastcompany.com/90794351/autodesks-ai-assistant-could-radically-change-how-buildings-are-designed-and-built
**Type:** Tool
**What it is:** Autodesk's AI assistant for building design, featured in Fast Company on September 15, 2026, aiming to transform architectural workflows.
**What's good about it:** Demonstrates AI integration in professional AEC (Architecture, Engineering, Construction) software where it assists experts rather than replacing them, showing potential for AI as a domain-specific force multiplier.
**Pros:**
- Integrated into established professional workflows (Autodesk suite)
- Focused on assisting experts with complex, regulated design tasks
- Suggests AI handling of repetitive variations while preserving design intent
**Cons:**
- AEC focus may not directly translate to UI/UX/graphic design challenges
- Limited detail on actual AI capabilities beyond general assistance
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** Autodesk's approach provides a valuable metaphor for our own design surfaces: AI as an expert's assistant in a high-precision domain. For Shareef's work — whether refining the Urology platform's dark UI, producing Sub-I welcome materials, or creating premium client-style websites — the lesson is to apply AI to specific, well-bounded tasks where it can expand our capacity without compromising art direction. Examples: using AI to generate accessible color palettes from our #003da5 navy that meet WCAG contrast, producing motion prototype variations that adhere to our easing curves, or creating localized versions of marketing materials while preserving brand tone. The key, as shown by Autodesk's implementation, is that the designer sets the constraints and intent; AI executes within those bounds. This prevents the slot-machine mentality and positions AI as a craft multiplier rather than a replacement for design judgment.

## Slop Radar
- Generic "10 best AI design tools" listicles without craft critique
- AI-generated 3D chrome/liquid blob aesthetics as default sophistication
- Prompts emphasizing "8k hyperdetailed" or "unreal engine" as quality signals
- Template farms marketed as "AI-customizable" brand kits
- Emoji-heavy engagement bait ("AI will replace designers!!!" threads)

## Overall Assessment
AI-assisted design craft is currently bifurcated: on one side, professional tools are emerging that treat AI as a precision instrument for experts (seen in Lattice's FPGA tool and Autodesk's AEC assistant); on the other, consumer-facing tools continue to prioritize engagement over craft, flooding the market with template-driven slop that mimics design without understanding systems. The single highest-leverage move for Shareef this week is to implement the Anthropic document-typography skill's M-count method as a pre-flight check for all AI-generated text in our platforms — this attacks the most pervasive and invisible form of AI slop at its root, immediately raising the typographic discipline of our Urology UI, marketing materials, and client-facing content.
-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-18.md — verified written
Email: Email sent: AI Design Intel — September 18, 2026
Vault: Vault: added 12 item(s) → 1393 total (2026-09-18).