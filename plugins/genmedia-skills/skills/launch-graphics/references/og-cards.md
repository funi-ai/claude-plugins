# Link cards: Open Graph and X

The image a link shows when it is pasted into a feed, a chat or a team channel. It is seen for a second, at about 400 px wide, next to a title the platform renders itself. This file covers which pages get their own card, what goes on one, which layout to pick, the type scale, the safe area, series and batch work, and the delivery note with the tags to add. Sizes and byte caps are in `surfaces.md`. Platform facts: **Verified: 2026-09-20** against the pages in section 11; `surfaces.json` and the official page win when they disagree with this file. Pixel values assume the 1200 px wide targets `og` (1200x630) and `x-card` (1200x600). `launchkit.py` abbreviates the call shown in SKILL.md.

## 1. Which pages get their own card

| Page | Card |
|---|---|
| Home page | own card; it doubles as the **brand default** for every page without one |
| Product, feature and use-case pages | own card: the feature's promise plus its real screen |
| Pricing | own card; a price on it only when the page shows the same price |
| Launch or announcement page, changelog highlight | own card; the link most likely to be shared in launch week |
| Blog posts, guides, release notes | own card each, produced as a series from the list of titles (sections 7 and 8) |
| Documentation | one card per section or product area, not per page |
| Comparison and alternatives pages | own card, without the other product's logo or name in the image |
| Legal, login, account, settings, search results, tag archives, paginated lists, error pages | the brand default |

Two reasons not to stop at one site-wide image: X's card documentation asked for an image that is specific to the page rather than a generic logo shared by many pages, and a feed full of identical cards tells a reader nothing about where the link leads. One reason not to make hundreds by hand: section 8.

## 2. What goes on a card

1. **Title**: one or two lines (three on a half-width layout), written for someone who has never heard of the product. It may be shorter than the page's own title; it is not the site name.
2. **One subtitle** at most: the fact the title lacks. Often none.
3. **One data point** at most, in `badge` (24 characters): a version, a date, a user-supplied number from `facts.numbers`, a category label ("Guide", "Changelog"). Every digit in it has to be in `facts.numbers`, a version or a date included. Two numbers on a card is a table nobody reads.
4. **Brand mark**: `app.logo`, or `app.icon` plus the app name, from the user's files. The layout fixes its place: top left, top centre on `card-centered` and `card-flow` (top left with `caption: "left"`), none on `card-browser`. Never a generated logo.
5. **Tone** follows the page: a changelog card is plain, a launch card may carry a plate. The claims gate applies as on any target (`store-policy.md` section 6).
6. The platform draws the page title, the description and the domain under or over the image. Repeating all three inside the image wastes the space; Apple's guidance for Messages previews goes further and advises against text in the image at all, because the image is shown at varying sizes. A card that must work in Messages keeps the title large and everything else out.

## 3. Layouts

| Layout | What it is | Use when | Avoid when |
|---|---|---|---|
| `card-hero-scene` | a generated plate with a flat chroma screen; the real capture is warped into the quad, the headline sits beside it | the home page, a launch, a mobile app that should feel held and used | the capture is a desktop screen; no budget for a plate; the title needs more than half the width (`text_overlaps_device` is a hard gate). Details: `hero-scenes.md` |
| `card-left-title` | title block on the left, framed capture on the right | feature and product pages with one clear screen; the workhorse | the screen is a dense dashboard that turns to grey noise at 400 px: use `card-browser` with a closer capture, or `card-minimal` |
| `card-centered` | title and capture on one centred axis | short titles, symmetrical brands, a single phone screen | titles that need more than two lines of about 24 characters |
| `card-minimal` | no capture: title, optional subtitle, `badge`, mark | blog posts, guides, docs sections, pricing, any page without a screen worth showing; the layout for series | the page sells an interface: show it |
| `card-browser` | a large framed desktop capture with a caption | web apps, dashboards, developer tools, terminal output | phone captures; captures with small text as the main content |
| `card-flow` | two captures side by side, before → after, frameless, an arrow between them | a product whose value is a transformation: the input and what it made of it; `caption: "left"` puts it in a `card-left-title` series (same lockup, text box and type size, the pair on the right) | the two screens are not one story; one of them is unreadable at the pair's size |

