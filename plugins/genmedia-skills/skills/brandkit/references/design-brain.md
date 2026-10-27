# Design brain: from a brief to a visual direction

Private art direction. The user sees the strategy snapshot and the candidates, never this reasoning, the rubric or the scores. Every recommendation must trace back to a line of the snapshot; a choice you cannot trace is decoration.

## 1. Strategy snapshot (`strategy.json`)

Written once after intake, shown in plain language at Review 1, approved with the palette. **Facts come from the user only.** A field the user did not give is written as `"not stated"`, never filled from the category or from model knowledge. Proposals (tone words, archetype, direction) are yours and are labelled as proposals when shown.

```json
{
  "offer": "Small-batch coffee roastery with one cafe in Izmir",
  "audience": "not stated",
  "tone_words": ["warm", "curious", "precise"],
  "tone_source": "proposed",
  "archetype": "Explorer",
  "positioning": "named after the fox that visits the street; roasts in small lots",
  "name_cues": "tilki = fox; two short words, strong T and K",
  "colours_use": [],
  "colours_avoid": ["red"],
  "existing_assets": [],
  "direction": "restrained geometric mark, warm earth palette, the symbol is the only loud element",
  "axes": {"restrained_expressive": 35, "geometric_organic": 40, "familiar_experimental": 45},
  "avoid": ["coffee bean", "steam swirl", "cup seen from the side"]
}
```

Required by the script: `offer`, `audience`, `tone_words` (3 to 5). The brand name lives in the ledger (`init --brand`), in the exact spelling the user typed. Everything else is free-form and lands in the brandbook's strategy table, so write it for a reader.

Evidence labels for anything taken from supplied assets or a site the user pointed to: **declared** (the user said it), **measured** (`svg-check` colours, file sizes), **observed** (you looked at it), **inferred** (your reading). Only declared and measured values may be registered with `--origin user`. A site URL is read for the user's own facts and colours; its layout and other people's marks are never imitated.

## 2. Reading the brief

Extract, in this order, and stop as soon as one is empty instead of inventing it:

1. **Product truth**: what is actually sold, to whom, where. One sentence.
2. **Audience desire**: what the buyer wants to feel or signal. Only if the user said something about the audience.
3. **Name cues**: meaning, sound, letter shapes, length. Short names carry a wordmark; long names need a compact symbol.
4. **Tone words**: three. They steer every later choice (section 3).
5. **Constraints**: colours to use or avoid, existing assets, where the mark must work first (shop sign, app icon, packaging, invoice).
6. **Forbidden clichés**: the first three images anyone would think of for this category. They go into `avoid` and into every logo prompt's negative tail.

Three axes, 0 to 100, from the user's adjectives (unspecified = 50): restrained ↔ expressive, geometric ↔ organic, familiar ↔ experimental. Persist them in the snapshot; when a later request contradicts them ("make it wilder"), that is a strategy change with an invalidation list, not a tweak.

## 3. Tone → form, colour, type

Use as a starting grid, then bend it to the product truth. Two tone words that pull apart (playful + premium) are resolved by giving each one system: for example form carries playful, colour and type carry premium.

| Tone family | Form | Colour | Type traits |
|---|---|---|---|
| calm, trustworthy, clinical | symmetric, closed shapes, even stroke, generous counters | cool or neutral primary, low-chroma accents, light background | humanist or neo-grotesque sans, regular weights |
| warm, handmade, local | slightly irregular geometry, rounded joins, one hand-cut detail | earth primary, cream background, one warm accent | soft serif or rounded sans, medium weight |
| bold, energetic, young | heavy mass, diagonal or stacked composition, tight spacing | saturated primary, near-black text, high-contrast accent | condensed or wide grotesque, bold |
| premium, quiet | thin precise geometry or a confident wordmark, much white space | near-black or deep tone plus one metallic-free neutral; colour used sparingly | high-contrast serif or refined grotesque, light to regular |
| playful, friendly | round forms, a character or a face-like cue, bouncy baseline | two or three clear hues, light background | rounded sans, geometric with quirks |
| technical, precise | grid-built, modular, monoline | cool primary, one signal colour | geometric or mono-flavoured sans |
| natural, slow | organic silhouette, negative-space idea | muted greens, clay, stone | old-style serif, humanist sans |

