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
