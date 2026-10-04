"""Live end-to-end QA suite for clockodo-mcp against a REAL Clockodo test company.

WARNING: this suite creates and deletes time entries and absences. Only run it
against a throwaway/trial company. See manual-test/LIVE_TESTS.md.

Configuration (environment, see manual-test/.env.live.template):
    CLOCKODO_API_USER, CLOCKODO_API_KEY, CLOCKODO_BASE_URL
    LIVE_CUSTOMER  customer name   (default "Demo Customer")
    LIVE_SERVICE   service name    (default "Demo Service")
    LIVE_EMPLOYEE  employee name   (default "Demo Employee")
    LIVE_WEEK      ISO date of a Monday used as the base of all test dates
                   (default 2026-10-12). The suite uses that week and the
                   following one, plus the DST change day 2026-10-25.
    CLOCKODO_TIMEZONE  zone for naive times (default Europe/Zurich)

Exit code is non-zero if any scenario FAILs or ERRORs.
"""

# pylint: disable=unexpected-keyword-arg

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import date, datetime, timedelta, timezone
from functools import partial
from typing import Any, Callable
from zoneinfo import ZoneInfo

import httpx

from clockodo_mcp import resources
from clockodo_mcp.client import ClockodoClient
from clockodo_mcp.services.hr_service import HRService
from clockodo_mcp.services.team_leader_service import TeamLeaderService
from clockodo_mcp.services.user_service import UserService
from clockodo_mcp.tools import user_tools

DEFAULT_WEEK = "2026-10-12"
DST_DAY = "2026-10-25"
SECRETS = [
    v for k, v in os.environ.items() if v and any(w in k for w in ("KEY", "TOKEN"))
]

Outcome = tuple[str, str]  # (actual, "PASS" | "FAIL" | "ERROR")
ROWS: list[tuple[str, str, str, str, str]] = []
ENTRIES: list[int] = []
ABSENCES: list[int] = []

client = ClockodoClient.from_env()
user_svc = UserService(client)
tl_svc = TeamLeaderService(lambda: client)
hr_svc = HRService(client)


def clip(value: Any, limit: int = 110) -> str:
    """Render a value for the table: masked secrets, no pipes/newlines, clipped."""
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    for secret in SECRETS:
        text = text.replace(secret, "***")
    text = text.replace("|", "/").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def run(num: str, name: str, expected: str, func: Callable[[], Outcome]) -> None:
    """Run one scenario; exceptions become ERROR rows."""
    try:
        actual, result = func()
    except Exception as exc:  # noqa: BLE001  pylint: disable=broad-exception-caught
        actual, result = f"{type(exc).__name__}: {clip(str(exc), 200)}", "ERROR"
        traceback.print_exception(type(exc), None, exc.__traceback__, file=sys.stderr)
    ROWS.append((num, name, expected, actual, result))


def check(ok: bool, actual: str) -> Outcome:
    """Turn a boolean into a PASS/FAIL outcome."""
    return actual, "PASS" if ok else "FAIL"


def raised(func: Callable[[], Any]) -> Exception | None:
    """Return the exception raised by func, or None."""
    try:
        func()
    except Exception as exc:  # noqa: BLE001  pylint: disable=broad-exception-caught
        return exc
    return None


def best_effort(func: Callable[[], Any]) -> None:
    """Run func, ignoring any error (cleanup helpers)."""
    raised(func)


def rows(resp: dict, *keys: str) -> list[dict]:
    """Extract a list from a response under one of the keys (or 'data')."""
    for key in (*keys, "data"):
        if isinstance(resp.get(key), list):
            return resp[key]
    return []


def find_by_name(items: list[dict], name: str, kind: str) -> int:
    """Return the id of the item with the exact name, or raise."""
    for item in items:
        if item.get("name") == name:
            return item["id"]
    raise LookupError(f"{kind} {name!r} not found (check LIVE_* variables)")


def entry_of(resp: dict) -> dict:
    """Unwrap an entry response."""
    return resp.get("entry") or resp.get("data") or resp


def absence_of(resp: dict) -> dict:
    """Unwrap an absence response."""
    return resp.get("absence") or resp.get("data") or resp


def track_entry(resp: dict) -> dict:
    """Remember an entry for cleanup and return it."""
    entry = entry_of(resp)
    if entry.get("id"):
        ENTRIES.append(entry["id"])
    return entry


