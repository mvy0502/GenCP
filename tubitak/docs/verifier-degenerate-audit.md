# Degenerate-invocation audit of every verifier

Standing practice 10 in `CLAUDE.md` was adopted because the link checker reported
`0 links checked across 0 files; 0 dead` and exited 0 when run with no arguments. This is
the audit that followed, and the count in the practice comes from here.

## Method

All 23 verification scripts under `tubitak/tests/` and `tubitak/scripts/`, each run three
ways with `GENCP_REPO_ROOT` pointed at an empty temporary directory:

1. no arguments
2. an empty input file as the sole argument
3. a path that does not exist as the sole argument

Recorded: exit status, and whether the output claims success. Raw results are in
`evidence/plugin_field_test/degenerate_audit.json`.

## Result before the fix

**Eighteen of twenty-three exited 0.** They divide into two classes, and the second is the
larger and the more dangerous.

| Class | Count | What happens |
|---|---|---|
| Examined nothing, reported success | 1 | `check_links.py` found no files, printed `0 dead`, exited 0 |
| Ignored the argument, re-ran the real work, printed PASS | 17 | `gate_g.py --overlp=2560` runs at 0 m and reports a green gate |

The second class is worse because nothing on screen is wrong. The gate really did run and
really did pass — for a configuration nobody asked for. A verdict that does not depend on
what you asked for is not a verdict about what you asked for.

Neither class could have been caught by the plant-a-dead-link discipline. That discipline
proves a checker reports a real defect, which says nothing about what the tool does when
you ask it the wrong question. The discipline covered the normal invocation only.

## Fix

`tubitak/tests/_guard.py` — `strict_argv()` exits 2 on any argument the script does not
declare. Applied to all 17 plain-python verifiers, each declaring the flags it genuinely
accepts (`gate_g.py`: `--overlap=`; `check_links.py`: `--no-net`, `--self-test-only`, plus
a file list).

QGIS `--code` harnesses are deliberately excluded: their `sys.argv` belongs to the QGIS
application (`--nologo --code <path>`), so refusing unknown entries would refuse QGIS's
own. They take their inputs from the environment, and the audit confirms they already fail
when `GENCP_REPO_ROOT` points somewhere empty.

`check_links.py` additionally exits 2 when it reads files and finds not one link — a broken
extractor or the wrong corpus, not a pass.

## Result after the fix

Empty-input and missing-file are refused across the board (exit 2). `no-args` still exits 0
for gates whose corpus is fixed in the repository, which is correct: that is their normal
invocation, and they do real work.

## What this does not cover

The audit tests the argument surface. It does not test what happens when the *data* a gate
reads is present but wrong — a corrupted reference chip, a truncated corpus. That is a
different failure mode and it has not been audited.
