# Surfaces: sizes, counts, formats

Every v1 target with its exact pixel size, how many files the platform wants, what format it takes and the one rule that decides the layout. **Verified: 2026-09-20**, each row against the page named in section 6; the Mac App Store, Play tablet slot, Chrome Web Store and GitHub rows were read on 2026-09-23, the App Store creative assets (section 1a) on 2026-10-07 and again on 2026-10-12, the Product Hunt rows on 2026-10-26, and each carries its date as its own `verified_on`. The machine-readable copy is `scripts/surfaces.json`; `launchkit.py specs` prints it with its `verified_on` date and its `unverified` list. When this page, `surfaces.json` and the official page disagree, the official page wins, then `surfaces.json`, then this page. `launchkit.py` abbreviates the call shown in SKILL.md.

Size tables that circulate in other tools, templates and blog posts are often one or two device generations behind. Never copy a size from anywhere but `surfaces.json`. A value that is `null` there was not verified: say so in the plan card and do not fill it from memory.

## 1. Store targets

| Target id | Pixels rendered | Also accepted in the same slot | Needed | Count | Rule that matters |
|---|---|---|---|---|---|
| `appstore-iphone-69` | 1320x2868 | 1290x2796, 1260x2736 | an iPhone app needs this set, or the 6.5" set instead | 1 to 10 | every smaller iPhone display is scaled down from it, so this is the one set most apps upload |
| `appstore-iphone-65` | 1284x2778 | 1242x2688 | only when no 6.9" set is provided | 1 to 10 | render it on request; otherwise Apple scales the 6.9" set |
| `appstore-iphone-63` | 1206x2622 | 1179x2556 | optional | 1 to 10 | absent → Apple uses the scaled larger set |
| `appstore-ipad-13` | 2064x2752 | 2048x2732 | when the app runs on iPad | 1 to 10 | 3:4, a different composition from the phone set, not a resize |
| `appstore-mac` | 2880x1800 | 2560x1600, 1440x900, 1280x800 | Mac apps | 1 to 10 | 16:10 landscape only; a desktop capture in `macos-window`, never a phone frame |
| `play-phone` | 1080x1920 | each side 320 to 3840 px, long side at most twice the short side | at least 2 screenshots across device types to publish | up to 8 per device type | four or more at 1080 px or larger, 9:16 or 16:9, is what makes an app eligible for Play's large promotional formats |
| `play-tablet` | 1440x2560 | each side 1080 to 7680 px, 9:16 or 16:9 | when the listing covers tablets or Chromebooks | 4 to 8 | Play asks large-screen screenshots to leave out text that is not part of the app, because it can be cut off on Play home pages |
| `play-tablet-7`, `play-tablet-10` | 1440x2560 | as `play-tablet` | when the 7-inch and the 10-inch slot get different screenshots | 4 to 8 each | the same large-screen rules; one folder per Console slot |
| `play-feature` | 1024x500 | none | required to publish a listing | 1 | focal point in the centre; the cutoff zones, about 15 percent on every edge, hold background only (`safe_insets`, warning `cutoff_zone`); no pure white, black or dark grey ground; text-free is the cheap default (below) |

Shared by all store targets:

