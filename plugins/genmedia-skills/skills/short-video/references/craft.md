# Craft: words and numbers for camera, light, sound, prompts

Vocabulary for the beat sheet and the prompts built from it. Numbers are working values for 3-8 s generated shots, not laws: they exist because a model (and a user reading the beat sheet) can act on "8% closer over 4 s" and cannot act on "cinematic".

## 1. Numbers instead of adjectives

| Instead of | Write |
|---|---|
| warm, cold | a colour temperature: 2700 K, 3200 K, 5600 K, 6500 K |
| slowly, fast | seconds, or a share of the frame: "10% of frame width over 5 s" |
| orbit, pan | degrees of arc: "20 degree orbit to the right" |
| small, big | share of frame: "the bottle fills a fifth of the frame height" |
| upbeat, calm music | BPM and instruments: "96 BPM, felt piano and soft kick, no vocals" |
| cinematic, stunning, premium, beautiful, epic | delete; name the lens, the light, the material that would cause the impression |
| sad, confident, cozy | the causes: posture, pace, light direction, palette; at most one closing mood line |

## 2. The style string

One paragraph, English, 35-60 words, written once per project and pasted **verbatim, last,** into every keyframe and clip prompt. Parts, in this order: lens and depth of field · light family and temperature · palette (2-3 named colours) and saturation · contrast and black level · texture (grain, sharpness) · frame rate feel. No subject, no action, no brand or film-stock names.

- Warm documentary: `35mm lens look, shallow depth of field, soft window light from the left at 3200 K, palette of walnut brown, cream and muted teal at 80% saturation, gentle contrast with lifted blacks, fine film grain, natural motion blur.`
- Clean product: `85mm lens look, deep focus on the subject, large soft overhead source at 5600 K with a thin rim from behind, palette of bone white, graphite and one brass accent at 65% saturation, crisp contrast, no grain, studio stillness.`
- Night tech: `28mm lens look, medium depth of field, screen glow as key at 6500 K with magenta practical spill, palette of near-black, electric blue and magenta, high contrast with deep blacks, light haze, clean digital texture.`

Negatives list, also fixed per project and pasted after the style string: `No text, no letters, no logos, no watermark, no subtitles, no UI, no extra people, no extra objects.` Add per format: F5 `no faces`; F6 `no hands, no camera shake`; F2 (non-UI shots) `no readable screens`.

## 3. Camera: one move per beat

| Intent | Move | Working numbers |
|---|---|---|
| calm authority | locked-off | zero camera motion; the change happens inside the frame |
| intimacy | slow push-in | 5-10% closer over 4-6 s; "felt, not seen": 8% over 10 s |
| reveal | pull-back | detail to context in about 2 s, then settle |
| reveal of scale | rise / crane up | ground detail to wide in about 2 s |
| product hero | orbit | 20-90 degrees over 4-5 s; portrait 180 degrees in 8 s |
| establish a world | lateral drift | 10-20% of frame width over 5 s |
| redirect attention | rack focus | 0.5-1 s, once, on the narrative pivot |
| life in a still | breathe | drift under 3% plus a slow zoom |
| documentary | handheld | camera trails the subject by about 0.3 s, one brief focus hunt |
| hook only | snap zoom | 0.3 s, no easing |
| hook only | whip pan | 0.5 s, overshoot and settle |
| hook only | drop | 0.4 s with a small landing shake |
| hook only | speed ramp | slow (about 10%) to fast (about 300%) on a hit, back to slow for the last beat |

- Every move carries a rate word (imperceptible, slow, medium, rapid) or a number. Drift up reads as hope or scale, down as going deeper.
- Premium envelope (F6, and any "expensive" look): push 10-20% of frame width per 5 s, orbit 5-15 degrees per 5 s, tilt up to 15 degrees per 5 s, or static. Never handheld, whip, fast zoom, dutch angle or two moves.
- A move needs room to end: if it takes 3 s, order 5 s and ask for the hold.
- Transitions are motivated: an object crosses the lens, the camera passes behind the subject, a door opens, light changes. Unmotivated transitions read as effects.

## 4. Light: direction plus temperature