The frame comes from the capture's `os`: `web` and `desktop` resolve to `browser` (its address pill shows the host of `app.url`), `ios` to `iphone`, `android` to `android-phone`; the drawn window never shows a real browser's chrome. The frame never crops the capture; a bleeding layout lets the device run off the card's edge. The same layouts serve `ph-gallery` and `play-feature`. On `play-feature` `frame: "auto"` draws the Android phone: to leave the device out (`store-policy.md` section 3) use `card-minimal` or `frame: "none"`. Geometry and `bleed` per layout: `templates.md` section 2.

## 4. Backgrounds: free or generated

| Kind | Cost | Looks like | Use for |
|---|---|---|---|
| `solid` | $0 | one theme colour | documentation, changelogs, anything that should look calm and load small |
| `gradient` | $0 | two theme colours at an angle (`from`, `to`, `angle`) | the default for series; varies per category by swapping the pair |
| `plate` | one generation, then $0 for every card that reuses it | an abstract or scenic image made to sit behind text | the brand default, launch cards, a series that wants its own look |
| `plate` with a chroma quad | one generation per scene | a hand-held or desk scene for `card-hero-scene` | hero cards only |

- CSS-only grounds are the default. Propose a plate when the user asks for one, when the card is the brand default, or when a launch deserves it, and say what it costs before generating (`plates-and-prompts.md`).
- A plate for text needs a quiet area where the title goes. The contrast gate measures the real pixels under each text box: below 3.0 fails, 3.0 to 4.5 warns. Fix the plate or the placement, not the gate.
- Plates carry no text, no logos and no interface. Everything readable is HTML on top.

## 5. Type scale: what the script does

There is no size ladder to choose from. Every layout has one start size, a share of the card's width unit (the smaller of the width and 1.9 times the height); the fit pass keeps it when every authored line fits on one row of the text box, and otherwise shrinks it in 2 percent steps down to 72 percent. Below that the page fails with `copy_too_long`: rewrite the title. `fit_scale` under 0.9 warns. `launchkit.py text` and the fit pass decide, not this table; the pixel values are for `og` (unit 1197 px) and come from the script's shares.

| Layout | Start size | Floor | Text box | Budget: lines x characters | `sub` | `badge` |
|---|---|---|---|---|---|---|
| `card-minimal` | 89 px (7.4 percent) | 64 px | 960 px | 3 x 20 | 30 px | 24 px |
| `card-centered` | 74 px (6.2 percent) | 53 px | 960 px | 2 x 24 | 27 px | 20 px |
| `card-left-title` | 72 px (6 percent) | 52 px | 528 px | 3 x 14 | 27 px | 20 px (floor) |
| `card-hero-scene` | 72 px (6 percent) | 52 px | from the margin to 60 px before the screen quad, on the side away from the phone | 3 x 14 | 27 px | 20 px (floor) |
| `card-browser` | 51 px (4.3 percent) | 37 px | 1008 px wide; its height grows with the caption and the window shrinks to fit | 2 x 34 | 26 px | 20 px (floor) |
| `card-flow` | 67 px (5.6 percent) | 48 px | 1008 px wide; its height grows with the caption and the pair shrinks to fit | 2 x 28 | 28 px | 20 px (floor) |
| `card-flow`, `caption: "left"` | 72 px (6 percent) | 52 px | 528 px, as `card-left-title`; the pair sits in the right 42 percent | 3 x 14 | 27 px | 20 px (floor) |

- **The 20 px floor.** `og`, `x-card` and `github-social` carry `min_text_px: 20` in `surfaces.json`: `sub` and `badge` never render below 20 px, however far the headline shrinks. Copy that would have needed smaller type runs out of room and fails as `copy_too_long`; anything that still ends under the floor warns `small_text`. Every file reports `metrics.min_text_px`, the smallest copy size it rendered.
- `x-card` runs about 5 percent smaller (unit 1140 px), `ph-gallery` about 6 percent larger (1270 px), `email-card` about 1 percent larger (1208 px), `play-feature` about 20 percent smaller (950 px). Above the floor `sub` and `badge` shrink with the headline. `ph-gallery`, `email-card` and `play-feature` have no floor: a `card-left-title` badge on `play-feature` starts at about 15 px, so judge those on the `sheet`.
- The character budgets assume a heavy sans with an average glyph about half an em wide; a condensed or a wide face, capitals and wide letters shift them. `metrics.headline_px` tells the size a page ended up with.
- **The badge is the smallest type on a card.** At a 400 px preview a 20 px badge is under 7 px high: a colour chip with a hint of a word, not something to read. Keep it to one word or one number and never put the card's key fact only there.
- A title that needs the floor is usually a page title pasted in. Write the card title instead: drop the site name, the series name (it lives in `badge`) and the subtitle after the colon.
- Decide the line breaks yourself (line arrays). Break by phrase; balance the lines; no single word alone on the last line.