- **Format:** App Store takes `.jpeg`, `.jpg`, `.png`; Play takes JPEG or 24-bit PNG. **No alpha anywhere.** `compose` writes RGB PNG by default, or JPEG where the set's `export` says so (`composition.md` section 2); `validate` fails a file with an alpha channel.
- **Orientation:** the App Store sizes and the Play screenshot sizes also exist swapped for landscape (`orientation_swappable`). One set has one orientation (`sets[].orientation`). Re-read on 2026-09-23: every iPhone and iPad landscape size on Apple's page is the portrait size turned sideways, so an App Store landscape set is a set with `"orientation": "landscape"` on the same targets, not a target of its own. The Mac sizes are landscape only (`orientation_swappable: false`).
- **Byte cap:** neither Apple's specification page nor Play's help page states one for these targets, so `max_bytes` is `null`. If a console refuses a file for its weight, export that target as JPEG and say what the console reported. A JPEG export on a target with a `null` cap stays under `jpeg.working_max_bytes` in `surfaces.json` (5 000 000, the lowest cap any web surface here states). Where `surfaces.json` applies a cap that the platform does not state, it is a working limit of this skill, not a platform rule.
- **Search results:** on the App Store the first one to three screenshots (how many depends on their orientation) appear in search when the app has no preview video, and only while the app sets no search results creative asset (section 1a). With one set, iOS 27 and iPadOS 27 show that asset instead; the screenshots still reach search only on iOS 26 and earlier, which never show creative assets. Slides 1 to 3 carry the set.
- **Play alt text:** Play's help page recommends alt text of 140 characters or fewer per graphic, but the Play Console has no field for it: the store listing's screenshot and feature graphic views have none, and the Android Publisher API's `Image` resource carries no text (checked September 2026). Do not write alt lines for Play and do not tell the user to paste any into the console. Write them only when the user asks (for a press kit or their own site), one per slide, 140 characters or fewer, so they also fit the day the field appears.
- Apple's page already lists sizes for a folding iPhone and says uploads for it open later. It is not a v1 target.
- **Mac App Store (`appstore-mac`).** One of four 16:10 sizes; 2880x1800 is rendered, the three smaller sizes pass `validate` as accepted alternates. `frame: "auto"` gives the capture a `macos-window` in every mode (a universal set keeps it too: a Mac window identifies no phone platform), and a per-OS capture map takes its `default` entry. A desktop capture on the landscape canvas stacks: headline on top, the window below; `zoom` shows the crop card alone. Give the Mac target a set of its own: its captures, layouts and landscape canvas share nothing with the phone set.
- **Play tablet slots.** Play Console keeps two tablet slots, 7-inch and 10-inch (the Publisher API names them `sevenInchScreenshots` and `tenInchScreenshots`), under one rule set for large screens. `play-tablet` is the one set that goes into both. Use `play-tablet-7` and `play-tablet-10` only when the slots get different sets, for example a portrait 7-inch set and a landscape 10-inch set; `validate` then counts each folder on its own. Neither slot has a pixel size of its own on Google's page.
- **A feature graphic without copy.** Google asks for the graphic and its text to be localised per market, so a graphic with copy is one render per store language, while a text-free one is a single file for every locale. Play also shows the app's icon and name next to the graphic and adds its own overlays in the promotional formats, so a lockup in the image repeats them, and a tagline may cover 20 percent of the image at most. Say all of that once in the plan card and offer the text-free version (a slide with no `copy`, plus `lockup: false`; `templates.md` section 2). Copy earns its place when the graphic has to say something the listing does not; the user decides. A brand graphic (a plate with the lockup large in the middle, `card-lockup`) repeats the icon's branding, which Google's page asks the feature graphic to avoid: say so once, the user decides.
- **The feature graphic's cutoff zones.** Play's page asks for the brand logo, the app name, the primary slogan and the main UI outside the zones it draws at the edges, for background elements at the edges only, and says a graphic that ignores the focal point and the zones may become ineligible for the formats that add their own UI overlays. Google draws the zones and states no number for them: `safe_insets` on `play-feature` is that 406x198 diagram measured on 2026-09-22 (left 61, right 59, top 29, bottom 31 px), about 15 percent per edge, so the safe box at 1024x500 is x 154 to 876, y 73 to 422. Card layouts lay their lockup, text and capture out inside that box by themselves; `compose` warns `cutoff_zone` when a rectangle still reaches a zone, which on a card means an explicit `bleed: true` or a plate whose screen sits at an edge. The measurement is in the `unverified` list of `surfaces.json`: it is read off a drawing, not from a published number.

## 1a. App Store creative assets (iOS 27 and iPadOS 27)

Apple published them on 2026-10-05; read on its pages on 2026-10-07 and again on 2026-10-12, unchanged (section 6). Optional images that App Store Connect keeps apart from screenshots and previews. They are card targets of store `app-store`.

| Target id | Pixels rendered | Also accepted in the same slot | Format | Art safe area (x, y, width, height) | Rule that matters |
|---|---|---|---|---|---|
| `appstore-header` | 3840x1646 (21:9) | 5244x2950 (16:9), PNG only | JPEG or PNG | 1097, 493, 1646x661: centred | the top of the product page: one clear idea for someone who has never seen the app, not a feature list |
| `appstore-search` | 3840x2560 (3:2) | any exact 3:2 from 1920x1280 to 3840x2560; 5244x2950 (16:9), PNG only | JPEG or PNG | 836, 765, 2168x1030: centred | the app's tile in search results: what it does, obvious at a glance, with the real interface |
| `appstore-universal` | 5244x2950 (16:9) | none | PNG only | 1921, 660, 1402x962: centred across, above the middle | the one file both placements take; App Store Connect offers "Use header asset in search results" only for it |

