# Use Superlite beside Superpowers

Keep your normal Superpowers setup. Start a fresh session with the Superlite
options below when you want its plan and parallel review workflow. The host
selects the workflow before sending the first prompt. Resume a chat with the
same workflow it started with. On Codex and Pi, if the run moves to a
different worktree, start a fresh Superlite chat in that worktree before
writing the review plan. Approval hooks use the chat workspace.

Use a checkout of [mahmoudimus/superlite](https://github.com/mahmoudimus/superlite).
In the examples, set `sl` to the absolute path to its `scripts/superlite-session`.
The launcher requires Python 3.12 or later and the host on PATH.

## Claude Code

From the project:

```sh
"$sl" claude
```

The launcher finds installed Superpowers and Superlite plugin IDs, disables
those IDs for this session, and loads the fork from the checkout. The normal
`claude` command keeps using your existing plugins. The runtime does not edit
Claude settings on a new run. Finishing an older upstream run can still
restore settings changed by that version.

## Codex CLI and Desktop

Install the fork into Codex's local marketplace, then disable it in the
default configuration so other sessions still use Superpowers:

```sh
codex plugin marketplace add mahmoudimus/superlite
codex plugin add superlite@superlite-maintained
```

After installation, set `enabled = false` in the existing
`[plugins."superlite@superlite-maintained"]` section of your user
`config.toml` (normally under `~/.codex`). Keep any existing Superpowers
settings. Generate the Superlite plugin selection with:

```sh
"$sl" codex-config
```

- **CLI.** Save or merge that output into `~/.codex/superlite.config.toml`
  (or your `CODEX_HOME`). From your project, run `"$sl" codex`.
- **Desktop.** Merge that output into `.codex/config.toml` of a **separate
  checkout or worktree** for Superlite. Open and trust that workspace in
  Codex. Use an ordinary workspace for the Superpowers chat. Keep a local
  overlay out of commits if it is just for you.

Review and trust the fork's `SessionStart` and `UserPromptSubmit` hooks
before the first build. In the CLI use `/hooks`. In Desktop use **Review hooks**
from the composer or **Settings > Hooks**. The first hook loads the
workflow instructions. The second records a chat reply for the plan
approval gate. In human mode, send your approval in a new chat message
after reviewing the plan. Codex uses native subagents where available.

Superlite's session and checkpoint commands write Git metadata. If Codex
blocks them, approve the specific Git operation through the host. For
unattended trials, use a dedicated disposable clone and a Codex permission
profile that allows writes to that clone's Git metadata. Keep the normal
profile for your everyday workspace.

The overlay targets local marketplace plugins. Workspace-managed plugins
and standalone copies of Superpowers skills are configured separately.

## Pi

From the project:

```sh
"$sl" pi
```

This loads the fork with its skills and bootstrap and skips auto discovery
of extensions and skills. Add any desired companion extensions explicitly.
For example, if `pi-subagents` was installed in the usual package directory:

```sh
"$sl" pi -e "$HOME/.pi/agent/npm/node_modules/pi-subagents"
```

Use natural language to start a run. Give approval as a separate message
after the plan. Agent-generated extension input is not recorded as approval.
The default `pi` command keeps its normal resource discovery.

## Check the workflow

Open a fresh Superlite session and a normal session side by side. In each,
ask for a plan for the same small two-task change. In the Superlite session
confirm Superlite routes the request, waits for a plan approval, and runs
its dispatch and final review after approval. Send a follow-up and compact
the session where the host supports it. Keep a separate worktree for each
session that edits files.
