# Audit a CRM phone-number export

**Domain:** Telecom data quality · **Estimated time for an expert:** 1.5 h

Before a CRM migration, the agent audits an exported customer phone list. The new system rejects the whole batch if any audit field is off. Each number is parsed with its default region where one is given, and the audit reports the totals, which numbers are invalid, a histogram of line types and the carrier of each number.

## What the agent starts with

`/app/contacts.csv` (id, the number as typed, an optional default region). The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

`/app/report.json`: every field, compared with the correct values for the batch. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t phone-list-cleanup environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" phone-list-cleanup \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
