# Add a /health endpoint

## Objective & definition of done
`GET /health` returns 200 with `{"ok":true}`. Done when `curl -s localhost:3000/health` prints `{"ok":true}` against the running dev server.

## Context
Express 4.19 (`package-lock.json`). Routes live in `src/routes/`, registered in `src/app.js`.

## Assumptions
- No auth on `/health`: load balancers call it unauthenticated.

## Pre-flight (user)
None.

## Steps
1. Add `src/routes/health.js` exporting a router with `GET /health`. **Verify:** `node -e "require('./src/routes/health')"` exits 0.
2. Register it in `src/app.js` next to the other routers. **Verify:** `npm test -- health` passes.

## Test plan
`npm test`, `npm run lint`; then `curl -s localhost:3000/health` → `{"ok":true}`.

## Risks & rollback
Revert the two files with `git revert <sha>`.

## Executor rules
Work on branch `feat/health`, one commit per step, don't push. Stop and ask if `npm test` fails before step 1. Don't expand scope.

## Hardening log
Round 1 (critic:correctness): 2 found, 2 fixed. TBD items in earlier drafts were resolved.
