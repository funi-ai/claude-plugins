# Concept frameworks

A thumbnail is a one-second pitch at postage-stamp size. A framework is a proven way to stage that pitch. Use this file in Workflow step 3: brainstorm at least five concepts, keep three that use different frameworks. Prompt wording lives in `prompt-blueprint.md`; text rules in `text-and-readability.md`.

## Four laws (apply to every framework)

1. **Open a gap, do not close it.** The picture raises one question; the title sharpens it; the video answers it. A thumbnail that already answers the question removes the reason to click.
2. **Title and thumbnail are a pair.** They never say the same thing. The title names the topic; the image shows the stake, the result or the feeling. On-image text adds a third piece of information or is left out.
3. **One focal point.** One face, or one object, or one number. Everything else is background. If you need "and" to describe the image, it is two thumbnails.
4. **Truthfulness test.** Ask: "would a viewer who watched to the end say the thumbnail lied?" Exaggerating scale, colour, expression and drama is fine. Showing a result, number, object, person or reaction that is not in the video is not. When unsure what the video delivers, ask the user before promising it.

## Library

Sketches are 16:9; `T` marks the text zone. The bottom-right corner stays empty in every layout (the duration badge sits there).

### 1. Curiosity gap

- **Use when:** the video has a reveal, a surprising answer, a secret, a mistake. Essays, investigations, tests, "I tried X".
- **Staging:** show the situation around the answer, hide or crop the answer itself: a covered object, a door ajar, a blurred panel, a finger pointing out of frame, a face looking at something we cannot see.
- **Text:** the question's hook, never the answer: "NOBODY CHECKS THIS", "DAY 3...".
- **Truth risk:** hiding something that does not exist. The hidden thing must be in the video.

```
+------------------------------+
| T T T            [ covered ] |
| [face 40%] ---> [  object  ] |
+------------------------------+
```

### 2. Before / after

- **Use when:** there is a visible transformation: renovation, fitness, editing, cleaning, a redesign, a skill.
- **Staging:** two states of the same subject, same angle, maximum contrast between them; a hard vertical split or a diagonal wipe. "Before" is desaturated and flat, "after" is lit and saturated.
- **Text:** the cost of the change: "6 WEEKS", "$200", "1 TOOL". Labels "before/after" are wasted words.
- **Truth risk:** the "after" must be the real result, not an idealised render. Use the user's own photos or frames as references when they exist.

```
+---------------+--------------+
|  dull state   |  bright state|
|      T T      |              |
+---------------+--------------+
```

### 3. Big number

- **Use when:** the hook is a quantity: money, days, items in a list, a score, a percentage, a speed.
- **Staging:** the number is the hero, 30 to 50 percent of the frame height, with one supporting object or face that says what is being counted.
- **Text:** the number plus at most two words: "$1,000 / DAY", "7 MISTAKES", "0 TO 60".
- **Truth risk:** highest of all frameworks. The number must appear in the video, with the same unit and meaning. Never round up.

```
+------------------------------+
|  ###   ###                   |
|  # #   # #   [object/face]   |
|  ###   ###  two words        |
+------------------------------+
```

### 4. Reaction face

- **Use when:** a person carries the channel and the video contains a genuine emotional beat: surprise, disgust, joy, fear, focus.
- **Staging:** head and shoulders, 40 to 60 percent of the frame, eyes sharp, looking at the cause of the reaction (an object, a screen, the text). One emotion, readable from across a room. Rim light separates the head from the background.
- **Text:** the cause in two words, placed where the eyes point.
- **Truth risk:** an expression the video never earns. Match the emotion to the actual moment; "mild surprise" is a valid choice. Needs the identity lock in `prompt-blueprint.md`.

```
+------------------------------+
|            |   T T T         |
| [face 50%] -->  [cause]      |
+------------------------------+
```

### 5. Versus

