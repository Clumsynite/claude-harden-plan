---
description: No plan exists; the skill drafts one for the task, hardens it, and saves it to ./PLAN.md.
expected_outcome: PLAN.md is created with the required sections and the draft marker, grounded in notes/db.py and unittest, with no source edits.
runs: 1
max_turns: 200
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Agent, AskUserQuestion, TodoWrite, Bash, Edit, Write, WebSearch, WebFetch]
---
/harden-plan:harden-plan add a `delete <id>` command that removes a note
