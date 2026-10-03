---
type: llm
focus: { source: file, path: PLAN.md }
---
PASS if all of these hold: every step has a concrete verification command with an expected result; the vague "Handle errors appropriately, update the README, etc." step has been replaced by specific changes; and deleting a non-existent id is specified to fail visibly (a non-zero exit code and/or an error message, not printing "deleted"), with a test for it.
FAIL if any step lacks a verification, the vague wording remains, or deleting a missing id still reports success.
