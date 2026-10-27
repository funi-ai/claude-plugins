# Delivery targets (dated: verified 2026-09-20; creative-asset videos 2026-10-07)

Read when choosing targets or answering a size, length or format question. The numbers live in `scripts/video-surfaces.json` and are printed by `democut.py specs`; this file explains them. A `null` in the data file is a number nobody read from the official page — never fill one in from memory. Rows with `official: false` are this project's defaults, not a platform rule. A row's own `verified_on` wins over the file's date.

## 1. App Store app previews

Source: App Store Connect help, app preview specifications (read 2026-09-20).

| Row | Size (portrait) | Devices |
|---|---|---|
| `appstore-iphone-69` | **886x1920** (landscape 1920x886) | 6.9", 6.5", 6.3", 6.1" |
| `appstore-iphone-55` | 1080x1920 | 5.5" and 4" (4.7" is 750x1334) |
| `appstore-ipad-13` | 1200x1600 (landscape 1600x1200) | 13", 11", 10.5" (9.7" is 900x1200) |
| `appstore-mac` | 1920x1080, landscape only | Mac and Apple TV (Vision Pro: 3840x2160) |

Everything else is common to all of them: **15-30 s**, up to **3 previews per device**, H.264 (High profile, up to level 4.0, progressive) at 10-12 Mbps VBR and at most 30 fps, or ProRes 422 HQ at about 220 Mbps; `.mov`, `.m4v` or `.mp4`; stereo audio, AAC 256 kbps (or PCM in ProRes), 44.1 or 48 kHz; up to 500 MB; the poster frame defaults to 5 s in.

Two consequences worth stating out loud:

- 886x1920 is the iPhone's own aspect (1290x2796 → 0.4614). A full-screen phone recording scales into it with no stretch and no bars. A 1080x1920 recording does **not** fit the 6.x rows — that size belongs to the 5.5"/4" row.
- The frame-rate cap is 30. A 60 fps recording is resampled by `build`; record at 60 if you like, deliver at 30.

## 1a. App Store creative-asset videos (iOS 27 and iPadOS 27)

Source: App Store Connect help, creative assets specifications and "Manage your App Store assets", and Apple's App Store asset best practices (published 2026-10-05, read 2026-10-07).

| Row | Size | Sound |
|---|---|---|
| `appstore-header-video` | **3840x1646** (21:9), exactly | muted by default; the viewer may unmute it on the product page |
| `appstore-search-video` | 3:2, **1920x1280 to 3840x2560**; renders 3840x2560, any exact 3:2 with even sides in the range passes | muted in search results and cannot be unmuted |

Common to both: **30 or 60 fps exactly**, **5-30 s**, `.mov`, `.m4v` or `.mp4`, and the video **loops continuously**. Optional, separate from previews and screenshots, uploaded per language, shown on iOS 27 and iPadOS 27 or later; a search results asset takes the place of in-app events, previews and screenshots in search there. Apple lists **no universal (16:9) video**: the universal asset is a still. Codec, bitrate, byte cap and audio format are not stated (`null`); `build` writes H.264 High 4:2:0 at CRF 18 and, with audio on, AAC 192 kbps stereo at 48 kHz, this project's choices. Each gap is in `unverified`.

What `time` and `validate` do with these rows:

- `wrong_size`, `fps_not_allowed`, `duration_out_of_range` are errors. 29.97 is not 30: `build` writes exactly 30 or 60.
- `quick_cut` (a scene under `min_scene_seconds`, 2 s) and `fast_motion` (`speed` above `max_scene_speed`, 2x) are warnings: Apple asks for no quick cuts and no fast-moving visuals. The thresholds are this project's reading, not Apple numbers. Cut a long wait out rather than playing it at 4x.
- `narration_muted` (a scene has `voice`) and `audio_never_heard` (audio on for the search video) are warnings: the video must work silent; sound is brand texture, a short music loop that loops cleanly, never information.
- `loop_seam` (a warning from `validate`): the last frame measured against the first (SSIM at 640 px). Under 0.95 the loop visibly jumps every time it restarts; a cut to another screen measured 0.52-0.85, one changed button 0.99. End on the opening state, or hold the same region.
- New variants start with `audio: false`; set it to `true` only for a music bed on the header.