Archetype shorthand (pick at most one, as a tiebreaker, never as a costume): Explorer → open forms, horizon or path cues; Caregiver → enclosing forms; Creator → constructed, visible geometry; Sage → symmetry, restraint; Jester → asymmetry, surprise; Ruler → axial symmetry, weight; Everyperson → plain wordmark, honest colour.

**A single loud element.** Every system gets exactly one. Expressive symbol → restrained palette and type. Loud colour → quiet mark. Characterful typeface → simple symbol. When everything shouts, nothing is recognisable at 24 px.

## 4. Three candidates that are genuinely different

The logo review is only worth a hard stop when the three marks are three answers, not three renderings. Build them from different **sources of the idea**:

| Slot | Source | Typical mark type |
|---|---|---|
| `logo-A` | the **name**: its meaning, initials, letter shapes | lettermark, monogram, wordmark with one altered letter |
| `logo-B` | the **product or place**: a tool, gesture, ingredient, silhouette seen from an unusual angle | pictorial symbol + wordmark |
| `logo-C` | the **benefit or attitude**: what changes for the customer, as an abstract form | abstract symbol + wordmark, emblem |

Rules the script enforces, and the ones it cannot:

- Enforced: different prompts, and no two candidates with the same `mark_type` **and** `idea` in their data file.
- Yours: the three differ in at least two of {mark type, central idea, composition (stacked, horizontal, enclosed), stroke logic (solid, monoline, negative space)}. Colour is never the difference: all three use the approved palette.
- The user asked for one type only ("just a wordmark") → three wordmarks with three different mechanisms (ligature, cut, weight contrast), and say that the spread is narrower by request.
- Each candidate gets a one-line idea in plain words (`idea` in `logo-A.json`). If you cannot say the idea without adjectives, there is no idea yet.

Per candidate data file (`logo-A.json`): `mark_type`, `idea` (required), plus `mechanism`, `composition`, `treatment` (`flat`, `monoline`, `negative-space`, `hand-cut`) for your own prompt writing (`logo.md`).

## 5. Anti-cliché list

Reject on sight, in concepts and in results: leaf for "natural"; sparkle or star for "premium" or "AI"; shield for "trust"; globe, orbit or network dots for "global" or "tech"; light bulb for "idea"; handshake; upward arrow for "growth"; generic swoosh; random gradient to look modern; gold plus serif for luxury; initials in a circle with no reason; two metaphors fused into one unreadable shape; the category's literal object drawn plainly (a bean for coffee, a tooth for a dentist) unless the angle is new.

Named-brand requests ("like Apple", "Nike tarzı"): never imitate. Translate into formal qualities (single solid silhouette, no text, one cut) and say that you did.

## 6. Private rubric (never shown, never scored aloud)

Before a candidate goes to the board, answer yes to all or replace it:

1. Traces to a snapshot line (which one?).
2. Survives at 24 px and in one colour (look at the board's small sizes and think of the mono variant).
3. Distinct from the other two in idea, not only in rendering.
4. Free of the category clichés and of the user's `avoid` list.
5. Drawable as a simple vector: few shapes, no photographic effects, no tiny details.
6. Does not resemble a famous mark you know. When it does, drop it; the trademark notice is not a licence to ship a lookalike.
7. Works with the approved palette roles (primary carries the mark, accent is optional).

When recommending, give one line with a reason tied to the brief ("B reads best on the shop sign you mentioned"). Recommending is allowed; choosing is the user's.

## 7. Revision logic

| The user changes | Recheck | Usually stale |
|---|---|---|
| tone words or direction (strategy) | everything against the new snapshot | palette, logo, typography, lock, applications, book (the script lists them; elements that still fit are re-approved in the user's words) |
| palette | logo colours, contrast pairs, lock | generated logo, lock, applications, book; typography stays |
| logo | lock wording (construction, clear space, misuse), icon | lock, applications, book; palette and typography stay |
| typography | lock, text-bearing applications | lock, applications, book |

"Make it pop", "more modern", "daha şık": ask which single thing (colour, form or type) before spending; then it is a new round for that slot only.
