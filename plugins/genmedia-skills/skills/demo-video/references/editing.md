# Editing a product demo from a real recording

Read at Workflow steps 2 and 3: choosing what to keep, how long each beat runs, when to zoom, how to pace a demo that someone watches with the sound off.

## 1. The three shapes a demo takes

| Shape | Length | Arc | Where it goes |
|---|---|---|---|
| Product demo | 45-90 s | problem in one line → the flow, start to finish → the payoff → what to do next | website, docs, sales, Product Hunt |
| Store preview | 15-30 s (Apple: 15-30 exactly) | the app opening → the one thing it does best → a second capability → a settled last frame | App Store previews, Play promo video |
| Feature loop | 3-12 s, silent | one action, one result, ends where it started | changelog, release note, README, feature card, PH GIF thumbnail |
| Creative-asset loop | 8-15 s (Apple: 5-30), works silent | the value first, one clear idea, calm scenes of 2 s or more, ends where it started | App Store header and search results videos (iOS 27 and iPadOS 27) |

A demo is not a tutorial. One flow, done properly, beats six half-shown screens. When the user asks for "everything the app does", make the 60-90 s demo and offer a set of loops for the rest.

## 2. What the detectors tell you, and what they do not

`democut.py analyze` returns four kinds of spans:

- `scene_changes` — the picture changed a lot: a navigation, a modal, a new screen. These are candidate cut points, because a cut on a change reads as intentional.
- `freezes` — nothing moved for over a second. Usually the user thinking, a loading spinner that does not spin, or a screen left open after the action. Cut it, or speed it up.
- `silences` — if the recording has sound, where nobody is speaking.
- `black` — a fade, a screen lock, a screen recorder starting or stopping.

`dead_spans` merges freezes and black; `keep_spans` is what is left. **Neither is an edit.** A settled screen is sometimes the whole point (a result, a chart, an empty inbox). Look at `sheet` before trusting a span, and never cut a span you have not seen.

What the detectors cannot tell you: whether the UI is in the right state, whether a private name or a real e-mail address is on screen, whether the cursor is where the eye should be. That is what the contact sheet and `grab` are for.

## 3. Building the edit list

1. `analyze`, then `sheet` over the whole recording (12 tiles), then `sheet --from --to` over the interesting minute, then `grab` on the two or three frames you will zoom into.
2. Write the scenes in order. Each scene is one idea: an action and its result. Give every scene an `id` that names the idea (`compose`, `send`, `filed`, `result`), never `scene1`.
3. Trim heads and tails hard. A scene starts one beat before the action and ends one beat after the result lands, not when the user moved the mouse away.
4. Typical scene lengths: an action 1.5-3 s, a result that must be read 2.5-4 s, a screen with numbers or a long list 3-5 s. Under 1.2 s nothing registers; over 6 s without narration, attention goes.
5. Dead time inside a scene is not always a cut: `speed` 1.5-2.5x over a wait reads as "fast", while a cut reads as "something is missing". Use speed for waits and for long typing; cut for navigation you do not need to show.
6. Loading spinners: speed them up or cut them. Never let a demo show 4 s of spinner — every viewer reads it as "this is slow".
7. Keep the order the product has. Re-ordering screens so the story flows better makes a demo of a product that does not exist.

## 4. Zoom grammar

`zoom` has three useful kinds, all measured in **fractions of the source frame** (`[x, y, w, h]`, 0-1, read off `grab --grid` or `sheet --grid` where each cell is 0.1):

- `hold` — a static punch-in. Exact, no interpolation, no jitter. The default whenever a detail must be read: a form field, a number, a toggle.
- `push` — starts on the whole frame and eases into the region. Use when the eye needs to be led to where the action will happen. One per demo, two at most.
- `pull` — starts on the region and eases out to the whole frame. Use once, to reveal context after a detail ("and it is everywhere in the app").

Rules:

- A 1280x800 desktop recording zoomed to 0.3 of its width delivers 384 px into a 1920 px frame: soft. Record at 2x or keep the zoom above ~0.45 of the frame width. `time` warns above 4x (`zoom_deep`).
- The region is reshaped to the destination aspect automatically (`region_adjusted`). That means the region you give is the *minimum* the viewer will see, never a stretch.
- Never zoom and cut at the same moment. Let the zoom finish, hold 0.5 s, then cut.
- Never zoom on a scene whose content moves across the frame; the push will fight the motion.
- A vertical cut of a desktop recording is a zoom, not a squeeze: choose `fit: "crop"` and a region, or accept the padded bars.

## 5. Transitions

- `cut` everywhere. It is the professional default and costs nothing.
- `dissolve` of 0.3-0.5 s only between two scenes that are far apart in time or place (end of a flow → a new context; last screen → end card). A dissolve overlaps the two scenes, so the timeline gets shorter: `time` does that arithmetic.
- No wipes, no slides, no zoom transitions. They date a demo in a year and distract from the product.
- A dissolve longer than half of either neighbour is refused (`transition_too_long`).

## 6. Text on the picture

The recording carries the product's own words; anything you add is an overlay PNG composited by `build` (`overlays` in the scene), never text drawn by a model into the picture, and never a caption file baked into a store preview.

- A headline overlay: 3-6 words, on screen 1.5-3 s, entering with a 0.2-0.3 s fade, leaving before the next cut.
- A lower third: name what the viewer is looking at when the UI does not say it.
- Render the PNGs where text is already exact: `/genmedia-skills:launch-graphics` composes them at the right size in every locale, and hands them over as files. `/genmedia-skills:brandkit` has the logo sting and the end-card lockup.
- Keep overlays out of the bottom 12% and top 10% of a 9:16 cut: platform interface sits there.

## 7. First and last frame

- The **first frame** is the poster frame of a store preview, the thumbnail of a web player and the still frame of a GIF that only animates on hover. It must show the product doing something recognisable — never a splash screen, a login, an empty state or a fade-in from black.
- The **last frame** settles: no motion, the result visible, the end card or the product's own screen held for 0.5-1.5 s. A loop's last frame should match its first (`hold_last` and the same region) so the repeat does not jump.

## 8. Rhythm check before you render

- Read the scene list aloud in order. If two consecutive scenes explain the same idea, cut one.
- Does the first 3 s show the product doing its job? A Play promo autoplays only 30 s; a store preview is judged in 2.
- Is there one moment that is the point of the video? If not, the demo has no ending.
- Does any scene need narration to make sense? Sound is off by default on every autoplay surface: overlays and the picture carry it, narration is the bonus.
- Does the cut still work at the length the platform allows? `time` is the arbiter, and it refuses a store preview outside 15-30 s and a creative-asset video outside 5-30 s.
