# AI Design Intel — October 26, 2026

Sources scanned: X (partial — site:x.com returned live design threads but most results were undated; 2 dated, verifiable finds kept, 1 dropped as stale), Reddit (r/graphic_design via RSS — came through; r/web_design, r/UI_Design, r/midjourney, r/StableDiffusion, r/FigmaDesign JSON/RSS blocked — covered via Google News site:reddit.com queries instead; r/StableDiffusion MOSS-Image-Edit thread verified through Hugging Face primary source), HN (hnrss: q=AI+design and q=typography returned empty; q=generative+design returned only old/low-relevance hits — the last30days-pro aggregator supplied the HN layer), GitHub (repo search + created:>2026-10-19 topic sweeps: ai+design, design-tools, figma, generative-art, typography, image-generation), Google News (AI design tool + figma/design-system queries), DesignArena/Hugging Face primary sources. Candidates considered: 27. Passed the bar: 6.

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| Canva Craft | Tool | 👀 Watch it | First image model architected around *planning composition and typography before rendering* — the right idea, and Canva's template corpus is the correct training diet, but the output still reads Canva-branded unless you art-direct hard. |
| Desk Studio | Workflow | ✅ Adopt it | An actual studio org chart — roughs → art director pick → polish → pixel-level proof → sign-off on an 8-axis rubric — running inside Claude Code/Codex. This is the discipline layer we keep hand-rolling. |
| email-design-md (EMAIL.md) | Workflow | 👀 Watch it | The best worked example I've seen of a written design system an agent can be graded against — including the finding that self-review rounds up 23 points vs. a blind critic. |
| BRND ProType | Tool | ✅ Adopt it | A free, genuinely well-drawn neo-grotesque superfamily — 49 styles, three variable fonts, real OpenType — that fixes the "everything is Inter" problem in our hero type. |
| Mesh Gradient Generation (agent skill) | Technique | 👀 Watch it | Teaches editable, reproducible gradient construction (planes + Gaussian masks + explicit blur values) instead of the purple-blob slot machine. Requires a live Figma execution tool — we don't have one wired. |
| MOSS-Image-Edit-HQ v4/v5 | Tool | 👀 Watch it | The most honest open eval I've seen in image editing: publishes losses, targets "unedited pixels stay at source," and directly attacks the saturation/drift that ruins client asset tweaks. Local GPU only. |

---

### Canva Craft
**Link:** https://www.canva.com/newsroom/news/canva-craft/
**Type:** Tool
**What it is:** Canva Research's first from-scratch image generation model, live for all Canva users (Dream Lab) and via the Canva public API. It uses a two-stage architecture: an image *planning* model writes a composition spec — which elements appear, spatial relationships, relative scale, visual hierarchy, and any text — and a separate renderer produces the image at up to 2K across 30+ aspect ratios.
**What's good about it:** The architecture is the story, not the leaderboard position. Every other major image model generates pixels directly from a prompt and hopes composition emerges. Craft separates "decide the layout" from "render the layout," which is exactly the gap that makes AI output unusable for design work — you cannot put a headline in a reserved zone if the model never reserved a zone. Canva also trained it on millions of *human-made templates* (posters, social posts, presentations, infographics) rather than photographs, so the training signal is hierarchy and typographic structure, not just what finished images look like. And Canva's own account of evaluation is unusually specific: designers judged 25,000 head-to-head pairs, and when automated evals disagreed with designers, designers won. JSON boundary boxing feeds Magic Layers, so generated output becomes editable layers rather than a flat JPEG.

**Pros:**
- Composition planning before rendering means reserved negative space and legible in-image text are a structural property, not a lucky roll — the single biggest practical unlock for social/marketing creative where a headline has to land somewhere specific.
- Editable-by-construction: JSON boundary boxes → Magic Layers means one asset can become a layered, revisable design element instead of a re-roll.
- 55-language in-image text at 2K across 30+ aspect ratios covers the actual aspect-ratio matrix we post to (1:1, 4:5, 9:16, 16:9) without upscaling.
- Public API + announced MCP means agent-driven pipelines can call it, not just humans in the editor.

