---
type: llm
focus: { source: file, path: PLAN.md }
---
The repo's real code is `notes/db.py` with `connect(path)`, `add_note(conn, text)` and `list_notes(conn)`. There is no `notes/storage.py` and no `get_connection()`.
PASS if the plan's steps put the delete function in `notes/db.py` (or another file the plan explicitly creates) and use `connect(...)` / a `conn` argument, and no step still tells the executor to edit `notes/storage.py` or call `get_connection()` as if they exist.
FAIL if a step still relies on `notes/storage.py` or `get_connection()` existing.
