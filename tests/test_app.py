import json
from pathlib import Path
from unittest import mock

import pygame
import pytest

from raspi_openweather import app
from raspi_openweather.weather import FixtureClient, WeatherClient

SIZE = (800, 480)


def event(type_, **attrs):
    return pygame.event.Event(type_, attrs)


def test_parse_args_defaults():
    args = app.parse_args([])
    assert args.config == Path("open_weather.json")
    assert not args.debug
    assert not args.windowed
    assert args.refresh_interval == app.WEATHER_REFRESH_INTERVAL


def test_parse_args_options():
    args = app.parse_args(["-c", "cfg.json", "--debug", "--windowed", "--refresh-interval", "5"])
    assert args.config == Path("cfg.json")
    assert args.debug and args.windowed
    assert args.refresh_interval == 5


@pytest.mark.parametrize(
    ("evt", "expected"),
    [
        (event(pygame.QUIT), True),
        (event(pygame.KEYDOWN, key=pygame.K_ESCAPE), True),
        (event(pygame.KEYDOWN, key=pygame.K_a), False),
        (event(pygame.MOUSEBUTTONDOWN, pos=(700, 50), button=1), True),
        (event(pygame.MOUSEBUTTONDOWN, pos=(100, 300), button=1), False),
        (event(pygame.MOUSEMOTION, pos=(700, 50)), False),
    ],
)
def test_should_quit(evt, expected):
    assert app.should_quit(evt, SIZE) is expected


@mock.patch.object(pygame.display, "flip")
@mock.patch.object(pygame.event, "get")
def test_run_renders_until_quit(get_events, flip):
    get_events.side_effect = [[], [event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]]
    display = mock.Mock()
    display.screen.get_size.return_value = SIZE
    store = mock.Mock()
    app.run(display, store, fps=1000)
    display.render.assert_called_once_with(store.get.return_value)
    flip.assert_called_once()


def test_main_missing_config(tmp_path, caplog):
    assert app.main(["-c", str(tmp_path / "missing.json")]) == 1
    assert "not found" in caplog.text


@pytest.mark.parametrize(
    ("flag", "client_cls"), [("--debug", FixtureClient), (None, WeatherClient)]
)
@mock.patch.object(app, "run")
@mock.patch.object(app, "start_updater")
def test_main_wires_everything(start_updater, run, tmp_path, flag, client_cls):
    config = tmp_path / "open_weather.json"
    config.write_text(json.dumps({"api_key": "secret"}))
    argv = ["-c", str(config), "--windowed"] + ([flag] if flag else [])
    assert app.main(argv) == 0
    store, client, interval, stop_event = start_updater.call_args.args
    assert isinstance(client, client_cls)
    assert interval == app.WEATHER_REFRESH_INTERVAL
    assert stop_event.is_set()  # updater is told to stop on exit
    run.assert_called_once()
    assert run.call_args.args[1] is store