**Cons:**
- Canva's ranking claim is thinner than the press release reads. Craft debuted fourth on DesignArena (scored 1,341) behind GPT-Image-2.5 Sunburst (1,406), Flare (1,382) and GPT Image 2 (1,362) — the "world's second most advanced image lab" line follows from counting three OpenAI models above it, not from an independent lab ranking. Results were described as preliminary.
- Trained on Canva's template library, which is the same corpus that produced a decade of "Canva look." The model is excellent at the visual grammar of platform templates; that is the opposite of art direction that doesn't look templated.
- The output is destined to be edited in Canva by whoever opens the file — for us that's a handoff with no design control, and no obvious way to enforce a type scale or a single accent.
- Craft-fast/Craft-ultrafast, MCP availability, and pricing/usage limits are all announced, not confirmed shipped. No independent hands-on review of typographic accuracy at production sizes yet.

**Should we...**
- 👀 **Watch it**

**Why:** For a design director this is a genuinely interesting architectural bet and a mediocre *tool* today. The reason to care isn't image quality — it's that someone finally built "plan the grid, then render the grid" instead of "render and pray," which is the only path by which generated imagery becomes art-directable rather than curated by rejection sampling. Where it could fit: Sub-I welcome materials and residency marketing social creative are produced on a fixed matrix (name, credentials, date, one photo, one accent) — that is exactly a planning problem, and a model that reserves the text zone solves a real failure we hit today. Where it can't fit: the Urology Unified Platform UI (premium dark, single accent, Inter, SVG iconography) and the Big Reef Chapter Player must stay code-native and component-driven; generating those gives us raster mockups of interfaces we'd then have to rebuild, which is worse than useless. And the Canva template diet is the risk: the whole reason our creative reads premium is that it refuses the platform look, and this model's training data *is* the platform look. My bet is Craft is worth a single controlled test — one Sub-I announcement post, same brief, Craft vs. our current path, blind-compared by someone who didn't make either — before anyone adopts it into a pipeline.

---

### Desk Studio
**Link:** https://github.com/adityareddy-dev/deskstudio
**Type:** Workflow
**What it is:** An open-source (MIT) design studio that runs inside the coding agent you already have — Claude Code natively via plugin, or Codex/Cursor/Gemini CLI/Copilot/Windsurf/OpenCode via `npx deskstudio add`. Every job runs like an agency floor: three roughs from a senior model, an Art Director picks and writes notes, a builder desk revises with the notes *and the screenshot*, then an automated pixel proof, then a Creative Director sign-off.
**What's good about it:** The structure is the product, and the structure is unusually honest for AI design tooling. It names the actual failure mode of agent design work — that a single model grading itself produces incremental micro-slides, not directions — and fixes it with separated roles and quality gates. The proof stage is the part I'd steal even if I never install the repo: it renders every polished file in Chrome at each target size and checks *pixels* — text contrast against the pixels behind it, overflow and clipping, platform safe zones, colours inside the brand palette, type on the brand scale, every line of copy present, carousel consistency across slides. No model in that loop. It's a lint pass for design, and it runs on the finished artifact rather than on the model's description of it. Sign-off scores eight axes (hierarchy, typography, spacing, colour, composition, originality, brand fit, copy) and fails anything below 8 on any axis. Every golden example ships with renders, state and cost — social cards at roughly $0.65–$2.40 a job, decks around $8 — so the economics are legible before you commit.

**Pros:**
- Roughs → pick → polish → proof → sign-off mirrors how an actual studio protects quality: directions are chosen before detail work, and detail work is checked on rendered pixels, not on vibes.
- The proof stage catches the exact defects that make AI design work look sloppy at scale — contrast on the rendered background, clipped overflow, safe-zone violations, off-palette colours, type off the scale.
- Runs on your machine against the CLIs you're already signed into; MIT licensed; the desks are markdown briefs, so we can author a Big Reef desk (tokens, accent rule, photography standard, voice) rather than accept a stranger's taste.
- Cost per job is published, and the failures are published too — "a builder that misses the same note twice hands the file to a senior" is a real escalation rule, not marketing.

**Cons:**
- The "8.5+ average" scores come from the studio's own model reviewers, not independent benchmarks. A rubric graded by models that were also told the rubric is a weak signal about quality; it's a strong signal about internal consistency, which is a different thing.
- Only the `design` command (social cards) runs outside Claude Code. Decks, dashboards, email templates, carousels, motion and video are Claude-Code-only for now — a hard dependency on one vendor's CLI.
- 41 desks is a big surface area from a very new repo with a small star/fork base; expect rough edges, and expect the brand-fit axis to be the weakest scorer because it has no way to know what our brand actually values.
- It will happily produce competent, generic output and grade it 8.6. Nothing in the loop rewards distinctiveness beyond an "originality" axis that a model is bad at judging.

