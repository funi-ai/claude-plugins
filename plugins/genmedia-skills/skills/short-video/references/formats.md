# Formats: ten short-form structures

Pick the format in SKILL.md Routing, then copy the matching structure into the beat sheet and replace every cell with the user's subject. Timings are craft heuristics, not platform rules: they give a first draft that the measured voice (Workflow step 7) then corrects.

## How to read a structure

- Rows are **segments**. A segment holds one or more **beats** (one idea, one camera move, one sound entry each). The beat sheet lists beats, not segments.
- A video gets longer by **adding beats, never by stretching them**: hook beats stay 1-2 s, body beats 2-5 s, the end hold 0.5-2 s at every length.
- Time ranges are contiguous and end exactly at the target length. `(3)` after a range = number of beats inside it.
- From 30 s up, plant a **re-hook** near the middle (a question, a second reveal, a change of location): write it as its own beat.
- Voice budget: words <= 2.3 x voiced seconds (Turkish 1.7: two Gemini voices measured 1.4 to 1.9, `platform.md` section 10). Voiced seconds = length minus the end hold minus about 10% for breaths. 15 s: about 28 words (TR 20); 30 s: about 58 (TR 42); 45 s: about 90 (TR 66). Hook text and end-card lines are composited, not voiced; they are outside this budget only while they stay on screen.
- Every format lists three asset groups. **From the user**: nobody else can supply it. A missing item costs no question: it becomes a labelled placeholder in the beat sheet and a line under "Needed from you", and its beats are not generated until it arrives (SKILL.md UX rule 3). **Generated**: models make it. **Composited**: added after generation (`finishing.md`), never requested from a video model.
- Production detail for any shot: `production.md`. Hook choice: `hooks.md`. Words for camera, light and sound: `craft.md`.

## F1. Viral hook

**When**: one product, place or idea needs attention; no story, no explanation. **Arc**: stop the thumb, confirm it was worth stopping, pay off, loop.

| Segment | 8 s (default) | 15 s | 30 s | 45 s | What happens |
|---|---|---|---|---|---|
| Hook | 0-1.5 | 0-1.5 | 0-2 | 0-2 | one mechanism from `hooks.md`, readable muted |
| Confirm | 1.5-3.5 | 1.5-4 | 2-5 | 2-5 | partial reveal; the cause or the whole stays hidden |
| Payoff | 3.5-7 | 4-8 | 5-10 | 5-11 | hero view of the subject, music established |
| Escalation | - | 8-13.5 (2) | 10-27 (5), re-hook at 15 | 11-41 (9) in three rounds, each ends on a small payoff | new angle or second reveal per beat, never a repeat |
| Hold | 7-8 | 13.5-15 | 27-30 | 41-45 | settled hero frame; last frame echoes the first for the loop |

- From the user: a photo of the real product or place (else a generic subject is generated and said so). Generated: every shot; native sound. Composited: hook text, handle.
- Production: up to 15 s in one set = ONE generation with timed ranges in the prompt (tie-breaker 3). Beyond 15 s use separate shots.
- Pitfalls: two hook mechanisms at once; a payoff weaker than the hook; aggressive camera after the hook (only beat 1 may snap or whip); any flicker or strobe.

## F2. App or SaaS launch

**When**: software, a feature, a launch date. **Arc**: the itch, the product appears, it performs, the outcome, the name.

| Segment | 15 s (default) | 30 s | 45 s | What happens |
|---|---|---|---|---|
| Hook | 0-2 | 0-2 | 0-2 | the stuck moment (frozen cursor, overflowing list) or a teaser of the result |
| Reveal | 2-5 | 2-6 | 2-7 | device in a lit workspace, screen glow as key light, slow push |
| Features | 5-11 (3) | 6-20 (4) | 7-32 (6), re-hook at 20 | one feature per beat; the interface acts, nobody explains |
| Outcome | 11-13 | 20-26 | 32-40 | the finished state; a number only if the user gave it |
| End card | 13-15 | 26-30 | 40-45 | logo, tagline, CTA; music resolves; hold |