- **Where and when.** Shown on iOS 27 and iPadOS 27 or later (`shown_on`), on the product page, in search results, on custom product pages and in product page optimization tests. Uploaded per language. Apple reviews them against the app's latest version, alone through the Asset Library or with a version, and they go live with it. One asset per placement, page and language is what a product page shows; Apple states no count, so `max_count` is `null`. `compose` writes one file per locale as on every card; a text-free asset is the same file in every language.
- **Search results.** A search results asset takes the place of the screenshots and previews in search on iOS 27 and iPadOS 27; without one, in-app events, previews and screenshots appear as before. Older systems show no creative asset, so the first screenshots keep their job there (section 1).
- **Not the `universal` mode.** `appstore-universal` is Apple's name for one asset across two App Store placements. The skill's `universal` mode is one design for both stores. A set may list any of the three targets in any mode; `frame: "auto"` gives them `iphone` (`neutral-phone` in a `universal` deck, `browser` for a web or desktop capture), and a frameless phone capture borrows the iOS bars.
- **The art safe area.** Devices and orientations crop each placement differently. Apple asks for the focal point in the centre and the key elements inside a safe area, and draws that area only in its downloadable templates. `safe_insets` are the "Art Safe Area" rectangles of Apple's Sketch template, read on 2026-10-07 (in the `unverified` list: read from a template, not a published number). With `cutoff_zones` set, the card layouts lay lockup, copy and captures inside that box, as on `play-feature`; only the background reaches the edges, and `compose` warns `cutoff_zone` when something else does. A `card-lockup` slide without its own `width` takes the box's width where that is under 0.35 of the canvas: about 0.235 on `appstore-universal`. The boxes hold 17, 23 and 9 percent of the canvas: short copy or none, one capture at most, and a ground that carries the rest.
- **Judge in App Store Connect.** Its Preview shows the header and the search results asset on iPhone and iPad, in both orientations and every language. The `sheet` judges each asset at the width an iPhone gives it, measured on 2026-10-12 from Apple's demo videos on the best-practices page (unverified: Apple states no display size). The search results asset shows whole, as a rounded 3:2 card about 343 pt wide: its sheet is 343 px. The header shows at about 1.55:1 on an iPhone in portrait, roughly the centre two thirds of its width, under the back and share buttons at the top corners: its sheet is the whole canvas at 400 px, smaller than the phone shows it, and the template's safe box sits inside that crop. The universal asset keeps 640 px. The sheet shows no device's crop: after delivery, tell the user to check the Preview before submitting.
- **Content.** Apple's asset best practices: no prices, discounts, URLs or copyright symbols; no award or recognition the app did not receive; no Apple recognition (Editors' Choice, App of the Day, Game of the Day, Apple Design Award) even when it did; no logos of, or references to, other platforms or marketplaces; suitable for a 4+ age rating whatever the app's own rating; text optional, short and localised; current UI. `content_rules` makes `launchkit.py text` fail the first six (`store-policy.md` section 2a). Imagery and age suitability are yours to judge.
- **Video.** Both placements also take a looping video (`video` in the row): header 21:9 at 3840x1646, search results 3:2 from 1920x1280 to 3840x2560, 30 or 60 fps, 5 to 30 seconds, `.mov`, `.m4v` or `.mp4`, muted by default; in search results it cannot be unmuted. Apple lists no universal video. This skill composes stills; the videos are `/genmedia-skills:demo-video` work (`appstore-header-video`, `appstore-search-video`), cut from the user's real recording. For a recording in a drawn device, hand that skill `layers` (`references/composition.md` section 7b).
- **Plates.** Every canvas here is larger than one generation: GPT Image 2.5 stops at a 3840 px edge and 8.3 MP, Seedream 5.0 Pro at a 2048x2048 area. Generation sizes, and the upscale step `appstore-universal` always needs: `plates-and-prompts.md` section 4.
- **Heavy pages.** Measured on 2026-10-07 with headless Chrome and four jobs: upright cards at these sizes came out at about 1.5 s a page; a tilted `card-flow` or a `card-hero-scene` renders at 2x (10488x5900 on `appstore-universal`), about 9 s a page, with one browser process at 3.7 GB.

## 2. Web and launch targets

