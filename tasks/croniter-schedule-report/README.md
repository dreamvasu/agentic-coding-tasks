# Most recent cron fire times

**Domain:** Scheduling · **Estimated time for an expert:** 1 h

Given a set of jobs with standard five-field cron expressions, the agent lists the three most recent times each job was scheduled to run strictly before a fixed reference instant (naive local time), most recent first, using the cron library provided in the image.

## What the agent starts with

`/app/schedules.json` (job name to cron expression) and the `croniter` library at `/app/croniter`. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

`/app/report.json`: exactly three ISO-8601 fire times per job, all correct. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t croniter-schedule-report environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" croniter-schedule-report \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
