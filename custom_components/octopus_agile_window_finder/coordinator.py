"""Shared plan for one appliance: recalculated on new rates and every half hour."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Callable

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_utc_time_change,
)
from homeassistant.helpers.storage import Store

from .const import (
    CONF_CURRENT_ENTITY,
    CONF_FUTURE_ENTITY,
    CONF_MAX_END,
    CONF_MIN_BLOCK_HOURS,
    CONF_MIN_START,
    CONF_MODE,
    CONF_RUN_HOURS,
    CONF_TOTAL_KWH,
    DEFAULT_MODE,
    DOMAIN,
    OPTIONAL_KEYS,
)
from .planner import Plan, Slot, make_plan, parse_rates, parse_time

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1


def merged_config(entry: ConfigEntry) -> dict:
    """Config with options applied. Optional keys missing from options are unset."""
    conf = dict(entry.data)
    if entry.options:
        for key in OPTIONAL_KEYS:
            conf.pop(key, None)
        conf.update(entry.options)
    return conf


class WindowFinderCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.plan = Plan("waiting_for_rates", [])
        self.last_calculated: datetime | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        # Refreshes can be triggered by the half-hour timer, new rates and the
        # service at the same moment; run them one at a time so an older
        # calculation can never overwrite a newer one.
        self._lock = asyncio.Lock()

    @property
    def conf(self) -> dict:
        return merged_config(self.entry)

    @property
    def slot_kwh(self) -> float:
        """kWh used per half-hour slot."""
        hours = float(self.conf.get(CONF_RUN_HOURS) or 0.5)
        slots = max(1, round(hours * 2))
        return float(self.conf.get(CONF_TOTAL_KWH) or 0) / slots

    async def async_setup(self) -> None:
        stored = await self._store.async_load()
        if stored:
            try:
                self.plan = Plan(
                    stored.get("status", "ok"),
                    [
                        Slot(datetime.fromisoformat(s), datetime.fromisoformat(e), float(p))
                        for s, e, p in stored.get("slots", [])
                    ],
                )
            except (TypeError, ValueError):
                _LOGGER.warning("Ignoring unreadable stored plan for %s", self.entry.title)

        conf = self.conf
        rate_entities = [conf[k] for k in (CONF_CURRENT_ENTITY, CONF_FUTURE_ENTITY) if conf.get(k)]
        if rate_entities:
            self._unsubs.append(
                async_track_state_change_event(self.hass, rate_entities, self._handle_rates_changed)
            )
        # Slot boundaries: switch the binary sensor and recheck the plan.
        self._unsubs.append(
            async_track_utc_time_change(self.hass, self._handle_tick, minute=[0, 30], second=5)
        )
        await self.async_refresh()

    @callback
    def async_shutdown(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()

    async def async_remove_store(self) -> None:
        await self._store.async_remove()

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(update_callback)

        @callback
        def remove() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return remove

    async def _handle_rates_changed(self, event: Event) -> None:
        await self.async_refresh()

    async def _handle_tick(self, now: datetime) -> None:
        await self.async_refresh()

    def _collect_slots(self, now: datetime) -> list[Slot]:
        conf = self.conf
        raw: list = []
        for key in (CONF_CURRENT_ENTITY, CONF_FUTURE_ENTITY):
            entity_id = conf.get(key)
            state = self.hass.states.get(entity_id) if entity_id else None
            if state is None:
                continue
            rates = state.attributes.get("rates")
            if rates:
                raw.extend(rates)
        slots = {s.start: s for s in parse_rates(raw, now.tzinfo)}
        # Keep slots from the existing plan that have dropped out of the rate
        # entities (e.g. yesterday's slots after midnight) so runs that have
        # already happened still count.
        for s in self.plan.slots:
            slots.setdefault(s.start, s)
        return sorted(slots.values(), key=lambda s: s.start)

    async def async_refresh(self) -> None:
        async with self._lock:
            await self._async_refresh_locked()

    async def _async_refresh_locked(self) -> None:
        now = dt_util.now()
        conf = self.conf
        slots = self._collect_slots(now)
        previous = list(self.plan.slots)

        plan = await self.hass.async_add_executor_job(
            make_plan,
            conf.get(CONF_MODE, DEFAULT_MODE),
            slots,
            now,
            float(conf.get(CONF_RUN_HOURS) or 0.5),
            conf.get(CONF_MIN_BLOCK_HOURS),
            parse_time(conf.get(CONF_MIN_START)),
            parse_time(conf.get(CONF_MAX_END)),
            previous,
        )
        if plan.status != "ok" and previous and any(s.end > now for s in previous):
            # Don't throw away a plan that still has runs to come just because
            # rates are momentarily unavailable (e.g. during a restart).
            plan = Plan("ok", previous, self.plan.period_start, self.plan.period_end)

        changed = plan.slots != self.plan.slots or plan.status != self.plan.status
        self.plan = plan
        self.last_calculated = now
        if changed:
            _LOGGER.debug("%s plan now %s %s", self.entry.title, plan.status, plan.blocks())
            await self._store.async_save(
                {
                    "status": plan.status,
                    "slots": [[s.start.isoformat(), s.end.isoformat(), s.price] for s in plan.slots],
                }
            )
        for update_callback in list(self._listeners):
            update_callback()
