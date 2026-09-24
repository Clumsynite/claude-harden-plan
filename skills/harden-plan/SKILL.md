---
name: harden-plan
description: Draft (if missing), adversarially review and repair an implementation plan until it can run unattended in auto mode. Grounds the plan in the real codebase, researches best practices, lists every gap/flaw/risk with a fix, iterates until clean, asks all open questions in one batch, then stops without implementing.
argument-hint: "[plan-file | task description] [focus notes]"
disable-model-invocation: true
effort: high
---

# Harden Plan

Goal: turn the current plan into one that an executor with **no access to this conversation** could implement end to end in auto mode, making no guesses and needing no mid-run questions. You review, research, fix, and ask. You do **not** implement anything.

User input (may be empty): `$ARGUMENTS`

## Ground rules

- **No implementation.** Don't edit source files, install packages, run migrations, commit, or push. Read-only commands (reading files, grep, `git log`, `--version`, dry runs, running existing tests) are fine. The only file you write is the plan.
- **Evidence over opinion.** Every finding cites proof: `file:line`, command output, a doc URL, or a quoted line from the plan. Tag each one `CONFIRMED` (you checked it) or `UNVERIFIED` (a reasoned risk you couldn't check). Speculation like "might be slow" must name the mechanism.
- **Deliberate choices still get reviewed.** A choice being intentional doesn't exempt it. Don't pad the list either: a clean area gets one line saying so.
- **Decide what you can; ask only what you can't.** If the codebase, conventions, docs, or an obvious default answer something, decide it and record it under Assumptions. Ask the user only about real preferences, business rules, trade-offs with no clear winner, credentials or access, and anything destructive or irreversible.

## Phase 0: Locate the plan

Use the first match:
1. A file path in `$ARGUMENTS`.
2. In plan mode, the plan file named by the system (usually `~/.claude/plans/*.md`).
3. The latest plan written in this conversation. Save it to `./PLAN.md`, or to the plan file if in plan mode, so there's one source of truth to edit.
4. The newest file in `~/.claude/plans/` that matches this project. Confirm it with the user before using it.

**If no plan exists, create one.** The task comes from the non-path text in `$ARGUMENTS`, or else from what the user asked for in this conversation. If there's no task anywhere, ask the user what to plan (one question) and stop.
1. Explore the codebase enough to plan concretely (send `Explore` agents in parallel for large repos): the relevant files, conventions, and test/build commands.
2. Write a first draft using the section structure from Phase 6 (objective, context, steps with verification, test plan, risks, executor rules). Save it to the plan file if in plan mode, otherwise to `./PLAN.md`.
3. Mark it as `Draft: written by harden-plan` and tell the user in one line that you created it. Then continue to Phase 1 and harden it as rigorously as a plan someone else wrote. Being its author earns it no leniency. In Phase 3, the fresh-eyes critic is **mandatory**, because it's the only reviewer that didn't write the draft.

When a plan already exists, any non-path text in `$ARGUMENTS` is focus notes: weight those areas more heavily, but still cover everything.

Restate the plan's **objective, scope, and definition of done** in 2–4 lines. If you can't, that is finding #1.

## Phase 1: Ground in reality (parallel where possible)

Check that the plan matches the actual world before critiquing its logic:
- **Codebase:** every file, function, route, table, env var, script, and config the plan names. Does it exist, with that signature, at that path? Read the neighbouring code for conventions the plan should follow. Check CLAUDE.md / AGENTS.md / README / CONTRIBUTING for rules.
- **Toolchain:** real versions (lockfiles, `package.json`, `pyproject`, `go.mod`, and so on), test/lint/build/typecheck commands, CI config.
- **State:** git branch and dirty tree, existing tests and whether they pass now (if cheap), DB/migration state if relevant.
- For a large codebase, send `Explore` agents in parallel, one per area, instead of reading everything yourself.

## Phase 2: Research

For each significant technical decision, library, API, or pattern in the plan, look up current best practice and known pitfalls with WebSearch / WebFetch. Prefer official docs for **the versions actually installed**, changelogs and migration guides, GitHub issues for known bugs, and security advisories. Keep it targeted: 3–8 lookups for a typical plan, more for unfamiliar or high-risk tech. Record each source URL next to the finding it supports. If you find a clearly better approach, raise it as a finding with the trade-off. Don't silently rewrite the architecture.

## Phase 3: Critique

Run two passes and merge them:
1. **Your pass:** go through every dimension in [references/checklist.md](references/checklist.md). Skip a dimension only if it clearly doesn't apply, and say which ones you skipped.
2. **Fresh-eyes pass:** spawn one `general-purpose` subagent using the prompt in [references/critic-prompt.md](references/critic-prompt.md). Give it the plan's file path, the repo root, and the objective. Give it **none** of your findings, so it isn't anchored to them. For large or high-risk plans (auth, payments, data migrations, infra, more than ~15 steps), spawn two in parallel, one focused on correctness and completeness and one on failure modes, security, and operations.

Merge: drop duplicates, verify each subagent claim yourself (reject any you can't confirm and note why), and rank by severity:

| Sev | Meaning |
|---|---|
| **S1 Blocker** | Executor will fail, break things, lose data, or open a security hole |
| **S2 Major** | Likely rework, wrong behaviour in real cases, or the executor has to guess |
| **S3 Minor** | Quality, clarity, maintainability |
| **S4 Nit** | Optional polish (list briefly, don't expand) |

Present the findings as a table: `# | Sev | Area | Finding | Evidence | CONFIRMED/UNVERIFIED | Fix`. Each fix is concrete: what changes in the plan. Where it's a judgement call, give 2–3 options with a recommendation (include "do nothing" if that's reasonable).

## Phase 4: Fix, then iterate

1. Apply every fix that doesn't need the user's input directly to the plan file.
2. Mark every item that needs the user as an **Open Question** (hold them for Phase 5).
3. **Re-review the revised plan.** Fixes introduce new problems. Rerun the checklist on the changed sections, and check that step ordering and dependencies still hold as a whole.
4. Repeat until a round finds **no new S1/S2 issues**. Cap at **4 rounds**. If the same issue keeps coming back, or the cap is reached, stop and list it as unresolved with the reason. Don't loop.

Report each round in one line: `Round N: X found (S1:a S2:b S3:c), Y fixed, Z → questions`.

## Phase 5: Ask everything at once

Collect **every** open question and ask them together using AskUserQuestion (up to 4 per call; make back-to-back calls with no work in between if there are more). For each question:
- Give plain-English context and what goes wrong if the choice is wrong.
- Put the recommended option first, labelled "(Recommended)", with a one-line reason.
- Offer 2–4 concrete options, with trade-offs in the descriptions.
- Use multiSelect only for choices that aren't mutually exclusive.

Put destructive, irreversible, or outward-facing actions (data deletion, force-push, prod deploys, sending messages, paid resources) in their own explicit question. Never assume them.

After the answers arrive, fold them into the plan and run one more targeted Phase 4 pass on the affected sections. If the answers raise new questions, ask them in one more batch. If there are no open questions at all, say so and skip this phase.

## Phase 6: Readiness gate and handoff

The plan must pass **every** item in the "Auto-mode readiness gate" section of [references/checklist.md](references/checklist.md). Fix any failure, or list it as a known limitation.

Make sure the final plan file contains these sections (add any that are missing):
- **Objective & definition of done**: measurable acceptance criteria.
- **Context**: key files and conventions, verified versions, and decisions made with their reasons.
- **Assumptions**: what you decided without asking, and why.
- **Steps**: ordered, each with its exact files, the change, and a **verification command with expected result**.
- **Test plan**: new and updated tests, plus the full-suite / lint / typecheck / build commands.
- **Risks & rollback**: how to undo each risky step.
- **Executor rules**: stop-and-ask conditions (for example "if migration X fails, stop; don't retry with --force"), what's out of scope, and "don't expand scope".
- **Hardening log**: a short summary of the findings fixed, the questions answered, and anything unresolved.

Then output a short final summary: the plan path, a count of issues fixed by severity, decisions taken, anything unresolved, and the line **"Plan hardened. Ready for auto mode."** (or "Not ready: <reason>").

If you're in plan mode, call ExitPlanMode with the final plan so the user can approve it and pick auto mode. Otherwise, **stop**. Don't begin implementing, even if it seems obvious.
