---
description: Harden a short plan with seven planted defects against a tiny stdlib Python repo.
expected_outcome: Every planted defect is fixed in PLAN.md or turned into an explicit question, no source file is edited, and the reply ends with a Ready / Not ready verdict.
runs: 1
max_turns: 200
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Agent, AskUserQuestion, TodoWrite, Bash, Edit, Write, WebSearch, WebFetch]
---
/harden-plan:harden-plan PLAN.md
