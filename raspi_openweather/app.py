"""Command line entry point and main loop."""

from __future__ import annotations

import argparse
import logging
import threading
from collections.abc import Sequence
from pathlib import Path

import pygame

from raspi_openweather.config import ASSETS_DIR, DEFAULT_CONFIG_PATH, ConfigError, load_settings
from raspi_openweather.display import SCREEN_SIZE, Display
from raspi_openweather.formatting import is_exit_click
from raspi_openweather.weather import FixtureClient, WeatherClient, WeatherStore, start_updater

logger = logging.getLogger(__name__)

FPS = 3
WEATHER_REFRESH_INTERVAL = 900  # seconds
DEFAULT_FIXTURE = ASSETS_DIR / "fixtures" / "weather.json"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Full-screen OpenWeatherMap display.")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="path to the JSON config file (default: %(default)s)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="verbose logging and weather data from a local fixture instead of the API",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="fixture used with --debug (default: %(default)s)",
    )
    parser.add_argument(
        "--windowed", action="store_true", help="run in a window instead of full screen"
    )
    parser.add_argument(
        "--refresh-interval",
        type=float,
        default=WEATHER_REFRESH_INTERVAL,
        help="seconds between weather updates (default: %(default)s)",
    )
    return parser.parse_args(argv)


def should_quit(event: pygame.event.Event, size: tuple[int, int]) -> bool:
    """Whether an input event asks the application to exit."""
    if event.type == pygame.QUIT:
        return True
    if event.type == pygame.KEYDOWN:
        return event.key == pygame.K_ESCAPE
    if event.type == pygame.MOUSEBUTTONDOWN:
        logger.debug("Click at %s", event.pos)
        return is_exit_click(event.pos, size)
    return False


def run(display: Display, store: WeatherStore, fps: int = FPS) -> None:
    """Render frames until the user exits."""
    clock = pygame.time.Clock()
    size = display.screen.get_size()
    while True:
        if any(should_quit(event, size) for event in pygame.event.get()):
            return
        display.render(store.get())
        pygame.display.flip()
        clock.tick(fps)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        settings = load_settings(args.config)
    except ConfigError as e:
        logger.error("%s", e)
        return 1
    logger.debug("Settings: %s", settings)

    if args.debug:
        logger.info("Debug mode: loading weather data from %s", args.fixture)
        client = FixtureClient(args.fixture)
    else:
        client = WeatherClient(settings)

    store = WeatherStore()
    stop_event = threading.Event()
    start_updater(store, client, args.refresh_interval, stop_event)

    # Only the subsystems we need; full pygame.init() would also start audio.
    pygame.display.init()
    pygame.font.init()
    try:
        flags = 0 if args.windowed else pygame.FULLSCREEN
        screen = pygame.display.set_mode(SCREEN_SIZE, flags)
        run(Display(screen, settings), store)
    finally:
        stop_event.set()
        pygame.quit()
    return 0
