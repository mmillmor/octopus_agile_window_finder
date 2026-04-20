# Octopus Best Window Finder

A Home Assistant integration to find the cheapest adjacent electricity slots for Octopus Agile customers. This tool identifies the best future window for appliances based on run time and energy consumption.

## Features
- **Dynamic Search**: Finds the cheapest contiguous window for a specified number of hours.
- **Cost Estimation**: Calculates the predicted cost in pence based on your appliance's kWh.
- **Binary Sensor**: Optional sensor that turns `on` when the identified window is active.
- **Time Constraints**: Set optional minimum start and maximum end times to allow operation within a particular window, e.g. charging a car overnight.

## Installation

### HACS (Recommended)
1. Open **HACS** in Home Assistant.
2. Click the three dots in the top right and select **Custom repositories**.
3. Paste your repository URL, select **Integration** as the category, and click **Add**.
4. Search for "Octopus Best Window Finder" and click **Install**.
5. Restart Home Assistant.

### Manual
1. Copy the `octopus_agile_window_finder` folder to your `custom_components` directory.
2. Restart Home Assistant.

## Configuration
1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for **Octopus Agile Best Window Finder**.
3. Complete the setup form:
   - **Current Rates Entity**: The event entity for today's rates.
   - **Future Rates Entity**: The event entity for tomorrow's rates.
   - **Run Duration**: How many hours the appliance runs (e.g., 1.5).
   - **Appliance Consumption**: Total kWh used per full run.
   - **Binary Sensor**: Toggle to enable the "Window Active" sensor.

## Sensors
- `sensor.octopus_{name}_best_window`: The start time of the cheapest future window.
- `binary_sensor.octopus_{name}_window_active`: Turns on during the calculated window.
