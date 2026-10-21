"""Verifier (v2) for the airflow #39801 NFMOS-in-mapped-group silent-skip bug,
HARDENED against the known over-broad "accidental symptom fix".

Design principle (anti-cheat): the verifier ships its OWN faithful DAGs and runs them
against whatever airflow source is installed in the env. It does NOT trust an
agent-authored DAG, so a "fix" that merely rewires the DAG input cannot pass. The
verifier asserts on real metastore state after fresh in-process DAG runs.

Two independent gates, BOTH required to PASS:

  1. test_nfmos_task_in_mapped_group_expands_and_succeeds  (the #39801 bug is fixed)
       Pass <=> the sibling-only NFMOS task expands and every instance SUCCEEDS.
       Fail <=> any NFMOS instance is SKIPPED/UPSTREAM_FAILED (the vacuous-count bug).

  2. test_per_index_isolation_preserved  (the #50210 regression guard -- NEW in v2)
       Constructs a mapped task group where ONE map index's upstream FAILS and the
       others SUCCEED. Per-index isolation REQUIRES that only the failing index
       resolves to upstream_failed while the sibling indices still SUCCEED -- and,
       crucially, that the consumer EXPANDS per index rather than collapsing to a
       single whole-group verdict.

       The known over-broad "fix" (broadening the query helpers so an unexpanded
       mapped-group TI with map_index<0 depends on ALL upstreams) zeroes the #39801
       vacuous count and thus passes gate 1 -- but it makes the consumer's summary TI
       (map_index=-1) see a failed upstream from a *different* index, resolve the whole
       group to upstream_failed, and never expand. That collapse is exactly what this
       gate catches.

A correct, per-index-preserving fix (deferral: adding NONE_FAILED_MIN_ONE_SUCCESS to
the fast-trigger exemption tuple so the summary TI defers instead of miscounting)
passes BOTH gates.
"""
import os
import subprocess
import sqlite3
import sys
import tempfile
import textwrap
from pathlib import Path

import shutil
import pytest


# The verifier runs under uvx's isolated venv: it has pytest but NOT airflow.
# airflow lives in the agent container's system python; invoke that, not sys.executable.
def _airflow_python():
    for exe in ("/usr/local/bin/python", "/usr/local/bin/python3",
                shutil.which("python3"), shutil.which("python")):
        if exe and subprocess.run([exe, "-c", "import airflow"],
                                  capture_output=True).returncode == 0:
            return exe
    raise RuntimeError("verifier: no python with airflow importable")

_AF_PY = _airflow_python()

# ---- the faithful sibling-only #39801 repro DAG the verifier controls ----
FAITHFUL_DAG = textwrap.dedent('''
    from __future__ import annotations
    import pendulum
    from airflow.decorators import dag, task, task_group
    from airflow.utils.trigger_rule import TriggerRule

    @dag(schedule=None, start_date=pendulum.datetime(2024,1,1), catchup=False)
    def verify_39801_faithful():
        @task
        def init():
            return ["a", "b", "c"]
        @task_group
        def tg(message):
            @task
            def imsleepy(message):
                return message
            @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
            def imawake():
                print("awake")
            # imawake's ONLY upstream is the SIBLING imsleepy (no group-input dep)
            imsleepy(message) >> imawake()
        tg.expand(message=init())
    verify_39801_faithful()
''')

# ---- masking-shape control: proves the verifier tests the RIGHT #39801 shape ----
MASKING_DAG = textwrap.dedent('''
    from __future__ import annotations
    import pendulum
    from airflow.decorators import dag, task, task_group
    from airflow.utils.trigger_rule import TriggerRule

    @dag(schedule=None, start_date=pendulum.datetime(2024,1,1), catchup=False)
    def verify_39801_masking():
        @task
        def init():
            return ["a", "b", "c"]
        @task_group
        def tg(message):
            @task
            def imsleepy(message):
                return message
            @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
            def imawake(message):   # consumes group input -> init is direct upstream (masks bug)
                print("awake", message)
            imsleepy(message)
            imawake(message)
        tg.expand(message=init())
    verify_39801_masking()
''')

# ---- #50210-style per-index isolation guard DAG ----
# One expanded index's upstream FAILS; the others SUCCEED. Each consumer index must
# depend only on its OWN upstream index (per-index isolation), so exactly the failing
# index propagates and the siblings still SUCCEED. The consumer must EXPAND per index.
PER_INDEX_DAG = textwrap.dedent('''
    from __future__ import annotations
    import pendulum
    from airflow.decorators import dag, task, task_group

    @dag(schedule=None, start_date=pendulum.datetime(2024,1,1), catchup=False)
    def verify_50210_per_index():
        @task
        def make_list():
            return [0, 1, 2]
        @task_group
        def tg(v):
            @task
            def maybe_fail(v):
                if v == 1:
                    raise ValueError("boom index 1")
                return v
            @task
            def consume(v):          # default all_success; upstream is the SIBLING maybe_fail
                print("consume", v)
            consume(maybe_fail(v))
        tg.expand(v=make_list())
    verify_50210_per_index()
''')


