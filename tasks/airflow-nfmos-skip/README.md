# Airflow: a mapped task group skips a task

**Domain:** Workflow scheduling (Apache Airflow) · **Estimated time for an expert:** 1.5 h

A DAG that expands a task group dynamically has one task inside the group marked `skipped` on a fresh run, even though its upstream (also inside the group) succeeds. Clearing and re-running does not reproduce it. The agent tracks the cause down in the scheduler and fixes it at the root, for any mapped task group that hits it, and adds regression tests.

## What the agent starts with

An Apache Airflow source tree at `/app` and a minimal reproduction DAG at `/app/data/repro_dag.py`. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

Scheduler behaviour for mapped task groups on fresh runs, including cases beyond the reproduction, with the existing behaviour preserved. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t airflow-nfmos-skip environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" airflow-nfmos-skip \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
