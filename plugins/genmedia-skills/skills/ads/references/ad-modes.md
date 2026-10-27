# Ad modes: beats, shot lists, prompts, route

Seven video modes. Each gives the beat structure per duration, a shot-list template, prompt patterns and the production route. Scripts: `scripts-and-claims.md`. Hooks: `hooks.md`. Plans and fields: `production-routes.md`. Statics: `static-formats.md`.

## 1. Platform → ratio and length

Widely known basics only. Ad specs change: **check the platform's current ad specs** before promising a placement, and never quote a file-size, bitrate or length limit from memory.

| Placement the user names | Ratio | Default length | Notes |
|---|---|---|---|
| TikTok, Instagram Reels and Stories, YouTube Shorts, Snapchat | 9:16 | 15 s | Full-screen vertical, sound on is common, captions still expected. Keep copy and faces out of the top strip, the bottom fifth and the right edge (platform UI) |
| Instagram and Facebook feed | 4:5 (or 1:1) | 15 s | Most viewers start muted: the hook must read without sound |
| YouTube in-stream, web, TV-style spot | 16:9 | 15 or 30 s; 6 s for a bumper | The first 5 s decide on skippable placements |
| Marketplace or store product video | 16:9 or 1:1 | 15 to 30 s | Marketplaces restrict claims, prices and contact details in video: the user checks the listing rules |
| Nothing said | 9:16 | 15 s | State it under Assumptions |

- Image-to-video follows the keyframe's ratio: make keyframes in the delivery ratio (1080x1920, 1080x1350, 1920x1080, 1080x1080 on Seedream). Second ratio → new keyframes and clips for hero shots, or a crop (`production-routes.md`, section 7) when the framing allows. Plan safe framing up front when two ratios are wanted.
- 6 s: one shot or two, three beats. 15 s: four to six shots. 30 s: eight to twelve shots; never one 30 s generation for a cut ad.

## 2. Two looks; commit to one

| | UGC look | Polished look |
|---|---|---|
| Camera words | phone selfie, handheld, slight sway, arm's length, front camera wide angle, desk tripod, mirror shot | locked-off or slow dolly, 50 to 85 mm, shallow depth of field, macro, controlled orbit |
| Light | window daylight, mixed room light, a little noise | shaped key light, rim light, gradient backdrop, clean reflections |
| Setting | real rooms: car, kitchen counter, bathroom shelf, desk, doorstep | studio sweep, styled set, hero surface (stone, water, sand) |
| Person | everyday clothes, natural skin texture, imperfect framing | styled wardrobe, deliberate pose, or hands only |
| Sound | room tone, the voice close to the phone | music-led, designed sound |
| Modes | presenter, how-to, unboxing, problem-solution, testimonial | showcase, tv-spot |

Mixing the two (a studio-lit face in a "selfie") reads as fake. A believable presenter frame has: eyes to the lens, asymmetry, a stray hair, real skin texture, light that matches the room, one hand doing something. Do not write "AI avatar", "digital human" or "3D render" in a prompt for a realistic person: describe a person.

## 3. Shot-list template

Saved in `plan.md` and shown in the plan card:

```text
| # | Beat | Sec | Shot (what we see) | Frame | Clip | Audio |
| 1 | HOOK | 0.0-3.3 | presenter to camera, bottle beside shoulder | kf-presenter | head-a (talking head) | vo-a |
| 2 | PRODUCT | 5.2-8.0 | oil poured over salad, bottle right third | kf-pour | broll1 (i2v) | vo-b |
| 6 | END | 13.2-15.0 | end card: name, line, CTA | endcard (typography) | still to clip | music only |
```

Rules: every row has exactly one frame and one clip id; every product row's frame is an edit of the user's photo; seconds come from the measured voice once it exists; one shot = one action (a clip prompt with two actions gives neither).

## 4. Prompt patterns shared by all modes

Keyframe (Seedream edit, product first in `image_urls`):

```text
Figure 1 is the real product[; Figure 2 is the presenter]. {LOCK} <who or what, doing what, where>. <product placement: hand, surface, position in frame, label facing the lens and unobstructed>. <look: UGC or polished words from section 2>. <framing and the calm area kept free for copy>. Exactly <n> product(s). No added text, badges or logos.
```

Clip (image-to-video; the frame already holds the look, so describe only what moves):

```text
<camera: one move or "static">. <subject action, one>. The product stays still and unchanged[, label toward the camera]. <ambient detail>. No text, no subtitles[, no people speaking].
```

Speaking clip (route A), Seedance: add `She says to the lens in <language>, <tone>: "<line>"`. Boreal: `[VISUAL] ... [SPEECH] <line> [SOUNDS] ...`, no `[TEXT]`.

Talking head (route B): the keyframe IS the performance frame: mouth closed, eyes to lens, hands where they will stay. The optional `prompt` of `fal-ai/bytedance/omnihuman/v1.5` takes gesture direction only.

Hands holding a product are the most fragile frame. When two Seedream attempts fail on grip or scale, try `bria/fibo-edit-1.5/product-holding` (`person_image_url`, `product_image_urls` 1 to 3, optional `instruction`, `aspect_ratio`; ~$0.04/image as of 2026-09-19, confirm with `gm.py price`; output under `image`), then run the fidelity check again: it is a different model with no lock string.

## 5. Modes

### `presenter`: talking presenter, UGC selfie (default)

