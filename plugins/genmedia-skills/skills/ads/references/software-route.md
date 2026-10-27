# Software route: ads for apps, SaaS, developer tools and extensions

A software product has no packshot. Its product reference is the user's REAL captures and screen recordings, and the rule is the one `launch-graphics` lives by: **no generative model draws, restyles, translates or "enhances" the interface in a delivered pixel.** A model that repaints a screen misspells it, and an ad that shows an interface the app does not have breaks every platform's policy (section 8). Models paint what is not the product: a presenter, a problem scene, an environment. The interface arrives by composition. Platform numbers on this page were read on the platforms' own pages on **2026-09-20**; ad specs change, so say "as published on that date" and re-read the page before promising a placement.

`gm.py`, `pipeline.py`, `frames.py`, `adkit.py` abbreviate the calls in SKILL.md. `launchkit.py` belongs to `/genmedia-skills:launch-graphics`.

## 1. When this route applies, and what to collect

Any ad whose product is an interface: mobile app, web app, SaaS, developer tool, browser extension, game menu. Intake (inside the question budget; the first answer replaces the product photo):

| Need | From the user | If missing |
|---|---|---|
| Captures | PNG or JPEG of the real screens the ad is about, at native size | ask for them: the one question without a default. A design mock counts only when the user says it ships like that; it is marked `mockup: true` and the delivery says so |
| Screen recording | 10 to 60 s of the real flow, no notifications, no personal data | optional for statics; for video, stills with a local push replace it, but see TikTok's still-image rule in section 5 |
| Destination | App Store, Google Play, both, or a web URL | decides the device frame and which store rules touch the copy |
| Icon, logo, brand colours | files; a BRAND LOCK from `/genmedia-skills:brandkit` | the app name in plain type; colours measured from the captures by `launchkit.py capture add` |
| Facts | what the app does, numbers, ratings, prices, awards, each with its source | no fact, no claim: same sheet as every ad (`scripts-and-claims.md`) |

Capture hygiene: fictional account data, a clean status bar (iOS simulator: `xcrun simctl status_bar booted override --time "9:41" --dataNetwork wifi --wifiMode active --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState discharging --batteryLevel 100 --operatorName ''`), the ad's language. Read every capture with the Read tool; read the recording through `frames.py sheet`.

## 2. Who makes which pixel

| Pixel | Made by | Never |
|---|---|---|
| Any frame region that shows the interface | the user's capture or recording, placed by `launchkit.py compose` or `layers` plus local ffmpeg | an edit or image-to-video job with the capture as input; a video model animating a screenshot (it morphs the text) |
| Device frame, status bar, headline, sub line, badge, lockup, end card | `launch-graphics` (HTML, real fonts, every locale) | the typography model: on this route no copy is baked by a model |
| Presenter, problem scene, environment, hands without a readable screen | this skill's usual routes (Seedream stills, talking head, image-to-video b-roll) | a phone or laptop with a readable screen in a generated frame: screens are off, face away, or out of frame |
| Hand-held phone showing the app | a `card-hero-scene` still from `launch-graphics` (key-colour plate, real capture warped in), moved only by a local push | image-to-video on that still |
| Motion inside the interface | the recording itself | invented taps, cursors or transitions |

## 3. Static ads: copy here, pixels in `launch-graphics`

This skill owns the angle, the copy, the claim check and the placement list. `launch-graphics` owns composition. Steps:

1. Facts sheet, then copy per placement; lint it as `copy.json` with `adkit.py check`. Copy that will ALSO sit on a store asset (listing screenshots, an Apple custom product page, the Play feature graphic) carries `"store_listing": true`: ranking, price, offer, award and call-to-action wording then fails even when sourced (`store_listing_claim`). Ad-only copy may call to action.
2. Hand over to `/genmedia-skills:launch-graphics` with explicit values: capture paths, the approved copy per locale, the facts, the targets below, the brand colours. It builds `deck.json` with one set per shape (portrait targets together, landscape apart), runs `text`, `compose`, `sheet`, `validate`.
3. Back here: Read the sheet and every file, check every string against `copy.json`, deliver with the claims line.

