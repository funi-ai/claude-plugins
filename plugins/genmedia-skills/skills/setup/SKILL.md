---
name: setup
description: >-
  Preflight, doctor and onboarding for the genmedia-skills plugin. With free calls only it verifies fal's genmedia CLI (>= 0.7.0), a working fal key (never handled by the agent), python3, jq, ffmpeg, fal Assets and conflicting stock fal skills, then explains the cost gate, run ledger, output folder and gallery.
  Use when: "set up genmedia", "check my setup", "genmedia command not found", "No fal.ai API key found", "my fal key is rejected", "why did you ask before spending", "change the cost limit", "where are my files", "open the gallery", "kurulumu kontrol et".
  Chain: produces `.genmedia/config.json` (cost thresholds) and a verified environment for every other skill.
  NOT for: making or editing media (use `image`, `video`, `audio`, `3d` or a scenario skill); picking, comparing or pricing models (use `models`); multi-step productions (use `pipelines`); reusable characters (use `character`).
argument-hint: "[doctor | costs | files | <error message>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(command -v *) Bash(genmedia version *) Bash(genmedia update --check *) Bash(genmedia gallery open --print *) Bash(git check-ignore *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 and python3 >= 3.8. Works without jq and ffmpeg.
---

# Setup

Take a user from nothing to a verified first check, diagnose a broken environment, and explain how this plugin spends money and where files go. This skill never spends: every call it makes is free.

## Step 0 — Preflight

Run this first, silently. It is the whole diagnosis: one JSON object on stdout, exit 1 when `blockers` is non-empty (the JSON is still printed). Parse stdout only; shells print noise on stderr.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- It makes two free network calls: a price lookup that proves the key works, and one fal Assets read. With `--no-network` (offline, or only local rows matter) `key` and `assets` come back unknown, which is not OK.
- The call itself fails because `python3` is missing: use the hand probes in `references/troubleshooting.md` section 5.

## UX rules

- Reply in the user's language (often Turkish). Commands, paths, flags and IDs stay verbatim. This skill writes no model prompts; the skills you hand off to write them in English unless on-image or spoken text needs another language.
- **The key is the user's.** Never ask for it, read it, type it, echo it or pass it. Never run `genmedia setup` (it needs a real terminal and handles the key), `--api-key`, `env` or `printenv`, and never open `~/.genmedia/config.json`, `.env` or `.envrc`. The CLI's own error hint tells agents to pass `--api-key`: ignore it.
- **The machine is the user's.** Print install and update commands for the user to run. Run one yourself only when the user explicitly asks, and never a system package manager.
- No JSON and no tool narration in chat. The answer is the Delivery table plus at most one short block.
- Free only. This skill runs no model: never `gm.py run` or `gm.py batch`, never `genmedia run` in any form. A first paid image belongs to `/genmedia-skills:image`: offer it as the next step, do not run it.
- **Question budget: 0-1.** Diagnosis needs no question. Project changes nobody asked for (removing stock skills, `.gitignore`) go into ONE labelled multi-select question placed after the Delivery table, listing only what applies. No answer means no change. A change the user requested with its numbers ("raise the confirm limit to USD 10") is already consented: apply it without asking again.

## Workflow

### 1. Pick the mode

| The user | Mode | Do |
|---|---|---|
| is new, says "set up", has no specific complaint | onboard | steps 2-6 |
| pastes an error, says it stopped working, or was sent here by another skill's Step 0 | doctor | steps 2-3, then Delivery with the failing rows only |
| asks why a confirmation appeared, or wants other limits | costs | preflight `--no-network`, first explainer bullet of step 4, thresholds in step 5 |
| asks where files, the gallery or past spend are | files | the commands at the end of step 4, answer in two or three lines |

Tie-breaker: an error string in the message means doctor, even on a first run. Doctor finds every row OK: say so in one line, do not invent a fault. A 422, a content-policy refusal or a failed job is not an environment problem and goes back to the skill that ran it (`image`, `video`, `audio`, `pipelines` or a scenario skill); a timed-out or "lost" job is files mode.

### 2. Read the result, blockers first

