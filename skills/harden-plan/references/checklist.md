# Plan review checklist

Work through each dimension. For every item, ask: *would an executor with no chat history get this right the first time?*

## 1. Goal & scope
- Is the objective unambiguous, and does the plan actually achieve it (not just something nearby)?
- Does it match what the user literally asked for? Trace every place the behaviour shows up for them (UI, live paths, mocks, sockets, other services). If the request has two readings, has the plan picked one silently?
- Is anything in scope only because it was found in the environment (hosts in shell history, repos in ssh config, other projects) rather than named by the user?
- Is the definition of done measurable (a command, a test, observable behaviour)?
- Is scope explicit: what's in, and what's deliberately out? Is there any hidden scope creep or gold-plating?
- Is this the simplest approach that meets the goal? Is there a smaller or safer path? Did hardening add machinery (containers, services, abstractions) the objective doesn't need?
- Proportion: a plan longer than the code it describes is a transcript of the code, not a plan.

## 2. Grounding & feasibility
- Do all referenced files, symbols, APIs, tables, env vars, and scripts exist as described? (Verify them, don't assume.)
- Do library/API usages match the **installed** versions, not the latest docs?
- Are any required capabilities missing (permissions, credentials, network access, paid services, OS/tooling)?
- Are any steps impossible in a non-interactive run (prompts, logins, browser OAuth, 2FA, GUI-only steps)?
- Is there any step only a human can do ("confirm…", "use it for a few days", "check that it feels right")? Move it to a pre-flight list the user does before handoff, or to user acceptance after the run.

## 2b. Executor environment (will the run actually be allowed to do this, here?)
- Hooks and guards in `~/.claude/settings.json`, `.claude/settings*.json` and installed plugins (command guards, clean-guard, PreToolUse hooks): which planned commands will they block? Common ones: `rm -rf "$VAR"`, `> "$VAR"` redirects, `<(…)`, `--no-verify`, force-push, `git stash`/`checkout` in a shared tree. Rewrite steps to avoid them (the Write/Edit tools instead of heredocs, literal paths).
- Commands that only the user may run (e.g. a per-repo decision a hook reserves for the user): list them as pre-run actions.
- Shell: the user's shell (zsh doesn't word-split unquoted `$VAR`), and whether scripts run under `sh`, `bash` or `dash`.
- Auto mode: steps the safety check is likely to block (prod data, unknown remotes or hosts, broad deletes, credentials). Get specific approval up front, or rewrite them.
- Plan mode must be off before any implementation step or implementation subagent runs.
- Where it runs: which branch (and base), which worktree, which DB (never a prod copy unless approved), which host, and how the user actually reaches it (ssh alias or IP). Is someone else's uncommitted work in the same files?
- Versions on **every** target host, not just this machine (runtime, package manager, OS).
- Data: if the approach depends on data shape or volume, has it been measured on real data?

## 3. Completeness
- Missing steps: config, env vars, dependency installs, codegen, migrations, seed data, feature flags, docs, changelog, types, i18n strings, exports/barrels, route registration, DI wiring.
- Are all callers and consumers of changed interfaces updated (grep for usages)?
- Build/CI changes, lockfile updates, Docker/infra files?
- Cleanup: dead code, temporary scaffolding, old feature flags.

## 4. Ordering & dependencies
- Is each step's precondition produced by an earlier step?
- Can the repo build and pass tests at each checkpoint, or at least at clearly marked ones?
- Are migrations ordered safely with deploys (expand → migrate → contract)?
- Which steps can run in parallel, and which must be sequential?

## 5. Correctness & edge cases
- Empty, null, missing, huge, malformed, unicode, and boundary inputs.
- Concurrency: races, double submits, retries, idempotency, ordering.
- Time: timezones, DST, clocks, expiry, leap cases.
- Partial failure midway: what state does it leave?
- Backward compatibility: existing data, old clients, public APIs, serialized formats, cached values.

## 6. Error handling & failure modes (pre-mortem)
- Imagine it shipped and failed badly a week later. What are the three most likely causes? Does the plan prevent or detect each one?
- Are external calls handled for timeouts, retries with backoff, rate limits, and non-2xx responses?
- Are errors surfaced, logged, and actionable rather than swallowed?