- From the user: real screenshots or a screen recording, logo file, tagline, CTA, launch date. Generated: environment, device and hands shots WITHOUT a readable screen (off, facing away, out of frame), UI sounds, music. Composited: every frame region that shows the interface, feature labels, end card, captions.
- Production: never invent, edit or animate the interface with a model; the same rule as `launch-graphics` and the software route of `ads`. A model that receives a screenshot returns misspelt lettering, and image-to-video on a screen morphs it. UI shots are the user's recording, normalized and cut in (`finishing.md` S2), or a real screenshot as a still clip with a local slow push (2-3 s, so small text survives). A framed page around the capture (device frame, headline, exact size) is composed by `/genmedia-skills:launch-graphics`; its `layers` command cuts the screen out so the recording plays under the drawn frame. Read every frame of the sheet: lettering that differs from the capture is a failed shot.
- Pitfalls: a flat full-screen screenshot with no depth; feature count above one per 2 s; metrics the user never supplied; a fake notification or fake platform UI as hook.

## F3. Personal brand

**When**: a founder, creator or expert is introduced. **Arc**: caught working, the space, the person, eye contact, the name.

| Segment | 12 s (default) | 15 s | 30 s | 45 s | What happens |
|---|---|---|---|---|---|
| Hook | 0-2 | 0-2 | 0-2 | 0-2 | hands at work in macro, or a walk toward camera; foley only |
| Space | 2-4.5 | 2-5 | 2-6 | 2-8 | pull back: the room states who this is |
| At work | 4.5-8 | 5-9 | 6-18 (3) | 8-32 (6): a day, light temperature follows the clock | absorbed, three-quarter view, window key |
| Contact | 8-10.5 | 9-13 | 18-26 | 32-41 | looks into the lens; camera stops; their one line (voice or caption) |
| Hold | 10.5-12 | 13-15 | 26-30 | 41-45 | back to work or a still look; handle appears |

- From the user: 3-6 photos of the person or an `@handle`, their confirmation of consent, the line, the handle text. Generated: keyframes as Seedream edits with the person's photos as references, low-motion clips. Composited: name, handle, captions.
- Production: identity drifts with motion. Clips of 5 s or less, one slow move, face checked in the last tile of every sheet. Speech to camera is the F9 route.
- Pitfalls: a generated stranger presented as the user; big head turns; status props the person does not own.

## F4. Course or webinar promo

**When**: a course, cohort, workshop or live event with a date. **Arc**: pain, recognition, teacher and proof, promise, one step.

| Segment | 15 s (default) | 30 s | 45 s | What happens |
|---|---|---|---|---|
| Hook | 0-2 | 0-2 | 0-2 | the learner's pain, wordless or in 3-5 words |
| Recognition | 2-5 | 2-7 | 2-8 | the frustration made specific; music enters |
| Teacher and proof | 5-9 | 7-14 | 8-18 (2) | instructor portrait; one proof line with its source |
| Promise | 9-13 | 14-25 (3) | 18-38 (5), re-hook at 22 | "from X to Y in Z": what you get, one item per beat |
| CTA card | 13-15 | 25-30 | 38-45 | hard cut; verb, date, time, timezone; near-silence; hold |

- From the user: offer name, date with time and timezone, instructor photo with consent, proof (numbers, student results, source), CTA verb and destination. Generated: learner and workspace b-roll, portrait keyframe from their photo, voice, music. Composited: all words, numbers, the CTA card.
- Pitfalls: invented student results or income claims; urgency that is not true ("last seats" without the user saying so); a CTA with two actions.

## F5. Faceless narrated b-roll

**When**: a topic told by a voice over footage; the default for "a short video about X". **Arc**: claim that raises a question, setup, body, turn, close.

