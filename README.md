# Octopus Best Window Finder

A Home Assistant integration that finds the cheapest times to run an appliance on Octopus Agile. It reads the rate events from the [Octopus Energy integration](https://bottlecapdave.github.io/HomeAssistant-OctopusEnergy/) and plans when your appliance should run.

## Features
- **Two scheduling modes**
  - **Continuous block**: the cheapest single window of the run time, looking across today's and (after about 4pm) tomorrow's rates. Good for a dishwasher or a car.
  - **Cheapest slots**: the cheapest half-hours adding up to the run time each day, not necessarily together, with an optional minimum block length. Good for a pool pump or anything that just needs N hours a day.
- **Runs aren't cut short**: once a planned run has started it stays in the plan, even when new rates arrive at 4pm. In cheapest-slots mode, time already run counts towards the day's total.
- **Cost estimate**: predicted cost in pence from the appliance's kWh.
- **Window Active binary sensor** (optional): turns on and off at the start of each planned half-hour, ready to trigger automations.
- **Time constraints**: optional earliest start and latest finish, including overnight ranges such as 22:00 to 06:00.

## Installation

### HACS (recommended)
1. Open **HACS** in Home Assistant.
2. Click the three dots in the top right and select **Custom repositories**.
3. Paste this repository's URL, select **Integration** as the category, and click **Add**.
4. Search for "Octopus Agile Best Window Finder" and click **Install**.
5. Restart Home Assistant.

### Manual
1. Copy the `custom_components/octopus_agile_window_finder` folder to your `custom_components` directory.
2. Restart Home Assistant.

## Configuration
1. Go to **Settings > Devices & services**.
2. Click **Add integration** and search for **Octopus Agile Best Window Finder**.
3. Fill in the form. Add one entry per appliance.

| Setting | Meaning |
|---|---|
| Appliance name | Used to name the sensors. |
| Today's rates | The Octopus Energy *Current Day Rates* event entity. |
| Tomorrow's rates | The Octopus Energy *Next Day Rates* event entity. |
| Scheduling mode | Continuous block or cheapest slots. |
| Run time | Hours to run. In cheapest-slots mode, the total per day (or per allowed time range). |
| Minimum block length | Cheapest-slots mode only. The shortest run in one go. Set it equal to the run time for one block per day. |
| Energy used | kWh over the full run time, for the cost estimate. |
| Earliest start / Latest finish | Optional daily time range. In cheapest-slots mode this range is the "day" the run time is spread over. |
| Create 'window active' sensor | Adds the binary sensor. |

Settings can be changed later with **Configure**; the plan is recalculated straight away.

## Entities
- `sensor.<name>_best_window`: start time of the current or next planned run. Attributes:
  - `start_time`, `end_time`: the current or next block.
  - `blocks`: every planned block.
  - `estimated_cost_pence`, `average_rate_pence`.
  - `planned_hours`, `mode`, `status`.
  - `period_start`, `period_end` (cheapest-slots mode).
- `binary_sensor.<name>_window_active`: on during planned slots.

## Example automation
```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.pool_window_active
    to: ["on", "off"]
actions:
  - action: "switch.turn_{{ trigger.to_state.state }}"
    target:
      entity_id: switch.pool_pump
```

## Service
`octopus_agile_window_finder.update_windows` recalculates every appliance's plan now. Plans are also recalculated every half hour and whenever the rate entities change.
