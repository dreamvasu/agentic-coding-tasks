# Jekyll: Liquid tags that render `_data/`

**Domain:** Static site generation (Jekyll) · **Estimated time for an expert:** 1.5 h

Authors paste reference tables and version strings into Markdown by hand, and they drift from the files under `_data/`. The agent adds three Liquid tags to a Jekyll checkout (`data_table`, `data_value`, `data_list`) that render `_data/` content inline, following how the codebase already builds tags. When a value in `_data/` changes, every page that renders it must show the new value.

## What the agent starts with

A Jekyll source checkout at `/app`. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

Rendered sites using the three tags, including after the data they read has changed. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t jekyll-data-tags environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" jekyll-data-tags \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
