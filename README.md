# Funi AI plugins for Claude Code

This repository is the Claude Code plugin marketplace of Funi AI. It currently holds one plugin.

| Plugin | What it does |
|---|---|
| [genmedia-skills](plugins/genmedia-skills/) | 17 agent skills that drive fal.ai's `genmedia` CLI: images, video, audio, consistent characters, 3D models, brand kits, App Store and Google Play graphics, demo videos and multi-step media pipelines. Model routing is checked against fal's live catalog, and every paid job is priced before it runs. |

genmedia-skills is an unofficial community project. It is not affiliated with, endorsed by or supported by fal or Anthropic.

## Install

Inside Claude Code:

```text
/plugin marketplace add funi-ai/claude-plugins
/plugin install genmedia-skills@funi-ai
```

Or from a terminal:

```bash
claude plugin marketplace add funi-ai/claude-plugins
claude plugin install genmedia-skills@funi-ai
```

Then run `/genmedia-skills:setup` inside Claude Code. It uses free commands only and tells you what is missing: the `genmedia` CLI, a fal API key (which you set up yourself, the plugin never touches it), `python3` and the optional local tools.

The plugin's [README](plugins/genmedia-skills/README.md) covers what each skill does, what it costs and what it sends where. [INSTALL.md](plugins/genmedia-skills/INSTALL.md) covers updates, pinning a release and uninstalling.

## Releases

Each release is tagged `<plugin>--v<version>`, for example `genmedia-skills--v0.1.0`, and listed on the [releases page](https://github.com/funi-ai/claude-plugins/releases) with its notes. Claude Code offers an update when the version in the plugin's `plugin.json` changes.

## Issues and contributions

Bug reports and feature requests are welcome in [issues](https://github.com/funi-ai/claude-plugins/issues/new/choose). We don't accept pull requests; [CONTRIBUTING.md](CONTRIBUTING.md) explains why and how to send a fix anyway. For security problems, see [SECURITY.md](SECURITY.md). Everything else: [SUPPORT.md](SUPPORT.md).

## License

[MIT](LICENSE).
