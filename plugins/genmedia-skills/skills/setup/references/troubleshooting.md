# Setup troubleshooting

Checked on 2026-09-19 against genmedia v0.7.0: live calls, `--help`, the CLI's installer and source. Read the section that matches the failing row. Command syntax and JSON shapes are in [cli-contract.md](cli-contract.md); billing, concurrency and account errors are in [platform.md](platform.md). `gm.py` below stands for the canonical helper call shown in SKILL.md.

Two rules hold everywhere: the user runs anything that installs, updates or stores a key; you never see the key.

## 1. States that look alike

| You see | It means | Not |
|---|---|---|
| `ok:true` from `preflight --no-network` | local rows are fine; `key` and `assets` were not probed | "the key works" |
| `key.valid:null` plus a CLI blocker | the key is probed only after the CLI row passes | "the key is missing" |
| warning `key check inconclusive: ...` | network, DNS, proxy or a rate limit during the probe | "the key is bad" |
| `key.present:false` after the user ran `genmedia setup` | an empty `FAL_KEY` is exported and masks the saved key (section 4) | "setup failed" |
| `assets.enabled:false` | an optional feature is off | a blocker |
| `config.exists:false` | no `.genmedia/config.json`, or one that is empty or not valid JSON; either way the defaults 0.5 / 2 are in force | "safe to write a new file" (Read it first; a broken file is shown to the user, not replaced) |
| ledger row with status `submitted` | the job was accepted; the wait timed out locally or the result was never fetched | "failed" or "lost" (resume with `gm.py wait <endpoint_id> <request_id>`, free; never resubmit) |
| `genmedia version --json` with `update_available:null` | the cache is empty; agents never trigger the background check | "this is the latest" (use `genmedia update --check --json`) |
| `stock_skills: []` | no install manifest in this project | "no competing skill anywhere" (hand-copied folders and `AGENTS.md` text are not detected) |

## 2. Install and PATH

The user runs the official one-liner in their own terminal:

```bash
curl https://genmedia.sh/install -fsS | bash          # macOS, Linux
```

Windows (PowerShell): `irm https://genmedia.sh/install.ps1 | iex`.

What the installer does (read from `install.sh`): downloads the release binary for the OS and CPU, verifies its sha256 when the release ships checksums and `sha256sum` or `shasum` exists (a mismatch aborts), places it at `~/.genmedia/bin/genmedia` (`GENMEDIA_DIR` changes the base), links it into `~/.local/bin` when that directory is writable, and otherwise appends a PATH line to `~/.zshrc`, `~/.bash_profile` or `~/.bashrc`, or the fish config.

| Symptom after a successful install | Cause | Fix |
|---|---|---|
| `genmedia.found:false`, `command not found: genmedia` | the PATH change lives in the shell profile, and this session started before it | The user opens a new terminal and restarts Claude Code from it. |
| still missing in a new shell | neither `~/.local/bin` nor `~/.genmedia/bin` is on PATH | The user adds `export PATH="$HOME/.genmedia/bin:$PATH"` to their profile. |
| `Unsupported architecture` from the installer | no release binary for this CPU | Stop; report it. Do not build from source for the user unasked. |

If the user explicitly asks you to run the installer, the permission prompt must show the exact one-liner above, nothing else. Never add `sudo`.

## 3. Version and update

```bash
genmedia version --json          # {version, update_available}
genmedia update --check --json   # {current, latest, updated:false, staged:false}; free, asks GitHub
```

- Below 0.7.0 is a blocker: the user runs `genmedia update` (downloads the latest release, verifies the checksum when present, swaps the binary), then you rerun preflight.
- Newer than 0.7.0 passes the gate. This plugin's contract was verified on 0.7.0; if a newer CLI behaves differently, report what you saw instead of guessing.
- The CLI stages updates only from the user's interactive terminal and swaps a staged binary in on the next launch, so the version can change between two of your calls. `GENMEDIA_NO_UPDATE=1` in the user's profile stops new background checks.

## 4. Key

Where the CLI looks, first hit wins:

1. `FAL_KEY` in the environment of the process (shell profile, direnv `.envrc`, CI secret).
2. A project `.env` in the working directory, only if the user turned on "Auto-load .env" in `genmedia setup`; a shell value still wins.
3. The key saved by `genmedia setup`, encrypted in `~/.genmedia/config.json`, shared by all projects.

`genmedia setup` is an interactive wizard. Without a terminal it fails with `` `genmedia setup` requires an interactive terminal. `` and prints a hint to pass `--api-key`: that hint is for CI, not for you. The user runs the wizard in their own terminal window.

Which key is being rejected? This test prints a word, never the value:

```bash
if [ -z "${FAL_KEY+x}" ]; then echo unset; elif [ -z "$FAL_KEY" ]; then echo "set but empty"; else echo set; fi
```

