# genmedia-skills

Agent skills for Claude Code that drive [fal.ai](https://fal.ai)'s `genmedia` CLI: images, video, audio, consistent characters, 3D models, brand kits, store and launch graphics, and multi-step media pipelines.

> **Unofficial community project.** Not affiliated with, endorsed by, or supported by fal or Anthropic. `genmedia` and fal.ai belong to their owners. You pay fal directly for every generation you run. This plugin adds no fees and collects nothing.

## What this is

A Claude Code plugin with 17 skills. Each skill covers one media job from start to finish: which model to use and why, how to call the CLI safely, what to ask you (rarely), what the job will cost, and how to hand back the files.

## Why it exists

The `genmedia` CLI reaches more than a thousand fal endpoints, and the catalog changes every week. Left alone with it, an agent guesses endpoint IDs, invents parameters, resubmits paid jobs after a timeout and pastes JSON into the chat. The skills deal with each of those:

- Routing tables are dated. Every endpoint ID in them was checked against the live catalog on the date printed next to it, and the tables are re-checked every week. Before the first paid call of a session, the agent looks the endpoint and its schema up again.
- Prices come from `genmedia pricing`, never from memory. Small jobs run, larger ones are announced, and anything at or above the confirmation threshold waits for your yes. So does every training job.
- The bundled helper, `gm.py` (Python standard library only), submits jobs to fal's queue and writes the request ID to a ledger before it starts waiting. It polls with a time limit, downloads the results, and never resubmits a job that already has a request ID.
- State lives in `.genmedia/` inside your project: runs, characters, project manifests. A session that timed out can pick up where it stopped.
- Replies follow a fixed contract: your language, no JSON dumps, no narration of tool calls, local file paths first.

## Quickstart (about 60 seconds)

Requirements: Claude Code, the `genmedia` CLI 0.7.0 or newer, a fal API key, and `python3` 3.8 or newer. `jq` and `ffmpeg` are optional for most skills. `demo-video` needs `ffmpeg`, and `launch-graphics` renders with a Chromium-family browser (Chrome, Chromium, Edge or Brave). `/genmedia-skills:setup` tells you what is missing.

1. Install the CLI (official installer, from the genmedia README):

   ```bash
   curl https://genmedia.sh/install -fsS | bash
   ```

2. Give the CLI your key. Do this yourself, in your own terminal. The skills never read, ask for, or type a key.

   ```bash
   genmedia setup
   ```

   Exporting `FAL_KEY` in your shell works too.

3. Install the plugin. Inside Claude Code:

   ```text
   /plugin marketplace add funi-ai/claude-plugins
   /plugin install genmedia-skills@funi-ai
   ```

4. Verify for free. Still inside Claude Code:

   ```text
   /genmedia-skills:setup
   ```

   The setup skill only runs free commands (version, a catalog lookup, local tool probes) and reports what is missing. To check by hand instead:

   ```bash
   genmedia version --json
   genmedia models "flux" --limit 3 --json
   ```

   The second command needs a working key and costs nothing.

5. Ask for something: "Make a square product photo of a ceramic mug on a linen tablecloth." Generation is paid per call; the skill estimates the cost with `genmedia pricing` first.

More install options, updating and uninstalling: [INSTALL.md](INSTALL.md).

## Skills

Invoke a skill explicitly with `/genmedia-skills:<skill>`, or just describe what you want and let Claude pick one.

| Skill | Invoke | Status | What it does |
|---|---|---|---|
| `setup` | `/genmedia-skills:setup` | available | Preflight and doctor: CLI present and new enough, key present (never handled), `python3`/`jq`/`ffmpeg` probes, fal Assets availability, conflict with `genmedia init` stock skills, gallery and cost-policy explainer. Writes `.genmedia/config.json`. |
| `models` | `/genmedia-skills:models` | available | Owner of routing knowledge: which model for a task, side-by-side comparisons, pricing and cost estimates, discovering new models, checking that an ID is alive, refreshing the routing tables. Questions about models land here; making the deliverable does not. |
| `image` | `/genmedia-skills:image` | available | One-off still images and edits: text-to-image, posters and on-image text, SVG icons, multi-reference edits, inpaint/outpaint, background removal and replacement, upscale, vectorize, layerize. Scenario requests (product shoots, listing cards, ads, thumbnails, logos) go to their scenario skill. |
| `video` | `/genmedia-skills:video` | available | One-off clips and clip edits: text-, image-, first/last-frame- and reference-to-video, native-audio video, extend, restyle, reframe, motion transfer, lipsync and talking head, video upscale; keyframe-first ladder. Shorts, ads and explainers go to their scenario skill. |
| `audio` | `/genmedia-skills:audio` | available | One-off audio: text-to-speech in many languages, voice clone, music, sound effects, foley from video, speech-to-text, SRT/VTT, dubbing, cleanup. Voiced or narrated videos go to their scenario skill. |
| `character` | `/genmedia-skills:character` | available | Identity consistency: a local character sheet under `.genmedia/characters/<handle>/`, reference sheets, optional LoRA training, `@handle` resolution for `image`, `video` and the scenario skills. |
| `pipelines` | `/genmedia-skills:pipelines` | available | Engine for multi-step productions that no scenario skill owns (storyboard to film, stitching clips, muxing voice-over, music and captions onto a video, batch variations): plan card, cost gate, staged queue submission, bounded wait, QA gate, assembly, manifest. |
| `product-photoshoot` | `/genmedia-skills:product-photoshoot` | available | Product photography from your real product photos: packshot, lifestyle, flat lay, hero banner, in-hand, try-on, text-free ad-ready variants. Product-fidelity lock, hero approval, per-image fidelity QA. Ads with copy go to `ads`, listing cards to `marketplace-cards`. |
| `ads` | `/genmedia-skills:ads` | available | Ads from your real product: UGC-style and polished ad videos (presenter, how-to, unboxing, showcase, testimonial, TV spot) and static ads with exact copy. Hook library, timed scripts, two production routes, strict claim discipline (no invented testimonials or ratings). Software route for apps and SaaS: real captures and screen recordings are composited (recording under a drawn device frame, dated Meta, TikTok and Google placement sizes), never regenerated. |
| `short-video` | `/genmedia-skills:short-video` | available | Short-form video for TikTok, Reels and Shorts in ten formats (hook, app launch, course promo, faceless narrated, before/after and more), built from an approved beat sheet: keyframes first, draft tier before the quality tier, sidecar captions. |
| `video-explainer` | `/genmedia-skills:video-explainer` | available | Narrated explainers of about 1-5 minutes in fixed-length blocks: one style key, narration generated and measured before any picture, three cost tiers (animatic, hybrid, full motion), resumable per-block state, SRT. |
| `youtube-thumbnail` | `/genmedia-skills:youtube-thumbnail` | available | Thumbnails and covers that survive at small size (YouTube 16:9, Shorts/Reels/TikTok covers 9:16, podcast and course covers 1:1): three draft concepts, a small-size readability gate, identity lock, narrow-scope revisions. |
| `marketplace-cards` | `/genmedia-skills:marketplace-cards` | available | Listing-image sets for one product (Amazon, Etsy, Shopify) from your real photos and facts: main packshot, benefit infographic, dimensions, what's-in-the-box, A+ banners. Baked-in text is read back letter by letter; no invented specs. |
| `brandkit` | `/genmedia-skills:brandkit` | available | Logos and brand identity in approved stages: palette, three logo candidates as real SVG, typography, a frozen BRAND LOCK, applications conditioned on the approved logo, an HTML brandbook and a hand-off package, all in a resumable approval ledger. App icon files for the App Store, Google Play, Android adaptive icons, favicon and PWA, and macOS, plus a logo sting for video, rendered locally from the approved SVG. |
| `3d` | `/genmedia-skills:3d` | available | 3D mesh files: image-, multi-view- and text-to-3D plus mesh post-processing (remesh, retexture, rig, animate, convert to USDZ, FBX or STL) for product visualisation, game props, AR and 3D printing; every file is checked by a bundled GLB inspector. |
| `launch-graphics` | `/genmedia-skills:launch-graphics` | available | Launch and listing stills for software products: App Store and Google Play screenshot sets, Play feature graphic, Open Graph and X link cards, Product Hunt gallery and thumbnail, ad-placement sizes and video layers for `ads`. Your real captures are composed, never redrawn: drawn device frames and status bars, HTML text in every locale, exact store sizes from headless Chromium; models only paint background plates, scene plates with a key-colour screen and decor. |
| `demo-video` | `/genmedia-skills:demo-video` | available | Product demos, store preview videos and feature loops cut from your real screen recording: local ffmpeg trims, speeds, zooms, frames the recording inside a drawn device, mixes and normalises the sound, exports MP4, WebM and GIF inside a measured byte budget, and checks every delivered file against dated App Store, Play and Product Hunt rules. The interface is never regenerated; models add only narration, music, sound, plates and end cards. |

Selection rule of thumb: a scenario request goes to its scenario skill (`product-photoshoot`, `ads`, `short-video`, `video-explainer`, `youtube-thumbnail`, `marketplace-cards`, `brandkit`, `3d`, `launch-graphics`, `demo-video`); a plain one-off generation or edit stays with `image`, `video` or `audio`; a multi-step job that no scenario skill owns goes to `pipelines`; a question about models goes to `models`.

## How the skills chain

Skills share no hidden state. They pass values to each other:

- `setup` writes `.genmedia/config.json` (cost thresholds, defaults). Every other skill reads it.
- `models` owns the routing tables. Generating skills carry a copy of the table for their modality and defer to `models` for comparisons, pricing questions and refreshes.
- `character` produces an `@handle`. `image`, `video` and the scenario skills (`ads`, `short-video`, `video-explainer`, `youtube-thumbnail`, `product-photoshoot`) resolve `@handle` to the stored reference images; `3d` takes a single cropped figure from a character sheet.
- `image` produces local files plus CDN URLs. `video` consumes them as keyframes; expensive ladders pause for your approval between stages (keyframes before image-to-video, clips before voice-over, music or upscale).
- `audio` produces narration, music and effects for `video` and `pipelines`.
- `pipelines` runs multi-step plans that no scenario skill owns and writes a manifest under `.genmedia/projects/<slug>/`. Its engine (`pipeline.py`: plan, `@ref` filling, manifest) is copied into the scenario skills that stage their work.
- `product-photoshoot` consumes your real product photos and an optional `@handle` model; it produces approved, fidelity-checked stills and a manifest that `ads`, `marketplace-cards`, `short-video` and `video` reuse.
- `ads` consumes product photos, `product-photoshoot` stills and `@handle` presenters; it produces ad videos or static ads with a plan and a manifest. For software it consumes real captures and screen recordings and hands composition to `launch-graphics` (ad-size stills, and `layers` that let the recording play under the drawn frame).
- `short-video` consumes stills from `image` or `product-photoshoot` and an optional `@handle`; it produces the cut, an SRT file and a manifest.
- `video-explainer` consumes a topic, document or script and an optional `@handle` mascot; it produces one MP4, an SRT file and a per-block ledger (`blocks.json`) so a single block can be redone.
- `youtube-thumbnail` consumes a title plus an optional face photo, `@handle`, brand colours or a frame of your video; it produces sized PNG and JPEG files.
- `marketplace-cards` consumes your product photos, your facts and approved `product-photoshoot` stills; it produces listing files in listing order and a manifest.
- `brandkit` produces approved SVG logos, palette hex values, platform app icon files (`app-icon/`) and a BRAND LOCK block that you paste into `image`, `ads`, `product-photoshoot`, `youtube-thumbnail`, `marketplace-cards` or `launch-graphics` requests.
- `launch-graphics` keeps one `deck.json` per product under `.genmedia/projects/<slug>/launch-graphics/` (captures, copy per locale, layouts). It consumes a BRAND LOCK and icon files from `brandkit` and plates from `image`; its PNG sets and link cards are final deliverables, and its ad stills and video layers go back to `ads`.
- `demo-video` keeps one `cut.json` per product under `.genmedia/projects/<slug>/demo-video/` (recordings, ordered scenes, variants). It consumes your screen recordings, device frames (`layers`) and end cards from `launch-graphics` and a BRAND LOCK from `brandkit`; it produces MP4, WebM and GIF files, SRT/VTT cue files, poster frames and a manifest. Play and Product Hunt take a YouTube URL, so the file is yours to upload.
- `3d` consumes reference pictures from `image` (or your photos) and produces GLB, USDZ, FBX, OBJ or STL files.

Deliverables land in `./genmedia-output/<label>/`. The run ledger is `.genmedia/runs.jsonl`.

## Cost and safety

- The agent estimates the cost before spending. Under $0.50 the job just runs; from $0.50 to $2 the agent states a one-line estimate and proceeds; at $2 or more, and for every training job, it shows the estimate and waits for explicit confirmation. Override the thresholds in `.genmedia/config.json` (`announce_above_usd`, `confirm_above_usd`).
- Prices are read live with `genmedia pricing`, plus the Pricing paragraph of the model's `llms.txt` (fetched by the helper, `gm.py price --explain`) when the billing unit is not per image or per second. They are never quoted from memory.
- If you name a model, that model is used or the agent tells you why it cannot be. It never swaps in another one silently.
- Jobs go to the queue, the request ID is written to the ledger before any waiting, and a timed-out job is resumed, not resubmitted, so nothing is billed twice by accident. Repairs are bounded: at most three attempts per step, and something must change each time.
- Skills check that your key is present; they never read, print, request or type it, and no documented command passes `--api-key`.
- Real-person likeness needs your confirmation that you have consent. The skills fabricate no testimonials, ratings or metrics, and use no third-party logos or IP unless you own them.
- Outputs are public URLs: fal CDN links are unauthenticated and may expire. The local file is the durable copy.
- The `genmedia` binary reports anonymous usage analytics to its maintainers. Opt out with `export GENMEDIA_NO_ANALYTICS=1`.

## What runs on your machine and what leaves it

The plugin has no hooks, no MCP servers and no install step. Its skills run these programs, and only when a skill needs them:

- the `genmedia` CLI, which you install and configure yourself;
- the Python scripts inside each skill's `scripts/` folder, standard library only, readable source;
- `ffmpeg` and `ffprobe` for local cuts, mixes and checks;
- a Chromium-family browser in headless mode, which `launch-graphics`, `brandkit` and `youtube-thumbnail` use to render HTML and SVG layouts into images;
- `sips` on macOS, to resize and convert images, HEIC photos included, when `ffmpeg` is missing or cannot read them.

Network traffic:

- Prompts, parameters and the input files you pick go to fal through the `genmedia` CLI. Inputs are uploaded to fal's CDN so the models can read them, and results are downloaded from fal's CDN into `./genmedia-output/`.
- `gm.py price --explain` reads the public `llms.txt` page of a model on fal.ai for its pricing text.
- `pipeline.py fetch` downloads a result over HTTPS from a URL in the run ledger or one you give it.
- The HTML brandbook that `brandkit` writes links Google Fonts stylesheets for the typefaces you approved, so opening it in a browser loads those fonts from Google.

Nothing else is sent anywhere. The plugin collects no analytics. It never prints, stores or sends your fal key: the helper only checks that `FAL_KEY` is set and masks it in error text. Its state and outputs stay in your project, in `.genmedia/` and `./genmedia-output/`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/plugin marketplace add` fails to clone | The `owner/repo` shorthand clones over SSH and you have no GitHub SSH key | `export CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`, or add the marketplace by its `https://` URL |
| `genmedia: command not found` | CLI not installed, or its bin directory is not on `PATH` | Install it (Quickstart step 1), open a new shell, check `command -v genmedia` |
| `No fal.ai API key found.` | No `FAL_KEY` in the environment and no key saved by `genmedia setup` | Run `genmedia setup` yourself, or export `FAL_KEY`, then start a new Claude Code session so it inherits the variable |
| Skills do not show up after install | Plugin disabled, or the session predates the install | `/plugin` to check it is enabled, then `/reload-plugins` or restart Claude Code |
| A generic `genmedia` skill answers instead of these skills | `genmedia init` (or `genmedia skills install`) put fal's stock skills into this project. They trigger on the same requests and carry older guidance | See the next section |
| `/plugin update` says already up to date | Releases are pinned by the `version` in `plugin.json`; no new version has been published | Nothing to do. `/plugin marketplace update funi-ai` refreshes the catalog |
| 403 `authorization_error` from `genmedia assets ...` | fal Assets is not enabled on your account | Nothing to fix: Assets is an optional mirror, local `.genmedia/` state is the source of truth |
| Permission prompts in default mode, or refusals in a headless run (`claude -p`) | Each skill pre-approves only its helper scripts, the free `genmedia` commands, `Read` and edits under `.genmedia/`, and only for the turn that invoked the skill. Two Claude Code behaviours seen on 2026-09-20: a headless default-mode session refuses the Skill tool itself unless `Skill` is allowed, and on a resumed headless turn (after a checkpoint) the skill's pre-approvals no longer applied, so the helper asked again | Headless: pass `--allowedTools Skill`, or use `--permission-mode auto`; in default mode expect the helper to ask again after a checkpoint. Interactive: approve once per session, or add the rules to your own settings |
| A job seems stuck | Queue wait exceeded the helper's bound, or the job never finishes | Ask the agent to resume it; it uses the recorded request ID. Check https://fal.ai/dashboard/requests for the final state |

### Conflict with `genmedia init` stock skills

`genmedia init` and `genmedia skills install <name>` write fal's own skills into the current project: `.claude/skills/<name>/` (or `.agents/skills/<name>/` when `.agents/` exists), a Cursor rule under `.cursor/rules/`, and a block in `AGENTS.md` between `<!-- BEGIN genmedia:<name> -->` and `<!-- END genmedia:<name> -->`. Nothing collides on disk, because plugin skills live in Claude Code's plugin directory and are namespaced (`/genmedia-skills:image`). The conflict is about triggering: two skills answer the same request, and the `AGENTS.md` block is loaded as always-on context.

Pick one per project. To keep this plugin, run `/genmedia-skills:setup` (it detects the stock skills and tells you what it found), then remove them yourself:

```bash
genmedia skills remove genmedia
```

Repeat for any other installed stock skill, and delete leftover `genmedia:` blocks from `AGENTS.md` if the command left them behind. The skills in this plugin never run `genmedia init` or `genmedia skills install`.

## More

- [INSTALL.md](INSTALL.md): prerequisites, install paths, verify, update, uninstall.
- [CHANGELOG.md](CHANGELOG.md): release notes.
- Bugs, wrong prices, dead model IDs and feature requests: [open an issue](https://github.com/funi-ai/claude-plugins/issues/new/choose).
- Security problems: report them privately, as described in [SECURITY.md](https://github.com/funi-ai/claude-plugins/blob/main/SECURITY.md).

## License

[MIT](LICENSE).
