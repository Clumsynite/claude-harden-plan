---
type: llm
focus: { source: file, path: PLAN.md }
---
The repo has `notes/db.py` (`connect`, `add_note`, `list_notes`), an argparse CLI in `notes/cli.py`, unittest tests in `tests/`, and a CLAUDE.md saying stdlib only.
PASS if the plan adds the delete function in `notes/db.py` and the subcommand in `notes/cli.py` via argparse, tests with `python3 -m unittest discover -s tests`, adds no third-party dependency, gives every step a verification command with an expected result, and says what happens when the id doesn't exist (a visible error, not silent success).
FAIL if any of those is missing or wrong.
