# A UTC-offset resolver for any IANA zone

**Domain:** Time zones · **Estimated time for an expert:** 1.5 h

A scheduling service stamped several events with the wrong UTC offset. The agent writes `resolve(zone, instant)`, which returns the offset in effect for any IANA zone at any UTC instant, and runs it over a sample batch. The resolver has to be right for any site the service has, not just the sample.

## What the agent starts with

`/app/locations.csv` (location id, IANA zone, UTC instant). The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

`/app/offsets.json` for the sample, and `resolve` itself on zones and instants beyond it. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t tz-resolver-heldout environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" tz-resolver-heldout \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