- Use when: the user wants a person recommending or showing the product. Route: A for English single takes up to 15 s, B otherwise.
- Beats: 6 s: HOOK line while lifting the product → name + one feature → CTA. 15 s: HOOK (on camera) → PROBLEM (on camera) → PRODUCT (b-roll, voice over) → PROOF (b-roll or demo) → CTA (on camera) → end card. 30 s: add a second demo shot and a second proof; return to camera twice.
- Shots: presenter keyframe (product in hand, label visible) · 2 to 3 product b-roll frames (in use, close detail, hero) · end card.
- Keyframe scene words: car seat, kitchen counter, bathroom mirror, desk; product at chest or shoulder height, never covering the mouth.
- Script voice: brand or demonstrator voice, present tense. Not an invented personal history (`scripts-and-claims.md`, section 7).

### `how-to`: demonstration in steps

- Use when: the product needs showing how. Route: B without a talking head (voice-over + b-roll); add one on-camera opener if a presenter is wanted.
- Beats: 15 s: HOOK = the finished result (1 shot) → step 1, 2, 3 (one shot each, 2 to 3 s) → result again + CTA. 30 s: up to five steps; each step = one verb.
- Shots: top-down or 45-degree hands-only frames on one surface, same light in all of them; edit each step frame from the previous approved frame plus the product photo so the set holds.
- Clip prompts: one hand action per clip ("the hand presses the pump once; cream lands on the fingertips"). Liquids, pours and pumps work; threading, typing and writing fail often.
- Step captions ("1. Shake") are composited: captions or the user's editor, not the video model. Only steps the user confirmed; never invent usage, dosage or safety instructions.

### `unboxing`

- Use when: packaging is part of the appeal and the user has photos of the box AND the product. Route: B (voice-over or music only) or A for a short spoken reaction.
- Beats: 15 s: HOOK = hands on the closed box, one line of anticipation → lid lifts (end frame = open box) → product lifted out → hero of the product → CTA.
- Shots: closed box keyframe, open box keyframe, product-in-hand keyframe, hero. The reveal is a first-and-last-frame clip: `image_url` = closed, `end_image_url` = open, on `bytedance/seedance-2.5/us/image-to-video`.
- Never invent box contents, inserts, accessories or freebies: every item in frame is on the facts sheet or in a photo. No photo of the packaging → this mode is not available; offer `showcase`.

### `showcase`: product b-roll, no speech

- Use when: "product video", "b-roll", music-led, or the product sells on looks. Route: B without voice or with a short voice-over; music first-class.
- Beats: 6 s: macro detail → reveal → hero + end card. 15 s: withheld detail (hook) → two feature shots → in-use shot → hero → end card. Cut on the music's bars: ask for a tempo in the music prompt and size shots to it.
- Shots: from `product-photoshoot` stills when they exist (hero, detail, lifestyle). Moves: slow push-in, orbit of 15 to 30 degrees, light sweep across the label, liquid or steam or fabric motion around a product that stays still.
- Draft every clip on `minimax/h3-max-turbo/image-to-video`, re-make only the approved ones on Seedance when the user wants the quality tier.

### `problem-solution`

- Use when: the product fixes a visible annoyance. Route: B; A only for a short English to-camera version.
- Beats: 15 s: PROBLEM shown in 2 to 3 s (the hook) → turn ("then I found ...") → product doing the job → result → CTA. 30 s: two problem shots, a demo with a visible before and after inside one continuous clip.
- The problem shot never shows a competitor's product, pack shape or colours: use an unbranded generic. The "after" must be what the product really does per the facts sheet; demonstrations that exaggerate the effect are claims.
- Keyframes: problem frame by text-to-image or an edit without the product (no product in it, so no lock needed); every solution frame is a locked edit.

### `testimonial`: real quotes only

- Gate: available only when the user supplies the quote, its attribution and permission (`scripts-and-claims.md`, section 7). No quote → offer `presenter` or `problem-solution`.
- Route: B. Forms, in order of preference: (1) quote as text over product b-roll, voice-over reads it, attribution on screen; (2) a disclosed presenter reads it as a quote ("One customer wrote: ..."); (3) the real customer's own footage or photo, supplied with consent, with b-roll around it.
- Beats: 15 s: the strongest half-sentence of the quote as hook text → product b-roll with the full quote → attribution line → CTA. Quote on screen: at most about 15 words per card, on screen words ÷ 3 seconds, attribution appears after the quote has settled.
- Never: a generated face presented as the reviewer, star ratings without platform and date, a count of reviews the user did not supply, paraphrase that strengthens the quote.

### `tv-spot`: polished brand film

- Use when: "reklam filmi", "commercial", brand campaigns, 16:9. Route: B with voice-over; A only for a single dialogue moment.
- Beats: 30 s: opening image (restraint or metaphor hook) → world of the user (2 to 3 lifestyle shots) → product enters → proof shot → hero pack shot → end card with logo and line. 15 s: opening image → product in use → hero → end card.
- One look string for the whole film (palette, light, lens, grade) pasted into every keyframe prompt; make the first keyframe, get it approved, then edit the others from it plus the product photo.
- The logo on the end card comes from the user's logo file passed as a reference to the typography model, or is added in their editor. Never generated from the brand name alone.
- Quality tier by default (Seedance 2.5 at 720p); this mode crosses the confirm threshold almost always: show the draft-tier total next to it.

## 6. Picking a mode when the user did not

| Signal in the request or photos | Mode |
|---|---|
| "UGC", "influencer style", "someone talking", nothing said | `presenter` |
| "how to use", "nasıl kullanılır", steps, a device or cosmetic with an application | `how-to` |
| box photos supplied, "kutu açılışı", gift | `unboxing` |
| "product video", "b-roll", "no people", premium object | `showcase` |
| "before", "tired of", a named annoyance | `problem-solution` |
| a pasted review or quote | `testimonial` |
| "reklam filmi", "TV", "brand film", 16:9 | `tv-spot` |

State the pick and the runner-up in the plan card; the user can switch before anything is spent.
