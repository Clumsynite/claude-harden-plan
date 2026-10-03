#!/usr/bin/env bash
# Tiny Python notes CLI used by the harden-plan evals. Stdlib only, tests use unittest.
set -euo pipefail
mkdir -p notes tests
cat > notes/__init__.py <<'EOF'
EOF
cat > notes/db.py <<'EOF'
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect(path):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def add_note(conn, text):
    if not text.strip():
        raise ValueError("empty note")
    cur = conn.execute("INSERT INTO notes (text) VALUES (?)", (text,))
    conn.commit()
    return cur.lastrowid


def list_notes(conn):
    return conn.execute("SELECT id, text, created FROM notes ORDER BY id").fetchall()
EOF
cat > notes/cli.py <<'EOF'
import argparse
import os
import sys

from . import db

DEFAULT_DB = os.path.expanduser("~/.notes.db")


def main(argv=None):
    p = argparse.ArgumentParser(prog="notes")
    p.add_argument("--db", default=os.environ.get("NOTES_DB", DEFAULT_DB))
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("text")
    sub.add_parser("list")
    args = p.parse_args(argv)
    conn = db.connect(args.db)
    if args.cmd == "add":
        print(db.add_note(conn, args.text))
    elif args.cmd == "list":
        for row in db.list_notes(conn):
            print(f"{row[0]}\t{row[2]}\t{row[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF
cat > tests/__init__.py <<'EOF'
EOF
cat > tests/test_db.py <<'EOF'
import unittest

from notes import db


class DbTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")

    def test_add_and_list(self):
        nid = db.add_note(self.conn, "hello")
        self.assertEqual([(nid, "hello")], [(r[0], r[1]) for r in db.list_notes(self.conn)])

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            db.add_note(self.conn, "  ")


if __name__ == "__main__":
    unittest.main()
EOF
cat > README.md <<'EOF'
# notes

`python3 -m notes.cli add "text"`, `python3 -m notes.cli list`. Data lives in `~/.notes.db` (override with `NOTES_DB`).

Tests: `python3 -m unittest discover -s tests`.
EOF
cat > CLAUDE.md <<'EOF'
- Stdlib only: no third-party dependencies.
- Every change ships with unittest tests; run `python3 -m unittest discover -s tests`.
EOF
git init -q -b main
git -c user.name=eval -c user.email=eval@example.com add -A
git -c user.name=eval -c user.email=eval@example.com commit -q -m "notes: add and list"

# The plan under review. Planted defects: a file and function that don't exist,
# pytest instead of unittest, a third-party dependency against CLAUDE.md, an
# rm -rf on an unset variable, vague steps without verification, a delete that
# reports success for a missing id, and an unapproved push.
cat > PLAN.md <<'EOF'
# Plan: add a delete command to notes

## Objective
Users can delete a note by id.

## Steps
1. In `notes/storage.py`, add `delete_note(id)` that calls `get_connection()` and runs `DELETE FROM notes WHERE id = ?`.
2. Add `click` to the project and rewrite the CLI's `delete` subcommand with it. Print `deleted` after running the query.
3. Reset the dev database before testing: `rm -rf $NOTES_DIR/*`.
4. Handle errors appropriately, update the README, etc.
5. Run `pytest` and make sure everything passes.
6. Commit and push to `origin main`.
EOF
git -c user.name=eval -c user.email=eval@example.com add PLAN.md
git -c user.name=eval -c user.email=eval@example.com commit -q -m "Add plan for delete"
