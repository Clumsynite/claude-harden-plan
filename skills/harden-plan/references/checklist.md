# Plan review checklist

Work through each dimension. For every item, ask: *would an executor with no chat history get this right the first time?*

## 1. Goal & scope
- Is the objective unambiguous, and does the plan actually achieve it (not just something nearby)?
- Is the definition of done measurable (a command, a test, observable behaviour)?
- Is scope explicit: what's in, and what's deliberately out? Is there any hidden scope creep or gold-plating?
- Is this the simplest approach that meets the goal? Is there a smaller or safer path?

## 2. Grounding & feasibility
- Do all referenced files, symbols, APIs, tables, env vars, and scripts exist as described? (Verify them, don't assume.)
- Do library/API usages match the **installed** versions, not the latest docs?
- Are any required capabilities missing (permissions, credentials, network access, paid services, OS/tooling)?
- Are any steps impossible in a non-interactive run (prompts, logins, browser OAuth, 2FA, GUI-only steps)?

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
- Secrets: never hard-coded or logged; kept out of git; placed in the right secret store.
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

## 10. Performance & scale
- N+1 queries, unbounded loops or lists, missing pagination or indexes, memory growth, blocking I/O on hot paths.
- Only flag with a named mechanism, and a rough magnitude if possible.

## 11. Operations & release
- Deploy order, feature flags, config per environment, observability (logs, metrics, alerts).
- Rollback plan for each risky step.
- Anything outward-facing (emails, webhooks, prod, public releases) is explicitly gated.

## 12. Consistency & maintainability
- Does it follow repo conventions (naming, structure, error style, test style) and CLAUDE.md rules?
- Is there duplication with existing utilities (reuse rather than reinventing)?
- Internal contradictions: terminology drift, or steps that conflict with each other.

## 13. Ambiguity (the auto-mode killer)
- Flag every "TBD", "etc.", "as needed", "handle appropriately", "maybe", "if necessary", "similar to", and "clean up". Each forces the executor to guess.
- Any step with more than one reasonable interpretation → pick one and write it down.
- Is any decision deferred to "during implementation"? → decide it now or make it a question.

---

## Auto-mode readiness gate

All must be true before handoff:

- [ ] Objective and measurable definition of done are stated.
- [ ] Every step names exact files/paths and the concrete change.
- [ ] Every step has a verification command and an expected result.
- [ ] No TBD/vague wording remains; all decisions are recorded with reasons.
- [ ] All referenced files, symbols, commands, and versions were verified against the repo.
- [ ] Nothing requires interactive input (logins, prompts, GUI) mid-run, or it's handled up front.
- [ ] Destructive, irreversible, or outward-facing actions are either explicitly approved by the user or removed.
- [ ] Rollback is defined for risky steps.
- [ ] Stop-and-ask conditions for the executor are listed.
- [ ] Final full-suite check commands are listed (tests, lint, typecheck, build).
- [ ] No open S1/S2 findings remain (or each is listed as an accepted, user-acknowledged risk).
- [ ] All user questions are answered and incorporated.