## 6. Safe areas, feeds and the small-size check

1. **Gutter:** 60 px on every side. `compose` warns with `gutter` on `og` and `x-card` when text comes closer.
2. **The 2:1 band:** the centred 1200x600 area of the OG card is what the X card keeps. Title, subtitle, `badge`, mark and the part of the capture that matters all sit inside it; the outer 15 px at top and bottom hold background only. `safe_crop` names anything outside.
3. **Corners:** feeds commonly round the corners of previews (an interface habit, not a published rule). Keep marks and badges a little further in than the gutter demands, never in the extreme corner.
4. **Light and dark feeds:** a pure white card has no edge on a white page, a near-black one none in dark mode. Tint the ground: a `bg` one step away from pure white or pure black. The script draws no border around a card. The `sheet` shows every card on a light and a dark strip.
5. **The 400 px check:** build the `sheet`, Read it, look at the small view first. Can you read the title without guessing? Can you tell what kind of page this is? Does the capture look like a product or like texture? Write down what you read before comparing it with the deck.
6. Size and weight: a flat or gradient PNG is tens to a few hundred kilobytes. A photographic plate can pass 1 MB; above the 5 MB cap `compose` warns `bytes_over_cap` and `validate` fails the file as `too_large`, and well before that a JPEG export is worth offering: `"export": {"og": {"format": "jpg"}, "x-card": {"format": "jpg"}}` on the set (`composition.md` section 2). The browser picks the highest quality from 0.92 down that stays under 5 MB and the proof records it.
7. **2x for sharp screens:** `"scale": 2` in the same `export` entry renders `og` at 2400x1260 and `x-card` at 2400x1200 instead of the 1x file: same layout, gates and type floor, twice the pixels. X takes up to 4096x4096; the Facebook and LinkedIn pages read for this skill name minimums and byte caps, no maximum (`surfaces.md` section 4). A 2x PNG with a plate gets heavy fast: pair it with `jpg`. Offer it when the user asks for crisp previews; 1x stays the default.

## 7. Series consistency

| Stays the same on every card of the series | Varies per card |
|---|---|
| layout (`card-minimal` or `card-left-title`), margins, mark position | title and its line breaks |
| type family, weights, the layout's start size | `fit_scale`: write every title to the budget so it stays at 1.0 and all cards share one type size |
| palette and ground style (one gradient pair or one plate per series) | `badge` text: issue number, category, date |
| position and style of `badge` | the capture, on layouts that have one |
| tone of voice of the titles | an accent colour per category, from a fixed list of at most five |

Write the table for the user's series once in the plan, then apply it without drift. On a card series every slide shares one layout on purpose. `adjacent_layout_repeat` and `no_inverted_slide` are raised for store screenshot sets only, so a card set never sees them.

## 8. Batch production

1. The user gives a list: one row per page with slug, title, and optionally subtitle, `badge` and locale. A pasted table, a CSV or the site's content folder are all fine; read it, do not ask for it to be retyped.
2. Rewrite titles that break the budgets of section 5 and show the before and after for those rows only. The user approves the list once.
3. One set with the targets `og` and `x-card`, one slide per page (the slide id is the page slug: lower-case letters, digits and hyphens, 40 characters at most), one shared `background`. A plate is generated once, approved once, then reused: every further card costs $0 and a second of rendering.
4. `launchkit.py text` over the whole set (`findings[]` lists only the rows with a problem), then `compose`, then `validate`. Failures come back per slide in `failed[]` and warnings grouped in `warnings_by_kind`; fix those rows and compose them again by slide id.
5. Review the `sheet`, not forty full-size files: the small view shows the outliers (a title two sizes smaller than its neighbours, a `badge` that wraps).
6. New posts later: add slides to the same deck. The series table of section 7 is already decided, so the new cards match. Removing or reordering rows renumbers the files: run `compose` once without `--slide`, and the cards of rows that left the deck are pruned and listed in `pruned`.

