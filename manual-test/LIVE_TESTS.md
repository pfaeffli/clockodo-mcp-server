# Live QA suite

`manual-test/live_test.py` exercises the server code against a REAL Clockodo
company and prints a PASS/FAIL table. It complements the mocked unit tests and
guards regressions that only show against the real API.

> **WARNING:** the suite writes and deletes time entries and absences. Run it
> only against a throwaway Clockodo trial company, never production.

## Scenarios

| # | Scenario | Expected |
|---|---|---|
| 1 | tools/list for every role | non-empty; employee does NOT expose `list_users` / `get_raw_user_reports` |
| 2 | identity | list-based user id equals `v4/users/me` |
| 3 | clock start/get/stop | stopped entry keeps text and billable |
| 4 | time zones (naive, +02:00, Z, -05:00, DST day) | stored instant equals independently computed UTC; naive = `CLOCKODO_TIMEZONE` local |
| 5 | entry ownership | editing/deleting/moving others' entries raises `PermissionError` |
| 6 | vacation create/list/edit, half day | edited = 3 days, half = 0.5, multi-day half day raises `ValueError` |
| 7 | sick days | types 4 and 5; type 4 without `sick_note` rejected by API |
| 8 | delete lifecycle | service delete of approved absence fails without `auto_cancel`; `delete_my_vacation` tool removes it |
| 9 | team leader | create + approve for employee (0 to 1); self-approval raises `PermissionError` |
| 10 | HR summary | non-empty |
| 11 | resources | current-entry with idle clock reports no running entry; recent-entries only own entries |
| 12 | cleanup | nothing left behind |

## Setup

1. Create a Clockodo trial company with an admin user, one extra employee user,
   a team (admin as leader, employee as member), a customer and a service.
2. `cp manual-test/.env.live.template manual-test/.env.live` and fill in the
   credentials. Names default to "Demo Customer", "Demo Service",
   "Demo Employee" (override with `LIVE_CUSTOMER`, `LIVE_SERVICE`,
   `LIVE_EMPLOYEE`).
3. Test dates are based on the Monday `LIVE_WEEK` (default `2026-10-12`); the
   suite uses that week, the following week and the DST change day 2026-10-25.
   Pick a different Monday if those days are already used in your company.

`manual-test/.env.live` is git-ignored.

## Run

```bash
make live-test
```

Runs in the test Docker image with only the project directory mounted
read-only. The exit code is non-zero if any scenario FAILs or ERRORs. Secrets
are masked in output.

## Cleanup

Everything created is deleted at the end, even if a scenario failed. Running
clocks are stopped; approved absences are cancelled before deletion; items that
are already gone (404) count as cleaned. A cleanup row of FAIL lists what must
be removed by hand.
