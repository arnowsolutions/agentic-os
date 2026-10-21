# AI Design Intel — October 20, 2026

Sources scanned: X (available via web_search, 4 phrasings — surfacing the Figma Config India cluster and the "AI design is overhyped / worse than one-shot" practitioner disagreements; no craft before/after threads with a working artifact inside the window), Reddit (JSON API blocked for the sixth straight day — all six subs return the HTML challenge page; `site:reddit.com/r/graphic_design` web_search fallback returned only opinion and "AI slop got approved over my design" commiseration threads, nothing with a technique or release inside the window), HN (hnrss newest returned two real items — `adriankrebs.ch/blog/design-slop` and `learnui.design`'s "Where's the AI design renaissance?" — before the remaining three queries 502'd; Algolia not needed), GitHub (repos created since 2026-10-13 + topic searches on typography, design-tools, figma, generative-art — rate limit hit once mid-scan, recovered), Google News RSS (design/brand queries), plus last30days-pro for the "AI design tools" one-shot. Candidates considered: 29. Passed the bar: 6.

**Dedupe note:** Figma **Specs** was judged on Oct 17 and is **not** re-covered. Figma Specs, the Figma custom skills (`/better-interface` etc.), OpenPencil, desigma, Figxel MCP, Atlassian DESIGN.md, Solid Glass, Taste Library, Choreon, SlopCop, Awesome UX Skills, CSS Composite Font Workshop, Pablo Stanley's Design Team, MagicOS, the Copilot mark, Kuda/Barkas, Rocastle/Arsenal, Recto Studio, Harshpreet Hand, Pentagram Design Doha, Book Covers, Ochrelle, ArtCraft and Tate McRae are all judged and closed. Two items from today's scan are previous finds with **no new capability** and were not re-covered: OpenPencil now also ships a Codex plugin (`codex-openpencil`, 81★) and Recto Studio continues routine pushes — both are packaging, not new craft, so they stay closed. Two near-misses were explicitly cut rather than padding the list: **Taste Library** (Oct 14 last commit "Audit every TasteLabs result and test complete published coverage" now claims 49★, but nothing new shipped) and **Harshpreet Hand** (39★ now, still just the one font).

## Executive Summary
| Find | Type | Verdict | One-line why |
|---|---|---|---|
| AI Slop Meter (`aislopmeter`) — deterministic slop scan with named rules and `file:line` fixes | Tool / Critique | **Adopt it** | The first slop detector that scores on *measurable craft* — contrast, line length, real type, identical cards — not vibes |
| Golden Temple — 10 procedural shots, 31k lines, every surface hand-specified | Workflow / Idea | **Adopt it** | Proves the model can shoot *lit, framed, graded* imagery when a person writes the brief down as code |
| Krea 3 — regional edits, 2K native, style and character references | Tool | **Watch it** | Right controls for art direction (regional, hex, references) but every speed claim is vendor-measured |
| Pictoplasma × andstudio — an identity that is a ligature and two dots | Idea / Technique | **Watch it** | Type-only brand system whose whole idea is a glyph — a direct repudiation of "generated mascot" thinking |
| Business of Home — AI imagery is reshaping furniture, but the holdouts hold for a reason | Idea / Pattern | **Watch it** | The most credible field report on why "consistent and exact" still beats "fast and cheap" |
| HyperPlasma Skills — 300 styles, 400 pairings, 500 animations, compiled from AI catalogs | Tool | **Skip it** | It is a slot machine with a larger inventory; it replaces one default with 300 defaults |

---

### AI Slop Meter — deterministic slop scoring, with the fixes named

**Link:** https://github.com/omergocmen/aislopmeter
**Type:** Tool / Critique
**What it is:** An MCP server + CLI + bookmarklet (v0.3.2, Oct 17) that crawls a site, a localhost app, a project folder or a single file and scores it 0–100 across five areas using **more than 80 deterministic checks** — not an LLM judging screenshots. With Chrome or Edge installed it opens the page and measures computed colours and real contrast, the fonts actually rendered, how much is centred, whether cards are truly identical, line length, text size, content that spills or hides, and load errors. It writes a report, gives every finding a one-line fix, numbered steps, exact `file:line` locations, a before/after example, a "done when" check, and a copy-as-prompt button — then re-scans and shows a before/after table. Its own stated calibration: 34 real sites, AI-built pages median 25, hand-made pages median 12, and no hand-made page reached 20.

**What's good about it:** The rules list is the most useful artifact here, and several of them are things I would have written down myself. **Template design** checks: purple gradients, glow, emoji and stock icons, the standard landing-page and portfolio templates, Tailwind's default colours, grid backgrounds, **small caps labels above every heading**, **bouncing and pulsing motion**, **cards inside cards**, and drift from your own `DESIGN.md`. That's not a taste opinion — it's an enumerated inventory of the exact cluster our Slop Radar has been tracking for two weeks, written as machine checks. Better still, it inverts the current orthodoxy: "Why rules and not an AI judge? In the largest study so far, LLMs asked 'is this slop?' agreed with human editors at κ ≈ 0." So it measures with explainable rules and uses the model only to *fix* things. And it is honest about what it is not: "Not an AI-authorship detector. A page made entirely with AI can score clean, and a hand-written page can score high."

**Pros:**
- Enumerated, auditable criteria with cited sources (`docs/CRITERIA.md`) rather than a black-box score — you can read why a finding fired and disagree with it.
- Measures rendered reality, not source: computed contrast, actually-rendered fonts, whether an SPA ships an empty `client-shell` to crawlers, whether text is 11px or a line runs 140 characters.
- `file:line` output plus before/after screenshots and re-measurement means a fix is verifiable, which is exactly the discipline our `/better-interface` adoption asked for.
- Runs entirely locally — a department site with clinician names and internal links never leaves the machine, and `localhost` scanning works for unreleased work.
- The `--plan`, `keep` and target-score loop forces you to state what must survive the cleanup before anything is touched.

**Cons:**
- The scoring model is a *template* detector. It will fire on deliberate choices: our platform's all-caps section labels, dark-theme medium-grey body text, and repeated feature cards are all "template design" patterns in its eyes. Read the report, don't obey it.
- Several checks are Tailwind/shadcn-specific and the rest are heuristics — small caps above a heading is a legitimate editorial device at a premium brand and a tell at a landing page. Context is not in the tool.
- Calibration is one author, 34 sites, mostly landing pages; no design studio has published a teardown, and there is no independent benchmark of the false-positive rate (the author's own guess for the sibling Show HN study was 5–10%).
- It scores *copy and completeness* at least as hard as it scores *design* — "Substance" and "AI search readiness" are half the product, and that's a different job from art direction.
- Turkish-language lists are young, the repo is 9★ with one author and no contributors — treat it as a criteria library you can read, not a dependency you install.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** The criterion worth more than the tool is this: **slop is measurable, and the measurements are things a design director already looks for.** A premium surface fails on 1.4:1 secondary text, on 140-character measure, on six identical cards with a coloured left border, on bouncing motion nobody deliberately chose. Every one of those is in this tool's list, with the fix attached. Run it against the Chapter Player's marketing page and the residency campaign landing page first — not the dashboard (that's a production system, frozen by policy), and not as an authority but as a second pair of eyes that catches the things I stop seeing after a week. Then take the parts that travel: the enumerated tell-list into our review checklist, the `DESIGN.md` drift check into the platform repo's tokens, and the before/after screenshot requirement into every redesign brief. The most useful sentence in the whole repo is the one that disqualifies it as a gate — it cannot tell AI-made from human-made, only *careless from cared-for*, which is the only distinction that has ever mattered to a client.

---

### Golden Temple — a film where every light, lens and grade is a decision someone wrote down

**Link:** https://github.com/Leonxlnx/golden-temple
**Type:** Workflow / Idea
**What it is:** A 70-second, 1080p60 film of a golden-hour Japanese temple complex, rendered offline and released under MIT with full source (79★, 13 forks, first commit Oct 15). **There are no 3D models, no texture files, no HDRIs and no image assets in the repository** — buildings, roof tiles, bracket sets, statues, trees, lotus, koi, water and sky are all generated in JavaScript, with every surface a procedural GLSL shader injected into three.js physical materials. About 31,000 lines build a scene of 24.4 million triangles from a seeded generator, so every load is identical. The film is 10 shots of 7 seconds; **each shot opens on a macro close-up of one detailed object and pulls back to reveal the world around it.** Rendered frame by frame in headless Chrome, averaging 8 sub-frames per frame to buy anti-aliasing, motion blur, soft sun shadows and noise-free ambient occlusion, then depth of field, bloom, ACES/AgX tone mapping, a colour grade, vignette and grain.

**What's good about it:** Look at what is specified versus what is delegated. Each camera key carries its own **lens — focal length, focus distance and f-stop**; orientation is interpolated as a direction, ease curves "linger on the close-up," and a Gaussian smoothing pass removes snaps from hand-made keys. There is a physically based sky (Rayleigh/Mie/ozone single scattering, HDR sun disc), aerial perspective written into every material so water reflections share the haze, ambient-occlusion volumes that dim sky light under deep eaves, and a shadow frustum re-fitted per shot around that shot's subject. Then the discipline: `camcheck.mjs` reports **camera speed, turn rate and acceleration spikes per shot**; `lumaflicker.mjs` measures frame-to-frame brightness flicker per screen region; `mcflicker.mjs` measures motion-compensated shimmer; `splice.mjs` puts a re-rendered range back frame-accurate. Motion quality was *measured*, not judged. And the close-up-first rule is a director's instinct, not a default: every reveal is earned by starting on a lantern, a lotus stamen, a gilt finial.

**Pros:**
- The shot list is a storyboard with a craft rule (open tight, reveal wide) — portable to any product film, any campaign video, any 20-second residency reel.
- Quality tooling for camera motion and flicker is the part nobody builds; it converts "looks a bit janky" into numbers you can fix.
- Every lighting and grading decision is written in code and therefore repeatable — re-render at any resolution or aspect ratio, and the look holds. Seeded world, deterministic output.
- Real production receipts: ~3.3 s per 1080p frame with 8 sub-frames on a Radeon 780M integrated GPU, ~4 hours per film, GPU cool-down and rest pauses included, plus explicit `--spp 2 --w 960` draft mode.

**Cons:**
- It is a *rendering* showcase, not a design system. Nothing here helps you lay out a page or choose a typeface; the craft is lighting, lens and edit.
- The world is procedurally invented Japanese temple architecture. As reference it is beautiful; as a subject for a Bronx residency programme it is decorative tourism. Do not generate a "golden temple" for us.
- A 4-hour render job on a laptop for 70 seconds means this approach is for a hero film, never for volume social.
- 24.4M triangles, single commit, one maintainer plus Claude as co-author, no adoption evidence — young.
- The music is a Kevin MacLeod CC BY track; the film's emotional spine is licensed stock, which is exactly the seam that shows in AI work.

**Should we...**
- ✅ **Adopt it** — use it now; it raises our design ceiling
**Why:** This is last week's plate/letters rule with its other half attached. We have been saying *generate the plate, typeset the letters yourself.* Golden Temple says: **specify the plate too.** Lens, f-stop, focus distance, sun angle, shadow frustum, tone-mapping curve, grain — every one written down. The difference between its frames and a Midjourney prompt is not the renderer; it's that a person decided the focal length before a machine drew anything. That is the whole lesson, and it costs nothing to apply: write a shot list for the residency recruitment film with a lens and a light direction per shot, open every shot on a detail that means something (a resident's hands on a pen, a case list on a desk, a name badge), and measure the motion instead of eyeballing it. Where I would actually use the repo: it is the cleanest demonstration I've seen that cinematic image quality is a *specification* problem. Take the shot discipline and the flicker/motion checks; leave the temple.

---

### Krea 3 — editing that respects the frame, and holds half a dozen references

**Link:** https://www.krea.ai/blog/introducing-krea-3
**Type:** Tool
**What it is:** Krea's new first-party image model, built for editing first and generation second (launched Oct 15, open beta). Most edits return in **under 8 seconds at native 2K** (2736×1536) at $0.06 an image; it accepts **up to 6 reference images per edit**, supports hex codes in prompts ("on the product, and only on the product"), and — the headline feature — **regional edits**: draw a box, ask for a change, and everything outside the box stays pixel-exact (`regional_edit: true` in the API), so a chain of edits does not accumulate re-render artifacts. Distributed on day one through fal, Hedra, Together AI, Nous Research, OpenRouter and Replicate.

**What's good about it:** The prompt guidance in Krea's own post is the most art-directed thing in the release, and it reads like a photographer's brief: **"Start with what stays"** — name the label, the logo, the thing that must not move — *then* describe the change the way a photographer would: the scene, the light, the camera. Then number the references ("image 1 is the room, image 2 is the sofa") and use "only" when the edit must touch one thing. The kitchen demo is genuinely a controlled workflow: a hidden-line architectural drawing plus a flat six-colour palette (A–F) and the instruction "materialize … take every colour from the A–F palette" — palette-as-spec, not palette-as-vibe. Consistent-cast work (the same four plush characters on a boulevard, in a crosswalk, as giants in a tiled room) is the same technique applied to character continuity, and it's the only way a multiple-image campaign holds together.

**Pros:**
- Regional edit with pixel-exact preservation is the control we have actually been missing: change one element of an approved composition without regenerating the whole frame and losing what the client signed off on.
- Multiple named references (subject, product, setting, style) map directly onto how art direction is briefed; the model now takes a brief instead of a sentence.
- Up to 6 references plus hex codes makes palette compliance and cast consistency repeatable — the two things that break a campaign set.
- Day-one availability through OpenRouter and Nous Research means it is usable inside the pipelines we already run, not only in a browser tab.

**Cons:**
- Every speed and price number in the launch is **vendor-measured on Krea's own infrastructure** (`Sep 24 – Oct 1, 2026, queue included`), and the landing page's comparison quietly disagrees with the blog's (26.8 s vs 33 s for Nano Banana Pro). fal reports its own "under 6 seconds." Treat all of it as directionally true at best.
- **$0.06 is a floor, not a price.** The API table adds $0.02 per 1K reference image and $0.07 per 2K reference image, plus $0.02 for `high` thinking mode — a 2K edit on a 2K photo is $0.13, and four 2K references put you at $0.34 before thinking. Krea's own "100,000 edits a month" chart is footnoted "without image references," which is self-contradictory for an editing model.
- Early testers still report **scrambled small text** in some outputs — so it cannot be trusted to render type, which is precisely our standing rule anyway. Use it for the plate; letters still get set.
- Regional editing shines when the change is *small*. For background removal the "region" is most of the image and the advantage evaporates, as the HN thread on the launch pointed out.
- Closed weights (Krea 2 shipped open), API in early access, credit-based app pricing from free to $35/mo Pro, and every gallery image is Krea's own showcase — no independent craft teardown yet.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The controls are right even if the marketing is inflated — and for us the controls are the whole question. Our surfaces are full of moments where a real photograph must survive an edit: a resident's headshot in a campaign frame at a different crop; a facility photo relit warm for the Sub-I welcome packet; the same faculty portrait placed consistently across a dozen social formats without drift. That is reference-driven, regional, palette-locked editing, which is exactly what Krea 3 claims to do, and "your product stays your product" is the correct instinct finally stated as a feature. I would not adopt yet: the pricing is materially different from the headline, the text rendering fails, and the only evidence is the vendor's own. The test before adopting is concrete and cheap — take one real residency headshot and one facility photograph, ask for a crop change and a lighting change with hex-locked navy, and check whether the cast drift is zero and the price is $0.13 or $0.34 per finished asset. If it passes, it becomes the single most useful image tool in the stack; if it drifts, we keep shooting.

---

### Pictoplasma × andstudio — an identity that is a ligature and two dots

**Link:** https://www.creativeboom.com/work/how-two-simple-dots-gave-pictoplasma-a-face-after-20-years-of-neutral-design/
**Type:** Idea / Technique
**What it is:** Vilnius studio andstudio rebranded Pictoplasma, the Berlin festival of character design, which had deliberately kept its own branding neutral for two decades so the artists' work would dominate. The brief from the strategy — "Never faceless" — could easily have produced a mascot. Instead: **the identity is a typeface.** They licensed Melun from Lift Type and worked with the foundry to adapt it, adding a `ct` ligature to smooth the festival's name and, crucially, a **glyph for a pair of eyes**. Letters act as the body; the two dots as eyes; the whole identity can simply be typed. Colours and layouts change per city (Berlin, New York, London) while the type and the dots stay constant. Motion designer Greta Griniūtė built a motion identity that plays with the type and the two dots only — no additional character drawn. In physical space: two holes cut into the festival tents, a flash-tattoo booth offering one design (two dots), dots stuck on objects across the city as a guerrilla campaign. Tickets sold out six weeks earlier than usual.

**What's good about it:** The restraint is a *system decision*, not a mood. Because the identity is made of a glyph, nothing is illustrated on top — "nothing's drawn on top, so it never tips over into becoming a fully detailed character" — and the brand can never compete with the artists, which was the actual strategic constraint. Colour carries the edition; type carries the brand. That's a textbook two-tier system and it's the same structure we need for a department with three audiences (residents, faculty, applicants). The physical extension is the part most brand systems never reach: a rule that says "put two dots on any object, and it becomes a character" produced tent holes, tattoos and city stickers from one decision, at festival-budget cost. And the outcome is a commercial one: sold out six weeks early, which for a festival with shrinking cultural funding is the only metric that counts.

**Pros:**
- The entire identity travels as a font — any staff member can type the brand correctly. No asset library, no template, no designer needed per surface.
- Custom-foundry collaboration (a real ligature and a real glyph) is licensing-plus-craft: distinctiveness without a bespoke typeface budget.
- One rule generates unlimited physical and digital extensions, which is how a small budget looks generous.
- Edition-level colour variation with constant type is a clean answer to seasonal or programme-level differentiation.

**Cons:**
- The idea is spent on a name of eleven letters with a convenient `ct` pair and a built-in play on "character." Our name has no such gift, and forcing a pair of dots onto a Urology department's identity would be a gimmick.
- It is a festival identity — deliberately recessive, designed to let other people's artwork lead. A recruitment brand has to lead on its own.
- Nothing is AI, and the technique is not reproducible by prompting: it exists because a foundry was hired to alter letterforms.
- Creative Boom's write-up is admiring, agency-sourced, and its outcome metric (tickets) is a single unreplicated data point.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** Two things here are worth stealing and neither is the dots. First: **when the brand must not compete, make the brand the type.** Our Sub-I welcome packet and residency materials are often competing with clinical imagery and other departments' logos; a decision as plain as "our identity is one typeface, one tracking, one rule" would outperform any added graphic. Second: **one rule that generates every extension.** "Put two dots on any object" gave a whole festival its merchandise, its spatial design and its guerrilla campaign from a single sentence. We should be able to say the same sentence about our accent rule across the platform, the Chapter Player and the campaign. Watch rather than adopt because the specific device is name-dependent and the write-up is soft — but the strategic move, *let the character come from restraint*, is a direct answer to the "generated mascot" reflex that makes institutional design look cheap.

---

### Business of Home — AI imagery in the furniture trade, and the two companies that refused

**Link:** https://businessofhome.com/articles/how-ai-generated-imagery-is-quietly-reshaping-the-furniture-business
**Type:** Idea / Pattern
**What it is:** A field report (Oct 14) on AI imagery in home and furniture marketing: HookPic, Presti, DecorX and others turning factory-floor snapshots into campaign photography, with monthly platform fees from $800, brand-standard presets, per-audience scene targeting ("to pitch a retailer in Miami, spin up beachfront imagery"), and customers ranging from boutique makers to Wayfair and Ashley. Set against it, two mid-size brands publicly holding back — **Four Hands** (a 13,000 sq ft studio, nine photo bays, 160 products a month, its own rendering tools, and a deliberate investment in real photography) and **Samuel & Sons** (passementerie, where the product's construction is the product).

**What's good about it:** The practitioner quotes are the most useful thing I've read all week on the actual failure mode, and they are specific rather than moralistic. Four Hands' VP of creative services, Kristy Greene: "AI is not able to be consistent and exact enough yet. If you generate an image and then you want to change something about it, it becomes this endless loop of redirecting, redirecting, redirecting." That is the iteration problem, stated by someone with a production pipeline. Samuel & Sons' Milton De Paul places it in history rather than hysteria: "I don't think AI right now is that different from Photoshop in the past. Twenty years ago, someone had done a photo with trim that had been Photoshopped, and then we got clients asking: 'How do you sew the leather trim to make it look like that?' And it was physically impossible." And the AI vendors themselves draw our line for us — Presti's account executive, Jerrica Zaric: "Does that *look* like AI made it — that to me is AI slop — or does that look like a human used a tool? When you give AI all of the control, that's where we get the really bland rooms where everyone looks the same."

**Pros:**
- Names the real professional objection precisely: consistency across a *set* and controlled iteration, not "quality" in the abstract.
- The Photoshop analogy reframes the debate usefully — the risk isn't newness, it's depicting something that cannot physically exist, which has a hard clinical analogue for us.
- Gives the production-economics argument for restrained, human-directed work a real receipt: a 13,000 sq ft studio as a competitive bet, not sentiment.
- Flags the distribution risk nobody mentions: some retailers are reportedly **banning AI-generated brand content** over return-rate and trust concerns — a governance problem, not an aesthetic one.

**Cons:**
- It is one industry, and the product is furniture — where the thing being photographed is a physical object whose exact material matters. Photography of people in a clinical setting has different risks and different ethics.
- The holdouts' positions are reported with admiration but no numbers; the claim that real photography gives Four Hands an edge is asserted, not measured.
- Every AI-company claim (70 customers, monthly fees, enterprise clients) is self-reported, and two of the brands named are platform vendors whose incentives are clear.
- The ethical questions the piece raises — patient-adjacent imagery, disclosure, representation — are named but not answered, so it cannot be used as a compliance reference.

**Should we...**
- 👀 **Watch it** — promising, not proven yet
**Why:** The two sentences worth putting on a wall are "AI is not able to be consistent and exact enough yet" and "does that *look* like AI made it, or does that look like a human used a tool?" The first is our iteration-budget argument: if a change request costs forty redirects, you have not saved time, you have moved it. The second is the only test that matters, and it is the test our Slop Radar has been circling for two weeks — this is that test being said plainly by someone selling the technology. Watch rather than adopt because the field it describes isn't ours: a rendered sofa has one failure mode (it looks wrong), while a rendered *person in a clinical setting* has three — it looks wrong, it depicts something that did not happen, and it may depict a colleague, a patient, or a scene nobody consented to. For Shareef's surfaces the practical output is a hard rule with an escape hatch: facility and equipment imagery, texture, environment and light can be generated and are usually impossible to book as a shoot; **people are photographed.** Always. That rule survives every model release, and it's cheaper to state once than to defend per campaign.

---

### HyperPlasma Skills — 300 styles, 400 font pairings, 500 animations, compiled from AI catalogues

**Link:** https://github.com/gaur-avvv/HyperPlasma-Skills
**Type:** Tool
**What it is:** An agent skill (9★, MIT, created Oct 16) whose stated purpose is to stop your AI building "the same generic website every time." Before it writes UI code, it makes the agent ask you to pick a **design style** from 301 options, a **font pairing** from 400, and an **animation set** from 500, describing each so you can choose fast. Lists are split into category files with duplicate maps and a `validate.py` that checks every ID resolves in CI.

**What's good about it:** The diagnosis is correct and it is the same diagnosis this brief has made: left alone, a model produces one house look, so the instruction "different from last time" has to come from outside the model. The packaging is genuinely careful — the agent loads a ~165-line `SKILL.md` and then only the one or two reference files it needs, so it doesn't eat context; IDs are validated in CI; the project keeps its own duplicate map. And the README is unusually honest about provenance: "Style, font and animation lists were compiled from AI-generated catalogues, then deduplicated and annotated. Some names are informal community terms rather than industry standards, and a few font names could not be verified (flagged with `?`). Treat descriptions as inspiration, not authority." The commit that added "style 301 Liquid Chrome (morphism catalogue)" tells you exactly what the catalogue is.

**Pros:**
- Correct diagnosis of the default-look problem, and a working mechanism (force a choice before generating) rather than a better prompt.
- Context-efficient by design: load the index, load one category file, keep the rest on disk.
- Honest self-assessment about unverified font names and licenses, with fallbacks listed.
- Mutually exclusive categories and duplicate maps mean the catalogue is at least internally coherent.

**Cons:**
- **The catalogue is the problem.** 300 named styles and 500 animations is a slot machine with a bigger drum: a designer choosing "Style 187. Claymorphism" is doing exactly what the model does when it defaults to glassmorphism — picking a pre-existing look off a list instead of deciding anything. Choosing from 301 options is not art direction.
- Provenance is AI-generated and then lightly deduplicated. Some entries are community slang and some font names are unverified — this is the model's own average, indexed and sold back to it as variety.
- 500 animations pre-loaded as options is a direct invitation to the bouncing, pulsing, scroll-driven motion that every slop detector in this brief's history flags by name.
- Three days old, 9★, one author, no shipped examples, no adoption, no license audit on the fonts beyond a flag character. The "400 font pairings" in particular has commercial-embedding implications nobody has checked.

**Should we...**
- ❌ **Skip it** — slop-adjacent, hype, or redundant
**Why:** Everything our design surfaces already do well came from *not* choosing off a list. The Unified Platform works because one decision — premium dark, single accent, Inter, SVG icons — was made once and defended; the Chapter Player works because its light theme is a deliberate counterweight, not a style pick. A skill that hands the agent 801 menu items to choose from before it starts is the mechanical opposite of that discipline, and it will produce surfaces that are each individually defensible and collectively incoherent: a claymorphic Sub-I packet next to a liquid-chrome campaign next to a glassmorphic landing page. The failure this repo treats as a scarcity problem is a *decision* problem. The fix we already have is the right one: one named reference, a colour decision, a type decision and a layout intent, stated before anything is generated — and for new surfaces only, a stress-test of the direction, never a menu.

---

## Slop Radar
- **"Pick from a catalogue" disguised as variety.** 300 styles / 400 pairings / 500 animations is the same default-look problem with more inventory. Named-style selection is style-as-template; the antidote stays a reference, not a menu.
- **Vendor-measured speed as design relevance.** Launch posts lead with "under 8 seconds" and a comparison table Krea ran on Krea, with the price floor footnoted away. Speed is a supply-chain metric; it says nothing about whether the frame is right.
- **The AI-built look is now a *tool* category.** Slop detection is becoming a product, which means "does it look human-made" is a settled question with an enumerated answer list. Worth knowing the list; fatal to treat a score as a verdict.
- **Mascot reflex.** The instinct to answer "give this brand a face" with a drawn character — in a release, a campaign, or a generated image. Pictoplasma's answer, a glyph and two dots, is cheaper, more extensible, and unfakeable.

## Overall Assessment
The week's centre of gravity is **specification**, and it has moved one step past where we left it. Last brief's rule was *the model makes the plate, never the letters.* Golden Temple shows the other half: a person who writes down the lens, the f-stop, the focus distance, the sun angle, the tone curve and the frame rate gets cinematic imagery from the same models everyone else prompts in a sentence — and measures camera acceleration and luminance flicker instead of squinting. Krea 3 is the same thesis commercialised: hex codes, six named references, "keep the product exactly as it is," regional edits that touch one box. Those are not features, they are the vocabulary of a brief. Against that, the loudest *failure* signal of the week came from furniture, of all places: Four Hands has a 13,000-square-foot studio and 160 products a month because "AI … becomes this endless loop of redirecting, redirecting, redirecting" — the iteration problem, not the quality problem, is what sends professionals back to a camera. And when two independent teams (a Show HN scorer and a trade publication's AI vendor) are both reduced to the same test — *does that look like AI made it, or like a human used a tool* — that test has become the industry's working definition of slop, with an enumerated tell list attached: purple gradients, glow, all-caps labels above every heading, cards inside cards, bouncing motion, six identical icon-topped cards. The single highest-leverage move for Shareef this week: **write the shot list before the prompt.** Pick one surface — the residency recruitment creative — and produce a one-page spec per asset: what must not change, the light direction, the lens or crop, the palette with hex values, the type and the measure, the reference image named. Then generate against it. If a picture needs forty redirects, the spec was missing, not the model. That single discipline, applied to one campaign, does more for the ceiling than every tool in this brief.