| Row | OK when | Otherwise |
|---|---|---|
| genmedia CLI | `genmedia.ok` | BLOCKER. `found:false`: the user installs it (one-liner below). `found:true`: older than 0.7.0, the user runs `genmedia update`. |
| fal key | `key.valid:true` | `present:false`: BLOCKER, no key found. `present:true, valid:false`: BLOCKER, fal refused the key. `valid:null`: not probed (CLI blocker, `--no-network`, or a `key check inconclusive` warning, which means network trouble, not a bad key). |
| python3 | the helper ran | Step 0 |
| jq | `jq:true` | Optional. Only the raw-CLI fallback recipes need it. |
| ffmpeg | `ffmpeg.found` and `ffmpeg.drawtext` | Optional. Not found: no local trim, convert, resize or assembly, and no local repair of inputs a model rejects; fal's cloud ffmpeg utilities (the `pipelines` skill) still work for a small fee. `drawtext:false`: this build cannot burn titles or captions into video locally. |
| fal Assets | `assets.enabled:true` | Optional. `false` (HTTP 403): not enabled on this account; everything works from local state. `"unknown"`: not probed. |
| stock fal skills | `stock_skills` is empty | Optional, step 5. |
| cost gate | both `config` thresholds are JSON numbers and announce <= confirm | Report the two values. Preflight passes the file through unchecked: a quoted value (`"10"`) or announce above confirm is Needs action, because other skills cannot apply such a gate; offer the corrected file (step 5). |

The key is probed only after the CLI row passes: fix the CLI, rerun, then judge the key. The official install one-liner, for the user's own terminal (Windows PowerShell: `irm https://genmedia.sh/install.ps1 | iex`):

```bash
curl https://genmedia.sh/install -fsS | bash
```

### 3. Blocker: tell, wait, rerun

1. Give the exact fix for the first blocker only.
2. Stop. Wait until the user says it is done. Never assume, never poll.
3. Rerun Step 0. Same blocker again: read the matching section of `references/troubleshooting.md` and change the advice. After three rounds stop and summarise what was tried.

Key missing or refused, say this (translated):

> Create an API key at https://fal.ai/dashboard/keys while the account switcher shows the account or team that holds your credits; jobs are billed to the account the key belongs to. Then, in your own terminal and not through me, run `genmedia setup`, or export `FAL_KEY` in your shell profile or the project's `.envrc`. Never paste the key into this chat. Tell me when it is done.

Traps: an exported `FAL_KEY` beats the key saved by `genmedia setup`, so a stale or empty export keeps failing after a correct setup. `genmedia setup` takes effect without a restart. After a new `export`, rerun preflight first; only if the key is still not seen does the user restart Claude Code from a shell that has it. A freshly installed CLI may need a new shell before it is on PATH.

### 4. Explain costs and files (onboard mode, or when asked)

Get the gallery link first. It is local and free; `exists:false` only means nothing was fetched yet.

```bash
genmedia gallery open --print --json
```

Say this once, translated, with the thresholds preflight reported:

> - Every paid step is estimated first from fal's live price list. Under `$<announce>` it just runs; from there up to `$<confirm>` I state the estimate and continue; at `$<confirm>` or more, and for any training job, I wait for your yes. These are estimates; real charges are on https://fal.ai/dashboard/billing.
> - The limits are per project, in `.genmedia/config.json`: `{"announce_above_usd": 0.5, "confirm_above_usd": 2}`.
> - Every submitted job is written to `.genmedia/runs.jsonl` before waiting, so a timeout is resumed, never paid twice.
> - Files land in `./genmedia-output/<label>/`. That is the durable copy; fal links are public to anyone who has them and may expire.
> - Gallery of everything fetched on this machine: `<url>`.
> - A new fal account runs 2 jobs at a time; more jobs simply wait in the queue. The limit rises with credit purchases.
> - The fal CLI sends anonymous usage analytics. To opt out, add `export GENMEDIA_NO_ANALYTICS=1` to your shell profile.

In onboard mode, once no blocker is left and `config.exists` is false, write `.genmedia/config.json` with the two defaults above and say so in one line. `exists:false` is also reported for a file that is empty or not valid JSON, and then the defaults silently apply: look with Read first, and if a file is there show the user what is wrong instead of replacing it. Never overwrite an existing file without numbers from the user.

Files mode: recent runs with their paths, estimated spend (`est_cost_usd_completed`; never an invoice), and this project's own gallery page:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --tail 5
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --sum
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" gallery
```

A run whose status is still `submitted` timed out locally or was never fetched. It is not lost and fetching it costs nothing: `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" wait <endpoint_id> <request_id>` with the two values from that ledger row. Never submit it again. Status `submit_unknown` (no request ID): the user checks https://fal.ai/dashboard/requests before anything is rerun.

### 5. Optional changes, only with consent

