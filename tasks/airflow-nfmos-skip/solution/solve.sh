#!/usr/bin/env bash
# Reference solution for airflow #39801 (NFMOS-in-mapped-group silent skip).
#
# Root cause: in the mapped-task-group "fast trigger" exemption, the summary/unexpanded
# task instance is only exempted for the ONE_* trigger rules. NONE_FAILED_MIN_ONE_SUCCESS
# is missing from that tuple, so its expansion dependency is not deferred; the trigger-rule
# evaluation then runs with a vacuous upstream count and resolves the task to SKIPPED.
#
# Fix: add TR.NONE_FAILED_MIN_ONE_SUCCESS to the is_fast_triggered exemption tuple so the
# summary TI defers (like the ONE_* rules) instead of miscounting. One line.
set -euo pipefail

TARGET="/app/airflow/ti_deps/deps/trigger_rule_dep.py"

python - "$TARGET" <<'PY'
import sys

path = sys.argv[1]
src = open(path).read()

old = "is_fast_triggered = ti.task.trigger_rule in (TR.ONE_SUCCESS, TR.ONE_FAILED, TR.ONE_DONE)"
new = "is_fast_triggered = ti.task.trigger_rule in (TR.ONE_SUCCESS, TR.ONE_FAILED, TR.ONE_DONE, TR.NONE_FAILED_MIN_ONE_SUCCESS)"

if new in src:
    print("already patched")
elif old in src:
    src = src.replace(old, new, 1)
    open(path, "w").write(src)
    print("patched:", path)
else:
    sys.exit("expected fast-trigger tuple not found in " + path)
PY

echo "solve.sh: done"