| Target id | Pixels rendered | Platform rule | Format | Byte cap | Rule that matters |
|---|---|---|---|---|---|
| `og` | 1200x630 | Facebook: at least 1200x630 for high-resolution screens, 1.91:1, under 600x315 the preview shrinks, 200x200 is the floor. LinkedIn: at least 1200x627, 1.91:1, under 401 px wide it becomes a small thumbnail | PNG or JPEG | Facebook 8 MB, LinkedIn 5 MB → **5 MB** | everything that matters sits inside the centred 1200x600 band and 60 px from every edge |
| `x-card` | 1200x600 | 2:1, at least 300x157, at most 4096x4096 | JPG, PNG, WEBP, GIF (first frame only); no SVG | under 5 MB | its own render, not a crop of `og`; see section 4 for the state of X's documentation |
| `ph-gallery` | 1270x760 | recommended size; the gallery shows once it has 2 or more images; no maximum stated | PNG or JPEG | launch guide: all images under 3 MB → **3 000 000 bytes** (section 5) | each image is one idea; the `sheet` judges it at about 320 px wide |
| `ph-thumbnail` | 240x240 | recommended square size; under 3 MB, GIF or not; a GIF animates only while the pointer hovers over the post | PNG, JPEG, GIF | under 3 MB → **3 000 000 bytes** | designed large, judged at 240, 80 and 40 px |
| `github-social` | 1280x640 | at least 640x320, 1280x640 for best display (2:1); one per repository, shown only from a public one | PNG, JPG, GIF | under 1 MB → **1 000 000 bytes** | a link card like `og`: 64 px gutter, 20 px type floor; a plate usually needs `export` jpg to fit the cap |

`compose` writes PNG, or JPEG through the set's `export`, and `validate` accepts PNG and JPEG on every target (`formats` in `surfaces.json`), whatever else the platform takes. A JPEG export searches quality from 0.92 down to 0.60 for the highest one under the byte cap; nothing fits → `jpeg_over_budget`. `compose` renders stills. A GIF thumbnail is outside v1: deliver the still, and if the user animates it elsewhere, remind them that the first frame is what most visitors see.

GitHub accepts PNG transparency but recommends a solid background when unsure; `compose` renders it opaque like every target. The 20 px floor and the gutter are working limits of this skill, as on `og`.

## 2a. Chrome Web Store (store `chrome-web-store`)

Read on Google's pages on 2026-09-23. All three are card targets, so they take the card layouts.

| Target id | Pixels rendered | Also accepted | Needed | Count | Rule that matters |
|---|---|---|---|---|---|
| `cws-screenshot` | 1280x800 | 640x400 | every listing | 1 to 5 | square corners, no padding (full bleed); the store downscales every screenshot to 640x400, so the `sheet` judges it at 640 px; localisable per locale |
| `cws-promo-small` | 440x280 | none | every listing | 1 | not localised: one file for every locale; items without it are listed after items that have it |
| `cws-promo-marquee` | 1400x560 | none | only to be featured in the marquee | 1 | not localised; reviewed before it shows (Google says within a week) |

- **Promo tiles carry the brand, not a screenshot, and no copy.** Google asks to avoid text, to make the tile work at half size, to assume a light grey page, to prefer saturated colours over white and light grey, to fill the whole region and keep its edges defined. Since the tiles are not localised, text-free is the default: no `copy`; the lockup (icon and name) is the one piece of type worth keeping, and the user decides. The `sheet` shows each tile at half size.
- The pages name PNG or JPEG for the promo tiles and no format for screenshots, and no alpha rule anywhere: `compose` writes opaque PNG or JPEG for all three; both points are in the `unverified` list. No byte cap is stated.

## 2b. Ad placement targets (store `ads`)

Stills for paid placements, composed for `/genmedia-skills:ads`, which owns the angle, the copy and the claim check. Read on the platforms' own pages on 2026-09-20.

