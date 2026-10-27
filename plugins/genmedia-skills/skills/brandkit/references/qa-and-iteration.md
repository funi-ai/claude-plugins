# QA and iteration: slot rules, checks per slot, repair moves, invalidation etiquette

The ledger (`.genmedia/projects/<slug>/brandkit/state.json`, owned by `brandkit.py`) decides what is approved, what is open and what is stale. This file says how to read it, what to check before anything is shown, and how to behave when an approval makes other work stale. `brandkit.py` abbreviates the call shown in SKILL.md.

## 1. Slots, statuses, dependency graph

```text
strategy ──► palette ──► logo ──┐
    │                          ├──► lock ──► app-<name> … ──► brandbook
    └──────► typography ───────┘
```

| Slot | Built from | Candidate ids | Registered by |
|---|---|---|---|
| `strategy` | the intake | `strategy` | `add-candidate --data` |
| `palette` | strategy | `palette-A` … `palette-F` | `add-candidate --data` |
| `logo` | strategy, palette | `logo-A` … `logo-F` | `add-candidate --file … --data` |
| `typography` | strategy | `type-A` … `type-F` | `add-candidate --data` |
| `lock` | strategy, palette, logo, typography | `lock` | `lock --data` |
| `app-<name>` | lock (and everything under it) | slot name without `app-`, optional `-A`, `-B` | `add-candidate --file` |
| `brandbook` | lock and every approved application | `brandbook` | `book` |

- Slot status: `draft` (nothing yet) → `candidate` (a review round is open) → `approved` → possibly `invalidated`. Revision status: `candidate`, `approved`, `superseded`, `invalidated`. Revisions are numbered per slot (`r1`, `r2`); each records `built_from`: the upstream revisions that were approved when it was made. That stamp is what invalidation compares.
- **Stage gates** (refused with `kind: "upstream_missing"`): a logo candidate needs an approved palette; any `app-*` candidate needs an approved lock; `lock --data` needs all four foundation slots approved; `book` needs the five foundation slots approved; `approve` needs the slot's upstream foundation slots approved (strategy before palette, palette before logo).
- **Official assets** (`--origin user`): exempt from the gates, and never stale from an upstream change (an official logo does not become invalid because the palette changed). Use it only for what the user declared or what you measured from their files (`design-brain.md`, evidence labels); never for something you generated.
- Request type → slots: *new identity*: all. *Extend*: register what exists with `--origin user`, approve it in the user's words, build the rest. *Apply only*: official logo, colours and type registered, a strategy snapshot from what they said, then lock → applications. *Change*: section 5.
- `status` answers `slots`, `invalidated`, `stale_assets`, `palette` (approved colours with `rgb` objects) and `next` (`slot` + what to do). Read it first in every turn. Never hand-edit `state.json`; a concurrent write answers `kind: "state_conflict"`: run the command again.

## 2. Who checks what

| Question | Checked by | Never by |
|---|---|---|
| Hex values, contrast ratios, colours inside an SVG | `palette-check`, `svg-check` | your eyes on a render |
| Is the SVG safe and a real vector | `svg-check` (`unsafe`, `paths`, `text_elements`) | assumption |
| Was the mark redrawn when recoloured | geometry fingerprint in `svg-recolor`, `svg-variants`, `add-asset` | a side-by-side glance |
| Do the words match | your read-back (Read the image) + `text-check` / `add-candidate` comparison | "looks right" |
| Is the lock in the prompt, verbatim | `plan`, then `add-candidate` | copy-paste discipline |
| Idea readable, hierarchy, harmony, "one system", resemblance to a famous mark | your eyes (Read the board PNG or the output) | the script |
| Exact font in a mockup | nobody: image models approximate faces; judge against the `traits` and say so | a claim in the delivery |

A vision impression is never proof of an exact hex, font or spacing; a script result is never proof that something looks good. Use both, and say which one you used in the review's `Checked:` line.