| Preflight | Test says | Cause | The user does |
|---|---|---|---|
| `present:false` | `unset` | no key anywhere | `genmedia setup`, or exports `FAL_KEY` |
| `present:false` | `set but empty` | an empty export masks the saved key | removes the empty `FAL_KEY` line from the profile or `.envrc`; you rerun preflight, and if the empty value is still there they restart Claude Code from a clean shell |
| `present:true, valid:false` | `set` | the exported key is wrong, revoked or from another account; it overrides any saved key | replaces or removes the export |
| `present:true, valid:false` | `unset` | the saved key is wrong or revoked | reruns `genmedia setup` with a new key |

Verbatim rejections: `No fal.ai API key found.` (nothing found); `Pricing fetch failed (401)` with `Invalid API key or malformed Authorization header` (found, refused by fal).

More facts to pass on when relevant:

- Keys are created at https://fal.ai/dashboard/keys. A key belongs to the account, personal or team, that was selected when it was created, and every job bills that account. Credits on the team but a personal key (or the reverse) looks like "no credits" or a locked account although money is there.
- `genmedia setup` takes effect at once because the CLI reads the saved key on every call. Whether a new `export` reaches a Claude Code session that is already running depends on the user's shell setup (a direnv `.envrc` is often re-read on each command; a profile line usually is not). Do not predict it: rerun preflight, and only when the key is still not seen ask the user to restart Claude Code from a shell that has it.
- A key kept in `.env` or `.envrc` must not be committed. `git check-ignore .env .envrc` prints the ones that are ignored; suggest ignoring the others. Do not open these files.
- Account locked or credits exhausted is not a key problem: stop and send the user to https://fal.ai/dashboard/billing (`platform.md` section 4).

## 5. Probes without python3