**Should we...**
- ✅ **Adopt it**

**Why:** This is the first thing in months that turns "AI design workflow" from a prompt-craft trick into process discipline, and our process is where the ceiling actually is. The parts worth adopting aren't the models — it's the separation of *make* from *judge*, the blind proof pass on rendered pixels, and the eight-axis rubric. Where it fits immediately: residency marketing social creative runs on repeatable formats where contrast, safe zones and copy presence are the difference between premium and amateur, and a pixel proof that fails a card before it ships is worth more than a better prompt. The same proof logic maps onto Sub-I welcome materials — 600px email layouts, type on scale, accent used sparingly. On the Urology Unified Platform UI and the Big Reef Chapter Player I'd use only the rubric and the proof gate, not the generation, because those surfaces have to stay code-native with a real design system; a raster design that "looks right" is a step backwards there. Framed against the slop we're escaping: the failure mode of AI design isn't ugly output, it's *plausible* output that drifts a shade off-brand and gets shipped because nobody measured it — and this repo's entire contribution is instrumentation.

---

### email-design-md (EMAIL.md)
**Link:** https://github.com/kingadow/email-design-md
**Type:** Workflow
**What it is:** A design system for email, written as a file an agent reads before it designs anything. Ships an `EMAIL.md` template (palette with which colour pairs pass contrast, an email type scale, components, layout rules, photography rules, voice, and what each email is *for*), a Figma setup checklist, four Claude Code skills (design, blind review, remix, readiness audit), and a full worked example — a fictional tea brand with a homepage, brand kit and four lifecycle emails, all built and reviewed this way.
**What's good about it:** It respects how email actually breaks. The design skill builds a finished 600px Figma email from components with the subject line and preview text above it and the mobile version beside it — the three viewport decisions that get made last, badly, in most production. The `email-remix` skill is the most valuable one for us conceptually: take an email you admire, keep only its layout, rebuild it in your brand. That is legitimate reference-based art direction with an explicit anti-copying boundary, which is exactly the posture we want toward competitors' creative. And the repo states the number that matters: on a real build, the AI's self-review scored the work 75 while a blind panel scored it 52. Self-review rounds up by more than twenty points. That single data point justifies the blind-critic pattern for anything we hand to an agent.

**Pros:**
- `EMAIL.md` puts the parts of a brand kit that actually govern output — contrast-passing pairs, email type scale, component set — in one file the agent reads first, which is the difference between "close to our brand" and "our brand."
- The blind review skill enforces a structural rule: the critic never saw the build, so it can't rationalise it. Backed by a concrete 75-vs-52 finding.
- `email-remix` gives us a lawful, repeatable way to learn from good email design without copying it — useful for Sub-I communications where there's a real reference set of competitive residency programs.
- Corrections log: any miss that appears twice becomes a standing rule, so the system gets better at *our* brand instead of just better in general.

**Cons:**
- Requires Claude Code plus the Figma MCP server with write access and Figma's own `figma-use` skill. That's a real infrastructure requirement, not a drop-in — and it assumes the design lives in Figma, which ours largely doesn't.
- Six stars. This is one designer's well-documented opinionated system, not something with a community shaking it out.
- Scoped to Shopify/Klaviyo-style marketing email design. Our critical email surface is transactional and internal (reimbursement notices, call-out escalations, schedule changes) where deliverability, plain-text fallbacks and clinical-content constraints dominate. It will not teach us that.
- The worked example is thin enough that you're adopting the *method*, not a proven template library.

**Should we...**
- 👀 **Watch it**

**Why:** The method is more valuable than the repo, and the method is worth having. A single `EMAIL.md` that carries our navy #003da5 accent rule, our contrast-verified pairs, an email type scale, and the "accent is rare and intentional" constraint would end the recurring drift where an agent produces an email that's *almost* on brand — a shade off the navy, accent used three times, a CTA that fails contrast. The blind-critic pattern is the piece I'd adopt fastest, because our own experience says the same thing this repo measured: an agent grading its own work is a bad instrument. Where it fits: Sub-I welcome materials and resident-facing communications are exactly this shape — recurring formats, real brand rules, high stakes for looking institutional rather than improvised. Where it doesn't fit: our internal operational email (reimbursement, call-out, schedule) is judged on getting facts read and acted on, not on craft, and I don't want a Figma workflow injected into a pipeline that should be plain text with data inline. Watch, not adopt, because the infrastructure ask is Figma-MCP-shaped and we'd be building a parallel system against our actual stack — but the `EMAIL.md` idea and the blind review should be lifted into whatever we do build.