| Target (`launchkit.py specs --store ads`) | Pixels | Where it runs (as published 2026-09-20) | Layouts that fit |
|---|---|---|---|
| `ad-feed-4x5` | 1440x1800 | Meta Feed image 4:5 (JPG or PNG, 30 MB); Google App campaigns portrait (4:5, up to 5 MB) | `device-bottom`, `device-center`, `text-only` |
| `ad-square` | 1200x1200 | Google App campaigns 1:1; Meta 1:1 (1080x1080 or larger); TikTok carousel | `device-center` with a one-line headline, `text-only` |
| `ad-vertical-9x16` | 1440x2560 | Meta Stories and Reels image; TikTok carousel 9:16 | `device-bottom`, `device-center`: text starts below the top 14 percent by itself |
| `ad-landscape` | 1200x628 | Google App campaigns 1.91:1; TikTok carousel and Ad Network | `card-left-title`, `card-centered`, `card-browser` |

- Warnings to act on: `ad_safe_zone` (Meta: keep about 14 percent at the top, 35 at the bottom and 6 on each side of a 9:16 creative free of text and logos; TikTok publishes its safe zone only as templates, so the same box is the working default), `text_share` (Google asks for overlaid text and logos under 20 percent and suggests images with none: offer one text-free variant per ratio), `contrast`, `fit_scale`.
- Text the platform renders next to the image is the user's to paste, so deliver it with its limits: Meta primary text 125 characters (Feed: 50 to 150), headline 27 on Facebook Feed and 40 on Instagram; Google App campaigns up to five headlines of 30 and five descriptions of 90 characters, never translated by Google; TikTok carousel wants 2 to 35 images and a music track.
- **Apple Ads** takes no uploaded creative: every placement is built from the App Store product page or a custom product page (up to 70 per app; the Today tab needs one). "An Apple Search Ads creative" therefore means an App Store screenshot set: hand the whole job to `launch-graphics` (`appstore-*` targets) with `store_listing` copy rules; Apple refuses pricing, offers, rankings and awards in those assets.
- A/B variants: copy variants re-render for free; vary one axis (headline, capture, layout).

## 4. Video formats that work for software

All 15 s by default, 9:16, route B (TTS voice first; its measured length sets every beat). Beat sources: **REC** recording under a drawn frame, **STILL** composed page with a local push, **GEN** generated clip without any interface, **END** composed end card.

