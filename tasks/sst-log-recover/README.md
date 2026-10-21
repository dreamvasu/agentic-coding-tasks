# Recover payloads from a crash-damaged LevelDB store

**Domain:** Storage engines (LevelDB) · **Estimated time for an expert:** 3 h

A cache node crashed part way through a write. Opening its LevelDB store now returns older payloads for several objects, and standard recovery tooling does not return the current ones either, though the bytes still exist in the files. The agent recovers the current payload for twelve named objects. The store is live, volatile state, so it has to be handled with care.

## What the agent starts with

The damaged store under `/app/data/store` and an empty `/app/output`. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

The bytes written for each of the twelve ids, which must be exactly the current payload. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t sst-log-recover environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" sst-log-recover \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
