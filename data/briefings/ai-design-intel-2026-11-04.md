# AI Design Intel — November 04, 2026
Sources scanned: X (web_search — site:x.com queries returned design-tool threads and two technique write-ups; no account-level timeline access from this environment), Reddit (hot.json BLOCKED on all 6 subs — returned HTML block pages, not JSON; fell back to site:reddit.com web_search for graphic_design, UI_Design, canva), HN (RSS endpoint returned 502 Bad Gateway; covered via last30days-pro aggregator), GitHub (API repos + topic searches: generative-art, design-tools, typography, figma, image-generation), Google News (RSS, 30 items). Candidates considered: 27. Passed the bar: 5.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| unslop — a Claude skill that audits slop, picks a direction, then fixes the screen in nine ordered passes | Tool | ✅ Adopt it | The only free thing I found this week that encodes a redline review as a sequence rather than a vibe, and it refuses to redesign a screen that's already good |
| Canva Craft — image generation that plans the composition before it renders a pixel | Tool | 👀 Watch it | The planning stage is the right idea and the training set is design templates rather than photographs — but the weights are Canva's, the brand kit isn't wired in, and "ready to use" is a vendor claim, not a design-director observation |
| DesignArena "How OpenAI's Sol Finally Learned Design Taste" — the anti-pattern taxonomy, measured | Idea | ✅ Adopt it | The purple-gradient vocabulary is now a named, measurable cluster that a model can be shown to avoid — which means we can specify "don't" in a system instead of pleading for it in a prompt |
| DESIGN.md as a portable format — Stitch's spec, the open linter, and Refero's 2,000 extracted systems | Workflow | ✅ Adopt it | Tokens plus prose plus a lint command is the closest thing yet to a design brief a machine can be held to, and the linter catches broken token refs and contrast — the two failures our platform keeps shipping |
| Efecto / Design Team — 16 specialist design agents with stated personalities, running in parallel | Idea | 👀 Watch it | The most honest attempt yet to make AI disagree with itself, including the founder admitting he turns it off — promising, expensive, and the GitHub repo shows its age |

---

### unslop
**Link:** https://github.com/heydamir/unslop
**Type:** Tool
**What it is:** A Claude skill (CC BY 4.0) that takes a vibecoded or AI-looking interface, audits it for specific slop signals — purple gradients, glows, emoji labels, shouty copy, uneven spacing — then sets a design direction from the product and fixes the screen pass by pass in a fixed order: spacing, color, icons, copy, type, layout, details, visuals, motion. Works in Next.js, React, Vue, Svelte, Tailwind or plain CSS, and can operate on a live URL.
**What's good about it:** The ordering is the product. Most "deslop" skills are a banned-phrase list; this one is a redline sequence, which is how a senior designer actually works — you fix the grid before you argue about the accent color, and you don't touch type until the spacing is right. It also proposes the direction *before* editing, so you can steer early rather than reviewing a finished screen you'll reject whole. And the escape hatch matters: if the screen is already good, it says so and suggests small refinements instead of rebuilding.
**Pros:**
- Nine named passes in a deliberate order, with a direction-setting step that comes before any edit — the workflow shape, not just the taste list, is transferable to any model.
- It self-limits on imagery: dashboards and apps "rarely need one," and it shows the prompt and asks before every paid generation through fal/Replicate/OpenAI. That is a tool that has thought about cost and about not slopping in a stock photo.
- Bypasses the debate about whether AI should touch design at all — it assumes you already have a screen and treats the problem as critique and correction, which is where AI is genuinely better than a human's patience.

**Cons:**
- It ships a "story video" of the screen unslopping itself, which is a marketing artifact dressed as a feature; it needs Playwright and ffmpeg and it will end up on LinkedIn.
- The author sells a paid "hire the unslopper" service — one key screen, three days, built in your stack — directly against it. That's not disqualifying, but it means the skill is optimised to make a demo look good, and demos reward dramatic before/afters over quiet restraint.
- The known slop list is now about three years old. Purple gradients and emoji labels are yesterday's tells; today's tells are the glassmorphic card, the 70/20/10-less muted palette, and the Instrument Serif hero — an audit built on the old list will pass a page that still reads as AI to a designer in 2026.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The Unified Platform UI does not need this — it has a stated system, one accent, real icons and a dark palette chosen on purpose. What needs it is everything downstream of the platform: Sub-I welcome PDFs, interview-season leave-behinds, the social creative for the residency program, and any landing page we spin up for a campaign in a weekend. Those are exactly the surfaces that drift toward gradient-and-emoji because nobody gave them a system. Take the *pass order* and the *propose-direction-before-editing* rule and put them in our own brief template even if we never run the skill itself; that transfer is worth more than the tool. Judge the output against our own slop radar, not the repo's 2024-era list.

