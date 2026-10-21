# Compact number formatting for a dashboard

**Domain:** Internationalisation (CLDR, Babel) · **Estimated time for an expert:** 1 h

A metrics dashboard needs figures in compact notation (`1.5M`, `48.5K`) for `en_US`. Each figure comes with a maximum number of fraction digits; trailing zeros are dropped and halfway cases round to even. The image ships Babel vendored at `/app/babel`, which is what is on the import path.

## What the agent starts with

`/app/figures.json` (labels, integer values, fraction digits) and the vendored Babel library. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

`/app/report.json`: the compact string for every figure, compared with the correct CLDR output. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t babel-compact-format environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" babel-compact-format \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
