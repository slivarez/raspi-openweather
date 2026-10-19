"""Fetching and parsing weather data from the OpenWeatherMap API."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import requests

from raspi_openweather.config import Settings

logger = logging.getLogger(__name__)

API_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_ICON = "01d"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _timestamp() -> str:
    return time.strftime(TIMESTAMP_FORMAT, time.localtime())


@dataclass(frozen=True)
class WeatherData:
    """A snapshot of the current weather, ready to be displayed."""

    name: str = "Unknown"
    temp: float = 0
    feels_like: float = 0
    humidity: int = 0
    temp_min: float = 0
    temp_max: float = 0
    description: str = "N/A"
    icon: str = DEFAULT_ICON
    wind_speed: float = 0
    sunrise: int = 0
    sunset: int = 0
    last_updated: str = ""
    error: str = ""

    def with_error(self, error: str) -> WeatherData:
        """Return a copy of this snapshot flagged with an error message."""
        return replace(self, error=error)


def parse_weather(payload: dict[str, Any], last_updated: str | None = None) -> WeatherData:
    """Convert an OpenWeatherMap "current weather" response into WeatherData.

    Missing fields fall back to neutral defaults so a partial response never
    crashes the display.
    """
    main = payload.get("main", {})
    weather = (payload.get("weather") or [{}])[0]
    sys_info = payload.get("sys", {})
    return WeatherData(
        name=payload.get("name", "Unknown"),
        temp=round(main.get("temp", 0), 1),
        feels_like=round(main.get("feels_like", 0), 1),
        humidity=main.get("humidity", 0),
        temp_min=round(main.get("temp_min", 0), 1),
        temp_max=round(main.get("temp_max", 0), 1),
        description=weather.get("main", "N/A"),
        icon=weather.get("icon", DEFAULT_ICON),
        wind_speed=payload.get("wind", {}).get("speed", 0),
        sunrise=sys_info.get("sunrise", 0),
        sunset=sys_info.get("sunset", 0),
        last_updated=last_updated if last_updated is not None else _timestamp(),
    )


class WeatherError(Exception):
    """Raised when weather data could not be obtained."""


class WeatherClient:
    """Fetches current weather from OpenWeatherMap with retries."""

    def __init__(
        self,
        settings: Settings,
        session: requests.Session | None = None,
        *,
        max_retries: int = 6,
        retry_delay: float = 10,
        timeout: float = 5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self.session = session or requests.Session()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._sleep = sleep

    @property
    def params(self) -> dict[str, str]:
        return {
            "appid": self.settings.api_key,
            "lat": self.settings.lat,
            "lon": self.settings.lon,
            "units": self.settings.temp_unit,
        }

    def fetch(self) -> WeatherData:
        """Fetch the current weather.

        Network errors are retried with exponential backoff. HTTP errors are
        not retried. Raises WeatherError if no data could be obtained.
        """
        delay = self.retry_delay
        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(API_URL, params=self.params, timeout=self.timeout)
            except requests.RequestException as e:
                last_error = f"Network error (attempt {attempt}/{self.max_retries}): {e}"
                logger.warning(last_error)
                if attempt < self.max_retries:
                    self._sleep(delay)
                    delay *= 2
                continue

            if not response.ok:
                raise WeatherError(f"ERROR: {response.status_code} {_error_message(response)}")
            try:
                payload = response.json()
            except ValueError as e:
                raise WeatherError(f"ERROR: invalid JSON response: {e}") from e
            return parse_weather(payload)

        raise WeatherError(
            f"Failed to fetch weather data after {self.max_retries} attempts. {last_error}"
        )


def _error_message(response: requests.Response) -> str:
    try:
        return str(response.json().get("message", response.text))
    except ValueError:
        return response.text


class FixtureClient:
    """Serves weather from a local JSON file, useful for development."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def fetch(self) -> WeatherData:
        try:
            with self.path.open(encoding="utf-8") as f:
                return parse_weather(json.load(f))
        except (OSError, ValueError) as e:
            raise WeatherError(f"Cannot load fixture {self.path}: {e}") from e


class WeatherStore:
    """Thread-safe holder for the latest weather snapshot."""

    def __init__(self, initial: WeatherData | None = None) -> None:
        self._lock = threading.Lock()
        self._data = initial or WeatherData(last_updated=_timestamp())

    def get(self) -> WeatherData:
        with self._lock:
            return self._data

    def update(self, client: WeatherClient | FixtureClient) -> WeatherData:
        """Fetch fresh data, keeping the previous snapshot (flagged) on failure."""
        try:
            data = client.fetch()
        except WeatherError as e:
            logger.error("%s", e)
            with self._lock:
                self._data = self._data.with_error(str(e))
                return self._data
        with self._lock:
            self._data = data
            return data


def start_updater(
    store: WeatherStore,
    client: WeatherClient | FixtureClient,
    interval: float,
    stop_event: threading.Event,
) -> threading.Thread:
    """Refresh ``store`` every ``interval`` seconds in a daemon thread."""

    def run() -> None:
        while not stop_event.is_set():
            store.update(client)
            stop_event.wait(interval)

    thread = threading.Thread(target=run, name="weather-updater", daemon=True)
    thread.start()
    return thread
