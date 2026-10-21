# Aeromagnetic survey track reduction

**Domain:** Geophysics, survey navigation · **Estimated time for an expert:** 1.75 h

An aeromagnetic survey desk's `navkit` package is only partly written: the module layout, three survey data feeds and a small test suite exist, but eighteen functions raise `NotImplementedError`. The agent implements them so a single run reduces every survey track and writes a report. The stages form a chain (bearings need magnetic declination, leg geometry needs true bearings, closure needs the whole track), so an error early on carries through to every later number.

## What the agent starts with

A Python package under `/app` with its config, data model, readers for three feed formats, an entry point (`python -m navkit reduce`) and an in-repo test suite. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

The report the reduction writes: per-track bearings, leg geometry and closure, compared with independently computed values. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t aeromag-track-audit environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" aeromag-track-audit \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
