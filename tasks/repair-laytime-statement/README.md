# Repair a laytime and demurrage engine

**Domain:** Maritime contracts · **Estimated time for an expert:** 3 h

A tool settles demurrage and despatch with charterers from a charter-party contract and a port-call event log. Its statements do not follow the contract, which is written up in `/app/LAYTIME.md` and is authoritative. The agent repairs the engine so statements follow the contract for any contract document and event log, not only the sample, keeping the command line and library layout intact.

## What the agent starts with

The laytime library and CLI under `/app`, the contract document, a sample port call and a small smoke check. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

Statements produced for the sample and for further contracts and port calls, plus the evidence the agent is asked to provide with its repair. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t repair-laytime-statement environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" repair-laytime-statement \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