---

### BRND ProType
**Link:** https://github.com/brndconsulting/brnd-protype-font
**Type:** Tool
**What it is:** A neo-grotesque superfamily drawn from scratch by BRND (Maracaibo, Venezuela), released free for commercial use under SIL Open Font License 1.1. 49 static styles across Condensed, Normal, Extended and Mono; seven weights 300–900; 21 italics; three variable fonts (weight 300–900 with width 88.1–114.5, plus italic and mono variable); 566 characters per style with kerning, ligatures, automatic fractions, case-sensitive forms.
**What's good about it:** This is a typeface designed by a design consultancy for its own grid system, and it shows in the parts that usually go wrong. The width axis is real and usable — the variable font spans Condensed to Extended with 21 named instances, so you get genuine typographic contrast from one file instead of faux-bold and faux-condensed. It's drawn at low node count specifically so it survives physical output (plotter cutting, embroidery), which is an unusual concern that signals craft rather than a font-flipping exercise. The specimen does the work a specimen should: metro signage, newspaper front page, beer bottles, a museum type-anatomy wall, a four-column text setting at 27/21/16.5/13 px, baseball scoreboard, Orbita space-mission timeline. And the distribution is serious — SHA-256 manifest for every file, FONTLOG, WOFF2 for every style with a ready `@font-face` stylesheet, one zip per release.

**Pros:**
- A real width axis plus seven weights solves the "we only have Inter and now everything looks like a SaaS dashboard" problem without licence fees or a webfont performance penalty.
- Extends our palette honestly: the Urology platform's Inter stays as the UI workhorse, but marketing and editorial surfaces get a type voice that isn't the same voice as the product's chrome.
- OFL 1.1 with a reserved font name, commercial use permitted, self-hostable WOFF2 — no CDN dependency, no per-pageview cost, no licence audit.
- The specimen is a usable art-direction reference in itself: it demonstrates four-column text at small sizes and large-format display settings, which is precisely the range our Sub-I print and residency collateral needs.

**Cons:**
- A neo-grotesque superfamily is not a *distinctive* voice. It's an excellent workhorse; it will not make Big Reef or Montefiore Urology look like nobody else. Anyone expecting the typeface to supply personality will be disappointed — personality still has to come from art direction.
- Released five days ago by an agency whose own site is the primary distribution point; nothing here has five years of rendering history in production, and no independent foundry critique exists yet.
- Version 1.0.2 with a fresh specimen — expect detail fixes to letterspacing and hinting. Installing either static or variable in an app (the README warns against both) is a support detail that will bite somebody on the team.
- 566 characters is adequate Latin, but this is not a family for multilingual clinical or academic text.

**Should we...**
- ✅ **Adopt it**

**Why:** Every premium design system has a typographic idea, and ours currently has one sans doing everything — which is why some of our work reads as "competent software" rather than "art-directed institution." A free superfamily with a genuine width axis gives us contrast without buying a licence: narrow for data-dense or fast-moving surfaces, extended for the display line on a Sub-I welcome cover, condensed for a residency schedule sheet that has to look designed rather than exported. Where it fits: marketing and social creative for the residency program (display plus one weight does more for premium feel than any gradient), Sub-I welcome print, and Big Reef Chapter Player's light theme as an editorial voice distinct from the UI chrome. Where it doesn't: the Urology Unified Platform UI stays on Inter — a product interface is the last place to introduce a width axis, and swapping the UI face would be a regression dressed as a refresh. The honest caveat: this raises our floor, not our ceiling. Type sets the register; art direction still has to earn "premium," and a beautiful neo-grotesque applied without hierarchy discipline is just a nicer-looking default.

---