## 7. Security & privacy
- AuthN/AuthZ on every new entry point; tenant isolation; IDOR.
- Input validation and injection (SQL, shell, template, path traversal, prompt injection if LLM-facing).
- Secrets: never hard-coded or logged; kept out of git; placed in the right secret store. While grounding, read key **names** only. Don't print values from `.env`, shell history or config. If one turns up, report where it is, not what it is.
- Shared machines and accounts: does anything install, listen or store data where other users can reach it?
- PII handling, data retention, CORS/CSRF, dependency vulnerabilities and licences.

## 8. Data & migrations
- Reversible? Is there a tested down-migration or restore path?
- Locking and runtime on large tables; backfills batched?
- Is data loss possible? Is a backup taken before destructive steps?

## 9. Testing & verification
- Does each step have a concrete verification command and an expected result?
- Are new tests specified: unit, integration, e2e where it matters, and the edge cases from §5?
- Do existing tests need updating? Are flaky or slow tests accounted for?
- Is there a final full check (tests, lint, typecheck, build) with the exact commands?
- Does the definition of done exercise the user's actual outcome, end to end, on the real target? Unit tests prove the mechanism; also check the device, browser, host, installed plugin, or the upgrade from the previous version, whichever applies.
- Are the tools for that check actually available (Claude in Chrome, a connected device via adb, ssh to a test host)? Use them before calling a check impossible.

## 10. Performance & scale
- N+1 queries, unbounded loops or lists, missing pagination or indexes, memory growth, blocking I/O on hot paths.
- Only flag with a named mechanism, and a rough magnitude if possible.

## 11. Operations & release
- Deploy order, feature flags, config per environment, observability (logs, metrics, alerts).
- Rollback plan for each risky step.
- Anything outward-facing (emails, webhooks, prod, public releases) is explicitly gated.

## 12. Consistency & maintainability
- Does it follow repo conventions (naming, structure, error style, test style) and CLAUDE.md rules? Name the repo's pattern, citing a file, for each of these the plan touches: data access layer, seeding, migrations, config, tests, commit granularity (one commit per task or one at the end).
- Is there duplication with existing utilities (reuse rather than reinventing)?
- Internal contradictions: terminology drift, or steps that conflict with each other.

## 13. User-facing quality (skip only if nothing user-visible changes)
- Every new or changed screen or output: empty, loading, error and overflow states; long text and small screens; light and dark themes; accessibility basics.
- Layout collisions, duplicate keys or IDs, hidden navigation, unregistered shortcuts or commands.
- The user's stated style rules (CLAUDE.md, memory), e.g. no generic "AI-looking" UI.
- A runtime check for each: a screenshot or browser pass, a device run, or the real command's output, not just a build.

## 14. Ambiguity (the auto-mode killer)
- Flag every "TBD", "etc.", "as needed", "handle appropriately", "maybe", "if necessary", "similar to", and "clean up". Each forces the executor to guess.
- Any step with more than one reasonable interpretation → pick one and write it down.
- Is any decision deferred to "during implementation"? → decide it now or make it a question.

---

## Auto-mode readiness gate

All must be true before handoff:

- [ ] Objective and measurable definition of done are stated.
- [ ] Every step names exact files/paths and the concrete change.
- [ ] Every step has a verification command and an expected result.
- [ ] The definition of done is checked on the real target (device, browser, host, installed copy), not only by unit tests.
- [ ] `scripts/lint_plan.py` reports 0 errors, and each warning is fixed or explained in the Hardening log.
- [ ] No TBD/vague wording remains; all decisions are recorded with reasons.
- [ ] All referenced files, symbols, commands, and versions were verified against the repo.
- [ ] Nothing requires interactive input (logins, prompts, GUI) mid-run, or it's handled up front.
- [ ] No step will be blocked by the user's hooks, guards, or auto mode as written; user-only commands are listed as pre-run actions.
- [ ] Branch, worktree, push or no-push, and the target environment are stated.
- [ ] Destructive, irreversible, or outward-facing actions are either explicitly approved by the user or removed.
- [ ] Rollback is defined for risky steps.
- [ ] Stop-and-ask conditions for the executor are listed.
- [ ] Final full-suite check commands are listed (tests, lint, typecheck, build).
- [ ] No open S1/S2 findings remain (or each is listed as an accepted, user-acknowledged risk).
- [ ] An independent critic reviewed the plan, and the last one to review it (Phase 4, or the Phase 6 sign-off when that was required) left no unfixed confirmed S1/S2; or the summary says a critic couldn't run.
- [ ] All user questions are answered and incorporated.
