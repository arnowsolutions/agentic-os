# AI Design Intel — September 09, 2026
Sources scanned: X (unavailable today), Reddit (JSON API blocked, web search not attempted due to tool limitations), HN (available via one-shot aggregator and RSS), GitHub (available via one-shot aggregator and search), Google News (available via one-shot aggregator and RSS). Candidates considered: 38. Passed the bar: 4.

## Executive Summary
| Find | Type | Verdict | One-line why |
|------|------|---------|--------------|
| aievolutionpl/agent-design-taste | Skill | ✅ Adopt it | Embeds design taste into AI agents via style DNA and decision engine, reducing slop and raising intentionality. |
| ZSeven-W/openpencil | Tool | ✅ Adopt it | AI-native vector design tool with concurrent Agent Teams, ideal for scalable SVG/UI work with controlled AI assistance. |
| EightPotions/Myli | Tool | 👀 Watch it | Pre-alpha harness for agents to make precise JSON patch edits to design documents, offering controlled, programmatic design changes. |
| chokcoco/technical-image-generation-skill | Skill | 👀 Watch it | Skill for generating technical illustrations with a defined visual language and quality checklist, promoting clarity over slop. |

---
### aievolutionpl/agent-design-taste
**Link:** https://github.com/aievolutionpl/agent-design-taste
**Type:** Skill
**What it is:** A skill for AI agents that provides style DNA folders, decision engine, anti-slop rules, and taste scoring to improve the intentionality and quality of AI-generated designs.
**What's good about it:** Directly addresses the core problem of AI slop by embedding design taste into agents, enabling controlled, repeatable generation aligned with brand standards.
**Pros:**
- Focus on anti-slop and taste scoring aligns with premium design goals.
- Skill-based approach allows integration into agent systems like Hermes for workflow automation.
- Provides structured framework (style DNA, decision engine) for art-directed generation.
**Cons:**
- Effectiveness depends on underlying model quality and proper configuration of style DNA.
- May require learning curve to define style DNA for specific brand aesthetics.
- Does not directly enforce typographic or grid systems unless encoded in the skill.
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
- 👀 **Watch it** — (not applicable)
- ❌ **Skip it** — (not applicable)
**Why:** For Shareef's design surfaces (Urology Unified Platform UI, marketing/social creative, Sub-I welcome materials, premium client websites), integrating this skill into Hermes could help ensure that AI-assisted outputs (e.g., generating UI components, marketing graphics, website illustrations) adhere to intentional design principles and avoid generic AI slop. The skill's emphasis on style DNA and decision engine allows for art-directed generation, aligning with the goal of premium, professional design. By providing a framework for agents to make tasteful decisions, it elevates the design ceiling for AI-assisted work across all surfaces.

---
### ZSeven-W/openpencil
**Link:** https://github.com/ZSeven-W/openpencil
**Type:** Tool
**What it is:** An open-source AI-native vector design tool featuring concurrent Agent Teams, design-as-code, built-in MCP server, and multi-model intelligence for professional vector design with AI assistance.
**What's good about it:** Combines vector design precision with AI-native capabilities, enabling collaborative, iterative design processes while maintaining control over output.
**Pros:**
- Vector output is ideal for SVG icons, UI illustrations, and scalable graphics needed for Shareef's design surfaces.
- Concurrent Agent Teams allow multiple AI agents to collaborate on a design, potentially enabling sophisticated, controlled generation.
- Design-as-code approach facilitates versioning, reproducibility, and integration into development workflows.
**Cons:**
- May be early stage despite recent updates; maturity and stability need evaluation.
- Learning curve for new tool and its concepts (MCP, Agent Teams).
- Does not explicitly mention built-in typographic or grid controls, though vector tools typically support them.
**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
- 👀 **Watch it** — (not applicable)
- ❌ **Skip it** — (not applicable)
**Why:** For Shareef's Urology Unified Platform UI (which relies on SVG icons) and premium client-style websites (which often require vector illustrations), OpenPencil offers a professional-grade vector design environment enhanced with AI assistance. The tool's focus on AI-native vector design, combined with concurrent Agent Teams, could speed up creation of scalable graphics while allowing designers to retain control via agent collaboration. If the tool supports standard vector features (grids, typography, layers), it could integrate seamlessly into existing workflows and elevate output quality beyond prompt-only generators. Its recent updates indicate active development, making it a viable candidate for adoption now.

