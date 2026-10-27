# Security policy

## Reporting a vulnerability

Please report security problems privately through GitHub: open the [Security tab](https://github.com/funi-ai/claude-plugins/security) of this repository and choose **Report a vulnerability**, or go straight to the [report form](https://github.com/funi-ai/claude-plugins/security/advisories/new). Only the maintainers can see the report. Please don't open a public issue for a security problem.

If you can't use GitHub, email support@funi.ai with "Security" in the subject line.

Include the plugin version, the skill and script involved, and the steps or input that trigger the problem. We reply in the report thread, work on the fix there, and credit you in the published advisory unless you ask us not to.

## Scope

In scope is everything in this repository: the skill instructions and the scripts bundled with each skill. Examples of what we want to hear about:

- a script that writes, reads or deletes files outside the user's project, for example through a crafted path or a downloaded file name;
- the fal API key showing up in output, logs, the run ledger or a generated file;
- a skill instruction or script that runs a paid job without the cost check, or runs a command the skill does not describe;
- a downloaded result or user-supplied input that makes a script run code.

Out of scope, and better reported to their owners:

- the `genmedia` CLI, fal's API and fal's CDN: report to fal;
- Claude Code itself: report to Anthropic;
- the content a model generates. A wrong or unwanted image is not a vulnerability, but a bug report is welcome.

## Supported versions

Fixes go into the latest release only. Update with `/plugin update genmedia-skills@funi-ai`.