- **Use when:** two options are compared in the video: products, methods, tools, places, old and new.
- **Staging:** mirror symmetry, one item per half, colour-coded (warm against cool), a narrow divider or "VS" mark in the middle. Same scale, same angle, so the comparison feels fair.
- **Text:** "VS" or the deciding criterion: "WHICH LASTS?". Product names belong in the title.
- **Truth risk:** implying a winner the video does not pick; showing a product that is not tested. Real products: only the user's own photos as references, no invented packaging.

```
+--------------+---------------+
|   [item A]   VS   [item B]   |
|    warm      |     cool      |
+--------------+---------------+
```

### 6. Mystery object

- **Use when:** one unusual thing drives the video: a gadget, an ingredient, a found item, a strange result.
- **Staging:** the object alone, large, hero-lit on a plain dark or single-colour field; slightly low angle; optionally a hand for scale. No face.
- **Text:** a label that deepens the puzzle: "DON'T BUY THIS", "FROM 1974", or none.
- **Truth risk:** the object must be the real subject. A user photo as reference beats an invented lookalike.

```
+------------------------------+
|  T T       ___               |
|           /   \   <- hero    |
|          [object]            |
+------------------------------+
```

### 7. Tutorial result

- **Use when:** how-to, recipe, build, design or code tutorial. The payoff is the finished thing.
- **Staging:** the finished result at its best angle, large; optionally a small inset of the tool or the first step in a corner for context. Clean, bright, appetising.
- **Text:** the promise with a constraint: "IN 10 MIN", "NO OVEN", "7 GÜNDE".
- **Truth risk:** a result better than what the tutorial produces. Use the user's photo or frame of the real result as a reference whenever there is one.

```
+------------------------------+
| [step]                       |
|  inset    [ RESULT 60% ]     |
|  T T T                       |
+------------------------------+
```

### 8. Screenshot + callout

- **Use when:** the proof is on a screen or in the footage: software, games, dashboards, a moment from the video itself.
- **Staging:** a real frame or screenshot supplied by the user as the plate (get it with `thumbcheck.py frame`), cropped to the relevant area and enlarged; one circle or arrow; one or two words. This is an edit of a real image, never a generated imitation of someone's interface.
- **Text:** what to look at: "THIS SETTING", "FRAME 212".
- **Truth risk:** low when the plate is real. Never mock up the UI of a real platform, never fabricate a message, comment, chart or notification.

```
+------------------------------+
| [real frame, cropped in]     |
|      (O) <--- T T            |
+------------------------------+
```

### 9. Minimal type-only

- **Use when:** essays, podcasts, courses, news explainers, calm or premium brands; when no image is honest or available.
- **Staging:** two to four heavy words on a flat or softly graded brand-colour field; one word in the accent colour; optionally one small icon-like object. Generous margins.
- **Text:** the text is the image. It must not repeat the title: use the sharpest phrase, a contradiction, or a number.
- **Truth risk:** overclaiming in words. Same standard as a headline.

```
+------------------------------+
|                              |
|    HEAVY WORDS               |
|    ACCENT WORD        (icon) |
+------------------------------+
```

### 10. Timeline or progress

- **Use when:** challenges and journeys: "30 days of", "week 1 to week 12", level 1 to level 100.
- **Staging:** two or three panels in reading order, growing in drama, or one scene with a bold "DAY 27" badge. Pick a late, dramatic point of the journey that the video really reaches.
- **Text:** the badge is the text.
- **Truth risk:** a day or level the video does not reach.

```
+---------+----------+---------+
| DAY 1   | DAY 15   | DAY 30  |
| small   | medium   | BIG     |
+---------+----------+---------+
```

### 11. Scale contrast

- **Use when:** size, amount or power difference is the story: tiny house, giant pizza, budget against luxury, David against Goliath.
- **Staging:** the small thing and the huge thing in one frame, a person or hand for scale, wide lens, low angle on the big one.
- **Text:** the measurable difference: "$5 VS $500", "1 KG".
- **Truth risk:** exaggeration of scale is the accepted dramatisation here, as long as both things are in the video and the numbers are real.