| Segment | 15 s | 30 s (default) | 45 s | What happens |
|---|---|---|---|---|
| Hook | 0-2 | 0-2 | 0-2 | first word at 0.0 s; the strongest image of the whole piece |
| Setup | 2-5 | 2-6 | 2-7 | context in one sentence; pull back or reveal the place |
| Body | 5-11 (2) | 6-22 (5) | 7-36 (8), re-hook at 20 | one sentence = one shot; never the same place from the same angle twice |
| Turn | 11-13.5 | 22-27.5 | 36-42 | the answer, the twist or the takeaway |
| Close | 13.5-15 | 27.5-30 | 42-45 | last words end 0.5 s before the end; hold |

- From the user: nothing required; facts they want stated. Generated: script, voice, anchor keyframe plus edited keyframes, clips with audio off, music, optional effects. Composited: captions (they carry half the audience), hook text, handle.
- Production: voice first, then beats move to the measured sentences. No faces and no hands that imply a presenter; light is the character. Worked plan: `production.md` production A.
- Pitfalls: a script longer than the voice budget; stock-photo stillness (every shot needs one motion source); claims stated as facts that you did not check with the user.

## F6. Luxury or aesthetic product

**When**: an object shown with restraint: fragrance, watch, ceramics, furniture, packaging. **Arc**: space, one move, stillness.

| Segment | 8 s (default) | 15 s | 30 s | 45 s | What happens |
|---|---|---|---|---|---|
| Stillness | 0-1.5 | 0-2 | 0-3 | 0-3 | the empty space and the light before the object matters |
| Move | 1.5-6 | 2-13 (3 shots: space, material, hero) | 3-27 (6 shots of 4 s) | 3-41 (9 shots) | ONE barely visible move per shot; no cut under 3 s |
| Hold | 6-8 | 13-15 | 27-30 | 41-45 | hero frame, 2 s of nothing; logo may appear |

- From the user: a clean product photo (poor photo → `product-photoshoot` first), logo file. Generated: scene keyframe edited around the photo, one slow clip per shot, sparse sound. Composited: logo, one line at most.
- Production: 40-60% of the frame empty, the object about a fifth of it; saturation pulled down; silence or foley for the first 2-3 s. Camera envelope: `craft.md`. At 45 s prefer three 15 s cutdowns over one long film. Worked plan: `production.md` production C.
- Pitfalls: the words luxury, premium or elegant in a prompt (describe material, finish and light instead); handheld, whip or zoom; a label the model redrew (compare with the photo).

## F7. Before / after

**When**: a visible change of state: room, desk, garden, packaging, brand identity, routine. Never bodies, health, income. **Arc**: before, one motivated transition, after, hold.

| Segment | 8 s (default) | 15 s | 30 s | 45 s | What happens |
|---|---|---|---|---|---|
| Tease | - | 0-1.5 | 0-2 | 0-2 | 0.5 s flash of the after, then back |
| Before | 0-3 | 1.5-6 | 2-26: three areas, each 3 s before + 1 s transition + 4 s after | 2-10 (3 details) | locked-off, cool light (5000 K and up), thin ambience |
| Process | - | - | - | 10-25 (5), time-compressed work | only when effort is the story |
| Transition | 3-4, lands at 50% | 6-7.5 | inside each pair | 25-27 | wipe, pass-behind or light change; sound hits on its first frame |
| After | 4-7 | 7.5-13 | final wide 26-28.5 | 27-41 (3 details mirroring the before) | same framing, warm light (3200 K), full sound |
| Hold | 7-8 | 13-15 | 28.5-30 | 41-45 | best after frame, static: it is the cover |

- From the user: the before photo (and the after photo if the change is real and done). Generated: the after keyframe as an EDIT of the before (never independent), first + last frame clip. Composited: "before" and "after" labels, captions.
- Production: both keyframes share camera position, lens and geometry; only state and light change. Worked plan: `production.md` production B.
- Pitfalls: a generated after presented as a real result (label it a visualization); unequal detail between the states; two transformations in one clip; the transition before 40% or after 60%.

## F8. Testimonial or story

**When**: a customer's own words exist. No quote, no F8. **Arc**: result, person or context, the words, the product, the source.

