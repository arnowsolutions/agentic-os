# AI Design Intel — November 27, 2026

Sources scanned: X (**reachable via web search — four `site:x.com` queries returned ~30 posts, and seven status IDs were decoded to real timestamps rather than trusting search order; only two in-window posts surfaced: @igus_ai 23 Nov 20:55 UTC on Linen's designer → image model → LLM split, and @pwnies 23 Nov on Linen's relaunch. @ideogram_ai 17 Nov, @hakimieiqbal 11 Nov, @ycombinator 7 Aug and @reactiverobot 26 Aug were all outside the window; no other fresh craft post cleared the bar**). Reddit (**JSON API blocked on all six subs, eleventh consecutive run — `graphic_design`, `web_design`, `UI_Design`, `midjourney`, `StableDiffusion`, `FigmaDesign` each returned the identical 190,240-byte HTML challenge page to one polite request with a browser UA; `web_search` fallbacks for r/graphic_design and r/UI_Design returned no in-window thread with a verifiable date**). HN (**Algolia `search_by_date` for `design`, `AI design`, `generative design`, `typography`, `AI slop`, `Figma`, `graphic design` — ~120 stories read with points and dates; in-window candidates included the Joonoo comic, evancz's language-design essay, the Mozilla Nova UI thread and the "AI slop is a tax" talk**). GitHub (**REST `ai design created:>2026-11-20` = 1,933 results, top 15 read; topic sweeps `design-tools` 36, `typography` 78, `figma` 77, `image-generation` 160, `generative-art` 197, `creative-coding` 196 — almost entirely YouTube thumbnail generators, Windows app mirrors and template farms; no repo cleared the bar**). Google News (**eight feeds, ~250 items**: AI design tool, art direction AI, typeface design, brand identity design, Figma AI, AI slop design, graphic design AI, Adobe AI design — ~20 in-window after parsing `pubDate`). Plus the last30days aggregator (HN 8, web news 8 — mostly stale 2023–2025 results). Candidates considered: 22 opened and judged, ~240 headlines, posts and repo descriptions skimmed. Passed the bar: 7.

**Screened and dropped, with reasons:** *Caixa × Tátil* (Brazil's first redesign in almost 30 years — kept the name, the X and the blue/orange, redrew the typeface and folded 50+ sub-brands into one system, launched 9 Nov; genuinely excellent equity-preserving work, but 18 days old and no AI angle); *Envato's Beyond the Hype survey* (n=1,033 across 103 countries, published 10 Nov — taste outranks prompting 53% to 19%, only 5% of discarded AI concepts were dropped for "lacking soul"; strong data, but 17 days old and already in circulation); *No AI Slop Manifesto* (published 13 Nov at AIE Code Summit, the best definition of slop this month — "slop is when we put less effort into producing something than we ask the consumer to spend understanding it" — quoted in Slop Radar, but outside the window); *Foundry Lineu* (a 7×6 grid typeface from transport information boards, with a variable weight axis and an OpenType background grid — but the face has been in market since at least April 2026); *Turner's House × Stop, Look and Listen* (a T+H window monogram, muted palette, photography shot through panes and a secondary typeface across "Romantic / Revolutionary / Misunderstood" — 27 Nov, clean but too small for a full item); *module.build* (a Ukrainian senior designer's own AI editor — multi-provider, ComfyUI under the hood, point-query MCP instead of whole-screen context — 26 Nov, but closed alpha with no artifact); *Claude Design coverage* (26 Nov Arabic outlet recycling an April 2026 launch — stale); *Adobe MAX agentic coverage* (agents orchestrating the Creative Cloud chain, no finished artifact to judge); *"Web designers share how they've adapted to AI in 2026"* (26 Nov syndicated panel, no method, no sample); *Crystal Palace AI stadium* (25 Nov — Slop Radar, not an item); *Joonoo's 24-page comic* (24 Nov — Slop Radar); *"AI slop is a tax you make other people pay"* (26 Nov — context, not a finding); *Verve × Zero* (**previously covered 21 Nov; new: Design Week's 25 Nov piece reveals illustrator Kevin Lebon's hand-drawn landscapes were processed through Figma Weave to generate further scenes "within the established art direction" — significant workflow detail, but the identity was already judged, so no re-judgment**); *Figma Weave itself* (node-based AI workflows are from Config 2026, not new this week).

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| NYT bans Photoshop 2027 | Idea | ✅ Adopt it | The unit of risk is the delivered file: if it carries an AI tag, the photo is compromised no matter how little was changed |
| Real Madrid × Adobe Firefly | Workflow | ✅ Adopt it | Capture the real assets first, then generate only the impossible — the correct order of operations for clinical and campaign imagery |
| Deutsche Bahn × Ogilvy — 100% AI | Work | 👀 Watch it | One strong visual rule, but "100% AI" is a production boast, not a craft standard — and a hospital cannot afford it |
| Linen | Tool | 👀 Watch it | Diffusion for the visual, LLM for the code attacks the generic-mean problem; the output is still a picture, not a component |
| PRINT × Eric Snowden | Idea | ✅ Adopt it | "You can use AI without ever generating anything" — QC and prepress are the highest-return, lowest-risk use |
| FutureBrand — brand behaviour | Idea | 👀 Watch it | Machine-readable brand rules are the right architecture for AI-generated output; the proof is still a consultancy deck |
| ALIA — analogical reasoning study | Technique | 👀 Watch it | Generate analogies, not solutions — rigorous for novices, unproven for professionals |

For EACH item, the FULL deep breakdown:
---
### NYT bans Photoshop 2027
**Link:** [theverge.com — The New York Times warns photographers not to update Photoshop over AI features](https://www.theverge.com/ai-artificial-intelligence/1041227/the-new-york-times-warns-photographers-not-to-update-photoshop-over-ai-features) · [dpreview.com — NYT tells photographers not to use the latest Photoshop](https://www.dpreview.com/news/new-york-times-adobe-photoshop-2027-restriction-ai/) · [petapixel.com — NYT prohibits Photoshop 2027](https://petapixel.com/2026/11/24/new-york-times-prohibits-photographers-from-using-photoshop-2027/) · published **24 November 2026**
**Type:** Idea (a provenance policy, not a tool)

**What it is:** On 24 November, *The Verge* reported an email from the *Times*' photography leaders **Meaghan Looram** and **Josh Haner** telling contributing photographers to avoid **Adobe Photoshop 2027 (release 28.0.0 and subsequent updates)** on assignment. The reason is not that the software edits photographs; it is that some features use generative AI "in ways that may not be apparent to users," and that using them "can result in metadata identifying photographs as AI-generated." A *Times* spokesperson, Graham James, confirmed the requirement. The November Photoshop update added an **AI Assisted Editor** view, an AI assistant, prompt-based image transformation, new AI upscaling and an AI tool that recomposes images for different canvas sizes. Adobe began rolling out **C2PA** content credentials across its apps in August.

**What's good about it:** The distinction is precise, and almost everyone covering this has missed it. The *Times* is not banning AI editing in principle; it is banning a **version whose AI is invisible and whose metadata is blunt**. That is a mature position: the newsroom is not arguing about aesthetics, it is protecting the chain of custody. Second, it puts the burden where it belongs — on the tool vendor, not on the individual photographer remembering which menu item is generative. Third, it is a real newsroom with real consequences, not a think piece; the policy has teeth because assignment work depends on it. Fourth, the C2PA angle is the part that generalises: the label does not know whether you used Generative Fill on a whole building or an auto-selection tool on a hem, and a blunt label is still a label.

**Pros:**
- **Defines the unit of risk as the delivered file, not the intent.** A photograph that carries an "AI-generated" tag is compromised for editorial use regardless of how little was changed — which is exactly the standard a hospital should hold clinical and press imagery to.
- **Exposes the gap between "AI feature" and "AI effect."** Auto-selection, upscaling and recomposition can trigger the same provenance label as a generated scene, so "I only used the healing brush" is not a defence.
- **Gives an operational lever, not a vibe.** Pin the version, keep a separate retouch path, check the metadata before publish — all implementable this week without a new tool.
- **The receipt is a named policy from a named institution**, not a survey or a vendor claim.

**Cons:**
- **The *Times* has not named the specific offending features**, so the ban is broader than the published evidence. That is prudent for a newsroom and hard to implement precisely for everyone else.
- **C2PA metadata is a blunt instrument.** It can label a minimally cropped photograph as "AI-edited," which erodes trust in the label itself and punishes honest minimal retouching.
- **A version ban ages badly.** The next release may fix the metadata behaviour, and the policy then has to be rewritten — a feature-level rule would travel further.
- **It does not cover the real exposure:** AI features inside Lightroom, Capture One, phone pipelines and third-party plugins, which the *Times* policy leaves untouched.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling

**Why:** Apply the *Times* rule to Montefiore's photography before the next campaign ships. The 28 faculty interview clips, the OR and clinic photography, the Sub-I headshots — these are the receipts for every claim the residency programme makes, and a single file tagged AI-generated in a campaign undoes the credibility of every real photograph next to it. The policy writes itself: originals stay in a read-only archive; retouching happens on a pinned, non-generative path; no Generative Fill or Expand on patient-adjacent or press imagery; a C2PA/metadata check before anything goes to web, social or print; synthetic people, synthetic clinical spaces and synthetic instruments are banned outright. On the Unified Platform, hero imagery must be real photography — if we need an impossible image, it is illustration with a credit, not a synthetic photograph. This is the cheapest trust insurance available, and it costs one page and one conversation with the media team.

---
### Real Madrid × Adobe Firefly
**Link:** [blog.adobe.com — How Adobe Firefly took Real Madrid to the Moon](https://blog.adobe.com/en/publish/2026/11/25/how-adobe-firefly-took-real-madrid-to-moon) · published **25 November 2026**
**Type:** Workflow (a production case study)

**What it is:** A campaign for Real Madrid timed to the new kit launch and the start of La Liga, made with **Adobe Firefly** by creative director **Jan Gensch** and director **Joffrey Jans**. The story follows a young supporter from her family's living room into a fantasy where players sprint through clouds, rise alongside flying whales and kick a flaming football on the moon. The production had **less than a month** from storyboard to shoot and edit, and **45 minutes with the players**. The team built a photography studio to capture each player's likeness accurately, brought those stills into Firefly as references alongside images of the new Adidas kit and match ball, used **Kling** inside Firefly for the cloudscapes, metallic wings and lunar surface, shot the girl and the fans in a separate live-action unit, used **Premiere Pro** to add missing seconds without a reshoot, and extended the same visual world into static banners, secondary films and short social cuts.

**What's good about it:** This is the correct order of operations for AI-assisted campaign imagery, and it is rare to see it documented by the vendor. **The real photograph is the anchor, not the thing to be discarded.** The 45-minute constraint is the art direction: it forces a reference library, a shot list and a decision about what must be real before anyone opens a generator. Second, the division of labour is honest — players' likeness, the kit and the fans are captured; clouds, wings and the moon are generated. Third, the film is finished in the edit, not in the model: adding seconds in Premiere is a production decision, not a generation decision. Fourth, the stills become a system — banners, cutdowns, social — which is how a campaign actually ships.

**Pros:**
- **A clear rule: capture the irreducible real assets first, then generate only the impossible.** That rule alone would improve most AI-assisted campaign work.
- **Reference-locked likeness and kit accuracy** — the difference between a campaign and a lookalike, and the part most AI case studies skip.
- **A production system, not a one-off image.** The same photo session feeds static, video and social, which is where the efficiency claim becomes credible.
- **The constraint story is useful:** 45 minutes with the talent is a better brief than "make it epic," because it forces prioritisation.

**Cons:**
- **It is Adobe's own blog**, so the claims are self-reported and the workflow is designed to sell Firefly and Kling. There is no independent craft review.
- **"Accurate likeness" is asserted, not proven at full resolution.** The failure mode — uncanny faces, wrong kit details, plastic skin — is exactly what the case study does not publish.
- **The fantasy visuals are the easiest thing for AI to do and the least brand-specific.** Flying whales and a flaming football could belong to any sports brand; the craft is in the player portraits, which are the least AI-dependent part.
- **No cost or timeline numbers**, so "less than a month" and "lower costs" cannot be verified.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling

**Why:** This is the template for the residency campaign and the Sub-I welcome materials. Shoot the real people first — faculty, residents, the OR, the clinic, the actual building — with consent and rights sorted, and build a reference library that any generator must use. Then use AI only for the impossible: the metaphor, the scale, the motion. For the 28 interview clips, the real frame and the real name are the anchor; AI can extend the world around them, never replace them. On the Chapter Player, the same principle: real cover assets, AI only for texture or motion. The line to write into every brief is absolute: **no synthetic person, no synthetic clinical space, no synthetic instrument.** What is worth copying is not the fantasy; it is the discipline of deciding what must be photographed before anyone types a prompt.

---
### Deutsche Bahn × Ogilvy — 100% AI
**Link:** [ogilvy.com/de — Deutsche Bahn and Ogilvy bring new long-distance Sprinter services to life – with 100% AI](https://ogilvy.com/de/eng/ideas/deutsche-bahn-und-ogilvy-inszenieren-neue-sprinter-verbindungen-fur-den-personenfernverkehr) · coverage [horizont.net — Diese Bahn-Kampagne für den Sprinter ist komplett KI-generiert](https://horizont.net/marketing/diese-bahn-kampagne-fuer-den-sprinter-ist-komplett-ki-generiert-663132) · announced **23 November 2026**
**Type:** Work (a campaign and the production method behind it)

**What it is:** Deutsche Bahn's long-distance campaign for the **13 December timetable change**, produced entirely with AI-generated imagery by **Ogilvy Germany** with production company **27km** and directing duo **KRONCK**. The films visualise the new ICE Sprinter services as a force that distorts the world: a high-speed train thunders past and spooks the horses of the Quadriga on the Brandenburg Gate; the Eiffel Tower is twisted by the slipstream; sailboats off the Elbphilharmonie are tossed in the train's wake. The campaign is live across Germany on TV, out-of-home, social and digital. DB says its earlier AI-produced "Magic Moments" pilot scored **above average in ad tracking** for differentiation, likeability, relevance and activation, and that respondents rated the quality of the AI visuals positively.

**What's good about it:** The visual rule is genuinely good: **one physical law — speed distorts the world — applied consistently.** That is a system, not a collection of pretty frames, and it makes an abstract service improvement (20 minutes faster, more frequent) visible without a diagram. It also commits: 100% AI, no hybrid hedging, which forces the idea to carry the work rather than a celebrity or a location. And the idea is tied to the product truth — new routes, faster journeys, a Europe closer together — not to the tool. The craft reference is clear: the distortion is a visual metaphor for speed, not a random surreal flourish.

**Pros:**
- **One rule, many executions:** every frame is the same joke, escalated. That is how a campaign coheres across TV, OOH and social without a layout template.
- **The concept is product-led**, not tool-led: it would still work as an idea if it had been shot practically with miniatures.
- **The production method let them attempt images a shoot could not afford** — twisting the Eiffel Tower, spooking the Quadriga — which is a legitimate creative argument for AI.
- **They published the method**, which is more honest than hiding it and gives the industry a real case to argue with.

**Cons:**
- **"100% AI-generated" is the headline**, which means the production method is doing the marketing work. The idea is strong enough not to need the boast, and the boast invites the wrong conversation.
- **No human photography means no anchor of reality.** For a transport brand, the trains and the cities are the product; synthetic trains and synthetic landmarks are a credibility risk that a sportswear fantasy does not have.
- **The ad-tracking claims are self-reported and vague** — "above average" on four metrics, with no numbers, sample or methodology.
- **The distortions are a one-note visual.** The second campaign in this system will feel like the first, and the third will feel like a template.

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** The rule is adoptable; the production choice is not. A "speed distorts the world" concept could work for Montefiore on faster clinic flow, shorter waits or a new OR suite — one physical law, applied across every frame, is a strong art-direction system that a small team can execute consistently. But a hospital cannot go 100% synthetic. The trust asset is the real OR, the real faculty, the real patient experience, and a generated hospital is a liability in a way a generated Eiffel Tower is not. Watch this because it is the clearest test case of whether a fully generated campaign can carry a serious brand: if DB's tracking holds over a second wave, the production economics will be hard to ignore. For now, take the rule and leave the method — and note that the most interesting thing in the campaign is the discipline of the concept, not the absence of a camera.

---
### Linen
**Link:** [linen.ai](https://linen.ai/) · [siliconflorist.com — Can diffusion models design more effectively than LLMs? Linen is betting on it](https://siliconflorist.com/2026/11/24/can-diffusion-models-design-more-effectively-than-llms-linen-is-betting-on-it) · primary [@pwnies, 23 November](https://x.com/pwnies/status/2124965297144897686) · relaunch **23–24 November 2026**
**Type:** Tool

**What it is:** Linen is a **diffusion-based UI design tool**, relaunched on 23 November by founder **Jacob Miller** (the Show HN post is titled "I left Figma to build a diffusion-based UI design tool"). Its thesis is specific: LLMs are trained on code patterns, so when they approach frontend design by writing code, "it ends up resulting in designs that approach the generic mean." Diffusion models generate the interface as an image instead, which can preserve visual specificity. The new version adds **Sections** for longer scrolling pages, the ability to **learn a design from screenshots** of an existing site, **"Copy for agent"** which turns a design into a build skill any agent or codebase can use, a **Build** button that hands designs to a coding agent, and a **ChatGPT plugin**. Pricing is per design — 19¢ individual, team from $50/month.

**What's good about it:** The diagnosis is the most useful sentence in the tool space this week, and it is exactly the Unified Platform's problem: **code-first models regress to the mean.** Diffusion as the design engine, with the LLM downstream as the builder, is the right order of operations — the image model sets the visual direction, the code model implements it, rather than the code model deciding what the design is allowed to be. "Learn from screenshots" is a direct route to brand-specific output instead of a blank canvas, and "Copy for agent" acknowledges the only thing that matters: the design has to survive into code. The agent integration is also the right distribution model — the design lands in the repo, not in a screenshot folder.

**Pros:**
- **Attacks the root cause of generic AI UI** — the code-model prior — rather than adding another prompt wrapper on top of the same engine.
- **Learns from existing screenshots**, which is how you get an on-brand starting point rather than a template with your logo dropped in.
- **Separates design generation from build**, so the visual direction is not determined by what is easy to code.
- **Agent-native output:** "Copy for agent" and the Build button treat the design as an input to a pipeline, not a picture to be exported and recreated.

**Cons:**
- **Diffusion UI output is still an image.** Responsive behaviour, real content, accessibility, component states and interaction are downstream and unproven.
- **"Learn from screenshots" can clone the current design's flaws as faithfully as its strengths.** It has similarity, not taste, and it cannot tell you which of your existing patterns are the good ones.
- **The evidence is the founder's blog and a relaunch** — no independent craft review, no before/after on a real product, no published failure cases.
- **Per-design pricing encourages volume**, which is the opposite of the "fewer, better" discipline this brief keeps arguing for.

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** The Unified Platform's problem is not "can AI make a screen"; it is "can AI make a screen that looks like ours and not like a dashboard template." Linen's answer — diffusion for the visual, LLM for the code — is the most credible architectural answer I have seen this week, and it maps directly onto the platform's premium dark surface, single accent and Inter-based system. But the output is a picture, and the platform needs components, states, accessible markup and responsive behaviour. Test it on a low-stakes, high-visibility surface first: a Sub-I welcome one-pager or a residency campaign landing page. Give it three screenshots of the existing system, ask for one screen, and judge whether the result is distinguishable from the template. If it is, it is a real tool; if it is not, it is a faster way to make the same generic thing.

---
### PRINT × Eric Snowden
**Link:** [printmag.com — Adobe's Eric Snowden on How AI Is Changing the Way Designers Work](https://printmag.com/design-events-conferences/adobes-eric-snowden-on-how-ai-is-changing-the-way-designers-work) · published **25 November 2026**
**Type:** Idea (a working division of labour)

**What it is:** An interview with **Eric Snowden**, Adobe's Senior Vice President of Design, after Adobe MAX, about where AI actually belongs in a designer's day. His examples are all assistive, not generative: an agent that **lays out images or checks brand colours** while the designer works elsewhere in the same document; an **InDesign check for print-readiness**; an **After Effects agent** that roughs out an animation, which Snowden then adjusts keyframe by keyframe and asks to retime from 20 seconds to 10. His line: **"You can use AI without ever generating anything."** And his standard: **"It's now easier than ever to make something above average. I don't think it's any easier to make something great, frankly."**

**What's good about it:** It draws the line in the right place — AI as production QC and prepress, not as the author. The examples are boring in the best way: palette checks, image resolution, print readiness, retiming. Those are the tasks that get skipped at deadline and cause the most damage, and they are exactly where an agent has an advantage over a tired human. The "above average vs great" distinction is also a usable review standard: the floor has risen, the ceiling has not, and the job is still to get to the ceiling. Snowden also describes Disney building a custom model from its archive and a smaller studio starting with a logo, a typeface and a few colours — a realistic ladder of adoption rather than a binary.

**Pros:**
- **Reframes the value proposition from generation to verification** — a much better fit for regulated, clinical and brand-governed work.
- **The examples are specific and implementable this week:** palette audit, print-readiness check, resolution check, retiming.
- **The "above average is easy, great is not" line gives design review a clear language** for what AI can and cannot certify.
- **Keeps the designer in the file:** the agent acts, the human inspects, keyframes stay editable, and nothing is baked into a flattened output.

**Cons:**
- **It is Adobe's design chief speaking about Adobe's tools**, and the examples are demos, not measured outcomes.
- **"AI without generating anything" still means an agent reading and acting on your file.** The permission model, the audit trail and the rollback are unaddressed.
- **The interview accepts the efficiency frame too easily.** The same time saved can be spent on more versions rather than better work, and Adobe benefits either way.
- **No discussion of what happens when the QC agent is wrong** — the false negative is the dangerous case, especially in print and clinical work.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling

**Why:** This is the highest-leverage, lowest-risk AI use for Shareef's surfaces, and it can start before any new tool is bought. On the Unified Platform, an agent can audit every route for token drift, contrast failures, missing alt text, inconsistent spacing, stale components and broken responsive states — the boring checks a small team skips when it is shipping. On marketing, it can check every artboard for the approved navy, the right typeface, image resolution, crop safety and photo rights before anything goes to print or social. The "above average vs great" line belongs in the design review itself: the agent can tell you it is above average; only a human can tell you it is great. And the After Effects example is the model for the Chapter Player and campaign motion — let the agent rough it out, then adjust the keyframes yourself.

---
### FutureBrand — brand behaviour
**Link:** [futurebrand.com — Unmistakable brand behaviour for brands to own their futures](https://futurebrand.com/thinking/a-new-positioning-for-futurebrand) · coverage [designweek.co.uk — The Outline, 23/11/2026](https://designweek.co.uk/the-outline-futurebrand-relaunch-gta-vi-heist-kits-and-a-dalek-23-11-2026) · relaunch **17 November 2026**, coverage **23 November 2026**
**Type:** Idea (a brand-system architecture)

**What it is:** FutureBrand relaunched after 27 years with a positioning built on **"unmistakable brand behaviour"**: the way a brand looks, moves, talks, sounds and occupies space, and increasingly **how an AI trained on it makes decisions**. The claim is a shift from static identity systems — a kit of parts with rules for consistent use — to living, **machine-readable frameworks that train AI tools and guide people**. Its own identity applies the method: an angled **F** that works as a flexible system rather than a fixed mark, a slanted wordmark, a proprietary typeface called **Future Display**, dynamic box assets derived from the F, and a sonic identity drawn from the phonetics of the name. A report, *From Artefact to Infinite: The End of the Finished Brand*, was published on 18 November.

**What's good about it:** It names the real design problem of the next few years: **a PDF brand guideline is useless to an agent.** If the AI is generating the social post, the slide or the campaign variant, the identity has to exist as rules, examples, tokens and constraints that a model can consume. "Brand behaviour" is also a smarter frame than "brand consistency" because it allows flex while staying recognisable — which is exactly what a multi-surface department needs. And they applied it to themselves, which is the minimum proof: typeface, motion, sound, language and a published report as one system. The machine-readable framing is the part worth stealing even if the identity is not.

**Pros:**
- **Correct diagnosis:** static identity systems cannot govern AI-generated output at volume, and most brand teams have not admitted it yet.
- **"Machine-readable frameworks" is the right architectural direction** — tokens, rules, examples, do/don't and prompt packs, not another 80-page PDF.
- **The behaviour frame handles variation without falling back to rigid templates**, which is the only way a department-wide social programme stays coherent.
- **A complete demonstration:** typeface, wordmark, motion, sound and report shipped together, so the thesis is visible rather than asserted.

**Cons:**
- **It is a consultancy relaunch selling a methodology.** There is no client case study showing the framework actually controlling AI output at scale.
- **"Machine-readable" is asserted, not specified** — no schema, no example of an agent consuming the system, no measurement of whether it reduces drift.
- **Brand behaviour can become a licence for inconsistency** if the rules are not measurable; "flex" is doing a lot of work in the argument.
- **The identity itself is pleasant but not distinctive enough to prove the thesis.** An angled F and a slanted wordmark are a competent refresh, not evidence that a new model works.

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** The Unified Platform already has the bones of this — tokens, components, a single accent, Inter, SVG icons — but the marketing and social side is where brand drift actually happens, because that is where people outside the design system generate the work. The next step is to write Montefiore Urology's brand as a machine-readable behaviour spec: approved palette with roles, type scale, photography rules (real only, no synthetic patients or spaces), composition rules, motion rules, and a prompt pack any agent must consume before generating a post, a slide or a landing page. That is more useful than another guideline document, and it is the only way a department-wide social programme stays coherent when multiple people are generating. Watch FutureBrand because the direction is right but the proof is not there yet; steal the framing, not the identity.

---
### ALIA — analogical reasoning study
**Link:** [bioengineer.org — AI Synectic Triggers Elevate Novice Design Novelty in Controlled Ideation Trials](https://bioengineer.org/ai-synectic-triggers-elevate-novice-design-novelty-in-controlled-ideation-trials/) · paper: Kokate, R. & Onkar, P. (2026), *Design Science* 12, e4 · [doi.org/10.1017/dsj.2025.10044](https://doi.org/10.1017/dsj.2025.10044) · reported **26 November 2026**
**Type:** Technique (a facilitation method with evidence)

**What it is:** A controlled study at **IIT Hyderabad**, published in *Design Science*, testing whether structured analogical prompts from an LLM improve design ideation. Twenty-four first-year design students in two-person teams tackled six briefs; experimental teams used **ALIA**, a desktop application that transcribes the room's discussion and injects **synectic and dialectical prompts** (direct analogy, personal analogy, fantasy analogy) at staged intervals, while control teams used standard internet and generic chatbots. Six industry raters with 10+ years' experience scored 36 concept sheets on novelty and quality. ALIA teams scored significantly higher on **novelty** (mean 3.31/5, p < 0.05) with **no significant loss of feasibility or usefulness**. The paper also benchmarks LLMs on an Analogical Creativity Task: GPT-4o produced the most novel analogies (3.445), ahead of Claude 3.5 Haiku (2.556) and Mixtral-8x7B (2.334).

**What's good about it:** It isolates a specific, teachable use of AI — **generating analogies, not solutions** — and measures it against a control. The finding that novelty rises without a feasibility penalty is the useful part, because most "AI ideation" claims show volume, not quality. The ALIA design is also smart: it listens to the room and intervenes at stages, rather than being a chatbot on a laptop that everyone ignores. And the benchmark is a real attempt to measure creative output with expert raters, not a preference survey. The stage structure — problem definition, keywords, analogies, synthesis — is directly reusable in a workshop without any software at all.

**Pros:**
- **A concrete technique:** prompt for cross-domain analogies, not for finished concepts, and do the synthesis yourself.
- **Controlled design with expert raters and reported statistics**, not a vendor survey or an anecdote.
- **The stage structure is directly reusable** in a residency campaign or Sub-I workshop, with or without ALIA.
- **Separates novelty from quality**, which are the right two axes for judging ideation — and shows you can gain one without losing the other.

**Cons:**
- **Twenty-four first-year students is a small, novice sample.** Professionals with entrenched heuristics may not benefit the same way, and the paper says so.
- **The models are dated** — GPT-4o, Claude 3.5 Haiku, Mixtral-8x7B — so the benchmark says little about 2026 tools.
- **Text-only interaction:** no visual or spatial ideation, which is most of brand, UI and campaign work.
- **The effect is modest** (3.31/5 versus control) and the study is a single site with a single facilitation protocol.

**Should we...**
- 👀 **Watch it** — promising, not proven yet

**Why:** The technique is worth stealing even if the tool is not. In the next residency campaign ideation session, do not ask the model for "10 campaign ideas about urology"; ask it for analogies from outside medicine — what is a ureter like in architecture, music, cartography, or the post office? — and then do the synthesis yourself. That is what ALIA automates, and it is the opposite of the slot-machine prompt: the model widens the search space, the designer chooses. For the Sub-I welcome materials, the same move: generate metaphors for the transition from student to surgeon, then design the artifact. Watch it because the evidence comes from novices and older models; but the method is free, low-risk, and it fits the "AI as a thinking partner, not an author" position this brief keeps taking.

---

## Slop Radar
- **"100% AI" as the headline.** When the production method is the campaign, the idea is usually thinner than the claim. Deutsche Bahn's films are the test case: a strong visual rule, but the boast is doing the work — and a hospital cannot make the same boast.
- **Venue slop with your own name misspelled.** Crystal Palace's AI-generated Selhurst Park post (23 November) rendered "EAGLES" as "EACLES" while announcing a World Cup 2035 host bid. If you do not have a photograph of your own building, the problem is not the model; it is the media operation. (Creative Bloq, 25 November)
- **Template consistency sold as craft.** Joonoo's family-photo-to-24-page-comic pipeline (Show HN, 24 November) keeps faces consistent across pages, which is real pipeline work — but the product is a template with an AI-generated sample family. Consistency is not art direction.
- **The "above average" flood.** Adobe's own design chief says it is easier than ever to make something above average. The tell is a portfolio that looks like the median of its category: polished, on-trend, and forgettable. Polish is now the floor, not the differentiator.

## Overall Assessment
The week split along a single fault line: **provenance versus production**. The *New York Times* banned a Photoshop version because its AI can invisibly tag real photographs as synthetic; Deutsche Bahn and Ogilvy went the other way and made 100% AI the campaign. Between them sits the only defensible position for a clinical brand: real assets as the anchor, AI as a controlled pipeline, and a machine-readable system to keep it coherent. Real Madrid × Firefly shows the hybrid done right — 45 minutes of real photography, then generation only for the impossible. Linen and Snowden point to the tools: diffusion for visual specificity, agents for QC. The single highest-leverage move for Shareef this week is not a tool trial; it is a one-page **AI media policy** for the department — originals archived read-only, no generative fill on clinical or press images, a C2PA check before anything publishes, synthetic people and spaces banned, every AI-assisted asset disclosed internally. Then apply it to the residency campaign and the Sub-I materials. That policy is the difference between using AI and becoming indistinguishable from it.