```
+------------------------------+
|                  [  HUGE   ] |
| [tiny] T T       [  THING  ] |
+------------------------------+
```

### 12. Guest + quote

- **Use when:** interviews and podcasts, in 16:9 and 1:1.
- **Staging:** the guest's portrait (their own photo as reference, with consent), eye contact, brand-colour background; show name or episode number small at a fixed corner for series consistency.
- **Text:** a pull quote of two to four words the guest actually says, or the episode's topic. No quotation you cannot point to in the recording.
- **Truth risk:** an invented or distorted quote; a face generated without consent.

```
+------------------------------+
| [guest 45%]   "THREE WORD    |
|                QUOTE"   ep12 |
+------------------------------+
```

## Modifiers (combine with any framework, one at a time)

- **Callout:** one arrow or one circle. Two callouts cancel each other.
- **Badge:** "DAY 12", "PART 2", "NEW", episode number; small, in a fixed corner across a series (never bottom-right).
- **Quantity:** many copies of one object filling the frame, plus one thing for scale.
- **Route:** a map or aerial view with one highlighted path, for travel and logistics stories.
- **Brand field:** a flat brand-colour background for series recognition; give colours as hex plus a plain name.

## Picking three that differ

Group the frameworks into families and take at most one concept per family:

| Family | Frameworks | Leads with |
|---|---|---|
| Face-led | 4 Reaction face, 12 Guest + quote, 1 Curiosity gap (with a face) | emotion, trust |
| Object-led | 6 Mystery object, 7 Tutorial result, 2 Before / after, 11 Scale contrast | proof, desire |
| Graphic-led | 3 Big number, 5 Versus, 9 Minimal type-only, 8 Screenshot + callout, 10 Timeline | clarity, stakes |

No face available → two object-led concepts with different staging plus one graphic-led. The three concepts also differ in hook words and in dominant colour, so the comparison sheet shows three ideas, not three tints.

Starting points by video type (starting points, not rules):

| Video | Try first |
|---|---|
| Tutorial, recipe, DIY | 7 Tutorial result, 2 Before / after, 8 Screenshot + callout |
| Review, comparison | 5 Versus, 6 Mystery object, 4 Reaction face |
| Challenge, vlog, travel | 10 Timeline, 4 Reaction face, 11 Scale contrast |
| Essay, explainer, news | 1 Curiosity gap, 9 Minimal type-only, 3 Big number |
| Finance, data, business | 3 Big number, 1 Curiosity gap, 9 Minimal type-only |
| Gaming, software, screen recording | 8 Screenshot + callout, 4 Reaction face, 5 Versus |
| Podcast, interview | 12 Guest + quote, 9 Minimal type-only |
| Course or playlist cover | 9 Minimal type-only, 7 Tutorial result |

## Formats other than 16:9

- **9:16 cover (Shorts, Reels, TikTok):** stack instead of splitting: face or object in the upper-middle, text in the central band, nothing important in the top strip or the bottom third (interface overlays), and keep the essentials inside the central 4:5 area because profile grids crop to the centre. Frameworks 2, 5 and 10 become top/bottom splits.
- **1:1 cover (podcast, course):** centred composition, thicker type, at most three words: directories show it far smaller than a video thumbnail. Frameworks 9 and 12 are the natural fits.

## Tired moves (drop them unless the video earns them)

- A shocked face on a calm video; open mouths as a default.
- Red arrows and circles pointing at nothing specific.
- Money piles, flames, explosions or police tape that are not in the video.
- Fake play buttons, progress bars, notification dots, verified ticks, "LIVE" marks.
- A blur or "censored" bar hiding nothing real.
- "GONE WRONG", "YOU WON'T BELIEVE" and other words that fit every video.
- Another creator's face, a celebrity, or a lookalike of either.
