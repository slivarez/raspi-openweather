"""Pure presentation helpers, independent of pygame."""

from __future__ import annotations

import time

DEGREE = "\N{DEGREE SIGN}"

# Hours (local time) considered daytime for the background image.
DAY_START_HOUR = 6
DAY_END_HOUR = 18


def mps_to_kmph(mps: float) -> float:
    """Convert metres per second to kilometres per hour."""
    return round(3.6 * mps, 1)


def format_wind(speed: float, wind_unit: str, temp_unit: str) -> str:
    """Format wind speed as reported by the API for the given unit system.

    The API returns m/s for metric and standard units, and mph for imperial.
    """
    if temp_unit == "imperial":
        return f"Wind: {speed} mph"
    if wind_unit == "mps":
        return f"Wind: {speed} m/s"
    return f"Wind: {mps_to_kmph(speed)} km/h"


def format_clock_time(timestamp: float) -> str:
    """Format a Unix timestamp as local HH:MM, or "--:--" when unknown."""
    if not timestamp:
        return "--:--"
    return time.strftime("%H:%M", time.localtime(timestamp))


def is_night(now: time.struct_time) -> bool:
    return now.tm_hour < DAY_START_HOUR or now.tm_hour > DAY_END_HOUR


def background_file(now: time.struct_time) -> str:
    return "background_night.jpg" if is_night(now) else "background_day.jpg"


def is_exit_click(pos: tuple[int, int], size: tuple[int, int]) -> bool:
    """Whether a click landed in the exit area in the upper right corner."""
    x, y = pos
    width, height = size
    return int(width * 0.8) < x < width and 20 < y < int(height * 0.2)