## 3. Checks per slot, before anything is shown

| Slot | Must pass | Typical failure → move |
|---|---|---|
| strategy | every fact traceable to the user; unknowns written `not stated`; 3 to 5 tone words; `avoid` list present | invented audience or history → delete it; ask nothing, show it as `not stated` |
| palette | `problems` empty; every `text` on every `background` and `surface` at 4.5:1 or more; notes understood (accent "shapes only"); options differ in strategy | text fails contrast → darken the text tone, not the rule; two near-identical colours → merge |
| logo | `svg-check`: `unsafe` empty, paths in the hundreds at most, no live `<text>`; spelling read back letter by letter; idea survives the board's 24 px preview; three different ideas; no resemblance to a famous mark you know | misspelt → retry that letter with the name spelled out (`-t2`); an illustration instead of a mark → fewer shapes, "no texture" ; lookalike → drop it, do not show it |
| logo production set | `svg-recolor`: `not_found` and `left_unmapped` empty; variants looked at (touching shapes can merge in mono); PNG size and transparency as reported by `png` | detail lost in mono → hand-picked mapping (`logo.md` section 5) |
| typography | both families named, traits written, options differ in voice; board rows say whether the real face rendered | fallback everywhere → say you could not judge the letterforms; offer `--webfonts` |
| lock | required fields concrete and specific to this mark; nothing restated that the script writes; no invented facts | boilerplate misuse rules → derive them from the construction |
| application | section 4 table; text read back; logo compared with the approved PNG side by side | section 6 |
| brandbook | built only from approved slots (the script enforces it); every page looked at when a browser exists; nothing stale listed by `export-list` | missing variant plate → make the asset, `add-asset`, `book` again |

## 4. Batch consistency table

Fill this privately for the whole batch before the review message. Two rows that disagree without a reason written in the lock mean the set is coming apart: that is a fail even when each image looks good alone.

```text
asset            | logo = approved? | colours in palette? | type matches traits? | layout rule kept? | text exact? | size / format | verdict
app-business-card| yes              | yes                 | headline ok, body ok | left-aligned      | 4/4 lines   | 1536x1024 png | pass
app-social-post  | yes              | amber used twice    | ok                   | ok                | 1/1         | 1024x1280 png | retry: accent rule
app-merch-tote   | ear rounded off  | yes                 | n/a                  | n/a               | wordmark ok | 1280x1600 png | repair: logo
```

Logo check: same shapes, same proportions, same colours (or the intended single-colour variant), nothing added, clear space respected, not tilted unless the surface is. Colour check: brand elements only in palette colours; photographic surroundings may have their own colours. A row that fails is repaired alone; passing rows are kept and never regenerated "for consistency".

## 5. Re-rolls, retries, rounds

| Situation | Move | Budget |
|---|---|---|
| One output failed your QA (text, redrawn logo, artefacts) before anyone saw it | retry that job: changed prompt, job id `…-r1-t2`, then `-t3` | 3 attempts per candidate per round; the script counts refused attempts and answers `reroll_limit` on the fourth |
| The user saw the round and wants other options | `new-round --slot <slot> --change "<what is different>"`, job ids `…-r2` | 2 rounds per slot on your own initiative |
| The user explicitly asks for another round after that | `new-round … --user-asked "<their words>"` | theirs; priced and announced like any batch |
| A candidate stays, others change | register it again in the new round with its old file; the script records `carried_over` | free |
| Nothing changed in the prompt | refused: `prompt_unchanged` (at `plan` and at `add-candidate`) | change what the failure names: wording, text size, idea, route |

Platform failures follow the ordered checklist in SKILL.md (schema → reference URL → prompt), also at most 3 attempts. `content_policy` is never resent unchanged. After the budget: stop, say what failed and what was tried, offer a different route or idea. A delivered kit with one honest gap beats a fourth silent attempt.

## 6. Repair moves for applications