### Mesh Gradient Generation (agent skill)
**Link:** https://github.com/9929y/mesh-gradient-generation
**Type:** Technique
**What it is:** A bilingual (EN/中文) agent skill for building mesh gradients as *editable native Figma layers* rather than generated raster blobs. It ships art-direction guidance (which colour plays which role, where the main masses sit, where text needs space, how edges merge), four documented palette strategies, six native Figma studies at 1536×1024 with their full construction parameters, plus `grid`/SVG/`code`-rendering fallbacks and a motion note for slow movement or image reveals.
**What's good about it:** The parameters are the argument. Every sample publishes its actual construction: the Sky-inspired study is three curved planes plus two light fields at 125–155px blur; Flower is four translucent planes at 56–85% opacity with 125–160px blur and two reflections; Heightmap warps a multi-peak field and extracts 40 contour levels at 24–38px blur; Multipoint uses eleven Gaussian alpha-mask groups with zero extra blur. That is a *recipe*, not a prompt — reproducible, tweakable, and inspectable. The palette studies hold one composition constant and vary only the colour strategy (monochromatic / analogous / apricot-cobalt / cool-neutral accent) with a dark title zone reserved in the left third, which is a genuinely useful decision-making device: you choose the colour logic once, not the image 40 times. It also cross-references Muller-Brockmann-adjacent grid thinking and includes a 100/150/200px blur comparison for the same study — exactly the kind of side-by-side that teaches judgement rather than providing a look.

**Pros:**
- Reproducible, layer-level recipes instead of prompt roulette: you can dial an exact blur value, opacity, and plane count, and every element stays editable for whoever inherits the file.
- Explicitly designs for text: title-safe space, small-size readability, desktop/mobile crops, contrast protection — the thing generated mesh gradients always get wrong.
- The palette-strategy comparison (one composition, four colour logics) is a decision tool we can reuse for brand consistency across an asset family, not just a one-off background.
- Covers the whole realistic delivery surface: presentations, website heroes, campaign systems, and reference reconstruction, with documented limits (native layers vs. imported SVG vs. bitmap have different editability).

**Cons:**
- The native builder requires "a connected Figma execution tool." We don't have a Figma write/MCP loop wired into our design process, so out of the box this is a reading document, not a working tool. The browser/SVG fallbacks are explicitly uncalibrated against a live render.
- Mesh gradients are the most slop-adjacent surface in the entire craft. Done badly — and most of the internet does them badly — this is the purple-blue AI haze we are actively trying to look nothing like.
- 40 stars, single contributor, bilingual docs written partly for agent consumption; the parameter tables are honest but the "verified in real Figma" claim covers the six native studies and not much else.

**Should we...**
- 👀 **Watch it**

**Why:** This is the correct *way* to think about gradients and the wrong *look* to adopt wholesale. The slop we're escaping has a specific anatomy — a purple-to-blue mesh from the top-left, chrome blobs, an "8k" prompt as a substitute for a decision — and this repo's contribution is to replace that with explicit, art-directed construction: how many masses, at what opacity, at what blur, and where the title goes. Where it fits: the Big Reef Chapter Player's light theme and Sub-I presentation covers can use a two-or-three-mass field in one accent family as a *material* rather than a decoration, provided the palette is derived from our own navy-and-paper logic instead of the repo's blue/apricot samples. The reserved-text-zone discipline is the part worth lifting immediately regardless of whether we ever install anything. Where it doesn't fit: the Urology Unified Platform UI, where a premium dark surface with one accent should not have a mesh anywhere near it, and any marketing surface where a gradient is compensating for the absence of a photograph. Verdict is watch because the resource is genuinely good and the infrastructure to use it natively isn't ours yet — but read the parameter tables now and treat them as a written standard for how we do background fields.

---

### MOSS-Image-Edit-HQ (v5 / v6 checkpoints)
**Link:** https://huggingface.co/akhaliq/MOSS-Image-Edit-HQ
**Type:** Tool
**What it is:** A community fine-tune of OpenMOSS-Team's MOSS-Image-SFT — an instruction-based image-editing LoRA — that publishes every experiment, checkpoint and side-by-side eval, including the ones that lost. Recommended checkpoint is `armV5` (full scene captions, masked loss with `inverted_mask_prior`, preservation contracts, 256-token reference budget); loads natively in ComfyUI past v0.42.1 and is a drop-in replacement for the widely used `chinoll/Moss-Image-Edit` adapter.
**What's good about it:** The published failure analysis is the valuable artifact. V1 lost its own eval gate and the author says so plainly, with the diagnosis: their training targets were *restructured* versions of sources, so the model learned to restructure rather than to edit surgically — subjects morph, unrequested mood shifts appear. The v4 fix is the right one for design work: masked loss plus an inverted mask prior means unedited pixels stay at source colour, which directly attacks the two things that make AI editing unusable on a client asset — whole-image drift and saturation creep. The 50-step-vs-8-step comparison is equally blunt: the speed LoRA softens, object additions weaken, colour containment degrades, a red cast creeps in. Use 8 steps for drafts, 50 for final. And the credit line for the one genuine design-relevant capability — "can it relight a scene without changing the people? Yes, dramatic relighting is one of its strengths" — is testable.