def track_abs(resp: dict) -> dict:
    """Remember an absence for cleanup and return it."""
    absence = absence_of(resp)
    if absence.get("id"):
        ABSENCES.append(absence["id"])
    return absence


def parse_utc(value: str) -> datetime:
    """Parse a Clockodo timestamp as an aware UTC datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def expected_utc(value: str) -> datetime:
    """Independently compute the expected UTC instant of an input time."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        zone = ZoneInfo(os.getenv("CLOCKODO_TIMEZONE") or "Europe/Zurich")
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(timezone.utc)


def stored_since(entry_id: int) -> datetime:
    """Read back an entry's stored start as UTC."""
    return parse_utc(entry_of(client.get_entry(entry_id))["time_since"])


def status_code(exc: Exception | None) -> int | None:
    """HTTP status of an HTTPStatusError, else None."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code
    return None


def mcp_tools(role: str | None) -> tuple[list[str], list[str]]:
    """Start the MCP server over stdio with a role; return tool and resource names."""
    env = dict(os.environ)
    env.pop("CLOCKODO_MCP_ROLE", None)
    if role:
        env["CLOCKODO_MCP_ROLE"] = role
    msgs: list[dict] = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "live-test", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "resources/list"},
    ]
    proc = subprocess.run(
        [sys.executable, "-c", "from clockodo_mcp.server import main; main()"],
        input="\n".join(json.dumps(m) for m in msgs) + "\n",
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )
    out: dict[int, dict] = {}
    for line in proc.stdout.splitlines():
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if "id" in msg:
            out[msg["id"]] = msg.get("result") or msg.get("error") or {}
    tools = sorted(t["name"] for t in out.get(2, {}).get("tools", []))
    res = [r.get("uri", "") for r in out.get(3, {}).get("resources", [])]
    return tools, res


def day(base: date, offset: int) -> str:
    """ISO date base + offset days."""
    return (base + timedelta(days=offset)).isoformat()


def cleanup() -> Outcome:
    """Remove everything the suite created; already-gone (404) counts as cleaned."""
    left: list[str] = []

    def attempt(label: str, func: Callable[[], Any]) -> bool:
        try:
            func()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                left.append(f"{label}: {clip(str(exc), 60)}")
                return False
        except Exception as exc:  # noqa: BLE001  pylint: disable=W0718
            left.append(f"{label}: {clip(str(exc), 60)}")
            return False
        return True

    try:
        clock = client.get_clock().get("running")
        if clock and clock.get("id"):
            client.clock_stop(clock["id"])
            ENTRIES.append(clock["id"])
    except Exception as exc:  # noqa: BLE001  pylint: disable=broad-exception-caught
        left.append(f"clock: {clip(str(exc), 60)}")

    for aid in dict.fromkeys(ABSENCES):
        # Approved absences must be cancelled before they can be deleted.
        for status in (3, 4, None):
            if status is not None:
                best_effort(partial(client.edit_absence, aid, {"status": status}))
            before = len(left)
            if attempt(f"absence {aid}", partial(client.delete_absence, aid)):
                break
            if status is not None:
                del left[before:]  # retry with the next status before giving up
    for eid in dict.fromkeys(ENTRIES):
        attempt(f"entry {eid}", partial(client.delete_entry, eid))

    if left:
        return f"left behind: {left}", "FAIL"
    return (
        f"cleaned {len(set(ENTRIES))} entries, {len(set(ABSENCES))} absences",
        "PASS",
    )


def lookup_ids() -> dict[str, int]:
    """Resolve the demo customer/service/employee (by name) and the current user."""
    return {
        "customer": find_by_name(
            rows(client.list_customers(), "customers"),
            os.getenv("LIVE_CUSTOMER") or "Demo Customer",
            "customer",
        ),
        "service": find_by_name(
            rows(client.list_services(), "services"),
            os.getenv("LIVE_SERVICE") or "Demo Service",
            "service",
        ),
        "employee": find_by_name(
            rows(client.list_users(), "users"),
            os.getenv("LIVE_EMPLOYEE") or "Demo Employee",
            "employee",
        ),
        "me": user_svc.get_current_user_id(),
    }


def scenarios_roles_identity_clock(ids: dict[str, int]) -> None:
    """Scenarios 1-3: role exposure, identity, clock round-trip."""
    cust, serv, me = ids["customer"], ids["service"], ids["me"]
    tools_by_role: dict[str | None, list[str]] = {}
    for role in ("employee", "team_leader", "hr_analytics", "admin", None):

        def t1(role: str | None = role) -> Outcome:
            tools, res = mcp_tools(role)
            tools_by_role[role] = tools
            return check(bool(tools), f"{len(tools)} tools, {len(res)} resources")

        run("1", f"tools/list role={role}", "non-empty tool list", t1)

    def t1b() -> Outcome:
        employee_tools = tools_by_role.get("employee", [])
        exposed = [
            t for t in ("list_users", "get_raw_user_reports") if t in employee_tools
        ]
        return check(
            bool(employee_tools) and not exposed,
            f"employee exposes: {exposed or 'neither'}",
        )

    run(
        "1",
        "employee role hides list_users/get_raw_user_reports",
        "neither exposed",
        t1b,
    )

    def t2() -> Outcome:
        data = client._request("GET", "v4/users/me")  # pylint: disable=protected-access
        other = (data.get("data") or data.get("user") or data).get("id")
        return check(other == me, f"list-based={me} users/me={other}")

    run("2", "identity matches v4/users/me", "ids equal", t2)

    def t3() -> Outcome:
        started = user_tools.start_my_clock(
            cust, serv, billable=0, text="live-test clock"
        )
        started_run = started.get("running") or started.get("entry") or started
        got = user_tools.get_my_clock()
        stopped = user_tools.stop_my_clock()
        stopped_entry = stopped.get("stopped") or stopped.get("entry") or stopped
        if stopped_entry.get("id"):
            ENTRIES.append(stopped_entry["id"])
        ok = (
            (got.get("running") or {}).get("id") == started_run.get("id")
            and stopped_entry.get("text") == "live-test clock"
            and stopped_entry.get("billable") == 0
        )
        return check(
            ok,
            f"stopped text={stopped_entry.get('text')!r} "
            f"billable={stopped_entry.get('billable')}",
        )

    run("3", "clock start/get/stop round-trip", "stopped entry: text, billable=0", t3)


def scenarios_timezones(ids: dict[str, int], week: date) -> None:
    """Scenario 4: stored instant equals the independently computed UTC instant."""
    cust, serv = ids["customer"], ids["service"]
    tue = day(week, 1)
    cases = [
        ("naive = CLOCKODO_TIMEZONE local", f"{tue}T09:00:00", f"{tue}T09:30:00"),
        ("+02:00", f"{tue}T10:00:00+02:00", f"{tue}T10:30:00+02:00"),
        ("Z", f"{tue}T11:00:00Z", f"{tue}T11:30:00Z"),
        ("-05:00", f"{tue}T12:00:00-05:00", f"{tue}T12:30:00-05:00"),
        ("naive on DST change day", f"{DST_DAY}T01:30:00", f"{DST_DAY}T01:45:00"),
    ]
    for label, since, until in cases:

        def t4(label: str = label, since: str = since, until: str = until) -> Outcome:
            entry = track_entry(
                user_tools.add_my_entry(
                    cust, serv, since, until, billable=0, text=f"tz {label}"
                )
            )
            stored = stored_since(entry["id"])
            want = expected_utc(since)
            return check(
                stored == want,
                f"in={since} stored={stored.isoformat()} expected={want.isoformat()}",
            )

        run("4", f"tz {label}", "stored instant == expected UTC", t4)


def scenarios_entries_absences(  # pylint: disable=too-many-statements
    ids: dict[str, int], week: date
) -> None:
    """Scenarios 5-8: ownership guards, vacation, sick days, delete lifecycle."""
    cust, serv, emp, me = ids["customer"], ids["service"], ids["employee"], ids["me"]
    week2 = week + timedelta(days=7)

    def t5() -> Outcome:
        wed = day(week, 2)
        theirs = track_entry(
            client.create_entry(
                cust,
                serv,
                0,
                f"{wed}T09:00:00Z",
                f"{wed}T09:30:00Z",
                text="emp entry",
                user_id=emp,
            )
        )
        own = track_entry(
            user_tools.add_my_entry(
                cust,
                serv,
                f"{wed}T10:00:00Z",
                f"{wed}T10:30:00Z",
                billable=0,
                text="own",
            )
        )
        e_edit = raised(lambda: user_svc.edit_my_entry(theirs["id"], text="x"))
        e_del = raised(lambda: user_svc.delete_my_entry(theirs["id"]))
        move_kwargs: dict[str, Any] = {"users_id": emp}  # not an allowed field
        e_move = raised(
            lambda: user_svc.edit_my_entry(own["id"], **move_kwargs)
        )  # pylint: disable=E1123
        user_svc.edit_my_entry(own["id"], text="own edited")
        text = entry_of(client.get_entry(own["id"])).get("text")
        ok = (
            isinstance(e_edit, PermissionError)
            and isinstance(e_del, PermissionError)
            and isinstance(e_move, (PermissionError, TypeError))
            and text == "own edited"
        )
        return check(
            ok,
            f"edit-other={type(e_edit).__name__} delete-other={type(e_del).__name__} "
            f"move={type(e_move).__name__} own text={text!r}",
        )

    run("5", "entry ownership guards", "3x refused; own edit works", t5)

    def t6() -> Outcome:
        mon, wed, thu = day(week2, 0), day(week2, 2), day(week2, 3)
        vac = track_abs(user_tools.add_my_vacation(mon, thu))
        created_days = vac.get("count_days")
        mine = user_svc.get_my_absences(week2.year)["absences"]
        listed = [a for a in mine if a.get("id") == vac["id"]]
        user_tools.edit_my_vacation(vac["id"], date_until=wed)
        edited = absence_of(client.get_absence(vac["id"])).get("count_days")
        half = track_abs(user_tools.add_my_vacation(thu, thu, half_day=True))
        half_days = absence_of(client.get_absence(half["id"])).get("count_days")
        multi = raised(
            lambda: user_tools.add_my_vacation(day(week2, 1), wed, half_day=True)
        )
        ok = (
            bool(listed)
            and edited == 3
            and half_days == 0.5
            and isinstance(multi, ValueError)
        )
        return check(
            ok,
            f"create={created_days} listed={bool(listed)} edited={edited} "
            f"half={half_days} multi-day-half={type(multi).__name__}",
        )

    run(
        "6",
        "vacation create/list/edit + half day",
        "edited=3, half=0.5, ValueError",
        t6,
    )

    def t7() -> Outcome:
        wed, thu = day(week, 2), day(week, 3)
        first = track_abs(user_tools.add_my_sick_day(wed, wed, sick_note=False))
        second = track_abs(user_tools.add_my_sick_day(thu, thu, child=True))
        types = (
            absence_of(client.get_absence(first["id"])).get("type"),
            absence_of(client.get_absence(second["id"])).get("type"),
        )
        return check(types == (4, 5), f"types stored: {types}")

    run("7", "sick days stored as type 4/5", "types 4 and 5", t7)

    def t7b() -> Outcome:
        fri = day(week, 4)
        exc = raised(
            lambda: track_abs(
                client.create_absence(
                    date_since=fri, date_until=fri, absence_type=4, user_id=me
                )
            )
        )
        ok = isinstance(exc, httpx.HTTPStatusError) and "sick_note" in str(exc)
        return check(ok, f"{type(exc).__name__}: {clip(str(exc), 150)}")

    run(
        "7",
        "create_absence(type=4) without sick_note",
        "HTTPStatusError mentioning sick_note",
        t7b,
    )

    def t8() -> Outcome:
        fri = day(week2, 4)
        absence = track_abs(
            client.create_absence(
                date_since=fri, date_until=fri, absence_type=1, user_id=me
            )
        )
        status = absence_of(client.get_absence(absence["id"])).get("status")
        if status == 0:  # not auto-approved: plain delete must work
            user_svc.delete_my_vacation(absence["id"])
            ABSENCES.remove(absence["id"])
            return check(True, "enquired absence deleted without auto_cancel")
        refused = raised(lambda: user_svc.delete_my_vacation(absence["id"]))
        if refused is None:
            ABSENCES.remove(absence["id"])
            return check(False, f"approved (status={status}) deleted w/o auto_cancel")
        user_svc.delete_my_vacation(absence["id"], auto_cancel=True)
        ABSENCES.remove(absence["id"])
        return check(
            True,
            f"status={status}: no auto_cancel -> {type(refused).__name__}; "
            "auto_cancel=True deleted",
        )

    run(
        "8",
        "service delete of approved absence needs auto_cancel",
        "fails without, works with",
        t8,
    )

    def t8b() -> Outcome:
        fri = day(week2, 4)
        absence = track_abs(user_tools.add_my_vacation(fri, fri))
        status = absence_of(client.get_absence(absence["id"])).get("status")
        user_tools.delete_my_vacation(absence["id"])
        gone = raised(lambda: client.get_absence(absence["id"]))
        return check(
            status_code(gone) == 404,
            f"status before={status}; afterwards get -> {type(gone).__name__}",
        )

    run(
        "8",
        "delete_my_vacation tool removes approved absence",
        "absence gone (404)",
        t8b,
    )


def scenarios_team_hr_resources(ids: dict[str, int], week: date) -> None:
    """Scenarios 9-11: team leader, self-approval, HR summary, resources."""
    cust, serv, emp, me = ids["customer"], ids["service"], ids["employee"], ids["me"]

    def t9() -> Outcome:
        mon = day(week, 0)
        tl_svc.list_pending_vacations(week.year)
        absence = track_abs(
            tl_svc.create_team_vacation(emp, mon, mon, auto_approve=False)
        )
        before = absence_of(client.get_absence(absence["id"])).get("status")
        tl_svc.approve_vacation(absence["id"])
        after = absence_of(client.get_absence(absence["id"])).get("status")
        return check((before, after) == (0, 1), f"status {before}->{after}")

    run("9", "team leader creates + approves for employee", "status 0 -> 1", t9)

    def t9b() -> Outcome:
        fri = day(week, 4)
        absence = track_abs(
            client.create_absence(
                date_since=fri, date_until=fri, absence_type=1, user_id=me
            )
        )
        exc = raised(lambda: tl_svc.approve_vacation(absence["id"]))
        return check(
            isinstance(exc, PermissionError),
            f"approve own absence -> {type(exc).__name__ if exc else 'allowed'}",
        )

    run("9", "self-approval is refused", "PermissionError", t9b)

    def t10() -> Outcome:
        summary = hr_svc.get_hr_summary(week.year)
        return check(
            isinstance(summary, dict) and bool(summary),
            f"employees={summary.get('total_employees')}",
        )

    run("10", "HR summary", "non-empty summary", t10)

    def t11a() -> Outcome:
        if (client.get_clock() or {}).get("running"):
            return "a clock is running; cannot test idle case", "ERROR"
        res = resources.get_current_time_entry_resource()
        return check(
            res["content"] == {"running": False},
            f"content={clip(res.get('content'), 60)}",
        )

    run("11", "current-entry with idle clock", "no running entry", t11a)

    def t11b() -> Outcome:
        past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        for who, label, start in ((me, "own", "09"), (emp, "emp", "10")):
            track_entry(
                client.create_entry(
                    cust,
                    serv,
                    0,
                    f"{past}T{start}:00:00Z",
                    f"{past}T{start}:30:00Z",
                    text=f"{label} recent",
                    user_id=who,
                )
            )
        entries = resources.get_recent_entries_resource(30)["content"]["entries"]
        uids = sorted({e.get("users_id") for e in entries})
        return check(
            bool(entries) and uids == [me],
            f"{len(entries)} entries, users_ids={uids} (me={me}, emp={emp})",
        )

    run("11", "recent-entries returns only own entries", "users_ids == [me]", t11b)


def main() -> int:
    """Run all scenarios, print the result table, return the exit code."""
    week = date.fromisoformat(os.getenv("LIVE_WEEK") or DEFAULT_WEEK)
    if week.weekday() != 0:
        print(f"LIVE_WEEK {week} is not a Monday")
        return 2
    try:
        ids = lookup_ids()
    except Exception as exc:  # noqa: BLE001  pylint: disable=broad-exception-caught
        print("setup failed:", type(exc).__name__, clip(str(exc)))
        return 2
    print(f"setup: week={week} " + " ".join(f"{k}={v}" for k, v in ids.items()))

    try:
        scenarios_roles_identity_clock(ids)
        scenarios_timezones(ids, week)
        scenarios_entries_absences(ids, week)
        scenarios_team_hr_resources(ids, week)
    finally:
        run("12", "cleanup", "nothing left behind", cleanup)

    print("\n| # | Scenario | Expected | Actual | Result |\n|---|---|---|---|---|")
    for row in ROWS:
        cells = (clip(x, 400 if i == 3 else 70) for i, x in enumerate(row))
        print("| " + " | ".join(cells) + " |")
    bad = [r for r in ROWS if r[4] != "PASS"]
    print(f"\n{len(ROWS) - len(bad)}/{len(ROWS)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