| Format | Beats at 15 s | Use when |
|---|---|---|
| `problem-screen-outcome` (default) | GEN the annoyance, 0-3 s → REC the one flow that fixes it, 3-10 s, headline on the page → STILL the result screen, 10-13 s → END | the app removes a visible friction |
| `recording-with-presenter` | REC for the whole ad with a presenter circle over it (talking head from a generated or `@handle` presenter); END | the flow needs explaining; founder or creator voice |
| `ugc-reaction` | GEN presenter to camera, hook line, 0-3 s → REC full-screen flow with voice-over, 3-11 s → GEN presenter reaction, 11-13 s → END | social proof style without inventing a customer: the presenter is disclosed as AI-generated and speaks as the brand |
| `feature-countdown` | three REC or STILL beats of 3 s, each page headline one feature; the count is spoken by the voice-over, not printed (`launch-graphics` gates every printed number against `facts`) → END | several small features, no single story |
| `before-after-workflow` | GEN or STILL the old way (a generic spreadsheet, paper, a cluttered desk: never a named competitor's interface), 0-5 s → REC the same task in the app, 5-12 s → END | the app replaces a manual routine |

Rules for all: one idea per beat; UI beats at least 2.5 s so small type can be read; the recording is trimmed, never sped up past 1.5x and never reordered into a flow the app does not have; when sequences are shortened say so where the platform asks (Apple's marketing guidelines ask for a "sequences shortened" line). Hooks: `hooks.md`; claims: `scripts-and-claims.md`.

## 5. Platform facts for video (as published 2026-09-20)

| Platform | Ratio and size | Length | Notes |
|---|---|---|---|
| Meta Reels, Stories | 9:16, 1440x2560 stated for Stories and Reels, 1080x1920 for Instagram Feed video; MP4 or MOV, up to 4 GB | Reels ads up to 15 min, Facebook Stories 1 s to 3 min | safe zone as in section 3 (Facebook Stories video: 14 percent top, 20 bottom) |
| Meta Feed | 4:5, 1440x1800 | 1 s to 241 min (Facebook) | most viewers start muted: the hook reads without sound |
| TikTok in-feed | 9:16 at 540x960 or larger (16:9 and 1:1 allowed), MP4 or MOV, up to 500 MB | policy page: 5 to 60 s; reservation guidance recommends 9 to 15 s | audio is required; "Static images should not occupy more than 50% of the video": keep STILL beats under half and prefer REC; no QR codes, no TikTok watermark, nothing that mimics the TikTok interface; in listed markets avoid a person holding a phone with a still image on it |
| Google App campaigns | 16:9, 9:16 or 1:1, uploaded to YouTube first | 10 to 60 s recommended | hook in the first 2 to 3 s; Google may also build videos from the store listing |
| Apple Ads | no video upload: app previews on the product page | | out of scope here |

Render at 1080x1920 (`ad-video-9x16`) or 1920x1080 (`ad-video-16x9`); 4:5 video comes from `ad-feed-4x5` pages scaled to 1080x1350 in the assembly.

## 6. Production, step by step

Project state, plan card, cost gate, voice, music, captions and assembly are the ones in SKILL.md and `production-routes.md`. Write every ffmpeg call out in full: a shell variable that holds several options stays ONE argument in zsh, and ffmpeg then reports an unconnected filter output. What differs:

1. **Frame of the recording as the capture.** The page and the recording must share one geometry, so the slide's capture is a frame of the recording itself:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" probe ./recording.mp4
   python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" frame ./recording.mp4 --at 2.0 --out .genmedia/projects/<slug>/rec-frame.png
   ```
   Variable frame rate or an odd codec: normalize first (`production-routes.md` section 6, step 1) and keep the original.
2. **Pages in `launch-graphics`.** One set on `ad-video-9x16` with a slide per REC, STILL and END beat (headline per beat from the script's on-screen lines; the END slide is `text-only` or `device-center` with the lockup and the CTA as the sub line). `compose` renders the stills; for every REC slide:
   ```text
   launchkit.py layers --slug <slug> --set ads-video --slide flow --target ad-video-9x16 --locale tr
   ```
   (a `launch-graphics` command: run it while that skill is loaded, with its own helper path). The answer names `NN-<slide>.fg.png`, everything but the capture with a true alpha hole, and `ffmpeg_filter`, a ready filter with the hole's rectangle. Layouts: upright framed captures only; a hero scene or a zoom stays a STILL.
3. **REC beat** (recording under the drawn frame; verified 2026-09-20 with ffmpeg 9.0.2 on synthetic clips):
   ```bash
   ffmpeg -hide_banner -loglevel error -ss 3.2 -t 7 -i recording.mp4 -loop 1 -framerate 30 -i 02-flow.fg.png -filter_complex "<ffmpeg_filter from 02-flow.layers.json>" -t 7 -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p rec-flow.mp4
   ```
   The status bar the page draws stays on top of the recording; a recording with a busy bar gets the clean one that way.
4. **STILL beat** (composed page, slow push; the upscale first keeps the push from trembling):
   ```bash
   ffmpeg -hide_banner -loglevel error -loop 1 -framerate 30 -i 03-result.png -t 3 -vf "scale=2160:3840,zoompan=z='min(1+0.0008*on,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=1080x1920:fps=30,format=yuv420p" -an -c:v libx264 -preset medium -crf 18 still-result.mp4
   ```
   `d` = seconds x 30. No push wanted: the end-card recipe in `production-routes.md` section 6, step 4.
5. **Presenter over a recording** (`recording-with-presenter`; the head clip comes from the talking-head route and carries the voice):
   ```bash
   ffmpeg -hide_banner -loglevel error -i rec-flow.mp4 -i head-a_0.mp4 -filter_complex "[1:v]scale=360:360:force_original_aspect_ratio=increase,crop=360:360,format=yuva420p,geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':a='if(lte(hypot(X-180,Y-180),178),255,0)'[pip];[0:v][pip]overlay=48:H-h-560:shortest=1,format=yuv420p[v]" -map "[v]" -map 1:a:0 -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -ar 48000 -ac 2 rec-presenter.mp4
   ```
6. **A bare recording** with no page around it: `-vf "scale=-2:1720,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x<brand hex>,setsar=1,fps=30,format=yuv420p"`.
7. **GEN beats**: keyframe by `bytedance/seedream/v5/pro/text-to-image` (no product in frame, so no lock), clip by the b-roll tiers in SKILL.md. Prompt rule, pasted into every GEN prompt: `No readable screens: any phone, laptop or monitor is switched off, faces away from the camera or is out of frame. No text, no letters, no logos, no interface elements.` Read every frame of the contact sheet; a glowing invented interface is a failed clip. A GEN beat that needs a page headline plays under `layers` like a recording: register its keyframe as a capture with `"mockup": true` and `frame: "none"`, so every proof says that picture is not a screen of the app.
8. **Assemble** as `production-routes.md` section 6 from step 2 on: REC, STILL and GEN clips are b-roll (give each a voice-over or a silent track so every part has audio), the head clips keep their own audio, then concat, music, captions. Register local products with `pipeline.py add … --tool ffmpeg --from <ids>`; list the recording and every capture as sources so the manifest proves where the interface came from.

No local ffmpeg: statics still work through `launch-graphics` (it needs only a browser). Video on this route needs local ffmpeg for `layers` and the composites; say so, offer the statics plus a plan, and do not replace the composites with a generative job.

## 7. Cost and plan card

Pages, layers, REC and STILL beats and the assembly cost $0. Paid: voice (cents), music (about $0.60 per started minute), captions, and only the GEN beats and the talking head (the b-roll and head tiers in SKILL.md; price them with `gm.py price … --explain`). A `problem-screen-outcome` ad with one 3 s draft-tier GEN clip stays under the announce threshold on most days; a presenter format is priced like route B. The plan card adds two lines:

```
Interface: <n> captures and <recording name, seconds>, composed unchanged (launch-graphics); generated: <which beats, or "nothing">
Left out: <claims with no source>; <beats waiting for a capture or recording you still owe>
```

## 8. Policy facts to respect and to tell the user (read 2026-09-20)

- **Nothing the app cannot do.** Meta's policy checklist: no "images that portray non-existent functionality". TikTok: "All interactive elements within an ad must function as intended"; no fake play, close or call-to-action buttons, no "Swipe up" text. Google: no "non-functional elements that resemble buttons", no "inconsistencies between the ad and the landing page/app". Apple Ads 1.8: images and previews "must accurately reflect the app's intent and core experience". A drawn CTA button inside the creative is therefore out: the platform adds the real one.
- **AI disclosure.** TikTok: fully AI-generated images, video or audio need the AIGC label or a clear disclaimer, or the ad is "rejected or restricted". Meta applies an "AI info" label when it detects generative tools and offers self-disclosure in some regions. Google permits AI labels inside creatives since July 2026; YouTube asks for disclosure of realistic generated content. A generated presenter or scene in the ad → the delivery says which beats are generated and tells the user to switch on the platform's label. The interface beats are real and stay that way.
- **Store marks.** Apple's marketing guidelines: Apple-provided product bezels only, "as is", no competing devices in the image, one App Store badge per layout or video, never modified, angled or animated. Google Play badge: not on a device screen, at least as large as other badges. This project ships drawn frames, not Apple's bezels (`launch-graphics` explains the import path), and no store badges: the user adds official badge files in their editor.
- **Store-listing claims.** Play: no "ranking, price, Google Play categories" text on listing assets. Apple Ads Today tab: no "pricing, offers, rankings or awards claims". That is what `"store_listing": true` enforces.

## 9. QA before delivery

| Check | Pass when |
|---|---|
| Interface origin | every frame region with UI traces to a capture or the recording listed in the manifest; no generated or edited UI anywhere (read the contact sheet of the final at 8 frames or more) |
| Text | every headline equals the approved copy character by character, in every locale; nothing unreadable at phone size |
| Safe zone | 9:16: no text or logo in the top 14 percent or the bottom 35 percent; `compose` raised no `ad_safe_zone` you did not explain |
| Geometry | the recording fills its screen without bars or stretch (capture = frame of the recording); corners clean |
| Platform | TikTok: stills under half the runtime, audio present; durations inside section 5 |
| Claims and disclosure | `adkit.py check` clean; generated beats named; store-listing copy free of ranking, price and offer talk |
