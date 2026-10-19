# raspi-openweather

Super light-weight full-screen weather display application. Memory footprint: RSS=140KB, VIRT=600KB.
Minimal CPU load. Optimized for 800x480 screen. Tested on RaspberryPi 4.

Uses free API key from https://openweathermap.org/ - simply register, create a new API key and save it
in the `open_weather.json` file (excluded from repo via `.gitignore` for security reasons). We're using
API endpoint that does not require any subscription or providing CC info.

Here's an example of `open_weather.json` with Berlin GPS coordinates (don't forget to update them
to your location):

```json
{
  "api_key": "PUT_YOUR_API_KEY_HERE",
  "lat":"52.513988",
  "lon":"13.358462"
}
```

Optional settings (with their defaults):

- `temp_unit`: `metric` (default), `imperial` or `standard` (Kelvin)
- `wind_unit`: `kmph` (default) or `mps`; with `imperial` units wind speed is always shown in mph

## Installation and running

```bash
pip install -r requirements.txt
./weather.sh                  # or: python open_weather.py
```

Command line options (see `python open_weather.py --help`):

- `-c/--config PATH` - use a different config file (default: `open_weather.json`)
- `--debug` - verbose logging and data from `fixtures/weather.json` instead of the API
- `--windowed` - run in a window instead of full screen
- `--refresh-interval SECONDS` - how often to fetch new weather data (default: 900)

Exit with `ESC` or by tapping the upper right corner of the screen.

## Development

The code lives in the `raspi_openweather` package:

- `config.py` - settings and config file loading
- `weather.py` - API client with retries, response parsing and background updater
- `formatting.py` - pure presentation helpers (units, times, day/night)
- `display.py` - pygame rendering
- `app.py` - command line interface and main loop

```bash
pip install -r requirements-dev.txt
pytest --cov          # run tests (no display needed)
ruff check .          # lint
ruff format .         # format
```

## Screenshot

![screenshot](screenshots/20250920_berlin.png)

## Original source
Github: https://github.com/granpino/raspi-openweather.git
The complete project is located at https://www.hackster.io/Granpino/raspberry-pi-open-weather-display-6f12a7
