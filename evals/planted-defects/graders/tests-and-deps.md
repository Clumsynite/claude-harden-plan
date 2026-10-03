---
type: llm
focus: { source: file, path: PLAN.md }
---
The repo's CLAUDE.md says: stdlib only, and tests run with `python3 -m unittest discover -s tests`.
PASS if the plan's test commands use `python3 -m unittest` (not `pytest`) and the plan does not add `click` or any other third-party dependency (argparse, which the CLI already uses, is fine). A mention of click only in the Hardening log as a removed item is fine.
FAIL if a step still runs `pytest` or still adds `click` or another third-party package.