---
### EightPotions/Myli
**Link:** https://github.com/EightPotions/Myli
**Type:** Tool
**What it is:** A provider-neutral, pre-alpha Python harness for agents that propose RFC 6902 changes to application-owned JSON design documents, enabling precise, programmatic edits to design specs.
**What's good about it:** Focuses on controlled, exact modifications to design documents (e.g., adjusting layout, typography, colors via JSON patches), aligning with the need for intentional, repeatable design changes.
**Pros:**
- Enables agents to make precise, deterministic changes to design specs, reducing randomness and slop.
- Works with JSON design documents, which could correspond to formats like Figma JSON or custom design specs.
- Provider-neutral and independent of specific canvas formats or rendering stacks, enhancing flexibility.
**Cons:**
- Pre-alpha stage; may lack maturity, documentation, and stability.
- Unclear adoption and tooling ecosystem; may require significant integration effort.
- Effectiveness depends on the underlying design document format and the agent's ability to generate appropriate JSON patches.
**Should we...**
- ✅ **Adopt it** — (not applicable)
- 👀 **Watch it** — promising, not proven yet
- ❌ **Skip it** — (not applicable)
**Why:** For Shareef's workflow, a harness like Myli could enable Hermes agents to make precise, controlled edits to design specifications (e.g., adjusting spacing, typography, or color values in a design file) without resorting to full regeneration. This aligns with premium signals of controlled and repeatable generation and workflow integration. However, given its pre-alpha status and uncertainty about practical integration with existing design tools (Figma, etc.), it should be watched for now to see if it matures and gains adoption. If it proves stable and useful, it could be adopted to enhance the precision of AI-assisted design edits.

---
### chokcoco/technical-image-generation-skill
**Link:** https://github.com/chokcoco/technical-image-generation-skill
**Type:** Skill
**What it is:** A skill for generating technical illustrations with a defined visual language (watercolor infographic style) and quality checklist, aimed at creating clear explanatory diagrams.
**What's good about it:** Provides a structured approach to creating technical illustrations that emphasize clarity, explanation, and visual consistency, reducing reliance on prompt luck.
**Pros:**
- Focus on clarity and explanation aligns with intentional design for marketing/social creative and welcome materials.
- Skill-based approach includes references and a quality checklist, promoting repeatable, controlled generation.
- Produces illustrations that can elevate technical communication beyond generic AI-generated images.
**Cons:**
- Niche focus on technical illustrations may limit applicability to UI icons or websites.
- Specific visual style (watercolor infographic) may not match the premium dark UI aesthetic of Shareef's Urology UI.
- Still relies on underlying image generation model; quality varies with model capability.
**Should we...**
- ✅ **Adopt it** — (not applicable)
- 👀 **Watch it** — promising, not proven yet
- ❌ **Skip it** — (not applicable)
**Why:** For Shareef's marketing/social creative (e.g., explaining the residency program) and Sub-I welcome materials (e.g., informational diagrams), this skill could be useful to generate clear, explanatory illustrations that avoid the generic AI slop aesthetic. The skill's emphasis on a defined visual language and quality control supports intentional design. However, its niche applicability and specific style may not suit all design surfaces, so it should be watched for now to see if it proves valuable for specific use cases. If needed, similar skills could be developed for other illustration styles.

## Slop Radar
- Prompt-only AI design tools lacking manual refinement controls, leading to generic outputs (e.g., prompt-based tools like Google Pics).
- AI tools that replicate existing designs without sufficient transformation, raising plagiarism and slop concerns (e.g., Figma's disabled AI app design tool).
- Overemphasis on speed and accessibility over typographic discipline, grid systems, and brand consistency in many new AI design offerings.
- Niche AI skills (like specific illustration styles) applied systemically rather than selectively for campaign-specific needs.

## Overall Assessment
AI-assisted design is splitting between tools that prioritize speed and accessibility (often prompt-only) and those that embed AI as a collaborator within professional workflows to enhance control and craft. The most promising developments integrate AI to assist specific aspects of design—like agent-based taste skills, vector design tools with agent collaboration, or precise design document harnesses—while keeping the designer in charge of art direction, typography, and brand systems. For Shareef, the single highest-leverage move this week is to adopt the aievolutionpl/agent-design-taste skill within their Hermes agent workflow, as it directly upgrades the intentionality and quality of AI-generated outputs across all design surfaces by embedding design taste into agents, a foundational step toward premium, art-directed design.
-- Artifacts --
Brief file: /workspace/agentic-os/data/briefings/ai-design-intel-2026-09-09.md — verified written
Email: Email sent: AI Design Intel — September 09, 2026
Vault: Vault: added 4 item(s) → 1298 total (2026-09-09).