Without `python3` the helper cannot run: no ledger, no resumable batches, no normalized errors. Every skill then falls back to the raw recipes in `cli-contract.md`. Recommend installing Python 3.8 or newer (the user's choice of installer), and meanwhile probe by hand:

```bash
command -v python3 jq ffmpeg genmedia
genmedia version --json
genmedia pricing fal-ai/flux/schnell --json > /dev/null; echo "key probe exit=$?"
```

The price lookup is free. Exit 0: the key works. Exit 1: the reason is on stderr as `{error, details}`; match it against the verbatim strings in section 4. Stock skills: look for `.claude/skills/.installed.json` and `.agents/skills/.installed.json` with your file tools.

## 6. Optional tools and what degrades

| Missing | What stops working | What still works | Remedy (the user installs) |
|---|---|---|---|
| `jq` | the raw-CLI fallback recipes that build JSON literals and read fields | everything that goes through `gm.py` | any package manager; only needed when `python3` is missing too |
| `ffmpeg` | local trim, convert, resize, frame extraction, concat, audio mux; local repair of inputs a model rejects as too large, too long or in the wrong format | generation itself; fal's cloud ffmpeg utilities (small per-second or compute fees, routed by the `pipelines` skill) | any package manager |
| `ffmpeg.drawtext` (ffmpeg built without libfreetype) | burning titles, labels or captions into video locally; such builds usually lack the `subtitles` and `ass` filters too (no libass) | every other ffmpeg operation; text rendered inside an image by a typography-capable image model; fal's cloud captioning endpoints | a fuller build |

Observed 2026-09-19 on macOS: Homebrew's default `ffmpeg` 9.0.1 is built without libfreetype and libass, so `drawtext:false` is the normal result there. Homebrew's `ffmpeg-full` formula lists freetype, fontconfig, harfbuzz and libass as dependencies; it is keg-only, so after `brew install ffmpeg-full` the user must put `$(brew --prefix ffmpeg-full)/bin` ahead of the default on PATH. Preflight checks the first `ffmpeg` on PATH:

```bash
ffmpeg -hide_banner -filters | grep -E " (drawtext|subtitles) "
```

Report these rows as Optional. Never install system packages yourself.

## 7. fal Assets

`assets.enabled:false` carries fal's own text: `fal Assets is not enabled for this account. Visit https://fal.ai/assets to enable fal Assets before using the Platform API.` (HTTP 403). Assets is an optional cloud library (collections, characters, tags). This plugin keeps its state in the project (`.genmedia/`) and treats Assets as a mirror, so nothing breaks without it. If the user wants it: they enable it at https://fal.ai/assets, then you rerun preflight and expect `enabled:true`. Storing a file in Assets does not extend the lifetime of its URL.

## 8. Stock fal skills

`genmedia init` and `genmedia skills install <name>` write fal's own skills into the current project. Verified 2026-09-19 with the `genmedia` skill:

| Target | Path |
|---|---|
| skill folder | `.claude/skills/<name>/`, or `.agents/skills/<name>/` when the project has an `.agents/` directory (that one wins) |
| install manifest (what preflight reads) | `.installed.json` next to the skill folders |
| Cursor rule | `.cursor/rules/<name>.mdc` |
| always-loaded block | `AGENTS.md`, between `<!-- BEGIN genmedia:<name> -->` and `<!-- END genmedia:<name> -->` |

Why it matters: a project skill and this plugin's skills both claim "generate media with fal". Which one answers becomes a coin toss, and the stock text teaches patterns this plugin avoids (prompt-only smart routing, reading `.url` from an upload). The `AGENTS.md` block is loaded by agents that read that file regardless of any skill.

With the user's consent, per name from `stock_skills`:

```bash
genmedia skills remove <name> --json
```

- Output `{name, removed, installedDir, targets:[{kind, paths}]}`; local, no key, no network. `removed:false` means it was not in the manifest.
- It deletes the folder, the Cursor rule and the `AGENTS.md` block. Left behind: the manifest with an empty list, and an empty `AGENTS.md` if the CLI had created it. Mention these; delete nothing else yourself.
- In a git repository the removal is a visible diff; committing it is the user's call. Undo: the user runs `genmedia skills install <name>`.
- The user wants to keep them (for Cursor or another agent): keep them, and tell the user to call this plugin explicitly (`/genmedia-skills:<skill>`) whenever the stock skill answers instead.
- Never remove by deleting folders (the manifest goes stale and `genmedia skills update` restores them). Never run `genmedia init`, `genmedia skills install` or `genmedia skills update`.

## 9. Project state and `.gitignore`

| Path (project directory) | What | Safe to delete? |
|---|---|---|
| `.genmedia/config.json` | cost thresholds: `announce_above_usd` (default 0.5), `confirm_above_usd` (default 2). JSON numbers only. | yes, defaults return |
| `.genmedia/runs.jsonl` | append-only ledger: request IDs, inputs, outputs, estimated cost. It is how a timed-out job is resumed instead of paid twice. | only when no job is pending |
| `.genmedia/characters/`, `.genmedia/projects/` | reusable characters and production plans written by other skills | no, unless the user is done with them |
| `genmedia-output/<label>/` | downloaded results, the durable deliverables | the user's call |

Not to be confused with `~/.genmedia/` in the home directory: that is the CLI's own folder (binary, saved key, gallery). Never open or edit `~/.genmedia/config.json`.

`.gitignore`, only in a git repository and only with a yes. Test with `git check-ignore .genmedia/ genmedia-output/`; the trailing slashes matter, because a pattern such as `.genmedia/` does not match the bare name while the folder does not exist yet. Default suggestion:

```
.genmedia/
genmedia-output/
```

Reason to give: the ledger stores prompts and public media links, outputs are large binaries. A team that wants to share characters or plans can instead ignore only `.genmedia/runs.jsonl`, `.genmedia/tmp/` and `genmedia-output/`.

Threshold edits: `announce_above_usd: 0` announces every paid step; `confirm_above_usd: 0` confirms every paid step; a very high `confirm_above_usd` removes the confirmation for everything except training jobs. Apply only numbers the user gave, and repeat the consequence in one sentence.

## 10. Gallery

The CLI records every fetched result in a static HTML gallery under `~/.genmedia/gallery/`, no server, opened through a `file://` URL.

```bash
genmedia gallery open --print --json      # all sessions: bookmark this one
gm.py gallery                             # this project's page
```

- `gm.py gallery` runs `genmedia gallery open current --print --json` under the session the helper sets on every call (`session.name` in preflight: the project directory name unless the user set `GENMEDIA_SESSION_ID`), which is why one project maps to one gallery page across conversations. The CLI hashes that name into its own session id, so the page cannot be named by hand. Never prefix a `genmedia` command with `GENMEDIA_SESSION_ID=...`: no pre-approval matches that text, so it prompts.
- `exists:false` is normal before the first result. Give the all-sessions URL instead.
- Keep `--print`. Without it the CLI opens the user's browser; do that only when asked.
- Tiles point at the downloaded files, so moving or deleting `genmedia-output/` breaks them. `GENMEDIA_NO_GALLERY=1` turns recording off.

## 11. Analytics

Released builds of the CLI send anonymous usage events (command names, endpoint IDs, durations, the detected agent) to PostHog. Per the CLI's README no prompts, file paths, keys or error messages are sent; its source shows that the search text of `genmedia models` is. Opt-out: `GENMEDIA_NO_ANALYTICS=1`, exactly `1`, exported in the user's own shell profile or `.envrc`. You cannot make it stick from inside a session, and you do not edit the user's profile unasked. The config-file switch is erased by the next `genmedia setup`, so recommend the variable.
