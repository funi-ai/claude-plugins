# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version lives only in `.claude-plugin/plugin.json`.

## [0.1.0] - 2026-10-27

First public release. Needs Claude Code and fal's `genmedia` CLI 0.7.0 or newer, with a fal API key that you set up yourself.

### Added

- 17 skills. Invoke one as `/genmedia-skills:<skill>`, or describe what you want and let Claude pick:
  - `setup` checks the CLI, the key, `python3` and the optional local tools with free commands only, and writes `.genmedia/config.json`.
  - `models` says which model fits a job, compares models, estimates costs and checks that an endpoint ID is still live.
  - `image`, `video` and `audio` cover one-off generations and edits, from text-to-image and inpainting to image-to-video, lipsync, text-to-speech, music and transcription.
  - `character` keeps a local character sheet that other skills reuse through an `@handle`, with optional LoRA training.
  - `pipelines` runs multi-step productions that no other skill owns, such as storyboard to film, stitching clips, or muxing voice-over, music and captions onto a video.
  - `product-photoshoot`, `ads`, `short-video`, `video-explainer`, `youtube-thumbnail` and `marketplace-cards` produce finished product photos, ads, short-form videos, narrated explainers, thumbnails and marketplace listing images.
  - `brandkit` takes a brand from palette to approved SVG logos, a brandbook and app icon files for the App Store, Google Play, the web and macOS.
  - `3d` creates and post-processes mesh files (GLB, USDZ, FBX, OBJ, STL) and checks each one with a bundled inspector.
  - `launch-graphics` composes your real app captures into App Store and Google Play screenshot sets, App Store creative assets for iOS 27, Open Graph and X link cards, Product Hunt gallery images, email cards and ad sizes.
  - `demo-video` cuts product demos, store preview videos and App Store header and search videos from your real screen recording with local ffmpeg.
- Cost checks before every paid call. Prices come from `genmedia pricing`; small jobs run, larger ones are announced, and jobs at or above the confirmation threshold wait for your yes, as does every training job. The thresholds are in `.genmedia/config.json`.
- Dated routing tables for image, video, audio and utility models. Each endpoint was checked against fal's live catalog on the date shown, and the agent checks it again before the first paid call of a session.
- `gm.py`, the bundled helper (Python standard library only). It submits jobs to fal's queue, records each request ID before it waits, resumes a timed-out job instead of submitting it again, and downloads the results.
- Project state in `.genmedia/` and deliverables in `./genmedia-output/`, so an interrupted session can continue where it stopped.
- Installs from the `funi-ai` marketplace: `claude plugin marketplace add funi-ai/claude-plugins`, then `claude plugin install genmedia-skills@funi-ai`.

[0.1.0]: https://github.com/funi-ai/claude-plugins/releases/tag/genmedia-skills--v0.1.0