| Look | Recipe | Use |
|---|---|---|
| window natural | large soft side source, subject about 1 m from it, room as fill | trust, "caught working" (F3, F8) |
| one-key portrait | one key 45 degrees high at about 3500 K, shadow side about 30%, rim, dark background | founders, experts (F3, F4, F9) |
| seated interview | soft key 3200-4000 K, fill 1.5-2 stops under and cooler, hair light, background 1 stop under | testimonials (F8) |
| warm result | 2700-3000 K key at 30 degrees, warmer background, a third of a stop bright | the "after", results (F7, F4) |
| clinical before | flat overhead 5000-6500 K, drained colour | the "before", the problem (F7, F2) |
| screen as key | dark room, the interface is the only source, light haze, brand-colour spill | software (F2) |
| high-key studio | even soft light, white or grey gradient, minimal shadow | clean product, beauty |
| one hard source | one small hard source, 40-60% of the frame in shadow | premium objects (F6) |
| candle | 1800-2200 K, flicker, moving soft shadows | fragrance, hospitality |
| neon duo | two opposing saturated colours, no fill, rim separation | hooks, youth, gaming (F1) |
| silhouette | strong backlight, no fill | curiosity hooks (H2) |
| volumetric | beams through haze, visible particles | reveals, avatars |

5000 K and above reads analytical or "before"; 3200 K and below reads intimate or "after"; a deliberate mix reads as conflict or change. Any synthetic person: a catchlight in the eyes, never flat frontal light, shadows consistent with the room, room colour falling on the skin.

## 5. Sound: four layers, written per beat

Bed (ambience or chosen silence) · impacts (hits, whooshes, clicks on visual events) · music · voice. Every beat names its entry; silence is a valid entry.

| Format | Music brief to paste | Mix |
|---|---|---|
| F5, F10 narration-led | 80-100 BPM, felt piano or soft guitar, no vocals, no strong melody | music 12-15 dB under the voice, swelling in gaps; ducking does it (`finishing.md` S4) |
| F2 software | 90-110 BPM minimal electronic, no vocals, a filter sweep on feature reveals | one UI sound per interaction: click, 0.3 s swoosh, two-note chime for success |
| F4 promo | slow build around 72 BPM (piano, strings from 4 s) or 120 BPM four-on-the-floor for launch urgency | music drops away under the CTA card |
| F6 luxury | silence for 2-3 s, material foley, isolated piano notes at 40-80 BPM or one low bowed string | short natural reverb; no percussive attacks, no bright synths |
| F7 before / after | thin single tone before, full beat from the first after-frame | the onset sits exactly on the transition frame |
| F8 testimonial | sparse piano or guitar; one added instrument at the result | voice dry and centred, music 12-14 dB under it; resolve, do not swell |
| F9 avatar | none until speech starts; then about 90 BPM minimal | designed ambience (low hum, soft pings), not room tone |
| F1 hook | bass-forward, enters at 1-2 s | hook sound patterns: `hooks.md` |

- Voice pace: up to 2.3 words per second in English, 1.7 in Turkish (measured on Gemini voices, `platform.md` section 10); one breath between key statements; last word ends 0.5 s before the end.
- Native audio from the video model (ambience, foley) is kept only when no voice or music goes on top. Under a voice, generate clips with the audio switch off (`generate_audio: false` on Seedance, `audio: false` on Wan; the H3 draft model always adds a soundtrack: mute it in the cut).
- Effects come from the sound-effect endpoint (0.5-22 s each) only for beats the sheet names. Music length = cut length, instrumental when a voice is present.

## 6. Generated vs composited

| Generated by models (describe it in prompts) | Composited after generation (never in a video prompt) |
|---|---|
| picture, motion, light, atmosphere | hook text, titles, lower thirds, quote cards |
| ambience and foley (when native audio is on) | captions and subtitles |
| narration, music, sound effects (audio endpoints) | logos, brand marks, handles |
| an end-card background without words | prices, dates, numbers, counters, star ratings with their source |
| a device or screen as an object | readable interface content: use the user's real screenshot or recording |
| | mix levels, loudness, cuts, trims, speed changes |

Prompts reserve room instead: "clean, evenly lit area in the upper third, free of detail, for a title". In 9:16 keep the subject's eyes in the upper third and the lower third calm; in 16:9 leave one side empty; treat 1:1 as a poster. Text rules: hook text 3-5 words; quote cards up to 15 words; reading time = words / 3 s; no static text on a static frame for more than about 2 s; attribution 1 s after the quote; a rating always with its platform name; the CTA is one verb on a hard cut and holds.

