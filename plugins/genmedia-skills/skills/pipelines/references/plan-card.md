# Plan card

The plan card is the contract between you and the user for a multi-step production: what runs, on which model, why, for roughly how much, and where you stop for approval. It is shown in chat before anything is spent and saved to `.genmedia/projects/<slug>/plan.md`. Commands are abbreviated as `gm.py` and `pipeline.py`; call them the way SKILL.md shows.

## When a plan card is required

| Request | Plan card? |
|---|---|
| One generation, no assembly | No. Not this skill. |
| One stage of independent jobs (variations, format set, batch upscale) | Yes, short form: one table row per job group. |
| Two or more dependent stages, or any assembly of generated parts | Yes, full form. |
| Assembly of files the user already has | Short form. Usually under the announce threshold, so show it and proceed. |

The cost gate decides whether you wait (`platform.md` section 8, thresholds from `.genmedia/config.json`). The plan card is shown either way: a multi-step run the user never saw is a surprise even at $0.30.

## Before you write it

1. Node table drafted, every node has a unique id and a stage.
2. Every distinct endpoint verified `active` and its schema read (SKILL.md Workflow step 3). Do not show a plan that contains an unverified node.
3. Prices fetched in one call (`gm.py price a,b,c --explain`) and tiers read from `pricing_text` where `needs_llms_txt` is true. Estimates use the higher of the API price and the matching `pricing_text` tier, rounded up.
4. Quantities fixed: count, size or resolution, `duration` (never `auto`), `generate_audio`, text length. Defaults you do not override still drive the price; name them. A voice-over is not measured yet: estimate its length from the script at about 2.5 words per second, size the clips to that, and re-plan only if the measured length moves the total by more than 20 percent.

## Template

Save exactly this structure. Translate prose for the chat message; keep the file in the user's language too, with IDs, paths and numbers unchanged.

```markdown
# Plan: <title>
slug: <slug>   version: v1   date: <YYYY-MM-DD>   status: proposed

Goal: <one sentence: deliverable, length, aspect ratio, language>

| # | Step | Endpoint | Why | Inputs | Est. cost | Checkpoint? |
|---|---|---|---|---|---|---|
| 1 | Voice-over, 1 take (`vo`) | `fal-ai/gemini-3.1-flash-tts` | Turkish is in the schema enum | script, 412 chars | $0.03 | no |
| 2 | 4 keyframes (`kf01`-`kf04`) | `bytedance/seedream/v5/pro/text-to-image` | quality default for stills | 4 prompts, 1920x1080 | $0.27 | **yes: approve stills** |
| 3 | 4 clips x 5 s, 720p (`clip01`-`clip04`) | `bytedance/seedance-2.5/us/image-to-video` | quality default, native ambience | keyframes from step 2 | $11.35 | **yes: approve clips** |
| 4 | Music bed, 20 s (`music`) | `elevenlabs/music/v2.5` | exact length | mood prompt | $0.60 | no |
| 5 | Cut, mix, mux (`final`) | local ffmpeg | free, exact, ducking | steps 1, 3, 4 | $0.00 | no |

Total: about $12.25 (estimate, prices of <YYYY-MM-DD>; re-rolls are extra, max 2 per step without asking).
Cheaper route: clips on `minimax/h3-max-turbo/image-to-video` at 768P, total about $1.70. Say "budget" to switch.
Expected wait: about 15 min at an account limit of 2 parallel jobs.

Assumptions
- 16:9, 20 s, Turkish narration, no on-screen text.
- <real person / brand asset assumption, if any: "you have consent to use the presenter's photo">

Why this plan
- <2-3 lines: ordering logic, e.g. voice first because its length sets the clip count; stills approved before the expensive step>

## Log
- <timestamp> v1 proposed
```

Rules for the table:

- One row per step, not per job. Put the job ids in the Step cell so plan, batch plan, ledger and manifest share names.
- "Why" is one clause about the choice, not a description of the model.
- "Inputs" names what the step consumes, including which earlier step.
- Local work (ffmpeg) is a row with cost $0.00. Utility endpoints are rows with their cents.
- Unknown cost (compute-second utilities with unknown runtime): write "unknown, bound $<x>" or "unknown" and say so in the approval message. Never leave the cell empty.
- A user-named model stays in the plan even when it is the expensive line. Offer the alternative under "Cheaper route".

## Where checkpoints go

A checkpoint is a declared stop. Put one:

| In front of | Because |
|---|---|
| The first step that costs more than everything before it (image-to-video after stills, upscale after clips) | The cheap stage is where mistakes are cheap to fix. |
| Any step that bakes in a creative pick that is hard to reverse (hero variant, voice, character look) | Human decision, not yours. |
| Final-resolution renders when a draft tier exists | Approve drafts, then pay for finals. |
| Anything using a real person's likeness or voice the first time | Consent and fit. |

Do not put checkpoints between cheap mechanical steps (probe, trim, concat, loudness). Two or three checkpoints per plan is normal; more turns the run into a questionnaire.

Between checkpoints you decide reversible things alone: which re-roll is better, trimming a clip, music level.

## Approval rules (hard stops)

1. Plan approval and each declared checkpoint are the only questions you ask. Use the AskUserQuestion tool when available, with options such as `Go`, `Budget route`, `Change something`.
2. An approval must be an explicit yes to the version shown. Silence, a thumbs-up to an earlier version, a successful stage, or "looks good" about something else are not approvals.
3. An approval is consumed once. Approving the stills does not approve the clips.
4. While an approval is pending, submit nothing: no uploads, no canaries, no "free" utility calls that still cost cents.
5. Under the confirm threshold the plan approval is not required; declared checkpoints still are.
6. The user edits the plan in words ("drop the music", "make it 9:16", "use Kling for the clips"). Apply the edit, re-verify any new endpoint, re-price, bump the version.

## Versions

- A material change makes a new version: a new paid step, a swapped model, more jobs, or a total that rises by more than 20 percent. Re-rolls inside the stated budget are not a new version.
- Append the new table under a `## v2` heading in the same `plan.md`; mark v1 `status: superseded`. Never rewrite an approved version in place: the log must show what was approved.
- Removing a step removes the steps that depend on it; say which.

## Log lines

Append one line per event; keep them greppable (`Key: value`):

```markdown
- 2026-09-19T10:02Z v1 approved by user ("go")
- 2026-09-19T10:09Z checkpoint stills: approved 1,2,4; redo 3 ("less fog")
- 2026-09-19T10:12Z re-roll kf03 -> kf03-r2 (attempt 2 of 3)
- 2026-09-19T10:31Z checkpoint clips: approved all
- 2026-09-19T10:40Z delivered genmedia-output/spring-ad/final.mp4; est. spend $10.63 (ledger sum)
```

On resume in a later session, the log plus `pipeline.py urls --label <slug>` tell you where to continue and which approvals are already consumed. An approval recorded in the log for a step that has not run yet is still valid only if the plan version is unchanged.

## Spend reporting

- After each stage: nothing, unless a checkpoint message is due (it carries "Spent so far").
- At delivery: `gm.py ledger --label <slug> --sum` gives the estimated total per status. Report one number, `est_cost_usd_completed` (`est_cost_usd` also counts failed and unfinished requests), say it is an estimate, and mention that actual charges are on https://fal.ai/dashboard/billing.
- If spend is about to pass the approved total by more than 20 percent (re-rolls, repairs), stop and ask: that is a new version.