**Pros:**
- Preserves what matters in a client asset: reference up to 1024px, edits driven by natural instruction, and preservation contracts specifically to stop unasked-for changes to the parts you approved.
- The eval methodology is unusually trustworthy for open-weight tooling — blind side-by-side rows from held-out data, honest losses, superseded versions kept for reproducibility.
- Practical iteration story: 8-step draft mode for exploring directions, 50-step CFG 3 for finals, with the trade-off documented rather than hidden.
- Drop-in compatible with an existing, widely-used LoRA's workflows, so the switching cost is one file swap.

**Cons:**
- Needs ~20GB+ VRAM in bf16. There is no 6GB answer, and this does not run anywhere near our current tooling. "Local GPU only" means it's not a team capability, it's a workstation capability.
- It's an edit model, not an art director: it will faithfully execute "make the sky warm" and has nothing to say about whether that's the right decision.
- Multi-reference compositing — putting a person from one photo into another scene — is explicitly not trained for, which is the single most common thing our creative needs (faculty portraits into designed layouts).
- Community fine-tune of an Apache-2.0 base on GPL-3.0-adjacent plumbing; licence hygiene on a hospital-adjacent brand asset needs an actual check before anything ships. And v6 exists but is not recommended — the repo is moving fast enough that pinning a version matters.

**Should we...**
- 👀 **Watch it**

**Why:** The reason to watch this isn't that we need a ComfyUI rig — it's that the problem it's solving is our problem. Our faculty-photo workflow has exactly the failure mode this repo diagnoses: an agent or model asked for "crop it tighter and warm it up" returns a *different* person, a different skin tone, and a slightly different jacket. Surgical, preservation-constrained editing is the missing primitive for putting real people into designed layouts without losing them. Where it fits eventually: residency marketing and Sub-I collateral built from the 28-clip faculty library and still frames — relighting a frame to match a layout's light, extending negative space so a headline can breathe, without restaging the subject. Where it doesn't: anywhere near Montefiore patient data, and not as a driver of brand look — a model this literal is a retoucher, and retouching was never our bottleneck. Skip-adjacent flags worth naming: it is 100% instrumental slop if used to generate rather than correct, and the licence chain is unverified. Watch the *technique* — masked-loss preservation — because that's the principle we should demand from every image tool we touch: nothing you didn't ask to change changes.

---

## Slop Radar

- **"Generated" instead of "directed."** Canva Craft and every prompt-based model now produce hierarchy that *looks* intentional because the training corpus had hierarchy. The tell isn't the image — it's that nobody can tell you which decision was ours. Any asset we can't defend a decision on is slop, however pretty.
- **Self-graded quality scores.** This is the sharpest new one: an agent reviewing its own design rounds up (75 vs. 52 in a documented case), and pipelines that report "8.6/10, shipped" are laundering slop behind a number. Never trust a score from the same model that made the thing.
- **The Canva look as a "model breakthrough."** Training on platform templates produces the visual grammar of templates. Expect a wave of creative that is technically excellent and instantly recognizable as made-in-a-tool — the 2026 version of the stock-photo smile.
- **Mesh gradient as default hero.** Now easier than ever to generate and still the fastest way to make a premium brand look like a 2023 startup. A gradient is a material decision; if it can't name its masses, its roles, and where the title goes, it's decoration.

## Overall Assessment

The centre of gravity moved this week from *generating* to *governing*, and that is the best news for anyone trying to escape slop. Canva's Craft puts a planning stage in front of rendering so composition becomes a spec rather than an accident; Desk Studio puts an art director, a pixel-level proof pass and a sign-off rubric around generation; EMAIL.md puts the brand rules in a file the agent must read and then hires a blind critic to grade the result. Each is a different answer to the same realisation: the models got good enough that the remaining quality gap is process, not capability. The honest counter-current is that these tools also make mediocre work cheaper and more shareable than ever, and the failure mode has changed from "ugly" to "plausible and off-brand" — which is harder to catch and much harder to argue about in a review. The single highest-leverage move for Shareef this week: institute the blind proof pass before adoption of anything else. Take our most repeatable surface — residency marketing social creative, five cards we've already shipped — and check each one the way Desk Studio's proof stage does: contrast measured on rendered pixels, safe zones, every line of copy present, palette and type scale compliance, scored by someone who didn't make it. Whatever that pass catches in work we already consider finished is the real size of the problem, and it costs nothing but an afternoon.