| Segment | 15 s (default) | 30 s | 45 s | What happens |
|---|---|---|---|---|
| Result | 0-2 | 0-2 | 0-2 | the outcome alone on a calm frame; one resonant note |
| Context | 2-4 | 2-6 | 2-8, then the "before" story 8-16 (2) | where this customer works or lives: b-roll, objects, no invented face |
| Quote | 4-10 (2) | 6-20 (3): problem, turning point, result | 16-36 (5), re-hook at 22 | their sentences, word-synced captions; attribution 1 s after the quote settles |
| Product | 10-13 | 20-26 | 36-41 | the product in the situation the quote describes |
| Source | 13-15 | 26-30 | 41-45 | name or agreed anonymisation, rating with its platform, logo; hold |

- From the user: the quote verbatim, the name or the agreed anonymisation, permission to publish, any rating with its source, their photo or footage only with consent. Generated: b-roll, abstract or product shots, a narrator voice reading the quote (say it is a narrator; never clone the customer without consent). Composited: quote text, attribution, rating, logo.
- Pitfalls: editing the quote to sound better; a generated "customer" face; a rating without its source; ending on a generic CTA instead of proof.

## F9. AI avatar or talking head

**When**: a presenter speaks to camera. **Arc**: claim to lens, points, cutaways over joins, one ask.

| Segment | 15 s (default) | 30 s | 45 s | What happens |
|---|---|---|---|---|
| Hook line | 0-2.5 | 0-3 | 0-3 | first word at 0.0 s, eye contact, slight lean in |
| Points | 2.5-12 (2) | 3-25 (4), re-hook at 15 | 3-39 (6), re-hook at 20 | one point per beat; b-roll cutaway over every chunk join |
| Ask | 12-14 | 25-28.5 | 39-43.5 | one verb |
| Hold | 14-15 | 28.5-30 | 43.5-45 | closed mouth, settled look; handle |

- From the user: the script or topic; their portrait with consent when the presenter is a real person. Generated: portrait keyframe (one lane: photoreal, stylised 3D or 2D, never mixed), voice, talking-head chunks, cutaway clips. Composited: captions, lower third, the AI disclosure where the platform asks for it.
- Production: voice chunks of 8-15 s, each under the model's audio limit, one talking-head job per chunk; draft the whole piece on the budget avatar model first (`production.md`, Talking head). Portrait: catchlight in the eyes, light from the side, shoulders visible, mouth closed.
- Pitfalls: a chunk boundary in the middle of a sentence; no cutaway over a join (visible jump); a lookalike of a public figure; native-language claims you did not probe.

## F10. Podcast or audiogram clip

**When**: an existing recording becomes a visual clip. Their audio stays untouched. **Arc**: the quotable sentence, who speaks, the thought, identity.

| Segment | 15 s | 30 s (default) | 45 s | What happens |
|---|---|---|---|---|
| Quote slam | 0-1.5 | 0-2 | 0-2 | the key sentence as text, audio already running |
| Speaker ID | inside beat 2 | 2-5 | 2-5 | who speaks, which show: lower third |
| Thought | 1.5-12 (3) | 5-25 (6) | 5-38 (9), re-hook at 20 | one visual per sentence; emphasis words become visual events; hold the frame through pauses |
| Identity | 12-15 | 25-30 | 38-45 | show name, episode, where to listen; hold |

- From the user: the recording, the time span or the sentence to feature, show and speaker names, speaker photos only with their consent. Generated: abstract or symbolic b-roll with audio off, optional low bed. Composited: burned-in captions (mandatory here), quote card, lower third, identity card.
- Production: cut the span with `audiokit.py extract --start <s> --duration <s>`, upload it, transcribe with word timings, set beats on sentence starts. Slow speakers get long holds, fast speakers get layered motion, never faster cuts than the sentences.
- Pitfalls: cutting inside a pause; a generated likeness of a host or guest; music that fights the voice; trimming words so the meaning changes.
