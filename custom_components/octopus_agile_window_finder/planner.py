"""Slot planning for the Octopus Agile Best Window Finder.

This module has no Home Assistant dependencies so it can be unit tested on
its own. All datetimes are timezone-aware.

Two modes are supported:

* ``window`` - the cheapest *contiguous* block of ``run_hours`` within the
  known rates (today and, after ~4pm, tomorrow). Once a chosen window has
  started it is locked until it ends, so new rates arriving can't cut a run
  short.
* ``slots`` - the cheapest ``run_hours`` per day (or per allowed time range),
  not necessarily contiguous, with an optional minimum block length so the
  appliance isn't switched on and off every half hour. Slots that have already
  run (or are running now) are kept, so the daily total stays at
  ``run_hours`` however often the plan is recalculated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

SLOT = timedelta(minutes=30)
MODE_WINDOW = "window"
MODE_SLOTS = "slots"


@dataclass(frozen=True)
class Slot:
    start: datetime
    end: datetime
    price: float  # GBP/kWh inc VAT


@dataclass
class Plan:
    """Result of a planning run."""

    status: str  # "ok", "waiting_for_rates", "no_window"
    slots: list[Slot]  # chosen slots, sorted by start
    period_start: datetime | None = None
    period_end: datetime | None = None

    def blocks(self) -> list[tuple[datetime, datetime]]:
        """Merge adjacent chosen slots into (start, end) blocks."""
        out: list[list[datetime]] = []
        for s in self.slots:
            if out and out[-1][1] == s.start:
                out[-1][1] = s.end
            else:
                out.append([s.start, s.end])
        return [(a, b) for a, b in out]

    def is_active(self, now: datetime) -> bool:
        return any(s.start <= now < s.end for s in self.slots)

    def current_or_next_block(self, now: datetime) -> tuple[datetime, datetime] | None:
        for start, end in self.blocks():
            if end > now:
                return start, end
        return None


# --------------------------------------------------------------------------
# Rate parsing


def _to_dt(value, tz) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    # Work in local time so the daily time-range checks use local clock times.
    return dt.astimezone(tz)


def parse_rates(raw: Iterable[dict], tz) -> list[Slot]:
    """Turn Octopus Energy event ``rates`` attributes into sorted, de-duplicated slots."""
    seen: dict[datetime, Slot] = {}
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        start = _to_dt(item.get("start"), tz)
        end = _to_dt(item.get("end"), tz)
        price = item.get("value_inc_vat")
        if start is None or end is None or end <= start:
            continue
        try:
            price = float(price)
        except (TypeError, ValueError):
            continue
        seen[start] = Slot(start, end, price)
    return sorted(seen.values(), key=lambda s: s.start)


def parse_time(value) -> time | None:
    if value in (None, ""):
        return None
    if isinstance(value, time):
        return value
    try:
        return time.fromisoformat(str(value))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Time-range helpers


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _slot_allowed(slot: Slot, min_t: time | None, max_t: time | None) -> bool:
    """True if a slot lies wholly inside the allowed daily time range.

    The range may wrap midnight (e.g. 22:00-06:00). ``None`` means unbounded
    (start of day for ``min_t``, end of day for ``max_t``).
    """
    if min_t is None and max_t is None:
        return True
    lo = _minutes(min_t) if min_t else 0
    hi = _minutes(max_t) if max_t else 1440
    if hi == 0:
        hi = 1440  # an end time of 00:00 means midnight at the end of the day
    s = _minutes(slot.start.timetz())
    e = _minutes(slot.end.timetz())
    if e == 0 or e <= s:
        e = 1440  # slot ends at midnight
    if lo == hi or (lo == 0 and hi == 1440):
        return True
    if lo < hi:
        return lo <= s and e <= hi
    # Wrapping range, e.g. 22:00 -> 06:00
    return s >= lo or e <= hi


def _periods_around(now: datetime, min_t: time | None, max_t: time | None):
    """Yield (start, end) daily periods starting the day before ``now``."""
    tz = now.tzinfo
    lo = min_t or time(0, 0)
    hi = max_t or time(0, 0)
    for offset in (-1, 0, 1, 2):
        d: date = now.date() + timedelta(days=offset)
        start = datetime.combine(d, lo, tzinfo=tz)
        end_day = d if hi > lo else d + timedelta(days=1)
        end = datetime.combine(end_day, hi, tzinfo=tz)
        yield start, end


def _period_slots(slots: list[Slot], start: datetime, end: datetime) -> list[Slot]:
    return [s for s in slots if s.start >= start and s.end <= end]


def _expected_slot_count(start: datetime, end: datetime) -> int:
    # Convert to UTC first: subtracting datetimes that share a tzinfo uses
    # wall-clock time, which would ignore the DST change (46 / 50 slot days).
    delta = end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
    return int(round(delta.total_seconds() / SLOT.total_seconds()))


# --------------------------------------------------------------------------
# Contiguous window mode


def plan_window(
    slots: list[Slot],
    now: datetime,
    run_hours: float,
    min_t: time | None = None,
    max_t: time | None = None,
    previous: list[Slot] | None = None,
) -> Plan:
    needed = max(1, math.ceil(run_hours * 2))

    # Keep a window that is already running.
    if previous:
        prev_start, prev_end = previous[0].start, previous[-1].end
        if prev_start <= now < prev_end:
            return Plan("ok", list(previous))

    if len(slots) < needed:
        return Plan("waiting_for_rates", [])

    # Earliest allowed start is the beginning of the current half hour, so a
    # refresh a few seconds after a slot boundary can still pick that slot.
    floor_now = now - timedelta(
        minutes=now.minute % 30, seconds=now.second, microseconds=now.microsecond
    )

    best: tuple[float, int] | None = None
    for i in range(len(slots) - needed + 1):
        window = slots[i : i + needed]
        if window[0].start < floor_now:
            continue
        if any(window[j + 1].start != window[j].end for j in range(needed - 1)):
            continue  # gap in the rate data
        if not all(_slot_allowed(s, min_t, max_t) for s in window):
            continue
        total = sum(s.price for s in window)
        if best is None or total < best[0] - 1e-12:
            best = (total, i)

    if best is None:
        # If the known rates run out within a day, a suitable window may
        # simply not be published yet (tomorrow's prices arrive ~4pm).
        if slots[-1].end - now < timedelta(hours=24):
            return Plan("waiting_for_rates", [])
        return Plan("no_window", [])
    return Plan("ok", slots[best[1] : best[1] + needed])


# --------------------------------------------------------------------------
# Cheapest-slots mode


def _choose(
    prices: list[float | None],
    forced: list[bool | None],
    k: int,
    m: int,
) -> list[bool] | None:
    """Pick exactly ``k`` slots minimising cost, every run at least ``m`` long.

    ``prices[i]`` is None if the slot can't be chosen (unknown rate).
    ``forced[i]`` is True/False to fix a slot, None if free.
    Returns a list of booleans or None if infeasible.
    """
    n = len(prices)
    INF = float("inf")
    # dp[k][r]: r = 0 (not in a run) or 1..m (run length, capped at m)
    dp = [[INF] * (m + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0
    back: list[list[list[tuple[int, int, bool] | None]]] = []
    for i in range(n):
        ndp = [[INF] * (m + 1) for _ in range(k + 1)]
        nb: list[list[tuple[int, int, bool] | None]] = [[None] * (m + 1) for _ in range(k + 1)]
        can_take = forced[i] is not False and (prices[i] is not None or forced[i] is True)
        can_skip = forced[i] is not True
        cost = prices[i] if prices[i] is not None else 0.0
        for kk in range(k + 1):
            for r in range(m + 1):
                cur = dp[kk][r]
                if cur == INF:
                    continue
                if can_skip and (r == 0 or r == m):
                    if cur < ndp[kk][0]:
                        ndp[kk][0] = cur
                        nb[kk][0] = (kk, r, False)
                if can_take and kk < k:
                    nr = min(r + 1, m)
                    val = cur + cost
                    if val < ndp[kk + 1][nr] - 1e-12:
                        ndp[kk + 1][nr] = val
                        nb[kk + 1][nr] = (kk, r, True)
        dp = ndp
        back.append(nb)

    end_states = [(dp[k][r], r) for r in (0, m) if dp[k][r] < INF]
    if not end_states:
        return None
    _, r = min(end_states)
    kk = k
    chosen = [False] * n
    for i in range(n - 1, -1, -1):
        prev = back[i][kk][r]
        if prev is None:
            return None
        pk, pr, took = prev
        chosen[i] = took
        kk, r = pk, pr
    return chosen


def _plan_period(
    period_slots: list[Slot],
    now: datetime,
    k: int,
    m: int,
    previous_starts: set[datetime],
) -> list[Slot]:
    prices: list[float | None] = []
    forced: list[bool | None] = []
    for s in period_slots:
        if s.end <= now:
            # Already happened: keep whatever the previous plan did.
            forced.append(s.start in previous_starts)
        elif s.start <= now:
            # Running now: keep it on if it was planned; otherwise free.
            forced.append(True if s.start in previous_starts else None)
        else:
            forced.append(None)
        prices.append(s.price)

    k = min(k, len(period_slots))
    for mm in (m, 1):
        chosen = _choose(prices, forced, k, mm)
        if chosen is not None:
            return [s for s, c in zip(period_slots, chosen) if c]

    # Still infeasible (e.g. too few slots left). Keep forced-on slots and
    # add the cheapest remaining future ones.
    keep = [s for s, f in zip(period_slots, forced) if f is True]
    free = sorted(
        (s for s, f in zip(period_slots, forced) if f is None and s.end > now),
        key=lambda s: (s.price, s.start),
    )
    keep += free[: max(0, k - len(keep))]
    return sorted(keep, key=lambda s: s.start)


def plan_slots(
    slots: list[Slot],
    now: datetime,
    run_hours: float,
    min_block_hours: float | None = None,
    min_t: time | None = None,
    max_t: time | None = None,
    previous: list[Slot] | None = None,
) -> Plan:
    """Cheapest ``run_hours`` per period, in blocks of at least ``min_block_hours``."""
    k = max(1, math.ceil(run_hours * 2))
    m = max(1, math.ceil((min_block_hours or 0.5) * 2))
    m = min(m, k)
    previous_starts = {s.start for s in previous or []}

    plans: list[Slot] = []
    period: tuple[datetime, datetime] | None = None
    status = "ok"
    for p_start, p_end in _periods_around(now, min_t, max_t):
        if p_end <= now:
            continue
        p_slots = _period_slots(slots, p_start, p_end)
        expected = _expected_slot_count(p_start, p_end)
        # Agile prices are published for 23:00-23:00, so a calendar day is
        # usually missing its last hour until ~4pm. Allow up to an hour short.
        complete = len(p_slots) >= expected - 2
        started = p_start <= now

        if not complete and not started:
            status = "waiting_for_rates"
            if period is None:
                period = (p_start, p_end)
            break
        if not p_slots:
            continue

        plans = _plan_period(p_slots, now, k, m, previous_starts)
        period = (p_start, p_end)
        status = "ok"
        # Stop at the first period with a run still to come; otherwise move on
        # to the next period so the sensor can show the next start time.
        if any(s.end > now for s in plans):
            break

    if not plans and status == "ok":
        status = "no_window"
    return Plan(
        status,
        sorted(plans, key=lambda s: s.start),
        period[0] if period else None,
        period[1] if period else None,
    )


def make_plan(
    mode: str,
    slots: list[Slot],
    now: datetime,
    run_hours: float,
    min_block_hours: float | None,
    min_t: time | None,
    max_t: time | None,
    previous: list[Slot] | None,
) -> Plan:
    if mode == MODE_SLOTS:
        return plan_slots(slots, now, run_hours, min_block_hours, min_t, max_t, previous)
    return plan_window(slots, now, run_hours, min_t, max_t, previous)
