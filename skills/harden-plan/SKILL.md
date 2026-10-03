---
name: harden-plan
description: Draft (if missing), adversarially review and repair an implementation plan until it can run unattended in auto mode. Grounds the plan in the real codebase and executor environment, researches best practices, lists every gap/flaw/risk with a fix, iterates until a fresh critic signs off, asks all open questions in one batch, then stops without implementing.
argument-hint: "[--quick | --deep] [plan-file | task description] [focus notes]"
disable-model-invocation: true
effort: high
---

# Harden Plan

Goal: turn the current plan into one that an executor with **no access to this conversation** could implement end to end in auto mode, making no guesses and needing no mid-run questions. You review, research, fix, and ask. You do **not** implement anything.

User input (may be empty): `$ARGUMENTS`

Snapshot at invocation:
- Branch and tree: !`git status --short --branch 2>/dev/null | head -15 || true`
- Recent plan-mode files: !`ls -t ~/.claude/plans 2>/dev/null | head -5 || true`

## Ground rules

- **No implementation.** Don't edit source files, install packages, run migrations, commit, or push. Read-only commands (reading files, grep, `git log`, `--version`, dry runs, running existing tests) are fine. The only files you write are the plan, its synced copy, and scratch files.
- **Evidence over opinion.** Every finding cites proof: `file:line`, command output, a doc URL, or a quoted line from the plan. Tag each one `CONFIRMED` (you checked it) or `UNVERIFIED` (a reasoned risk you couldn't check). Speculation like "might be slow" must name the mechanism.
- **Never claim a pass you didn't run.** A `Round N` line, "no new findings", or "Ready" must point to the review that produced it. If a step was skipped or failed, say so.
- **Deliberate choices still get reviewed.** A choice being intentional doesn't exempt it. Don't pad the list either: a clean area gets one line saying so.
- **Decide what you can; ask only what you can't.** If the codebase, conventions, docs, memory, past plans, the machine or an obvious default answers something, decide it and record it under Assumptions. Ask the user only about real preferences, business rules, trade-offs with no clear winner, credentials or access, and anything destructive or irreversible.
- **Secrets:** when grounding reads `.env` files, shell history or configs, note key *names* only. Never echo a value; if one turns up in plain text, report its location.
- **Don't look idle.** Critics take minutes. Start them first and do your own work while they run. If you must end a turn while waiting, end it with: "Critic running; I'll continue automatically when it reports. No need to re-run /harden-plan."
- **After compaction**, re-read `references/checklist.md` and this file's current phase before continuing.

## Phase 0: Locate the plan and pick the mode

**Already running?** If an earlier /harden-plan run in this conversation hasn't finished (a critic is pending, or questions are unanswered), resume it. Don't start over.

**Find the plan.** Use the first match:
1. A file path in `$ARGUMENTS`.
2. In plan mode, the plan file named by the system (usually `~/.claude/plans/*.md`).
3. The latest plan written in this conversation. Outside plan mode, save it to `./PLAN.md` first so there's one file to edit.
4. The newest file in `~/.claude/plans/` that matches this project. Confirm it with the user before using it (this one can't wait for Phase 5).

**One working file, one durable copy.** In plan mode, edit the plan-mode file (that's what ExitPlanMode shows). Also decide the durable copy: the path from `$ARGUMENTS` if given; else the plan this conversation came from (for example, a hub `plans/*.md` named in CLAUDE.md); else `./PLAN.md`. Plan mode only lets you write the plan file, so the plan's **Step 0** tells the executor to copy the approved plan to the durable path (overwriting the older version) and keep its status line up to date. Outside plan mode, the working file *is* the durable copy.

**Stale plan?** If the plan's status says done, or its steps are already in the git log or tree, ask one question before doing anything else: harden the next iteration, re-check this one, or stop.

Other questions that come up here (scope, preferences) wait for the Phase 5 batch. Ask in Phase 0 only what blocks you from starting.

**Re-run mode.** If the plan already has a Hardening log, or the user rejected ExitPlanMode and re-invoked you, this is a re-run. The previous pass missed something. Don't repeat it:
- Re-read the whole plan and everything changed since the last log entry.
- In Phase 3, give the critic a lens the Hardening log hasn't used yet (see [references/critic-prompt.md](references/critic-prompt.md)). Once all lenses are used, use `correctness` again with a fresh agent.
- If the user said why they rejected it, that's the focus.
- Rounds count per invocation.

**If no plan exists, create one.** The task comes from the non-path text in `$ARGUMENTS`, or else from what the user asked for in this conversation. If there's no task anywhere, ask the user what to plan (one question) and stop.
1. If the target (which host, repo, device, environment) is unclear, settle it first. Don't access remote machines until you know which one.
2. Explore the codebase enough to plan concretely (send `Explore` agents in parallel for large repos): the relevant files, conventions, and test/build commands.
3. Write a first draft using the section structure from Phase 6. Save it to the working file.
4. Mark it `Draft: written by harden-plan` and tell the user in one line that you created it. Then harden it as rigorously as a plan someone else wrote. Being its author earns it no leniency.

When a plan already exists, any non-path text in `$ARGUMENTS` is focus notes: weight those areas more heavily, but still cover everything.

**Intent check.** Quote what the user literally asked for. Restate the plan's objective, scope and definition of done in 2–4 lines, then compare:
- Does the plan solve that request, or a nearby one?
- Where does the behaviour show up for the user (UI, live paths, mocks, other services)? Does the plan cover each place?
- Is anything in scope only because you found it in the environment (hosts in history, repos in ssh config) rather than because the user named it? Drop it, or make it a question with "keep generic" as an option.

If you can't restate the objective, or it doesn't match the request, that is finding #1.

**Pick the depth**, and state it in one line with the reason. `--quick` or `--deep` in `$ARGUMENTS` overrides the choice; otherwise decide from the plan:

| Depth | When | Phase 3 critics | Research | Fix rounds |
|---|---|---|---|---|
| `quick` | ≤ 5 steps, one area, nothing destructive, no auth/data/infra/remote hosts | none: your own pass only | only for libraries or APIs the repo doesn't already use | 1 |
| `standard` | everything else | 1, plus an `outcome` critic if anything user-visible changes | 3–8 lookups | up to 3 |
| `deep` | auth, payments, data migrations, infra, remote hosts or shared machines, > 15 steps, or a re-run after a "Ready" that was wrong | 2 or 3 in parallel (see Phase 3) | as needed, including advisories | up to 3 |

Every depth ends with the Phase 6 sign-off critic, so even `quick` gets one independent review of the final plan. A re-run is never `quick`.

## Phase 1: Ground in reality (parallel where possible)

Check that the plan matches the actual world before critiquing its logic:
- **Codebase:** every file, function, route, table, env var, script, and config the plan names. Does it exist, with that signature, at that path? Read the neighbouring code for conventions the plan should follow (data access, seeding, migrations, tests, commit style), and cite a file for each. Check CLAUDE.md / AGENTS.md / README / CONTRIBUTING for rules.
- **Toolchain:** real versions (lockfiles, `package.json`, `pyproject`, `go.mod`, and so on), test/lint/build/typecheck commands, CI config.
- **State:** git branch and dirty tree (including other sessions' uncommitted work in the files the plan touches), existing tests and whether they pass now (if cheap), DB/migration state if relevant.
- **Executor environment** (checklist §2b): hooks and guards in user, project and plugin settings and what they block; the user's shell; commands only the user may run; which branch, worktree, DB and host the run uses; versions on every remote target. Check remote hosts read-only.
- **The user's habits:** memory, CLAUDE.md and earlier plans in the same hub show how this user usually publishes, releases, tests and commits. Use them for defaults and recommended options.
- For a large codebase, send `Explore` agents in parallel, one per area, instead of reading everything yourself.

## Phase 2: Research

For each significant technical decision, library, API, or pattern in the plan, look up current best practice and known pitfalls with WebSearch / WebFetch. Prefer official docs for **the versions actually installed**, changelogs and migration guides, GitHub issues for known bugs, and security advisories. Keep it targeted: 3–8 lookups for a typical plan, more for unfamiliar or high-risk tech. Record each source URL next to the finding it supports.

If you skip research, write the reason in the Hardening log. Never state a technical claim to the user, or base a recommended option on one, without checking it. If you find a clearly better approach, raise it as a finding with the trade-off. Don't silently rewrite the architecture.

## Phase 3: Critique

Run two passes and merge them. Start the critic first so it works while you do your own pass:
1. **Fresh-eyes pass:** spawn a critic using [references/critic-prompt.md](references/critic-prompt.md). It tells you which agent type to use, how to give it the plan without your findings or the Hardening log, and which lens to give it.
   - `quick`: skip this pass; the Phase 6 sign-off is the critic.
   - `standard`: one critic, lens `correctness`. Add an `outcome` critic in parallel when the plan changes anything user-visible.
   - `deep`: two in parallel, `correctness` + `failure`, or `executor-env` instead of `failure` if the run touches hosts, hooks or deploys. Add `outcome` as a third when anything user-visible changes.
   - Never skip the critic because the plan looks fine, or because a general "no agents" preference exists. Invoking /harden-plan is the request for it.
   - If a critic errors or stalls, retry once with a narrower scope. If that also fails, do the review yourself on a clean read of the plan, label it "self-review (critic unavailable)", and say so in the final summary.
2. **Your pass, while the critic runs:** go through every dimension in [references/checklist.md](references/checklist.md). Skip a dimension only if it clearly doesn't apply, and say which ones you skipped.

**Critic budget per invocation:** critics run only here and at the Phase 6 sign-off, at most **3 critic rounds** in all (parallel critics in one round count as one round; the sign-off counts). Phase 4 re-reviews are your own.

**Merge:** drop duplicates. Verify each critic claim yourself, and reject any you can't confirm (note why). Rank by severity:

| Sev | Meaning |
|---|---|
| **S1 Blocker** | Executor will fail, break things, lose data, or open a security hole |
| **S2 Major** | Likely rework, wrong behaviour in real cases, or the executor has to guess |
| **S3 Minor** | Quality, clarity, maintainability |
| **S4 Nit** | Optional polish (list briefly, don't expand) |

Record the findings table in the plan's Hardening log: `# | Sev | Area | Finding | Evidence | CONFIRMED/UNVERIFIED | Fix`. In chat, show only the S1/S2 rows and the counts. Each fix is concrete: what changes in the plan. Where it's a judgement call, give 2–3 options with a recommendation (include "do nothing" if that's reasonable).

## Phase 4: Fix, then iterate

1. Apply every fix that doesn't need the user's input directly to the plan file.
2. For each fix, ask: what legitimate case does this now block, and what did it add that the objective doesn't need? A fix that over-restricts or bloats is a new finding.
3. Mark every item that needs the user as an **Open Question** (hold them for Phase 5).
4. **Re-review the whole revised plan**, not just the changed sections. Fixes break other steps: ordering, references, shared variables, shell flags. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/lint_plan.py <plan>` and fix its errors.
5. Only **CONFIRMED** S1/S2 findings start another round. UNVERIFIED ones become questions or go under Risks.

Stop when a round finds no new confirmed S1/S2, then go to Phase 5. Cap at **3 fix rounds** per invocation (1 at `quick`; rounds after the user's answers count too). If the same issue keeps coming back, or the cap is reached, list it as unresolved with the reason. Don't loop.

Report each round in one line, naming who reviewed: `Round N (self | critic:<lens>): X found (S1:a S2:b S3:c), Y fixed, Z → questions`.

## Phase 5: Ask everything at once

Ask only after every critic has reported and been merged. One batch, not a drip.

Before asking, try to answer each question yourself: check the repo, the machine (read-only), memory, CLAUDE.md, earlier plans and past choices, and the tools available (for example, a browser tool or a connected device). Drop any question you can answer and record the answer under Assumptions.

Then ask with AskUserQuestion: up to 4 per call; back-to-back calls with no work in between if there are more. For each question:
- Give plain-English context and say what goes wrong if the choice is wrong. Use the real names from the code and the user's words. Don't coin terms.
- Put the recommended option first, labelled "(Recommended)", with a one-line reason. Base it on checked facts and on what this user usually chooses, not on the most cautious option by default.
- Offer 2–4 concrete options, with trade-offs in the descriptions.
- Check the options across questions for combinations that conflict. If one question depends on another's answer, decide the first yourself or ask it alone first.
- Use multiSelect only for choices that aren't mutually exclusive.

Put destructive, irreversible, or outward-facing actions (data deletion, force-push, prod deploys, sending messages, paid resources, installing on shared machines) in their own explicit question. Never assume them. Ask one combined question about where the work lands (branch, worktree, push or not) unless the plan or the user already settled it.

**After the answers:**
- Fold each answer into the plan. Treat a free-text "Other" answer as an instruction, not as a prompt for clarifying questions, unless it conflicts with something.
- Run a Phase 4 round on every section an answer touched.
- If an answer changes the base branch, scope, target, core design or threat model, also re-run Phase 1 grounding on what changed.
- If the answers raise new questions, ask them in one more batch.

If there are no open questions at all, say so and skip this phase.

## Phase 6: Sign-off, gate and handoff

1. **Final critic sign-off.** Spawn one fresh critic on the **whole** final plan, with lens `correctness`, or `executor-env` if the run touches hosts, hooks or deploys. The fresh context is what matters, not a new lens. Skip it only if the previous critic round ran on this exact text with no edits since.
   - New confirmed S1/S2: fix them, run the lint, and do one more sign-off if the critic budget allows.
   - Still S1/S2, or no budget left: stop with "Not ready" and list them.
   - If the sign-off raises a question only the user can answer, ask it in one final batch, apply the answer, and note in the summary that this change had no critic pass.
   - Plan scope that changes after sign-off (the user adds a milestone, say) needs a new sign-off before handoff.
2. **Readiness gate.** The plan must pass **every** item in the "Auto-mode readiness gate" section of [references/checklist.md](references/checklist.md), and `python3 ${CLAUDE_SKILL_DIR}/scripts/lint_plan.py <plan>` must report 0 errors. Fix any failure. One that can't be fixed means "Not ready", unless the user explicitly accepted it as a risk.

Make sure the final plan file contains these sections (add any that are missing):
- **Objective & definition of done**: measurable acceptance criteria, checked on the real target.
- **Context**: key files and conventions, verified versions, and decisions made with their reasons.
- **Assumptions**: what you decided without asking, and why.
- **Pre-flight (user)**: anything only the user can do before the run (logins, user-only commands, approvals), or "none".
- **Steps**: ordered, each with its exact files, the change, and a **verification command with expected result**.
- **Test plan**: new and updated tests, the full-suite / lint / typecheck / build commands, and the runtime check of the user-visible outcome.
- **Risks & rollback**: how to undo each risky step.
- **Executor rules**: where the work lands (branch, worktree, commit granularity, push or not); stop-and-ask conditions (for example "if migration X fails, stop; don't retry with --force"); commands to avoid because a hook or guard blocks them; what's out of scope; and "don't expand scope".
- **Hardening log**: date, rounds with reviewer and lens, the findings table, questions answered, research skipped and why, and anything unresolved.

**Sync:** outside plan mode the working file is already the durable copy. In plan mode, check Step 0 names the durable path; the executor writes it after approval.

**Summary.** Output it before ExitPlanMode, always, starting with:
- The plan path(s): the working file and the durable copy.
- Where the work lands: branch, worktree, push or no push.
- The round lines, and the critics' lenses (covered and not covered).
- A count of issues fixed by severity, decisions taken, and anything unresolved.
- The verdict: **"Plan hardened. Ready for auto mode."** only if the final sign-off found no S1/S2 and the gate and lint pass. Otherwise **"Not ready: <reason>"**. Add "(self-reviewed; critic unavailable)" when that's what happened.

If you're in plan mode, call ExitPlanMode with the final plan so the user can approve it and pick auto mode. Otherwise, **stop**. Don't begin implementing, even if it seems obvious.