| Target id | Pixels rendered | Where it runs | Format and cap | Rule that matters |
|---|---|---|---|---|
| `ad-feed-4x5` | 1440x1800 | Meta Feed image 4:5 (the Ads Guide states this size); Google App campaigns portrait 4:5 (1200x1500 recommended, 320x400 floor) | JPG or PNG; Meta 30 MB, Google 5 MB → **5 MB** | Google wants overlaid text and logos under 20 percent (`text_share`); Meta asks non-9:16 feed ads to keep the bottom and sides calm, without numbers |
| `ad-square` | 1200x1200 | Google App campaigns 1:1 (200x200 floor); Meta 1:1 (1080x1080 or larger); TikTok carousel (640x640 or larger) | **5 MB** | a square holds one upright phone and one line: `device-center` |
| `ad-vertical-9x16` | 1440x2560 | Meta Stories and Reels image; TikTok carousel 9:16 (720x1280 or larger) | 30 MB | keep about 14 percent at the top, 35 at the bottom and 6 on each side free of text and logos (`safe_insets`, warning `ad_safe_zone`); portrait layouts start their text below the top strip by themselves |
| `ad-landscape` | 1200x628 | Google App campaigns 1.91:1 (600x314 floor); TikTok carousel and Ad Network | **5 MB** | a card layout; `text_share` applies |
| `ad-video-9x16` | 1080x1920 | not an upload: the canvas for `layers` and end cards of vertical video ads | PNG | same safe insets; 9:16 is the vertical video ratio on Meta, TikTok (540x960 or larger) and Google App campaigns |
| `ad-video-16x9` | 1920x1080 | not an upload: the canvas for 16:9 video ads (YouTube, Google App campaigns) | PNG | the ratio is published, the pixel size is this project's choice |

Apple Ads has no row: it accepts no uploaded creative and builds every placement from the App Store product page or a custom product page, so its "creative" is an `appstore-*` screenshot set. TikTok's in-feed safe zone exists only as downloadable templates; Meta's box is the working default there, and the delivery says so. On ad targets `frame: "auto"` follows the capture's OS, and the store word lists do not run (an ad may call to action) unless the same set also lists a store target.

## 2c. Email cards (store `email`)

An image card in the body of a marketing or product email: a short title and the real interface, the way a product-update email shows a feature. No sending platform or mail client defines a card size, so the row is this project's choice (in the `unverified` list); the platform limits were read on Customer.io's and Mailchimp's pages on 2026-10-13.

| Target id | Pixels rendered | Shown at | Format and cap | Rule that matters |
|---|---|---|---|---|
| `email-card` | 1208x680 | 604x340: the content column of a 680 px email with 38 px gutters, about 16:9, at 2x for high-density screens; about 320 px wide on a phone | PNG or JPEG; Customer.io takes JPG, PNG or GIF through its editors up to 4096 px a side and 2 MB, and both platforms recommend at most 1 MB → **1 000 000 bytes** | the email carries its message as live text and alt text; the card repeats one short title. Judge it on the `sheet` at 320 px |

- **Text stays text.** With images off a card says nothing. Keep the headline short, say the same thing in the email's own text, and write the alt line from the card's copy.
- **No lockup by default.** The email's header carries the brand, so a set of email cards usually says `lockup: false` and `compact: true`, which gives the lockup's room to the copy (`templates.md` section 2). `theme.badge_style: "text"` turns the badge into a quiet eyebrow (`composition.md` section 2).
- **Weight.** Export as `jpg` (`composition.md` section 2): the cards composed on 2026-10-13 came out at 80 to 107 KB at quality 0.92 on a gradient ground (`templates.md` section 6); a busy plate weighs more. A sending platform or review with a lower limit than 1 MB wins: re-encode the delivered JPEG for it and keep the composed file as the master.
- The row fits a column near 604 px: a 600 or 660 px template scales it by a few percent. A slot of another shape needs another size; say so instead of letting the client crop or stretch the card.

## 3. Why one file cannot serve both stores

| Surface | Long side : short side |
|---|---|
| `appstore-iphone-69` 1320x2868 | 2.17 : 1 |
| `appstore-iphone-65` 1284x2778 | 2.16 : 1 |
| `appstore-iphone-63` 1206x2622 | 2.17 : 1 |
| Play screenshot, any device | **at most 2 : 1** |
| `play-phone` 1080x1920, `play-tablet` 1440x2560 | 1.78 : 1 |
| `appstore-ipad-13` 2064x2752 | 1.33 : 1 |

An iPhone-sized file breaks Play's 2:1 limit, and a 9:16 file is not an accepted App Store size. Scaling one into the other means stretching or cropping, and Play's page says outright not to upload stretched or compressed images. So:

1. **`both`**: two sets with shared copy and layout choices, each rendered at its store's size with its own frame and status bar.
2. **`universal`**: one deck, one design, and still **one render per store size**. `sets[].targets` lists the targets of both stores; `compose` lays the page out again for each target (text box, device scale and margins are recomputed), so nothing is stretched. What makes it universal is the content: a `neutral-phone` frame or `none`, a status strip without glyphs, and nothing that identifies a platform (`store-policy.md` section 4).
3. The iPad and tablet sets are separate compositions. A phone slide scaled onto 3:4 leaves a device that is too small and an empty band; expect `device_share` and `empty_band` warnings if you try.

## 4. Open Graph and the X card from one layout

- One card layout produces one file per target: `og` at 1200x630 and `x-card` at 1200x600. The X file is rendered on its own page at 2:1, not cut from the OG file.
- The safe band is the centred 1200x600 area of the OG card: 15 px at the top and at the bottom hold background only. Inside the band keep a 60 px gutter. `compose` reports `safe_crop` when content leaves the band and `gutter` when it comes closer than 60 px to an edge.
- **2x (optional):** `scales: [1, 2]` on both rows. `"export": {"og": {"scale": 2}}` renders 2400x1260, `x-card` 2400x1200, for high-density screens; the 1x file stays the default and a 2x render replaces it rather than sitting next to it. X states at most 4096x4096. Facebook's and LinkedIn's pages, re-read on 2026-09-23, name a minimum and a byte cap but no maximum pixel size for link previews; LinkedIn's page caps single-image ads at 7680x4320, far above 2400x1260. Layout, gates and `min_text_px` stay in 1x pixels. The byte cap does not double: a 2x card with a plate usually needs `"format": "jpg"` too.
- The practical byte cap for both files is 5 MB: LinkedIn's limit is 5 MB, X's last documented limit is under 5 MB, and Facebook's 8 MB does not help when the same file serves all three. A flat or gradient card is far below that as PNG; a photographic plate may need JPEG.
- **X caveat.** X has no live official page for card images today: every Cards URL on the old developer site redirects to the general documentation home. The numbers in section 2 come from the last archived copy of the official "Summary with large image" page, captured 2026-01-12. Treat them as the last known official values and say so when the user asks.
- `surfaces.json` also gives `og` and `x-card` a type floor, `min_text_px: 20`: copy on these cards never renders smaller, and `compose` warns `small_text` below it. Like the 5 MB cap it is a working limit of this skill for a preview seen at about 400 px, not a platform rule.
- A LinkedIn or Facebook preview built from a file narrower than the thresholds above turns into a small thumbnail next to the text. 1200 px wide avoids that on both.
- Meta tags, caching and framework file conventions: `og-cards.md` section 9.

## 5. Product Hunt

- Gallery: 1270x760, at least two images or the gallery is not shown. No maximum is stated: plan four to six and stop when the story is told (`copy-and-narrative.md` section 7).
- Thumbnail: square, 240x240 recommended. The `sheet` also shows it at 80 and 40 px, because small placements are where a thumbnail fails.
- Byte cap, 3 000 000 bytes on both targets. The launch guide's thumbnail entry says "All images, GIF or not, need to be under 3MB"; the help page states the 3 MB only for a GIF thumbnail, and neither page names a byte limit in its gallery text. `surfaces.json` reads the guide's sentence as covering gallery images too, and 3 MB as 3 000 000 bytes: the lower readings, both named in the `unverified` entry `ph-gallery.max_bytes`. A gallery PNG over it warns `bytes_over_cap`; a JPEG export stays under it or fails `jpeg_over_budget`.
- GIF thumbnails: hover-only animation. Product Hunt's help page and launch guide warn against strobing, quick cuts and unreadable text and say its team may edit such files.
- Video on Product Hunt is a full YouTube URL. That is a video job, not a still: out of scope here; `short-video` and `video-explainer` make videos.

## 6. Sources (opened 2026-09-20 unless the row says otherwise)

