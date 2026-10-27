# Copy and narrative

How to write the words before any layout exists, how to judge the user's captures, and how to order a set so it reads as one story. A store visitor gives a set about as long as a swipe; the headline of slide 1, read at the size of a postage stamp, does most of the work. Numbers here are this skill's authoring targets, not platform rules; the binding budget per layout is what `launchkit.py text` reports, and it wins. The few platform facts repeated here (slide counts, what store search shows, Product Hunt's minimum) come from `surfaces.md`, Verified: 2026-09-20; `surfaces.json` and the official page win when they disagree. `launchkit.py` abbreviates the call shown in SKILL.md.

## 1. Copy first

1. Collect what is true: what the product does, for whom, and the user's own proof (`facts.numbers`, `facts.claims`). Look at every capture before writing a word.
2. Write **all** headlines of the set as plain text, three angles for slide 1 and for any slide you are unsure of (section 2). No layout, no colours yet.
3. Show the copy in the plan card as a numbered list, one line per slide, with your pick marked. The user approves or edits the words. Layout starts only after that; a layout built around unapproved words is built twice.
4. Write the approved lines into `copy` of each slide as **line arrays**: you decide the breaks, the compositor never re-wraps. Run `launchkit.py text` before composing.
5. After approval, words change only when the user asks or a gate fails (`copy_too_long`, a claims failure). A failed fit is fixed by rewriting, never by shrinking below the floor.

## 2. Headlines: three angles, one idea

| Angle | Question it answers | Example (fictional budgeting app) |
|---|---|---|
| A moment | when do I reach for this? | `["Rent is due.", "You already know."]` |
| An outcome | what is different afterwards? | `["Know what's left", "before payday"]` |
| A pain removed | what stops hurting? | `["No more", "month-end surprises"]` |

1. **One idea per headline.** "Track, plan and share" is three slides or none.
2. **The capture proves the headline.** If the screen under the words does not show the thing the words promise, change one of them.
3. **Breaks are deliberate.** Break between phrases, never inside one: not after an article, a preposition or an adjective waiting for its noun. The last line is not a single short word left alone. Two lines are the norm, three the limit on a phone slide.
4. **`emphasis`** names one word or short phrase that occurs in the headline exactly as written; it takes the accent colour. It marks the payoff ("payday"), never a filler word, and there is one per slide at most.
5. **`sub`** is optional and earns its place only when it adds a fact the headline lacks. Most slides are better without it, and on `play-*` targets it is the first thing to go when `play_tagline_share` warns.
6. **`badge`** is the home of proof: one short user-supplied fact, slide 1 only on store sets (`store-policy.md` section 6).
7. Sentence case. All caps only for one or two words, taken from the `upper` field of `launchkit.py text --full` (upper-cased for the locale), never by hand.
8. Feature names, adjectives without a noun ("Powerful. Simple. Fast.") and words the store listing already carries in its title are wasted space.

## 3. Budgets per layout family

| Layouts | Script budget: headline lines x characters per line | Script budget: `sub` | Aim for |
|---|---|---|---|
| `device-bottom`, `device-top`, `two-devices` | 3 x 18 | 2 lines x 40 | 2 to 6 words on 2 lines, 16 characters or fewer; no `sub`, or one line |
| `device-center` | 2 x 20 | 2 x 40 | 2 lines; the `sub` sits alone under the device, so one line |
| `zoom` | 3 x 18 | 2 x 40 | 2 to 4 words, 1 or 2 lines, no `sub`: the crop is the message |
| `text-only` | 4 x 13 | 3 x 36 | up to 8 words over 3 or 4 short lines |
| `card-left-title`, `card-hero-scene`, `card-flow` with `caption: "left"` | 3 x 14 | 3 x 36 (`card-hero-scene`: 2) | 2 lines; the box is under half the card |
| `card-centered` | 2 x 24 | 2 x 56 | one line where possible |
| `card-minimal` | 3 x 20 | 2 x 56 | the title as the reader would say it |
| `card-browser` | 2 x 34 | 1 x 60 | one caption line; the window does the talking |
| `card-flow` | 2 x 28 | 1 x 60 | one line naming the change, or none: the pair and the arrow tell it |
| any `card-*` on `play-feature` | the layout's budget | the same | 2 to 4 words and usually no `sub`: `play_tagline_share` warns above 20 percent of the image |
| any `card-*` on an App Store creative asset | the layout's budget | the same | none, or 2 to 5 words and no `sub`: the header names one idea, the search asset says what the app does; Apple asks for short phrases that add to the picture, and the layout sits in Apple's art safe area |
| `thumb-icon` | no words; the icon, or the first letter of the app name | - | - |

The budgets belong to the layout, not to the target: type scales with the canvas, and `text` reports the same numbers for a phone, a tablet and a landscape set. The fit pass finds out what a box really holds; the side-by-side landscape layouts on tablet targets are the tightest (a 17-character line needed `fit_scale` 0.78 on a landscape `appstore-ipad-13` page). `badge` takes 24 characters everywhere. More lines than the budget is an error in `launchkit.py text` (`too_many_lines`), more characters a warning (`chars_per_line`). Start sizes and floors per layout: `templates.md` section 2 and `og-cards.md` section 5.

`launchkit.py text` and the fit pass decide, not this table. Longer lines do not fail at once: the fit pass shrinks the type in 2 percent steps, `fit_scale` below 0.9 is a warning that the words are too long for the box, and at 72 percent of the layout's start size the page fails with `copy_too_long`. Turkish, German and Finnish words run long: budget by characters, not by words (`localization.md`).

## 4. Capture triage and the capture list

Rate every capture the user gives before planning slides. Say the rating and the reason in one line each.

| Rating | Meaning | Typical signs |
|---|---|---|
| **Great** | use as is | the feature in its active state, believable data, native pixel size (`fullscreen_match` found), status bar clean or absent, same appearance mode as the rest |
| **Usable** | the content is right, the frame of it is not | status bar dirty over a flat colour (the status-bar policy repaints it), no status bar at all (a strip is added), a little empty space at the bottom |
| **Retake** | would weaken or mislead | empty state, test data ("asdf", "Test User", 0,00), debug banner or build ribbon, keyboard covering the content, spinner or skeleton, login, splash or onboarding-only screen, notification banner, real people's names or e-mail addresses, a forwarded or compressed copy, a simulator window with desktop chrome, the wrong language for the locale, light mode in a dark set |

Retake coaching, given as concrete instructions, not as a complaint:

1. **Real-looking data.** A demo account with a full week of entries, round-but-not-too-round amounts, names from the target market, no real customers.
2. **Active state.** The chart after the data arrived, the list with a swipe action open, the timer running at 12:34, the toggle on. The moment the headline talks about.
3. **One appearance mode per set.** All light or all dark; a single inverted slide is a design choice made in the deck, not an accident of the capture. `captures.<id>.colors.scheme`, measured by `capture add`, says `light` or `dark` per capture: a quick way to spot the odd one out.
4. **Nothing from the build.** No debug ribbons, no feature-flag menus, no "staging" labels, no placeholder avatars.
5. **Clean status bar, or none.** Simulator and emulator overrides are in `devices-and-statusbar.md`. A full-screen capture at native size beats a cropped one.
6. **Native size, original file.** PNG straight from the device or simulator. HEIC or TIFF → `capture add` answers `convert_first` with the conversion hint.

The capture list is what you hand the user when screens are missing. **Every slot names a real screen of their product and the state it should be in.** "Feature screen 2" or "a nice dashboard" is not allowed; if you do not know the product well enough to name the screen, ask what the screen is called.

```text
Capture list: Mola (focus timer), iOS, light mode, demo account
1. timer-running   Timer tab, session running at 12:34 of 25:00, task name "Sunum taslağı"
2. week-stats      Statistics tab, week view, at least five days with sessions, today highlighted
3. block-list      Blocked apps sheet, four apps switched on
4. session-done    Completion screen right after a session, streak visible
```

The ids become the keys of `captures`. A slot the user cannot fill is dropped from the set; it is never filled with a generated screen. A design export stands in only with `mockup: true`.

## 5. Weak versus better

All apps are fictional. Line arrays show the intended breaks.

| Product | Weak | Better | Why |
|---|---|---|---|
| Budgeting app | "Powerful budgeting features" | `["Know what's left", "before payday"]` | outcome instead of a feature label |
| Habit tracker | "Track your habits easily" | `["Two taps.", "Habit logged."]` | a moment; "easily" proves nothing |
| Meditation app | "The #1 meditation app" | `["Ten calm minutes", "before the inbox"]` | the ranking fails the claims gate; the moment does not |
| Plant care (tr) | "Bitkilerinizi kolayca takip edin" | `["Fesleğen susadı.", "Haberin olsun."]` | one plant, one moment; the capture shows the reminder |
| Running app (tr) | "Gelişmiş koşu istatistikleri" | `["Geçen haftaki", "kendini geç"]` | outcome; "gelişmiş" is an adjective without proof |
| Invoicing app (tr) | "Fatura oluşturma ve yönetim modülü" | `["Faturayı kes,", "işine dön"]` | pain removed, in the customer's words, 13 and 9 characters |
| Children's reading app (tr) | "Çocuğunuz için eğitici içerikler" | `["İlk kitabını", "kendi okusun"]` | the parent's wish; emphasis on "kendi" |
| Shared shopping list (tr) | "Alışveriş listesi paylaşım özelliği" | `["Evdeki herkes", "aynı listede"]` | says who benefits; no word ending in "özelliği" |
| Developer tool, link card | "Introducing v2 of our CLI with many improvements" | `["Preview every branch", "with one command"]` | the card is read in a feed by people who do not know v1 |
| Team calendar | "Seamless scheduling for modern teams" | `["Find the hour", "everyone is free"]` | concrete noun, concrete verb, no "seamless" |

Words that mark a weak line in any language: powerful, seamless, smart, easy, all-in-one, next-generation, gelişmiş, kolayca, akıllı, yenilikçi, "özelliği", "modülü".

## 6. Store sets: arc and rhythm

| Slide | Job | Notes |
|---|---|---|
| 1 | the hero benefit: what the app does for me | strongest capture, shortest headline; the only slide that may carry proof (`badge`); must work alone, because search shows one to three slides |
| 2 | the differentiator: why this one | the thing a competitor's slide 2 could not say |
| 3 to n-1 | features by the user's priority, one per slide | each headline passes the "so what?" test; drop the weakest before crowding |
| n | a closer | breadth (widgets, watch, sync, privacy) or a calm restatement; never a call to action on store targets |

Five to eight slides suit most apps; Play takes 8 at most, the App Store 10. Rhythm rules; the codes in brackets are what `compose` reports:

1. **No layout twice in a row** (`adjacent_layout_repeat`). Alternate `device-bottom` and `device-top`, break the run with `device-center`, `two-devices` or `zoom`.
2. **One or two inverted slides in sets of five or more** (`no_inverted_slide`): `invert: true` swaps ground and text colours. Place them where the story turns (slide 2 or the closer), not at random.
3. **At least one slide that is not a framed device.** `zoom` brings an enlarged crop of the real capture forward as a frameless card, with the whole screen dimmed behind it: use it for the detail a full screen hides. No warning backs this rule. `text-only` is the exception (one per set, never slide 1): stores want the app in use.
4. **Vary the framing, keep the system.** Same margins, type and palette on every slide; what changes is device position, scale and crop. `device_share` outside 0.50 to 0.85 and `empty_band` above 0.25 are signs that a slide lost its balance.
5. **Text never touches the device** (`text_overlaps_device` is a hard gate) and never comes closer to an edge than the gutter.

Panoramic `strip` sets (`background.kind: "strip"`): one wide plate or gradient runs behind all slides and each slide shows its own crop.

1. Only the background crosses a seam. Text boxes and devices stay at least 3 percent away from it (`seam`). The one exception is a device placed across a seam on purpose, a `device-span` pair (`templates.md` section 2): its device crosses, its text still keeps away.
2. Every slide must read alone: stores show slides singly and in search results. The panorama is a bonus for the visitor who swipes.
3. Keep a full device on slides 1 to 3 (Play's guidance on split interfaces); a `device-span` pair there warns `span_early` on a set with a Play target. Each half of a pair needs its own headline and a half-screen that reads alone.
4. The crop differs per target width. Check the seams on every target of the set, not only on the first.
5. The order is locked: tell the user in the delivery that reordering breaks the background.

## 7. Product Hunt gallery and thumbnail

Gallery images are 1270x760 cards (`card-*` layouts). Two is the minimum; four to six tell most stories. Image 1 leads the gallery and has to carry the promise alone.

| Product type | Image 1 | Then |
|---|---|---|
| SaaS or web app | the one-sentence promise over the main screen (`card-browser` or `card-left-title`) | the core workflow in two or three steps, the differentiator, integrations from the user's own logo files, a closer with the launch offer only if the user gave it |
| Mobile app | promise plus framed phone (`card-left-title`) or a hand-held scene (`card-hero-scene`) | three feature cards reusing the store captures, platforms in words |
| Developer tool | the problem in the developer's words plus the smallest working example | before and after, the editor or terminal capture, what it plugs into |
| API or CLI | a real request and its response, or the command and its output (`card-browser`, a terminal capture) | one use case per card, a limits-and-scope card with the user's numbers; no invented benchmarks |
| Browser extension | the page with the extension doing its job | where it lives in the toolbar, two use cases, the permissions it asks for in plain words |
| AI tool | a real input next to its real output (`card-flow`) | two more real examples, the control the user keeps, what it does not do; outputs are captures, never regenerated for the card |

Thumbnail (`thumb-icon`, 240x240):

1. Design it large, judge it small. `launchkit.py sheet` shows it at 240, 80 and 40 px on a light and a dark strip.
2. One shape, one or two colours, no words. A wordmark is unreadable at 40 px; use the symbol or a single letter.
3. A ground colour that is not white, so the tile has an edge on a white page.
4. A user who animates it later: the first frame must stand alone, because the GIF moves only on hover.

## 8. Small-size tests

Build the sheet, Read it, look at the small versions first and answer before looking at the large ones:

1. Slide 1 at about 220 px wide: can you say what the app does? Can you read the headline without guessing?
2. Does the capture look like an app in use, or like a grey rectangle?
3. Is there one focal point, or do device, text and decoration compete?
4. Slides 1 to 3 side by side: do they look like one set and three different reasons?
5. Thumbnail at 40 px: is it still one recognisable shape on both strips?
6. Any "no" → change the words or the layout, not the font size. Write down what you read in the small view before comparing it with the deck; knowing the text makes everything look legible.