---

### Canva Craft
**Link:** https://www.canva.com/newsroom/news/canva-craft/
**Type:** Tool
**What it is:** Canva's first in-house image generation model, trained from scratch by a 160-person research lab, available to all users through Dream Lab and to developers via public API. Its distinguishing feature is a two-stage architecture: one model writes an explicit plan of the composition — which elements appear, their spatial relationships, relative scale, hierarchy, and any text — and a second renders that plan to an image at up to 2K across 30+ aspect ratios. Text renders in 55 languages; outputs are JSON-boundary-boxed so Magic Layers can explode them into editable elements.
**What's good about it:** The training data is the interesting part, not the leaderboard position. Canva trained on millions of human-made *templates* — posters, social posts, decks, infographics, menus, typography-rich layouts — and the company's own claim is that this teaches the model how layout, hierarchy and typography fit together rather than what finished images look like. Whether or not that's true at scale, it is the correct hypothesis: the reason most image models produce slop is that they were trained on pictures, and pictures don't contain a grid. The planning stage then gives the model a place to resolve competing constraints (make the date legible, don't let the sponsor mark dominate) before committing any pixels, which is structurally closer to how a layout gets built than a one-shot render.
**Pros:**
- Separating plan from render means the failure is *addressable* — a bad composition is a bad plan you can read and correct, not a mystery you re-roll. That's the difference between a slot machine and a tool.
- Trained deliberately on typography-rich designed layouts, then fine-tuned and RL'd with professional designers in the loop across 25,000 head-to-head pairs — and Canva states that when automated evals and designer judgment disagreed, they sided with the designer.
- Public API plus an MCP server (coming) means outputs can be generated inside a real pipeline rather than by hand in a browser — rare for a consumer design tool.

**Cons:**
- It ranks fourth on DesignArena, behind three OpenAI models, and Canva's headline claim ("world's second most advanced AI lab") is a re-description of that same fourth-place finish. Read the newsroom copy carefully; it is marketing arithmetic.
- Brand Kit support is not here. A model that plans compositions but can't read your navy, your typeface and your logo grid will produce well-composed work in someone else's brand. For Montefiore that's an automatic no until your kit is load-bearing.
- It's Canva's weights on Canva's rails. The templates it learned from are the same template culture that produced the AI-sign epidemic designers have been photographing all year — training on a corpus of averaged layouts can reproduce the averageness with better kerning.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The honest assessment is that Craft is a real architectural advance wrapped in a claim it hasn't earned. Plan-then-render is the direction the whole field should move, and it's the single mechanism most likely to make generated social creative usable rather than embarrassing. But for our surfaces, the missing piece is the brand kit, and the target — Instagram carousels, event posts, recruitment creative — is exactly where Canva's learned aesthetics are least trustworthy, because the corpus is other people's marketing. Revisit when Brand Kit support ships and a real designer has published a side-by-side against GPT-Image on a healthcare or institutional brief. Until then it's a competent idea with a leaderboard screenshot attached.

---

### DesignArena — "How OpenAI's Sol Finally Learned Design Taste"
**Link:** https://notes.designarena.ai/how-openais-sol-finally-learned-design-taste/
**Type:** Idea
**What it is:** A research note from the crowd-sourced design benchmark, prompted by GPT-5.6 Sol debuting first on their non-agentic web-design arena — eighteen places above its predecessor and the first time an OpenAI model had taken the top spot. To explain it, they projected the CLIP embeddings of 1,000 generated websites into UMAP space and found something odd: the model's design manifold had *holes* exactly where GPT-5.5 reliably produced purple gradients, bento-box layouts, oversized hero type, and offset compositions. The same holes appeared for the other anti-patterns. Their read: the model has learned that these patterns exist and is actively suppressing them, not merely failing to learn them. They contrast this with GLM-5.2, which avoids anti-patterns by working from templates that simply don't contain them — a cleaner solution that buys less variety.
**What's good about it:** This is the first piece of evidence I've seen that "AI slop" is a *measurable, bounded region of a model's output space* rather than a vague complaint, and the method is legible enough to be argued with. It also produces the single most useful operational distinction in the piece: a model can avoid an anti-pattern by not knowing it, or by knowing it and refusing it — and those two models behave completely differently when you ask for variety. Add the confetti finding (Sol hand-rolls its own confetti library and ships it in 26.5% of generations) and you have a genuinely useful lesson: anti-pattern suppression is per-pattern and doesn't generalize, so a model that has cured gradients is not a model that has learned restraint.
**Pros:**
- Turns slop into a taxonomy with names and a method — purple gradients, bento grids, oversized hero type, offset layouts — each individually identifiable, which is what a design system needs in order to write a rule against it.
- The templating analysis is the sharpest thing in it: Claude Fable 5 is described as having almost no templating and a far more varied space, GLM-5.2 as avoiding slop by narrowing to clean templates. Three models, three different failure modes, all scoring well.
- The confetti finding generalises into a rule I would actually write down: every model has a house tic it falls back on when the brief is thin. Find yours, name it, forbid it.

**Cons:**
- It's a benchmark vendor publishing a favourable analysis of a ranking it also profits from. The embedding visualisation is seductive and unfalsifiable by a designer — you cannot see a hole in UMAP and disagree with it.
- UMAP is a lossy 2D projection of a very high-dimensional space; the authors acknowledge this with a parenthetical about "the right projection parameters," which is doing a lot of unexamined work.
- It tells you what a model avoids and almost nothing about what it should *reach for*. Avoiding gradients is a floor, not taste. A page with no anti-patterns can still be completely anonymous.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** What we take isn't the leaderboard, it's the vocabulary and the two rules. First, the anti-pattern list becomes a written prohibition in our design system for the Unified Platform and the Chapter Player — not "avoid AI look" but a specific, itemised list of the four patterns with the reasoning attached, so a future contributor reads *why* a bento grid is banned rather than assuming it's a style preference. Second, the per-pattern finding means we stop treating "premium" as one setting: the platform already kills gradients by having one accent and a dark neutral ground, but if we ever hand generative work to a model for marketing creative, we need to check each tic separately, because suppressing one proves nothing about the other four. And the "house tic" lesson transfers to humans too — every designer has one, and naming it is the fastest way to stop the work being recognisable from across the room.

---

### DESIGN.md — a portable design system for agents, with a linter
**Link:** https://styles.refero.design/design-md/what-is-design-md
**Type:** Workflow
**What it is:** A plain-text, version-controlled format — YAML front matter for machine-readable tokens (colors, type, spacing, radius, components), a markdown body for the prose that explains *why* those tokens have those values and when to use them. Originated with Google Stitch, whose spec was open-sourced under Apache 2.0 (google-labs-code/design.md) with an explicit philosophical position that "prose is the heart of the specification." It ships with a CLI linter — `npx @google/design.md lint DESIGN.md` — that checks for broken token references and WCAG contrast ratios. Refero Styles publishes 2,000+ systems extracted from real product websites as ready-to-paste DESIGN.md files, with exports for Tailwind v4 `@theme` blocks and CSS variables.
**What's good about it:** The two-layer split is correct and under-argued in the wider AI-design conversation: tokens alone can't tell an agent *which* valid choice is right in context, and prose alone can't be linted. Requiring both means the design intent survives contact with a coding agent and the mechanical failures survive contact with CI. The lint step is the part nobody else has — a broken token reference and a 2.9:1 contrast badge are the two errors that ship silently, because both look fine to the person who made them.
**Pros:**
- It is a *file*, not a service. Versionable, diffable, reviewable in a pull request — a design decision can now be argued about in the same place as the code it governs, with a blame trail.
- The linter checks contrast and token integrity automatically, which converts two subjective-feeling failures into hard CI gates. That's leverage on every future page rather than a one-time audit.
- The export formats land where our stack already is — Tailwind v4 theme blocks and CSS variables — so the handoff isn't a document nobody reads but a diff that changes the build.

**Cons:**
- Two thousand extracted systems is a candy store with no shopkeeper; the right way to use it is to pick a reference by density and tone, not by brand you admire, and almost nobody does that. There's a real risk of importing someone else's decisions wholesale and calling it a system.
- The prose half is the important half and the half no linter can verify. A DESIGN.md can lint clean — valid tokens, passing contrast — and describe a generic product. Lint proves consistency, never taste.
- It is one more artifact to keep current. A stale design system file is worse than none, because it silently misleads an agent with confidence.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The Unified Platform already has a real system — navy, one accent, Inter, SVG icons, a dark ground — but it lives in components and in Shareef's head, not in a file an agent can read. Writing it out as DESIGN.md is the highest-leverage documentation move available this week, because it converts the unstated rules that currently protect the platform into text a model can be held to when the next page gets built. Write it ourselves, in prose, with the *why*: why one accent and not two, why the neutral isn't true black, which four anti-patterns from the DesignArena piece are forbidden, what density we want. Then run the linter against it — not to prove it's good, but to catch the contrast failures we've been introducing one badge at a time. Do not start from a Refero reference; start from our own page and use Refero only to argue about density.

---

### Efecto "Agent Teams" / Design Team — sixteen agents with personalities, and a creative director who disagrees
**Link:** https://efecto.app/blog/your-ai-design-team
**Type:** Idea
**What it is:** Pablo Stanley's bet that one agreeable AI designer is the reason AI output converges. Efecto assembles a crew from 16 specialist roles (creative director, UX, visual, copywriter, researcher, brand strategist, illustrator, accessibility) chosen per brief; each has five personality sliders with a fixed trait budget so nobody is maximally everything, five emotional states that shift with the session, and per-agent plus team memory of the brand and of past sessions. They run in parallel on separate artboards and the creative director critiques across all of them. The role definitions are also open-sourced as a skills install (`npx skills add pablostanley/designteam-app`) usable in Claude Code or Codex. Stanley's framing — "AI agents are too agreeable; ask for a critique and you get a compliment sandwich; a good art director says *I've seen this a hundred times, too predictable, what else you got*" — is the thesis.
**What's good about it:** The diagnosis is the most accurate thing anyone has said about why AI design work flattens: it's not the model's taste, it's the *single* perspective. One model doing research, copy, layout and review has one voice and converges on it fast, and the reviewer and the maker are the same entity, so nothing ever gets rejected. Splitting the review into a separate agent with a stated and different personality is a structural fix, not a prompt trick — and the stated constraint output in the examples ("No gradients. No icon grids. No stock photography of handshakes or skylines. The restraint IS the design.") is exactly the register a real creative director uses.
**Pros:**
- Parallel artboards with a cross-cutting critic is a genuine structural difference from turn-taking chat, and the collaboration/conflict record gives you a visible trace of what was rejected and why — rare in AI design tools, where the process disappears into the output.
- The personality sliders have a fixed budget, so agents can't all be bold-and-experimental simultaneously. It's a small design decision that prevents a specific and common failure.
- The role prompts are MIT-ish open source and portable into a normal coding-agent workflow; you can take the *idea* (a separate critic with different instincts) without taking the product.

**Cons:**
- Stanley's own post is the most honest sentence in the whole thing — "Sometimes I open the panel and it looks like I opened a Slack with 16 coworkers and they're all typing at once. I've had moments where I missed a great critique because another agent was mid-sentence. So I turn it off sometimes." A tool its author disables is a tool with an open question, not an answer.
- The emotional-state layer reads as tamagotchi — "maybe I should be nicer to them" — and there's no evidence that mood mechanics produce better design rather than more *varied* output. Variation is not the goal; judgement is.
- The open-source repo behind it (pablostanley/designteam-app) shows 18 stars with its last push in April; the live product is a different, newer thing. Anyone installing from GitHub expecting what the blog describes will get an older artifact.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The insight is worth taking today even though the tool isn't: our own workflow has no reviewer that isn't also the maker. When we generate a Sub-I welcome page or a recruitment carousel, the same pass that made it approves it, which is precisely the compliment-sandwich problem. The cheap version of Stanley's idea, available right now with no product and no subscription, is to *separate the critic* — a second pass with a written brief that says what to reject, in the register of "I've seen this a hundred times." That's a line in our prompt template, and it costs nothing. The 16-agent product itself I'd wait on: the founder turns it off, the open repo is stale, and coordinating sixteen opinions is a problem we don't have. We have a one-reviewer problem.

---

## Slop Radar
- **Glassmorphism is the new purple gradient.** Frosted translucency plus a 1px light border plus a gradient backdrop is now the fastest tell of unedited AI output — and unlike the gradient, it actively damages readability. If a card needs a blur to feel layered, the underlying hierarchy is missing.
- **The Instrument Serif hero.** Serif display headlines have become the default "elegant" choice of at least one major model, which means a serif hero now reads as a default rather than a decision. In institutional and healthcare work it also fights the functional register — a residency page is a document, not a magazine cover.
- **The icon in a rounded square.** A generic glyph on a tinted rounded tile, repeated down a page, communicating nothing but decorating consistently. Cut the icon entirely unless it signals an action; the empty space is better typography than the decoration.
- **Emotional-UI theatre.** Mood meters, XP bars and agent "personalities" as visible product surface. Fun, and increasingly common in this category — but visible mechanics are not craft, and they are the visual signature of tools built for demos rather than for deliverables.

## Overall Assessment
The field has quietly shifted from *generating* to *supervising*, and this week's evidence is consistent about what good looks like: an explicit plan before pixels (Craft), a written system before screens (DESIGN.md), a named list of prohibitions before a direction (DesignArena), and a critic who is not the maker (Efecto). None of that is a model capability — it's process, and process is what a design director already owns. The slop comes from the gap where process used to be. The single highest-leverage move for Shareef this week is to write the Unified Platform's DESIGN.md by hand: the palette and type in the front matter, and in the prose the *why* — one accent because a second one competes with the primary action, a dark neutral ground because true black destroys depth, four named anti-patterns that are forbidden and the reason each one is forbidden. Then run the Google linter against it and fix what it finds. That file does more for every page we build next than any tool on this list, and it takes an afternoon.

-- Artifacts --