def _run_dag(dag_src: str, dag_id: str) -> dict:
    """Fresh AIRFLOW_HOME + sqlite DB, run one DAG in-process, return {(task_id,map_index): state}."""
    home = Path(tempfile.mkdtemp(prefix="af39801_"))
    dags = home / "dags"; dags.mkdir()
    (dags / f"{dag_id}.py").write_text(dag_src)
    db = home / "airflow.db"
    env = dict(os.environ,
        AIRFLOW_HOME=str(home),
        AIRFLOW__CORE__LOAD_EXAMPLES="False",
        AIRFLOW__CORE__DAGS_FOLDER=str(dags),
        AIRFLOW__CORE__EXECUTOR="SequentialExecutor",
        AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=f"sqlite:///{db}",
        AIRFLOW__LOGGING__LOGGING_LEVEL="ERROR",
    )
    subprocess.run([_AF_PY, "-m", "airflow", "db", "migrate"],
                   env=env, check=True, capture_output=True)
    # NOTE: no check=True on the run -- a per-index failure is an expected outcome of
    # the #50210 scenario and `dags test` may return non-zero; we assert on DB state.
    subprocess.run([_AF_PY, "-m", "airflow", "dags", "test", dag_id],
                   env=env, capture_output=True)
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT task_id, map_index, state FROM task_instance WHERE dag_id=? ORDER BY task_id, map_index",
        (dag_id,)).fetchall()
    con.close()
    return {(t, m): s for t, m, s in rows}


def test_nfmos_task_in_mapped_group_expands_and_succeeds():
    """CORE assertion (#39801). On buggy code imawake is SKIPPED -> this FAILS (bug caught)."""
    states = _run_dag(FAITHFUL_DAG, "verify_39801_faithful")
    imsleepy = {mi: st for (tid, mi), st in states.items() if tid == "tg.imsleepy"}
    imawake  = {mi: st for (tid, mi), st in states.items() if tid == "tg.imawake"}
    # sanity: the sibling upstreams really ran and succeeded
    assert imsleepy and all(s == "success" for s in imsleepy.values()), imsleepy
    # the NFMOS task must have expanded (>=1 positive map_index instance)...
    assert any(mi >= 0 for mi in imawake), f"imawake never expanded: {imawake}"
    # ...and every imawake instance must be success (bug -> 'skipped')
    bad = {mi: s for mi, s in imawake.items() if s != "success"}
    assert not bad, f"NFMOS task not all-success (bug reproduced): {imawake}"


def test_masking_shape_is_not_what_we_grade():
    """Anti-cheat sanity: the masking shape passes even on buggy code, proving the
    core test above is only satisfiable by fixing the sibling-only shape."""
    states = _run_dag(MASKING_DAG, "verify_39801_masking")
    imawake = {mi: st for (tid, mi), st in states.items() if tid == "tg.imawake"}
    assert imawake and all(s == "success" for s in imawake.values()), imawake


def test_per_index_isolation_preserved():
    """#50210 REGRESSION GUARD. One index's upstream fails; siblings succeed.

    Per-index isolation requires the consumer to EXPAND per index and only the
    failing index to propagate. The over-broad map_index<0 broadening collapses the
    consumer's summary TI to a single whole-group upstream_failed (never expands),
    which this test catches. A per-index-preserving fix passes it.
    """
    states = _run_dag(PER_INDEX_DAG, "verify_50210_per_index")
    maybe_fail = {mi: st for (tid, mi), st in states.items() if tid == "tg.maybe_fail"}
    consume    = {mi: st for (tid, mi), st in states.items() if tid == "tg.consume"}

    # scenario sanity: the per-index upstream failed for EXACTLY index 1
    assert maybe_fail.get(0) == "success", f"upstream index 0 unexpected: {maybe_fail}"
    assert maybe_fail.get(1) == "failed",  f"upstream index 1 should have failed: {maybe_fail}"
    assert maybe_fail.get(2) == "success", f"upstream index 2 unexpected: {maybe_fail}"

    # ISOLATION GATE 1: the consumer must have EXPANDED per index (map_index>=0),
    # NOT collapsed to a single whole-group summary verdict (map_index<0 only).
    expanded = {mi: st for mi, st in consume.items() if mi >= 0}
    assert expanded, (
        "per-index isolation collapsed: consumer never expanded per index "
        f"(whole-group verdict instead): consume={consume}"
    )

    # ISOLATION GATE 2: sibling indices are isolated from index 1's failure and SUCCEED;
    # only the failing index propagates.
    assert expanded.get(0) == "success", f"index 0 not isolated from index 1 failure: {consume}"
    assert expanded.get(2) == "success", f"index 2 not isolated from index 1 failure: {consume}"
    assert expanded.get(1) in ("upstream_failed", "failed"), (
        f"index 1 should reflect its own upstream failure: {consume}"
    )