| Symptom | Cheapest move that changes something |
|---|---|
| Logo redrawn, restyled or "improved" | two-reference repair edit with the failed image as image 1 and the logo as image 2 (`applications.md` section 7); if it fails again, a flat composition (logo on a plain surface seen front-on) instead of folds and perspective |
| Logo colours shifted | state the variant explicitly; supply the mono or reversed PNG that matches the surface instead of asking the model to recolour |
| Wrong letters | text retry ladder in `applications.md` section 3 |
| Extra invented text (addresses, slogans, "EST. 1987") | name the offenders in `Avoid:`, reduce empty label-like areas in the layout, fewer surfaces per image |
| Off-palette brand elements | name the role and the colour name from the lock in the application block ("the band is Pine, the dot is Amber"); never new hex values |
| Square output where a poster was planned | `image_size` was left to `auto`: send `{width,height}` |
| Looks like a stock mockup (marble, glossy plastic, floating product) | rewrite `Scene:` from the lock's imagery style: real surface, real light, one object |
| Generic, could be any brand | the application block ignores the lock's layout and `do` lines: quote one of them in the block's `Layout:` |

## 7. Invalidation etiquette

Registering a new candidate changes nothing. **Approving** it does: `approve` answers `invalidated` (slots whose `built_from` names another revision of the slot you just approved, and everything downstream of them), `still_valid`, `stale_assets` (production files derived from an older revision) and `next`.

| The user approves a new | Becomes stale | Stays |
|---|---|---|
| strategy | palette, logo, typography (generated ones), lock, applications, book | official assets (`--origin user`) |
| palette | logo (generated), lock, applications, book | strategy, typography |
| logo | lock, applications, book; logo assets (variants, PNGs, icon) | strategy, palette, typography |
| typography | lock, applications, book | strategy, palette, logo |
| lock | applications, book | the four foundation slots |
| one application | book | everything else |

Rules:

1. **Tell before you touch.** Send the invalidation notice from SKILL.md: what was approved, what is stale, what is still valid, what rebuilding costs (free stages named as free; paid batches priced with today's prices), and the options: rebuild all, rebuild some, keep as is.
2. **Nothing is regenerated silently**, not even free stages. The user may prefer to keep a logo whose shapes still work under the new palette.
3. **Keeping is an approval.** `approve --slot logo --candidate logo-B --note "<their words>"` on an invalidated revision re-stamps it against the current upstream (`kept_after_upstream_change: true`). Then bring its files in line without redrawing: `svg-recolor` with the old → new hex map, `svg-variants`, `png`, `add-asset` again. The geometry check proves it is the same mark.
4. **Rebuild in stage order**: palette and typography → logo → lock → applications → book. The lock is always recomposed (`lock --data`) and re-approved after any foundation change, because its header and values name revisions; `plan` then injects the new block, and old application prompts cannot slip through.
5. **Stale is not deleted.** Old files stay on disk and in the ledger's history; `export-list` simply stops listing them and names every stale or missing item under `problems` until it is rebuilt, re-approved, or deliberately left out (say which in the final message).
6. `invalidate --slot <slot> --reason "<text>"` is for what the graph cannot see: the user withdraws an approval, a file was lost, the user reports a conflict with an existing trademark. It cascades like an approval does.
7. Vague change requests ("make it pop", "daha modern olsun") are not yet a change: ask which single thing (colour, form or type), then open a round for that slot only.

## 8. Resuming and honesty

- New session: `status`, then continue at `next`. Open round → show its board again and wait; do not regenerate it. Chat claims an approval the ledger does not have → ask; the ledger wins.
- A paid batch that answered `pending` is resumed with the same `gm.py batch --plan` command; its outputs are then checked and registered as if nothing happened.
- Could not look (no converter), could not verify a font (not installed), could not make a PNG or PDF: say exactly that in the review or delivery line. A limitation stated once costs less than a check you pretended to do.
