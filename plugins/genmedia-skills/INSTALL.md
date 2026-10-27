# Install

genmedia-skills is a Claude Code plugin. It supports Claude Code only for now. Every skill folder is self-contained, so other agent hosts can be added later.

## Prerequisites

| Need | Why | Check |
|---|---|---|
| Claude Code | Hosts the plugin | `claude --version` |
| `genmedia` CLI 0.7.0 or newer | Every skill drives it | `genmedia version --json` |
| A fal API key | The CLI needs it for catalog, pricing and generation calls | `genmedia models "flux" --limit 1 --json` succeeds |
| `python3` 3.8 or newer | Runs the bundled helper `gm.py` (standard library only) | `python3 --version` |
| `jq` (optional) | Raw-CLI fallback recipes when `python3` is missing | `command -v jq` |
| `ffmpeg` (optional) | Local assembly in `pipelines` and `video`; fal-hosted utilities are used when it is absent | `command -v ffmpeg` |

Install the CLI with the official installer documented in the genmedia README:

```bash
curl https://genmedia.sh/install -fsS | bash
```

On Windows the genmedia README documents `irm https://genmedia.sh/install.ps1 | iex`. This plugin is developed and tested on macOS and Linux.

Set the key yourself, in your own terminal:

```bash
genmedia setup
```

or export `FAL_KEY` in the shell that starts Claude Code. Keys come from https://fal.ai/dashboard/keys. The skills never read, print, request or type a key, and they never run `genmedia setup` for you.

## Install the plugin

Inside Claude Code:

```text
/plugin marketplace add funi-ai/claude-plugins
/plugin install genmedia-skills@funi-ai
```

From a terminal (same result):

```bash
claude plugin marketplace add funi-ai/claude-plugins
claude plugin install genmedia-skills@funi-ai
```

`--scope project` writes the plugin into the repository's `.claude/settings.json` so teammates get it too; the default scope is `user`.

The format is `<plugin>@<marketplace>`: the plugin is `genmedia-skills`, the marketplace is `funi-ai` (hosted in the `funi-ai/claude-plugins` repository). Skills are invoked as `/genmedia-skills:<skill>`.

To stay on one release, add the marketplace at its tag, for example `funi-ai/claude-plugins#genmedia-skills--v0.1.0`. Tags are listed on the [releases page](https://github.com/funi-ai/claude-plugins/releases).

## Verify (free)

Inside Claude Code:

```text
/genmedia-skills:setup
```

The setup skill runs only free commands and reports: CLI found and version, key present (it checks presence only), `python3`/`jq`/`ffmpeg`, whether fal Assets is enabled on the account, and whether fal's stock skills are installed in the project.

By hand:

```bash
genmedia version --json
genmedia models "flux" --limit 3 --json
```

Neither command bills anything. Do not use a generation as an install check.

## Update

Releases are pinned by `version` in `.claude-plugin/plugin.json`. You receive an update when that version changes.

| What | Command |
|---|---|
| Refresh the marketplace catalog | `/plugin marketplace update funi-ai` |
| Update the plugin | `/plugin update genmedia-skills@funi-ai` (terminal: `claude plugin update genmedia-skills@funi-ai`) |
| Apply without restarting | `/reload-plugins` |
| Update the CLI | `genmedia update` (check only: `genmedia update --check`) |

See [CHANGELOG.md](CHANGELOG.md) for what changed.

## Uninstall

```bash
claude plugin uninstall genmedia-skills@funi-ai
claude plugin marketplace remove funi-ai
```

Project state created by the skills stays where it is: `.genmedia/` (ledger, config, characters, project manifests) and `./genmedia-output/`. Delete them yourself if you no longer want them.

## Run from a checkout

```bash
git clone https://github.com/funi-ai/claude-plugins
claude --plugin-dir ./claude-plugins/plugins/genmedia-skills
```

The plugin is loaded for that session only, without installing it.

## Problems

See the Troubleshooting section of [README.md](README.md#troubleshooting), including the conflict with skills installed by `genmedia init`.
