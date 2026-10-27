# Platforms: shapes, safe zone, soft defaults

> **UNVERIFIED HEURISTICS - check each platform's current specs.** Nothing on this page was measured or confirmed against TikTok, Instagram, YouTube, LinkedIn or Facebook documentation. The values are conservative working defaults from general creator practice. Platforms change limits, interface overlays, crops and labelling rules without notice. When a number matters (an ad placement, a paid campaign, a maximum length), tell the user it is a heuristic and ask them to check the platform's current rules, or check the official spec page yourself if a web tool is available. Never state any value below as a platform fact.

This is the only file of the skill that carries platform numbers. SKILL.md, the beat sheet and the other references point here.

## 1. Shape and size

| Placement the user names | Shape | Deliver | Generate at |
|---|---|---|---|
| TikTok, Instagram Reels, YouTube Shorts, Stories, "vertical", nothing named | 9:16 | 1080x1920 | keyframes 1080x1920; clips at the 720p tier (about 720x1280), one upscale or scale of the final cut |
| YouTube (regular), website hero, LinkedIn, presentation | 16:9 | 1920x1080 | keyframes 1920x1080; clips 720p tier |
| Feed post (Instagram, Facebook, LinkedIn), "square" | 1:1 | 1080x1080 | keyframes 1440x1440 (same keyframe price tier as 1080x1920); scale down in the cut |
| Feed post, taller | 4:5 | 1080x1350 | keyframes 1200x1500; image-to-video follows the keyframe's shape, so probe the first clip; if the model snaps to another ratio, generate 9:16 and crop |

- One 9:16 master serves TikTok, Reels and Shorts. Do not ask which of the three.
- Two shapes requested (9:16 and 16:9): they are two compositions, not one crop. Generate keyframes per shape from the same anchor and style string; reuse voice, music and captions. Price both before the beat sheet is approved. A centre crop is acceptable only when the subject sits in the central third of every shot.
- Container: MP4, H.264 video with `yuv420p`, AAC audio at 48 kHz stereo, 24 or 30 fps constant, `+faststart`. Every platform re-encodes uploads; deliver a clean high-bitrate file (CRF 18) and let them compress it.
- Loudness: normalize the final mix to about -16 LUFS with a -1 dB true-peak ceiling (`audiokit.py loudnorm` default). Platforms do not publish one common target.

## 2. The one safe-zone rule (9:16)

Platform interfaces cover parts of a vertical video: a top bar, a caption and account block at the bottom, a column of buttons on the right. Exact sizes differ per platform, device and ad placement and change over time. Use ONE conservative box for everything that must stay visible:

**Keep faces, products, all composited text and captions inside the area that leaves 15% free at the top, 25% free at the bottom and 10% free on each side. Centre text horizontally; never right-align it.**

| Master | Safe box (x, y, width, height) |
|---|---|
| 1080x1920 | x 108, y 288, 864 x 1152 |
| 720x1280 | x 72, y 192, 576 x 768 |

- Picture may fill the whole frame; only what must be read or recognised stays in the box.
- Captions: bottom-anchored caption styles usually land in the covered band. With `fal-ai/workflow-utilities/auto-subtitle` start from `position: "center"` plus a positive `y_offset` (range -200 to 200, positive moves down); with `veed/subtitles` use `customization.position`. Look at one frame of the result before delivering.
- Hook text sits in the upper part of the box, captions in the lower part; never both on the same line height.
- 16:9 and 1:1 placements show little or no overlay: keep a 5% margin on every side and one side calm for titles.
- Paid ad placements often publish their own safe-zone templates: the user checks the current template in the ad manager.

## 3. Length (soft defaults)

| Goal | Default | Note |
|---|---|---|
| hook, product moment, loop | 6-10 s | F1, F6, F7 defaults |
| launch, promo, testimonial, avatar | 12-20 s | F2, F3, F4, F8, F9 defaults |
| narrated topic, podcast clip | 25-45 s | F5, F10 defaults |
| anything longer than 60 s | not this skill's default | maximum lengths differ per platform and have changed several times: check the current limit, then plan the piece as chapters of 30-45 s |

Shorter is cheaper and usually stronger. When the user gives no length, take the format default from SKILL.md Routing; never pad a video to reach a number.

## 4. Pacing model (heuristic)

| Window | Job |
|---|---|
| 0-2 s | the gate: the hook (`hooks.md`); fast feeds want it before 1.5 s |
| 2-5 s | confirmation: the viewer learns the stop was worth it |
| 5-15 s | payoff |
| past 15 s | every further 10-15 s needs a reason to stay: the re-hook beat |

These are planning aids. No platform publishes them, and no skill output may promise reach, retention or "virality".

## 5. Cover frame and loop

- The end hold of the last beat doubles as the cover frame: sharp, composed, subject and title inside the central square (profile grids crop covers toward the centre; the exact crop varies: check).
- Export the cover as a PNG next to the final (`frames.py frame --at last`). The user selects it at upload; this skill does not upload.
- Loop: when the format loops (F1, F6), make the final composition echo the first frame, and let the last 0.5 s of motion flow toward it. Do not fake a loop with a crossfade to frame 1 unless the user asks.
- F7: the cover is the "after". F8: the cover is the result or the product, not a generic card.

## 6. Captions and text

- Many viewers watch muted: every video with speech ships a sidecar `.srt`; burned-in captions are the default recommendation for F5, F8, F9, F10 and an option elsewhere.
- Uploading the `.srt` where the platform accepts caption files keeps captions editable and searchable; burned-in captions look the same everywhere. Offer both when unsure.
- Caption language = spoken language. Translations are separate caption files, not a second burned layer.

## 7. Rules the user must check themselves

State these as reminders, not as legal or policy advice:

- **AI disclosure.** The large platforms have a label or setting for realistic AI-generated or AI-altered content, and their rules on when it is required differ and change. When the video shows a realistic synthetic person, voice or event, tell the user to check and set the label at upload.
- **Ads.** Testimonials, endorsements, results claims, health and finance content are regulated in most countries and restricted by platform ad policies. This skill does not invent proof (SKILL.md, "This skill does NOT"); what the user supplies is their responsibility to substantiate.
- **Music.** Generated music is not the platform's licensed sound library. Commercial accounts often cannot use trending sounds; the delivered mix must stand on its own. Licence terms of each generation model are on its model page (`platform.md`, Safety).
- **Real people.** Consent for likeness and voice is confirmed by the user before generation, again for every new person.
