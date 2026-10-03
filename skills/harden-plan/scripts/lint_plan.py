#!/usr/bin/env python3
"""Deterministic checks for a hardened plan file.

usage: lint_plan.py PLAN.md

Errors (exit 1): a required section is missing, the steps can't be found, or
vague wording or a reference to chat context remains. Warnings never fail:
resolve each one or say in the Hardening log why it's fine (step detection
is heuristic, so a sub-step under a verified step can show up here).
Section names are matched loosely (e.g. "Milestones" counts as Steps).
Text inside code blocks, inline code and the Hardening log is not scanned
for wording.
"""
import re
import sys

# Matched against the start of each section heading (numbering like "11." stripped;
# the H1 title is never a section).
REQUIRED = {
    "Objective & definition of done": r"objective|definition of done|goals?\b",
    "Context": r"context|background|why\b",
    "Assumptions": r"assumptions?|decisions",
    "Pre-flight (user)": r"pre-?flight",
    "Steps": r"steps\b|milestones|implementation steps|build (?:order|milestones)",
    "Test plan": r"test plan|tests?\b|testing|verification",
    "Risks & rollback": r"risks?\b|rollback",
    "Executor rules": r"executor rules|stop[- ]and[- ]ask",
    "Hardening log": r"hardening log",
}

# Each forces the executor to guess: errors.
VAGUE = [
    r"\bTBD\b", r"\bTODO\b", r"(?<![/\w])etc\b(?!/)", r"\bas needed\b", r"\bif necessary\b",
    r"\bif needed\b", r"\bhandle (?:it |them |errors? )?appropriately\b",
    r"\band so on\b", r"\bsomehow\b", r"\bsome kind of\b", r"\bduring implementation\b",
    r"\bdecide later\b",
]
# Often fine with specifics next to them: warnings.
SOFT = [r"\bsimilar to\b", r"\bmaybe\b", r"\bclean ?up\b(?!\s+(?:with|by|via)\b)", r"\bappropriate\b"]
CHAT_REFS = [
    r"\bas discussed\b", r"\bas (?:we )?(?:agreed|said|mentioned)\b",
    r"\b(?:earlier|above) in (?:the|this) (?:chat|conversation)\b",
    r"\byou (?:said|asked|mentioned)\b",
]
VERIFY = re.compile(r"(?<!un)verif|expect|should (?:print|return|show|pass|exit)|exits? 0|\b(?:prints|returns|passes|succeeds)\b|`\s*(?:→|->)", re.I)
FENCE = re.compile(r"^\s*(```|~~~)")


def headings(lines):
    out = []
    in_code = False
    for i, line in enumerate(lines):
        if FENCE.match(line):
            in_code = not in_code
            continue
        m = None if in_code else re.match(r"^(#{2,6})\s+(.*)", line)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def section(lines, heads, pattern):
    """Return (start, end, level) of the first heading matching pattern."""
    for n, (i, lvl, text) in enumerate(heads):
        if re.match(r"(?:[\d.]+[a-z]?\.?\s+)?(?:%s)" % pattern, text, re.I):
            end = len(lines)
            for j, l2, _ in heads[n + 1:]:
                if l2 <= lvl:
                    end = j
                    break
            return i, end, lvl
    return None


def prose(lines, skip):
    """Yield (lineno, text) outside code blocks and skipped ranges, inline code removed."""
    in_code = False
    for i, line in enumerate(lines):
        if FENCE.match(line):
            in_code = not in_code
            continue
        if in_code or any(a <= i < b for a, b in skip):
            continue
        yield i + 1, re.sub(r"`[^`]*`", "", line)


def steps(lines, start, end, lvl):
    """Split the Steps section into steps. Recognises, in order of preference:
    sub-headings, table rows, bold step labels (`**Step 1:**`, `- **M1:**`), top-level
    numbered items, other top-level bold bullets."""
    body = list(range(start + 1, end))
    rows = [i for i in body if re.match(r"^\|", lines[i]) and not re.match(r"^\|[\s:|-]+\|?\s*$", lines[i])]
    if len(rows) > 1:
        # A table whose header has a Verify column passes a row when that cell is filled in.
        cells = lambda i: [c.strip() for c in lines[i].strip().strip("|").split("|")]
        head = cells(rows[0])
        col = next((k for k, c in enumerate(head) if re.search(r"verif|expect|check", c, re.I)), None)
        if col is not None:
            return [(i, lines[i] + " verify" if len(cells(i)) > col and cells(i)[col] else "") for i in rows[1:]]
        return [(i, lines[i] + " (table has no Verify column)") for i in rows[1:]]
    named = r"(?i)^(?:[-*]\s+)?\*\*(?:step|milestone|m)\s*\d"  # **Step 3: …** or - **M2:** …
    for pat in (r"^#{%d,6}\s" % (lvl + 1), named, r"^\d+[.)]\s", r"^[-*]\s+\*\*"):
        subs = [i for i in body if re.match(pat, lines[i])]
        if subs:
            break
    bounds = subs + [end]
    return [(subs[k], "\n".join(lines[subs[k]:bounds[k + 1]])) for k in range(len(subs))]


def main(path):
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError as e:
        print(f"ERROR  can't read {path}: {e.strerror}")
        return 2
    heads = headings(lines)
    errors, warnings = [], []

    found = {}
    for name, pat in REQUIRED.items():
        found[name] = section(lines, heads, pat)
        if not found[name]:
            errors.append(f"missing section: {name}")

    skip = []
    if found["Hardening log"]:
        skip.append(found["Hardening log"][:2])
    for n, text in prose(lines, skip):
        for pat in VAGUE:
            m = re.search(pat, text, re.I)
            if m:
                errors.append(f"line {n}: vague wording '{m.group(0)}': {text.strip()[:100]}")
        for pat in SOFT:
            m = re.search(pat, text, re.I)
            if m:
                warnings.append(f"line {n}: check wording '{m.group(0)}' names the exact action: {text.strip()[:100]}")
        for pat in CHAT_REFS:
            m = re.search(pat, text, re.I)
            if m:
                errors.append(f"line {n}: refers to chat context '{m.group(0)}': the executor can't see it")

    if found["Steps"]:
        s, e, lvl = found["Steps"]
        parts = steps(lines, s, e, lvl)
        if not parts:
            errors.append("Steps section has no step headings, numbered items, bold bullets or table rows")
        for i, text in parts:
            title = lines[i].strip()[:70]
            if not VERIFY.search(text):
                warnings.append(f"line {i + 1}: step has no verification/expected result: {title}")
            elif "`" not in text:
                warnings.append(f"line {i + 1}: step has no command or path in backticks: {title}")

    for e in errors:
        print("ERROR  " + e)
    for w in warnings:
        print("WARN   " + w)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip())
    sys.exit(main(sys.argv[1]))
