We need a small scheduling report generated at `/app/report.json`.

`/app/schedules.json` maps a set of job names to cron expressions (standard 5-field `minute hour day-of-month month day-of-week`). For every job, compute the three most recent times it was scheduled to run strictly before the reference instant **2024-03-15T12:00:00** (local, naive -- no timezone math). List them most-recent-first.

Write `/app/report.json` as a JSON object mapping each job name to a list of its three fire times, each formatted as an ISO-8601 string (`YYYY-MM-DDTHH:MM:SS`). Use the cron library provided at `/app/croniter` to interpret the expressions. Every job in `/app/schedules.json` must appear in the report with exactly three entries.
