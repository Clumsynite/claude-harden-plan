# harden-plan

[![CI](https://github.com/Clumsynite/claude-harden-plan/actions/workflows/ci.yml/badge.svg)](https://github.com/Clumsynite/claude-harden-plan/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/Clumsynite/claude-harden-plan?sort=semver)](https://github.com/Clumsynite/claude-harden-plan/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Claude Code plugin that turns an implementation plan into one an agent can run **unattended in auto mode**: no guesses and no questions mid-run. It reviews, researches, fixes and asks. It never implements.

- **`/harden-plan:harden-plan`** finds the current plan (or drafts one if there isn't one), checks it against the real codebase, researches the libraries and patterns it relies on, lists every gap with evidence and a fix, repairs the plan, and repeats until nothing serious is left. Then it asks all remaining questions in one batch and stops.

## Why

A plan that reads fine in conversation often falls apart when an agent runs it alone: a file path that doesn't exist, an API from a newer version than the one installed, a step with no way to check it worked, a "handle errors appropriately" that forces a guess, or a destructive command nobody approved. Once you walk away, each of those is a failed or wrong run. harden-plan catches them first, while you're still at the keyboard.

## Install

From GitHub:

```
/plugin marketplace add Clumsynite/claude-harden-plan
/plugin install harden-plan@clumsyknight-harden-plan
```

From a local clone:

```
claude plugin marketplace add /path/to/harden-plan
claude plugin install harden-plan@clumsyknight-harden-plan --scope user
```

A local marketplace loads the plugin in place, so edits take effect after `/reload-plugins`.

## Usage

| Command | What it does |
|---|---|
| `/harden-plan:harden-plan` | Harden the plan in this conversation (or the plan-mode plan file) |
| `/harden-plan:harden-plan path/to/PLAN.md` | Harden a specific plan file |
| `/harden-plan:harden-plan path/to/PLAN.md focus on the migration` | The same, weighting some areas more heavily |
| `/harden-plan:harden-plan add rate limiting to the API` | No plan yet: draft one for this task, then harden it |

The skill is user-invoked only (`disable-model-invocation`), so Claude never runs it unless you ask. It runs at `effort: high`.

In plan mode it edits the plan file and finishes with `ExitPlanMode`, so you can approve the plan and pick auto mode. Outside plan mode it saves to `./PLAN.md` (or the file you gave it) and stops.

## What it does

| Phase | Work |
|---|---|
| 0. Locate | Find the plan: an argument, the plan-mode file, the latest plan in the conversation, or `~/.claude/plans/`. Draft one if there's none. |
| 1. Ground | Check every file, symbol, script, env var and version the plan names against the repo, CLAUDE.md, lockfiles and CI. |
| 2. Research | Look up best practice and known pitfalls for the installed versions, and cite the URLs. |
| 3. Critique | Its own pass over a 13-dimension [checklist](skills/harden-plan/references/checklist.md), plus a separate [fresh-eyes critic](skills/harden-plan/references/critic-prompt.md) subagent that sees none of its findings. Two critics for high-risk plans. |
| 4. Fix and iterate | Apply fixes, re-review the changed sections, and repeat until a round finds no new S1/S2 issues (at most 4 rounds). |
| 5. Ask | All open questions in one `AskUserQuestion` batch, with a recommended option first. Destructive or outward-facing actions always get their own question. |
| 6. Gate | Pass the auto-mode readiness gate, then hand off with the line "Plan hardened. Ready for auto mode." |

Every finding cites evidence (`file:line`, command output, a doc URL, or a quote from the plan) and is tagged `CONFIRMED` or `UNVERIFIED`. Severity runs from S1 Blocker to S4 Nit.

### The hardened plan

The final plan file always has these sections: objective and definition of done, context, assumptions, steps (each with exact files and a verification command with its expected result), test plan, risks and rollback, executor rules (stop-and-ask conditions and what's out of scope), and a hardening log.

### What it won't do

It doesn't edit source files, install packages, run migrations, commit or push. The only file it writes is the plan. Read-only commands such as `grep`, `git log`, dry runs and the existing tests are fine.

## Development

```
claude plugin validate .
```

CI (`.github/workflows/ci.yml`) checks the JSON manifests, the skill's frontmatter, and that the reference files exist.

The whole plugin is the skill: [`skills/harden-plan/SKILL.md`](skills/harden-plan/SKILL.md) plus its two reference files. It's user-invoked only, so there's no trigger-eval suite.

### Releasing

`version` in `.claude-plugin/plugin.json` pins installed copies: users only get changes when it is bumped.

1. Bump `version` in `.claude-plugin/plugin.json` and commit.
2. Wait for CI to pass on `main`.
3. `claude plugin tag --push .` (creates and pushes `harden-plan--v<version>`), then `gh release create harden-plan--v<version> --generate-notes`.

## License

MIT. See [LICENSE](LICENSE).
