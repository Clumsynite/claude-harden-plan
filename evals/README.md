# harden-plan evals

Two cases, both against a tiny stdlib Python repo that each case's `fixture.sh` creates (the two scripts share their first part; keep it in sync):

- `planted-defects`: hardens a six-step plan with seven planted defects (a missing file and function, pytest instead of unittest, a third-party dependency, `rm -rf` on an unset variable, vague steps without verification, silent success on a missing id, an unapproved push).
- `draft-when-missing`: no plan exists, so the skill drafts one and hardens it.

A full harden run spawns critics and can take 10–30 minutes, so each case runs once by default. The slash command doesn't exist without the plugin, so the no-plugin baseline isn't meaningful; use `--ablation none`.

```
claude plugin eval . --scaffold --ablation none --trust-plugin \
  --allow-tools Bash Edit Write WebSearch WebFetch --max-cost-usd 20
```

Results go to `evals/results/` (git-ignored).

If the eval refuses to start because `~/.docker` holds symlinks (Docker Desktop's own), Bash-granting evals can't run on that machine. The same check by hand:

```
d=$(mktemp -d) && cd "$d" && bash <plugin>/evals/planted-defects/fixture.sh
claude -p "/harden-plan:harden-plan PLAN.md" --output-format json \
  --allowedTools "Read Glob Grep Bash Edit Write Agent WebSearch WebFetch TodoWrite" < /dev/null > run.json
```

Then grade `PLAN.md` against the graders' rubrics; `run.json` has the cost per model.

Last manual run (2026-10-03, 0.2.0): all seven planted defects fixed, plus three real ones the plan had (a dirty-tree precheck that would always stop, a test helper named `run` that shadows `unittest.TestCase.run`, a final check that could never pass). 6 minutes, $2.00 list price: three critics at 200–240k cache-read tokens each (sign-off on Sonnet: $0.10).
