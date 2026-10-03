# harden-plan

[![CI](https://github.com/Clumsynite/claude-harden-plan/actions/workflows/ci.yml/badge.svg)](https://github.com/Clumsynite/claude-harden-plan/actions/workflows/ci.yml)
[![Release](https://github.com/Clumsynite/claude-harden-plan/actions/workflows/release.yml/badge.svg)](https://github.com/Clumsynite/claude-harden-plan/actions/workflows/release.yml)
[![Latest release](https://img.shields.io/github/v/release/Clumsynite/claude-harden-plan?display_name=release)](https://github.com/Clumsynite/claude-harden-plan/releases/latest)
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
| `/harden-plan:harden-plan --quick PLAN.md` | Small plan: own review plus one critic sign-off, one fix round |
| `/harden-plan:harden-plan --deep PLAN.md` | High-risk plan: two or three parallel critics, then the sign-off |

Without a flag it picks the depth from the plan: `quick` for ≤ 5 low-risk steps in one area, `deep` for auth, payments, data migrations, infra, remote hosts, more than 15 steps, or a re-run after a wrong "Ready"; `standard` otherwise.

The skill is user-invoked only (`disable-model-invocation`), so Claude never runs it unless you ask. It runs at `effort: high`.

In plan mode it edits the plan file and finishes with `ExitPlanMode`, so you can approve the plan and pick auto mode. Outside plan mode it edits the file you gave it (or saves a conversation-only plan to `./PLAN.md`) and stops.

## What it does

| Phase | Work |
|---|---|
| 0. Locate | Find the plan: an argument, the plan-mode file, the latest plan in the conversation, or `~/.claude/plans/`. Draft one if there's none. Detect a re-run (the plan already has a Hardening log) or a stale plan, and check the plan's objective against what you literally asked for. |
| 1. Ground | Check every file, symbol, script, env var and version the plan names against the repo, CLAUDE.md, lockfiles and CI, plus the executor environment: hooks and guards that would block commands, your shell, user-only commands, branch, worktree, DB, and versions on remote hosts. |
| 2. Research | Look up best practice and known pitfalls for the installed versions, and cite the URLs. Skipping research has to be justified in the log. |
| 3. Critique | Its own pass over the [checklist](skills/harden-plan/references/checklist.md), plus a read-only [fresh-eyes critic](skills/harden-plan/references/critic-prompt.md) that reviews a snapshot with the earlier findings stripped out. Each critic gets a lens (correctness, failure, executor-env, outcome, simplicity); re-runs use a lens not used before. |
| 4. Fix and iterate | Apply fixes, re-review the **whole** plan, run the plan linter, and repeat until a round finds no new confirmed S1/S2 issues (at most 3 rounds). |
| 5. Ask | Once every critic has reported: try to answer each question from the repo, the machine, memory and past plans, then ask the rest in one `AskUserQuestion` batch with a recommended option first. Answers that change scope or the target trigger a re-check. Destructive or outward-facing actions always get their own question. |
| 6. Sign-off and gate | A fresh critic reviews the final plan. "Plan hardened. Ready for auto mode." only if it finds no new S1/S2 and the readiness gate and linter pass; otherwise "Not ready: …". |

Every finding cites evidence (`file:line`, command output, a doc URL, or a quote from the plan) and is tagged `CONFIRMED` or `UNVERIFIED`. Severity runs from S1 Blocker to S4 Nit.

### The hardened plan

The final plan file always has these sections: objective and definition of done, context, assumptions, pre-flight steps for the user, steps (each with exact files and a verification command with its expected result), test plan, risks and rollback, executor rules (where the work lands, stop-and-ask conditions, commands your hooks block, and what's out of scope), and a hardening log.

In plan mode it edits the plan-mode file, since plan mode allows writing nothing else. The plan's Step 0 tells the executor to copy it, once approved, to a durable path: the one you passed, else the hub plan it came from, else `./PLAN.md`.

### What it won't do

It doesn't edit source files, install packages, run migrations, commit or push. The only files it writes are the plan and scratch copies for the critic. Read-only commands such as `grep`, `git log`, dry runs and the existing tests are fine.

## Development

```
claude plugin validate .
```

CI (`.github/workflows/ci.yml`) checks the JSON manifests, the skill's frontmatter, that the reference files exist, and that the plan linter passes `tests/fixtures/good-plan.md` and fails `tests/fixtures/bad-plan.md`.

The plugin is:
- the skill, [`skills/harden-plan/SKILL.md`](skills/harden-plan/SKILL.md), with its checklist and critic brief in `references/`;
- [`scripts/lint_plan.py`](skills/harden-plan/scripts/lint_plan.py), a deterministic check for required sections, vague wording, references to chat context, and steps without verification (`python3 skills/harden-plan/scripts/lint_plan.py PLAN.md`);
- [`agents/plan-critic.md`](agents/plan-critic.md), the read-only critic (no edit tools). If the skill is installed on its own, without the plugin, it falls back to a `general-purpose` agent with the same brief, or to a `Plan` agent if plan mode refuses that.

It's user-invoked only, so the evals test behaviour, not triggering. [`evals/`](evals/README.md) has two `claude plugin eval` cases: one plan with seven planted defects, and a draft-from-nothing run, both against a small fixture repo. A full run takes tens of minutes and counts against your usage, so CI doesn't run it:

```
claude plugin eval . --scaffold --ablation none --trust-plugin \
  --allow-tools Bash Edit Write WebSearch WebFetch --max-cost-usd 20
```

### Releasing

`version` in `.claude-plugin/plugin.json` pins installed copies: users only get changes when it is bumped.

Releases are built by CI/CD:

1. Bump `version` in `.claude-plugin/plugin.json`, commit, and push to `main`.
2. When CI passes on that push, `.github/workflows/release.yml` creates the tag `harden-plan--v<version>` and a GitHub release with generated notes at the tested commit. If that release already exists (e.g. a push without a version bump), it does nothing. It can also be run by hand from the Actions tab.

## License

MIT. See [LICENSE](LICENSE).
