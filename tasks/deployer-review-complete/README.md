# Review and complete a Kubernetes deployer fix

**Domain:** Kubernetes deployment (ZenML) · **Estimated time for an expert:** 1.25 h

In a slice of the ZenML codebase, the Kubernetes deployer renders a Deployment and a Service from Jinja2 templates. A user who sets custom pod labels gets pods that run but a Service with no endpoints. A teammate's fix is already applied to the tree; the agent reviews it, works out whether it really fixes the bug, and finishes the job.

## What the agent starts with

The relocated ZenML deployer code and templates under `/app`, with the teammate's change applied and summarised in `/app/PR.md`. The full ticket is in [`instruction.md`](instruction.md).

## What the verifier checks

The manifests the deployer renders for a range of label configurations: the Service routes to its pods, and the behaviour that already worked is preserved. Grading is deterministic: `tests/test.sh` runs the hidden tests and writes a reward of 1 (every test passes) or 0.

## Run it

```bash
docker build -t deployer-review-complete environment
docker run --rm -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" deployer-review-complete \
  bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes. To evaluate an agent, give it `instruction.md` in a container from the same image, then run `tests/test.sh`.
