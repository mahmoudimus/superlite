---
description: First-run check: toolchain, test command, model tiers, and conflicts with other plugins.
argument-hint: ""
---

Check and report, changing nothing without a yes:
- the project language and test command (`superlite-cli testcmd`, `test-cmd.json` or detection) and that it runs;
- Python 3.10+ for the `superlite-cli` tools;
- the model tiers in `config/models.json` and `config/routing.json`;
- whether the current session started with only the Superlite workflow enabled; see `docs/workflow-selection.md`;
- whether `.superlite/` is gitignored.
Give a pass or fix line for each.