What the numbers do not say, and the delivery does:

- **Poster frame.** The user picks it in App Store Connect; it applies wherever the asset is used and cannot be edited after approval. `poster_at` writes the frame you recommend; name its time in the delivery.
- **Composition.** One clear idea, the value first. A phone recording does not fill 21:9 or 3:2: play it in a drawn device (`frame`, `layers` from `/genmedia-skills:launch-graphics`) over the variant's `background`, or crop a desktop recording with a `hold` zoom. Keep the device and any text near the centre: Apple's art safe area exists only in its templates, drawn for the stills, and `/genmedia-skills:launch-graphics` records it. Text on the picture is short or absent, composed there where it is exact, and read against the content rules below.
- **At these sizes** a `push` or `pull` pre-upscales to twice the canvas (7680 px wide): slow. Calm `hold` zooms suit the placement better anyway.
- **Content** (`content_rules`, `references/store-policy.md` section 1a): no prices, discounts, URLs, copyright symbols, unverified awards, Apple recognitions or other platforms; 4+.

## 2. Google Play promo video

Source: Play Console help, preview assets (read 2026-09-20).

Play does not take a file. It takes a **YouTube URL** — not a playlist, not a channel, no extra parameters such as a timecode. The video must be public or unlisted, embeddable, not age-restricted, and its ads must be disabled. Only the **first 30 seconds autoplay**, and Google recommends that at least 80 % of the video shows the actual app experience. Landscape and portrait are both accepted.

So the skill's job is the file (`play-promo`, 1920x1080 by default); uploading it to YouTube and pasting the link into Play Console is the user's, and the delivery says so.

## 3. Product Hunt

Source: Product Hunt help, "How to post a product" (read 2026-09-20).

- Video: a **full YouTube URL** (a shortened link does not load). Upload before launch day and check it is not private.
- Gallery stills 1270x760, thumbnail square (240x240 recommended) — those are `/genmedia-skills:launch-graphics` work.
- **Every image, GIF included, must be under 3 MB.** A GIF animates only while the pointer is over the post, so its first frame has to carry the post on its own. `democut.py gif --budget-mb 3` measures the bytes instead of guessing, and writes the first frame as a PNG for you to look at.

## 4. This project's own defaults (not platform rules)

| Row | Size | Use |
|---|---|---|
| `web-16x9` | 1920x1080, 30 fps | the master; also the file you upload to YouTube for Play and Product Hunt |
| `social-9x16` | 1080x1920 | a vertical cut |
| `loop-16x9` | 1280x720, silent | a loop in a docs page or release note |
| `loop-1x1` | 1080x1080, silent | a feature card loop |
| `ph-thumbnail-gif` | 240x240 GIF, 3 MB cap | a Product Hunt animated thumbnail (export it with `gif`, never as a video variant) |

Safe zones and length limits for a specific social placement are deliberately **not** in this file: `/genmedia-skills:short-video` owns social formats and keeps its own dated table.

## 5. Choosing targets

- An app with a store listing: `appstore-iphone-69` (or the iPad/Mac row that matches the recording), plus `web-16x9` for the site, plus `play-promo` when the app also ships on Android.
- An App Store header or search results video: `appstore-header-video`, `appstore-search-video`, each its own short variant (8-15 s, one idea, silent). The still versions, and the universal still, are `/genmedia-skills:launch-graphics` work.
- A web product: `web-16x9` master, `social-9x16` cut, one or two loops.
- A launch: `web-16x9` (goes to YouTube for Product Hunt), one loop for the thumbnail GIF, and whatever stills `/genmedia-skills:launch-graphics` is making.
- One cut serves all of them: variants pick scene subsets, so the store preview is the demo without its long middle, and a creative-asset video is its calmest few scenes.

## 6. When a store rejects a file

The official page wins over this table. Read it again on the day, correct the row in `scripts/video-surfaces.json` with a new `verified_on`, and say in the delivery which number changed. Never leave a corrected number only in the chat.