| Facts | Page |
|---|---|
| App Store sizes, counts, formats, alpha, requirement notes | https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications |
| First one to three screenshots in search | https://developer.apple.com/app-store/product-page/ |
| Creative assets: image and video sizes, formats, alpha (opened 2026-10-07, re-read 2026-10-12) | https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications/ |
| Creative assets: iOS 27 and iPadOS 27, universal asset, "Use header asset in search results", languages, review (opened 2026-10-07, re-read 2026-10-12) | https://developer.apple.com/help/app-store-connect/manage-app-information/manage-your-app-store-assets/ |
| Creative assets: content rules, header and search guidance, safe area, search fallback, templates (opened 2026-10-07, re-read 2026-10-12) | https://developer.apple.com/app-store/asset-best-practices/ |
| Art safe areas: the Sketch template `creative_assets-templates.sketch` linked from that page (read 2026-10-07, not redistributed) | https://developer.apple.com/app-store/asset-best-practices/ |
| Play screenshots, feature graphic, counts, formats, 2:1 limit, promotion eligibility, large-screen text, alt text | https://support.google.com/googleplay/android-developer/answer/9866151 |
| No alt-text field on uploaded Play images (opened 2026-09-23) | https://developers.google.com/android-publisher/api-ref/rest/v3/edits.images |
| Facebook image sizes, 8 MB, thresholds, no maximum (re-read 2026-09-23) | https://developers.facebook.com/docs/sharing/webmasters/images/ |
| LinkedIn image size, 5 MB, 401 px threshold, no maximum for shares, 7680x4320 for ads (re-read 2026-09-23) | https://www.linkedin.com/help/linkedin/answer/a521928 |
| X large card | archived copy of 2026-01-12 of `developer.x.com/en/docs/x-for-websites/cards/overview/summary-card-with-large-image`; the live URL redirects to `docs.x.com/overview` |
| Product Hunt gallery, thumbnail, GIF, video (re-read 2026-10-26) | https://help.producthunt.com/en/articles/479557-how-to-post-a-product |
| Product Hunt launch guide: gallery 1270x760 and 2+ images, thumbnail 240x240, all images under 3 MB (opened 2026-10-26) | https://www.producthunt.com/launch/preparing-for-launch |
| Meta ad image sizes, formats, 30 MB, safe zones | https://www.facebook.com/business/ads-guide/update/image/facebook-feed/app-installs, `…/image/instagram-story/app-installs`, `…/image/instagram-reels/app-installs`, https://www.facebook.com/business/help/980593475366490, https://www.facebook.com/business/help/469767027114079 |
| Google App campaign image ratios, sizes, 5 MB, text share | https://support.google.com/google-ads/answer/17091671, https://support.google.com/google-ads/answer/6167158 |
| TikTok carousel and in-feed sizes | https://ads.tiktok.com/help/article/specifications-for-carousel-ads, https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads |
| Apple Ads creative source | https://ads.apple.com/app-store/help/ad-placements/0081-ad-placement-options |
| Mac sizes, iPhone and iPad landscape sizes (opened 2026-09-23) | https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications |
| Play 7-inch and 10-inch tablet slots, large-screen rules (opened 2026-09-23) | https://support.google.com/googleplay/android-developer/answer/9866151, https://developers.google.com/android-publisher/api-ref/rest/v3/AppImageType |
| Chrome Web Store screenshots and promo tiles (opened 2026-09-23) | https://developer.chrome.com/docs/webstore/images, https://developer.chrome.com/docs/webstore/cws-dashboard-listing |
| GitHub social preview (opened 2026-09-23) | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview |
| Email image limits: editor uploads, formats, 4096 px, 2 MB, hosted images under 1 MB (opened 2026-10-13) | https://docs.customer.io/messaging/channels/image-support/ |
| Email template widths 600 and 660 px, image widths, 1 MB recommendation (opened 2026-10-13) | https://mailchimp.com/help/image-requirements-for-templates/ |

Not in v1 and therefore not in the tables: Apple TV, Vision Pro, Apple Watch, Wear OS, Android TV, Android Automotive, Android XR, store preview videos, the creative assets' video variants, App Store in-app event media (on the creative assets page). A user who asks for one of them gets the honest answer that the size has not been verified for this skill, plus the official page to read.

## 7. Keeping the table honest

1. State the verification date in the plan card the first time a size is mentioned.
2. A user reports a rejected size, or the date is older than a device generation → open the source page, compare, and tell the user what changed before rendering again. Do not patch the number silently.
3. `validate` is the last word before delivery: exact size (or a listed alternate, or inside Play's allowed range or Apple's 3:2 search results range, each with a `size_note`, or the 2x size where the target lists `scales`), the format that size takes (5244x2950 is PNG only on every App Store creative asset), no alpha, a JPEG's content matching its name with three colour components, count inside the limits, zero-padded order, byte cap where one exists, and a proof file that matches each PNG.
