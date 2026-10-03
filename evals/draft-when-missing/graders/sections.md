---
type: regex
pattern: "#+ [^\\n]*Executor rules[\\s\\S]*#+ [^\\n]*Hardening log"
flags: i
target: { source: file, path: PLAN.md }
---