## 9. Delivery note: tags, URLs, caching

Deliver the files first (`og/<locale>/NN-<slide id>.png` and `x-card/<locale>/NN-<slide id>.png` under the output folder, `.jpg` for a JPEG export, or `og--<set id>/…` when an earlier set of the deck already owns the target; the user names them as the site needs), then this block with the user's real URLs filled in, then one line on where the files go.

```html
<meta property="og:image" content="https://example.com/og/pricing.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Pricing page of Mola: three plans side by side">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/og/pricing-x.png">
<meta name="twitter:image:alt" content="Pricing page of Mola: three plans side by side">
```

1. **Absolute HTTPS URLs**, publicly reachable without a login, cookies or JavaScript. Apple states that Messages neither runs JavaScript nor follows meta redirects when it builds a preview; assume the same of every other crawler.
2. **Width and height tags** let Facebook's crawler show the image on the first share instead of after it has fetched and measured the file.
3. **Alt text** describes what is in the image, not a caption. X's last documented limit is 420 characters; one sentence is enough.
4. **Replacing an image:** publish it under a **new file name** (`pricing-v2.png`) and update the tag. Facebook's documentation asks for a new URL and offers its Sharing Debugger to fetch the page again; LinkedIn's Post Inspector refreshes the preview for new posts, and posts already made keep the old image.
5. **`og:title`** without the site name keeps previews from saying the brand twice; Apple's guidance for Messages asks for exactly that and points to `og:site_name` for the brand.
6. **Where the file lives:** any path the site serves as a static file at a stable URL, usually the framework's public or static folder. Next.js App Router has a file convention instead of hand-written tags: `opengraph-image.(jpg|jpeg|png|gif)` and `twitter-image.(jpg|jpeg|png|gif)` placed in a route segment, with optional `opengraph-image.alt.txt` and `twitter-image.alt.txt` next to them; the tags are generated, and the build fails when `twitter-image` exceeds 5 MB or `opengraph-image` exceeds 8 MB. With hand-written metadata in Next.js, relative image paths resolve against `metadataBase`: set it. For any other framework, look at the project before advising and do not guess a convention.
7. This skill does not edit the user's site unless asked, and never deploys.

## 10. How chat apps treat the image

| App | Verified today | Otherwise |
|---|---|---|
| Apple Messages | reads `og:image`; wants images at least 900 px wide; under 150 px wide they may be ignored or shown as an icon; the page itself is limited to 1 MB and all fetched resources together to 10 MB; Apple calls these guidelines that may change | - |
| Slack | classic unfurls read Open Graph and X card metadata and draw a small approximation of the page | no sizes or crop rules are published: check in a test channel |
| WhatsApp, Telegram, Discord, Signal, Teams | nothing verified for this skill | check on the platform: paste the staging link into a private chat before launch |

What follows for design, regardless of app: previews are drawn at sizes the author does not control (Apple says so outright), so plan for the smallest case. The title sits in the middle band, and a card whose only content is a long sentence fails first.

## 11. Sources (all opened 2026-09-20)

| Facts | Page |
|---|---|
| Tag definitions, `og:image:alt` | https://ogp.me/ |
| Facebook sizes, width and height tags, new URL for a new image | https://developers.facebook.com/docs/sharing/webmasters/images/ |
| LinkedIn image rules; Post Inspector | https://www.linkedin.com/help/linkedin/answer/a521928 · https://www.linkedin.com/help/linkedin/answer/a6233775 |
| X large card, alt length, page-specific image | archived official copy of 2026-01-12 (`surfaces.md` section 4) |
| Apple Messages previews | https://developer.apple.com/documentation/technotes/tn3156-create-rich-previews-for-messages |
| Slack unfurling | https://docs.slack.dev/messaging/unfurling-links-in-messages/ |
| Next.js file conventions and `metadataBase` | Next.js documentation, `opengraph-image` and `generateMetadata` pages, read through `ctx7` |
