# Contributing

Thanks for wanting to help. Issues are open to everyone. Pull requests are turned off in this repository.

## Why pull requests are turned off

This repository is where releases are published. The plugin is developed in a separate repository, and every release replaces the plugin folder here with a fresh build. A change merged here would disappear at the next release.

Most changes also need checks we can't hand off. Every model ID, parameter and price in the skills is checked against fal's live catalog on the day it is written, and some changes only ship after paid test generations on our own fal account. We don't want contributors to pay for those.

## What helps

- A bug report with exact steps, versions and error output. The [bug report form](https://github.com/funi-ai/claude-plugins/issues/new?template=bug_report.yml) asks for each of them.
- A note when a model ID stops working or a price looks wrong, through [model or price out of date](https://github.com/funi-ai/claude-plugins/issues/new?template=routing.yml). Include the endpoint ID and the date you saw it.
- An idea for a skill, an output size or a platform, as a [feature request](https://github.com/funi-ai/claude-plugins/issues/new?template=feature_request.yml). One concrete example of the deliverable you want tells us more than a general wish.
- A fix you already worked out. Describe it in the issue or paste the diff in a code block, and if we use it we'll say so in the issue. By posting code in an issue, you agree that we may use it under this repository's MIT license.

Please keep API keys, private request IDs and media you don't want public out of issues. Security problems go through [private reporting](SECURITY.md).

## Forks

The plugin is MIT licensed, so you can fork it, change it and publish your own version. If you publish a fork, please give it a different name so people can tell the two apart.

## Conduct

Everyone who takes part follows the [code of conduct](CODE_OF_CONDUCT.md).
