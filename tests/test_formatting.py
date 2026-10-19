import time

import pytest

from raspi_openweather.formatting import (
    background_file,
    format_clock_time,
    format_wind,
    is_exit_click,
    is_night,
    mps_to_kmph,
)


def at_hour(hour):
    return time.struct_time((2025, 9, 20, hour, 0, 0, 5, 263, -1))


@pytest.mark.parametrize(("mps", "kmph"), [(0, 0), (1, 3.6), (2.68, 9.6), (10, 36)])
def test_mps_to_kmph(mps, kmph):
    assert mps_to_kmph(mps) == kmph


@pytest.mark.parametrize(
    ("wind_unit", "temp_unit", "expected"),
    [
        ("kmph", "metric", "Wind: 9.6 km/h"),
        ("mps", "metric", "Wind: 2.68 m/s"),
        ("kmph", "standard", "Wind: 9.6 km/h"),
        ("kmph", "imperial", "Wind: 2.68 mph"),
        ("mps", "imperial", "Wind: 2.68 mph"),
    ],
)
def test_format_wind(wind_unit, temp_unit, expected):
    assert format_wind(2.68, wind_unit, temp_unit) == expected


def test_format_clock_time():
    ts = time.mktime((2025, 9, 20, 7, 5, 0, 0, 0, -1))
    assert format_clock_time(ts) == "07:05"


def test_format_clock_time_unknown():
    assert format_clock_time(0) == "--:--"


@pytest.mark.parametrize(
    ("hour", "night"), [(0, True), (5, True), (6, False), (12, False), (18, False), (19, True)]
)
def test_is_night(hour, night):
    assert is_night(at_hour(hour)) is night


def test_background_file():
    assert background_file(at_hour(12)) == "background_day.jpg"
    assert background_file(at_hour(22)) == "background_night.jpg"


@pytest.mark.parametrize(
    ("pos", "expected"),
    [
        ((700, 50), True),
        ((799, 21), True),
        ((640, 50), False),  # too far left
        ((700, 10), False),  # too high
        ((700, 96), False),  # too low
        ((100, 300), False),
    ],
)
def test_is_exit_click(pos, expected):
    assert is_exit_click(pos, (800, 480)) is expected
