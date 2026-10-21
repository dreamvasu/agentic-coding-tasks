# Agentic coding tasks

Ten execution-graded tasks for evaluating and training autonomous coding agents. Each one is a realistic engineering ticket that runs in its own Docker environment and is graded by a deterministic verifier, not by a model or a rubric. A reference solution in every task proves it can be solved.

The tasks aim to be hard for the right reasons: the requirement is clear, and getting it right still means investigating the running system, carrying a rule to every path it applies to, or trusting the right source of truth. None of them rely on trick wording or hidden limits.

## What is in a task

```
tasks/<name>/
  instruction.md      the ticket, exactly as the agent sees it
  task.toml           category, time estimate, timeouts and resources
  environment/        Dockerfile and everything the agent starts with (code, data, libraries)
  solution/solve.sh   the reference solution
  tests/test.sh       the verifier: runs the hidden tests and writes a reward of 1 or 0
```

The layout follows the [Harbor](https://github.com/harbor-framework/harbor) task format, so any Harbor-compatible runner can execute these tasks.

## Running a task by hand

```bash
cd tasks/<name>
docker build -t <name> environment
docker run --rm \
  -v "$PWD/solution:/solution" -v "$PWD/tests:/tests" \
  <name> bash -c 'mkdir -p /logs/verifier && bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt'
```

A printed `1` means the reference solution passes the verifier. To evaluate an agent, start a container from the same image, give the agent `instruction.md`, let it work inside the container, then run `tests/test.sh` against what it left behind. Most verifiers install their test runner at grading time, so give the container network access while it is graded.

## The tasks

| Task | Domain | The agent has to... | Est. |
|---|---|---|---|
| [aeromag-track-audit](tasks/aeromag-track-audit) | Geophysics, survey navigation | finish an 18-function navigation package so every aeromagnetic survey track reduces correctly from declination through closure | 1.75 h |
| [airflow-nfmos-skip](tasks/airflow-nfmos-skip) | Workflow scheduling (Apache Airflow) | find and fix, at the root, why the scheduler skips a task inside a dynamically mapped task group, with regression tests | 1.5 h |
| [babel-compact-format](tasks/babel-compact-format) | Internationalisation (CLDR) | render dashboard figures in compact notation (`1.5M`, `48.5K`) with correct rounding for `en_US` | 1 h |
| [croniter-schedule-report](tasks/croniter-schedule-report) | Scheduling | list the three most recent fire times of each cron job before a reference instant | 1 h |
| [deployer-review-complete](tasks/deployer-review-complete) | Kubernetes deployment (ZenML) | review a teammate's fix for a deployer whose Service ends up with no endpoints, and finish it | 1.25 h |
| [jekyll-data-tags](tasks/jekyll-data-tags) | Static site generation (Jekyll) | add native Liquid tags that render `_data/` files, staying correct as the data changes | 1.5 h |
| [phone-list-cleanup](tasks/phone-list-cleanup) | Telecom data quality | audit a CRM phone-number export: validity, line types and carriers | 1.5 h |
| [repair-laytime-statement](tasks/repair-laytime-statement) | Maritime contracts | repair a laytime and demurrage engine so its statements follow the charter-party contract for any port call | 3 h |
| [sst-log-recover](tasks/sst-log-recover) | Storage engines (LevelDB) | recover the latest payloads from a crash-damaged key-value store that standard tooling reads wrongly | 3 h |
| [tz-resolver-heldout](tasks/tz-resolver-heldout) | Time zones | write a UTC-offset resolver that is right for any IANA zone and instant, not just the sample | 1.5 h |

## Notes

- Several environments vendor open-source projects (Apache Airflow, Jekyll, ZenML, croniter, Babel and others). Those keep their own licences, found in their folders.
- Some instructions carry a canary GUID. Please keep it: it lets training pipelines detect and exclude these tasks.
- Please don't publish solutions or agent transcripts for these tasks; that defeats their purpose as evaluations.

## Author

Vasu Kapoor