## 7. Prompt templates

Slots in `<>`. English. 60-160 words per prompt; a long tail gets ignored. Order matters: what the viewer must see first comes first.

**Anchor keyframe** (text-to-image, sets the look):
`<shot size and angle> of <subject with material and colour>, <placement in frame, share of frame>, <environment in 8-12 words>. <light: source, direction, temperature>. <reserved area: "clean dark area in the upper third for a title">. Vertical 9:16 composition. <STYLE STRING> <NEGATIVES>`

**Keyframe edited from the anchor** (keeps grade, product, person; `image_urls`: anchor first, then product or person references):
`Same place, same light and colour grade as the first image. <new shot size and angle> of <subject>; <what is different: position, action frozen mid-motion, time of day>. Keep <the product from the second image> identical in shape, label and colour. <reserved area>. <STYLE STRING> <NEGATIVES>`

**Clip from a keyframe** (image-to-video; the image already shows the look, so describe change only):
`<ONE camera move with amount and duration>. <what moves in the scene, in order, with seconds: "0-3 s steam rises and drifts left; 3-5 s the hand lifts the cup out of frame">. The last <1.0> s holds still on <the settled composition>. <sound: bed and one event, or "no audio needed">. No cuts, no new objects, no text. <STYLE STRING>`

**First + last frame clip** (before/after, reveals; describe the transition only):
`<camera: locked-off | one slow move>. From the first frame to the last frame: <the motivated transition with its timestamp: "at 2.0 s warm light sweeps left to right across the room and the furniture settles into place behind it">. Geometry, camera position and lens stay fixed. The video ends exactly on the last frame and holds it for <1.0> s. No flicker, no text, no extra objects. <STYLE STRING>`

**Chained continuation** (start image = exact last frame of the previous clip):
`Continue the same shot. <the SAME camera move, same direction and speed as the previous clip>. <next action with seconds>. <hold instruction if this is the final link>. No cuts. <STYLE STRING, identical>`

**Several beats in one uncut shot** (timed ranges; a request, not a guarantee: check the sheet):
`One continuous shot, no cuts. 0.0-1.5 s: <hook action>. 1.5-4.0 s: <confirmation>. 4.0-7.0 s: <payoff>. 7.0-8.0 s: hold still. Camera: <ONE move spanning the shot, or "locked-off until 4.0 s, then a slow push-in">. <sound per range>. <STYLE STRING>`

**End-card background** (words come later): `<brand-coloured calm backdrop, soft gradient, subtle texture>, large clean central area for a logo and one line. <STYLE STRING> No text, no letters, no logos.`

Draft pass: same prompts, same keyframes, draft endpoint and lowest resolution; only parameters change.

## 8. Prompt lint: run before every paid stage

1. Beat 1 is the hook, fits one sentence, names its family, works muted.
2. Every beat has a time range; ranges are contiguous and sum to the target; the last 0.5-2 s is a hold.
3. Exactly one camera move per beat, with a number or a rate word; aggressive moves only in beat 1.
4. Every light has a direction and a temperature.
5. Depth of field is stated for portraits and environments.
6. Every beat has a sound entry, tied to a visual event where there is one; silence is written as a choice.
7. The negatives list is present; the prompt has no empty quality adjectives and no brand, studio, film-stock, artist or celebrity names.
8. The style string is byte-identical in every prompt of the project.
9. Transformations: both states described with equal detail; the transition has a timestamp and a physical cause.
10. Shape and length are **parameters** (`image_size`, `duration`, `resolution`), set explicitly, inside the live schema's enums and ranges; `duration` is never `auto`.
11. No words, logos, numbers, ratings, captions or UI text are requested from a video model; the frame reserves room for them.
12. Reference images are named the way the target model expects (check its schema page), and the first image is the one whose look must win.
13. No invented proof, people or likenesses; consent and disclosure notes are in the plan where a person or a synthetic presenter appears.
14. No strobing or flashing; nothing imitates platform UI.
15. The prompt is 60-160 words; every job in the stage has `est_cost_usd`; the stage total matches the approved plan.
