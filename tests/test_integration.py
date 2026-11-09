"""End-to-end tests running the integration inside Home Assistant."""
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.octopus_agile_window_finder.const import DOMAIN

TZ = ZoneInfo("Europe/London")
CUR = "event.octopus_energy_electricity_x_current_day_rates"
NXT = "event.octopus_energy_electricity_x_next_day_rates"


def rates(day, prices):
    t = datetime.combine(day, time(0, 0), tzinfo=TZ)
    out = []
    for p in prices:
        e = t + timedelta(minutes=30)
        out.append({"start": t, "end": e, "value_inc_vat": p, "is_capped": False})
        t = e
    return out


TODAY = [0.33] * 12 + [0.5] * 30 + [0.45, 0.40, 0.41, 0.37]  # 46 slots, cheapest 2h at 21:00
TOMORROW = [0.30] * 4 + [0.10] * 4 + [0.30] * 38


async def setup(hass, freezer, data, now):
    await hass.config.async_set_time_zone("Europe/London")
    freezer.move_to(now)
    hass.states.async_set(CUR, "x", {"rates": rates(now.date(), TODAY)})
    hass.states.async_set(NXT, "x", {"rates": []})
    entry = MockConfigEntry(domain=DOMAIN, title=data["name"], data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def base(**kw):
    d = {
        "name": "Pool Winter", "current_entity": CUR, "future_entity": NXT,
        "run_hours": 2.0, "total_kwh": 2.0, "enable_binary": True,
    }
    d.update(kw)
    return d


async def tick(hass, freezer, when):
    """Simulate the half-hourly refresh (the timer itself is a standard HA helper)."""
    freezer.move_to(when)
    for coordinator in hass.data[DOMAIN].values():
        await coordinator.async_refresh()
    await hass.async_block_till_done()


async def test_window_runs_whole_window(hass: HomeAssistant, freezer):
    now = datetime(2026, 11, 9, 8, 40, tzinfo=TZ)
    await setup(hass, freezer, base(), now)
    s = hass.states.get("sensor.pool_winter_best_window")
    b = hass.states.get("binary_sensor.pool_winter_window_active")
    assert s.state == "09:00 pm", s
    assert b.state == "off"
    assert s.attributes["estimated_cost_pence"] == pytest.approx((0.45 + 0.40 + 0.41 + 0.37) / 4 * 2 * 100)

    await tick(hass, freezer, datetime(2026, 11, 9, 21, 0, 5, tzinfo=TZ))
    assert hass.states.get("binary_sensor.pool_winter_window_active").state == "on"
    assert hass.states.get("sensor.pool_winter_best_window").state == "09:00 pm"

    # 4pm-style arrival of cheaper rates mid-run must not cut it short
    hass.states.async_set(NXT, "y", {"rates": rates(datetime(2026, 11, 10).date(), TOMORROW)})
    await hass.async_block_till_done()
    await tick(hass, freezer, datetime(2026, 11, 9, 22, 30, 5, tzinfo=TZ))
    assert hass.states.get("binary_sensor.pool_winter_window_active").state == "on"

    await tick(hass, freezer, datetime(2026, 11, 9, 23, 0, 5, tzinfo=TZ))
    assert hass.states.get("binary_sensor.pool_winter_window_active").state == "off"
    assert hass.states.get("sensor.pool_winter_best_window").state == "02:00 am"


async def test_new_rates_move_unstarted_window(hass: HomeAssistant, freezer):
    now = datetime(2026, 11, 9, 15, 0, tzinfo=TZ)
    await setup(hass, freezer, base(), now)
    assert hass.states.get("sensor.pool_winter_best_window").state == "09:00 pm"
    freezer.move_to(datetime(2026, 11, 9, 16, 1, tzinfo=TZ))
    hass.states.async_set(NXT, "y", {"rates": rates(datetime(2026, 11, 10).date(), TOMORROW)})
    await hass.async_block_till_done()
    s = hass.states.get("sensor.pool_winter_best_window")
    assert s.state == "02:00 am"
    assert s.attributes["start_time"].startswith("2026-11-10T02:00")


async def test_slots_mode(hass: HomeAssistant, freezer):
    now = datetime(2026, 11, 10, 0, 5, tzinfo=TZ)
    await hass.config.async_set_time_zone("Europe/London")
    freezer.move_to(now)
    hass.states.async_set(CUR, "x", {"rates": rates(now.date(), TOMORROW)})
    hass.states.async_set(NXT, "x", {"rates": []})
    entry = MockConfigEntry(domain=DOMAIN, title="Pool", data=base(name="Pool", mode="slots", run_hours=3.0, min_block_hours=1.0))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    s = hass.states.get("sensor.pool_best_window")
    assert s.attributes["planned_hours"] == 3.0
    blocks = s.attributes["blocks"]
    assert any(b["start"].startswith("2026-11-10T02:00") for b in blocks)
    for b in blocks:
        assert datetime.fromisoformat(b["end"]) - datetime.fromisoformat(b["start"]) >= timedelta(hours=1)


async def test_config_flow_labels_and_options(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Pump", "current_entity": CUR, "future_entity": NXT, "mode": "slots",
         "run_hours": 1.0, "min_block_hours": 2.0, "total_kwh": 1.0, "enable_binary": True},
    )
    assert result["errors"] == {"min_block_hours": "min_block_too_long"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Pump", "current_entity": CUR, "future_entity": NXT, "mode": "slots",
         "run_hours": 2.0, "min_block_hours": 1.0, "total_kwh": 1.0, "enable_binary": True,
         "min_start": "22:00:00", "max_end": "06:00:00"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    # clear the time range, switch to window mode
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"current_entity": CUR, "future_entity": NXT, "mode": "window",
         "run_hours": 2.0, "total_kwh": 1.0, "enable_binary": False},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    from custom_components.octopus_agile_window_finder.coordinator import merged_config
    conf = merged_config(entry)
    assert "min_start" not in conf and conf["mode"] == "window"


async def test_translations_cover_fields():
    import json, pathlib
    p = pathlib.Path(__file__).parents[1] / "custom_components/octopus_agile_window_finder/translations/en.json"
    en = json.loads(p.read_text())
    for k in ["current_entity", "future_entity", "mode", "run_hours", "min_block_hours", "total_kwh", "min_start", "max_end", "enable_binary"]:
        assert k in en["config"]["step"]["user"]["data"]
        assert k in en["options"]["step"]["init"]["data"]



async def test_restart_mid_run_keeps_running(hass: HomeAssistant, freezer):
    now = datetime(2026, 11, 9, 8, 40, tzinfo=TZ)
    entry = await setup(hass, freezer, base(), now)
    await tick(hass, freezer, datetime(2026, 11, 9, 21, 30, 5, tzinfo=TZ))
    assert hass.states.get("binary_sensor.pool_winter_window_active").state == "on"
    # Restart with rates temporarily missing
    assert await hass.config_entries.async_unload(entry.entry_id)
    hass.states.async_set(CUR, "x", {"rates": []})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.pool_winter_window_active").state == "on"