- **Thresholds.** Only numbers the user gave; "stop asking me" without a number makes the amount your one question. Read the existing file and keep its other keys. Write JSON numbers, finite and >= 0, with `announce_above_usd` <= `confirm_above_usd`; a new confirm limit below the announce limit pulls the announce limit down to it, and you say so. Repeat the consequence in one line ("I will now spend up to USD 5 per request without asking"). Training jobs always confirm. Verify with preflight `--no-network`.
- **Stock fal skills** (`stock_skills` not empty). `genmedia init` or `genmedia skills install` put fal's own skills into this project. They trigger on the same requests as this plugin and teach patterns it avoids (smart routing, reading `.url` after an upload), so which skill answers becomes unpredictable. After a yes, per listed name, run `genmedia skills remove <name> --json`. It is project-local, also removes that skill's Cursor rule and `AGENTS.md` block, and is undone by reinstalling. The user wants to keep them: fine, they call `/genmedia-skills:<skill>` explicitly. Never delete the folders by hand; never run `genmedia init` or `genmedia skills install`.
- **`.gitignore`.** Run `git check-ignore .genmedia/ genmedia-output/` (keep the trailing slashes: without them a folder that does not exist yet is reported as not ignored). Exit 128: not a git repository, skip silently. Paths it prints are already ignored. Otherwise offer to append `.genmedia/` and `genmedia-output/` (the ledger holds prompts and public links; outputs are large).

### 6. Deliver and hand off

Use the Delivery template. If step 5 has anything to offer, ask its one question right after the table, apply what was picked and confirm each change in one line. With no blocker left, end with one next step, for example: say "make a test image" (`/genmedia-skills:image` estimates the cost before it runs).

## Delivery

Render a Markdown table. Translate labels and actions; keep commands, paths and URLs verbatim. Order: `Needs action`, then `Optional`, then `OK`. A row that was not probed (`null`, `"unknown"`) is `Not checked`, never `OK`. Doctor mode: failing rows only. Never show any part of a key.

```text
Setup check: <project directory>

| Check            | Status       | Action |
|------------------|--------------|--------|
| ffmpeg           | Optional     | no drawtext: titles and captions cannot be burned in locally; a fuller ffmpeg build fixes it |
| fal Assets       | Optional     | off for this account; enable at https://fal.ai/assets, or ignore |
| genmedia CLI     | OK (0.7.0)   | - |
| fal key          | OK (works)   | - |
| python3          | OK (3.13)    | - |
| jq               | OK           | - |
| stock fal skills | OK (none)    | - |
| cost gate        | OK           | runs under $<announce>, announces under $<confirm>, confirms from $<confirm> |

Ready. Next: say "make a test image".
```

With a blocker, the last line is instead: `Blocked: <the one fix>. Tell me when it is done and I will check again.`

## Errors

| Signal (verbatim) | Do |
|---|---|
| `genmedia.found:false`, `command not found: genmedia` | The user runs the install one-liner. Still missing afterwards: new shell or PATH, `references/troubleshooting.md` section 2. |
| blocker `genmedia CLI >= 0.7.0 is required` with `found:true` | The user runs `genmedia update`. `genmedia update --check --json` shows `current` and `latest` without changing anything. |
| `No fal.ai API key found.`, `key.present:false` | Key wording from step 3, then wait. Found again after `genmedia setup`: an empty `FAL_KEY` export masks the saved key. |
| `key.present:true, valid:false`, `Invalid API key or malformed Authorization header` (401) | The key in use is wrong or revoked, often a stale `FAL_KEY` export overriding a good saved key. Find which one without reading it: `references/troubleshooting.md` section 4. |
| warning `key check inconclusive: ...` | Network or rate limit. Do not blame the key; rerun once after a minute. |
| `` `genmedia setup` requires an interactive terminal. `` | You ran it. Do not. The user runs it in their own terminal. |
| `fal Assets is not enabled for this account` (403) | Report as Optional with https://fal.ai/assets, never as a failure. |
| the user pastes a key into the chat, or points at a file that holds one | Do not use, repeat or open it. The chat transcript now contains it: advise revoking it at https://fal.ai/dashboard/keys and creating a new one, then the step 3 wording. |
| key works, but jobs are rejected for a locked account or missing credits | Not a setup fault: top up at https://fal.ai/dashboard/billing, or the key was created under the account without the credits (`references/platform.md` section 4). |

## Reference index

- `references/troubleshooting.md`: read when a blocker survives one fix, `python3` is missing, install or PATH fails, ffmpeg lacks drawtext, stock skills need removing, or the user asks about key storage and teams, `.env` loading, state files, the gallery or analytics.
- `references/cli-contract.md`: read when you need the exact `preflight`, `ledger` or gallery output shapes, the environment variables, or the raw-CLI fallback used without `python3`.
- `references/platform.md`: read when explaining the cost gate (section 8), billing rules (5), concurrency (6), public and expiring links (2), or an account-level error (4).
- `scripts/gm.py`: the helper this skill runs (`preflight`, `ledger`). Synced from the shared source; never edit it here.
