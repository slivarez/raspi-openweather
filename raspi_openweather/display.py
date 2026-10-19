"""Rendering of weather data on the screen using pygame."""

from __future__ import annotations

import time
from pathlib import Path

import pygame

from raspi_openweather.config import ASSETS_DIR, Settings
from raspi_openweather.formatting import (
    DEGREE,
    background_file,
    format_clock_time,
    format_wind,
)
from raspi_openweather.weather import DEFAULT_ICON, WeatherData

SCREEN_SIZE = (800, 480)

CYAN = (50, 255, 255)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Vertical layout of the label rows
ROW_BASE = 164
ROW_STEP = 35


class Display:
    """Draws the weather dashboard onto a pygame surface."""

    def __init__(
        self,
        screen: pygame.Surface,
        settings: Settings,
        assets_dir: Path = ASSETS_DIR,
    ) -> None:
        self.screen = screen
        self.settings = settings
        self.assets_dir = assets_dir
        self.small_font = pygame.font.SysFont("sans", 18, bold=False)
        self.medium_font = pygame.font.SysFont("sans", 24, bold=True)
        self.medium2_font = pygame.font.SysFont("sans", 29, bold=True)
        self.large_font = pygame.font.SysFont("sans", 40, bold=True)
        self.xlarge_font = pygame.font.SysFont("sans", 80, bold=True)
        self._images: dict[str, pygame.Surface] = {}

    def _image(self, name: str) -> pygame.Surface:
        """Load an image from the assets directory, caching it for later frames."""
        if name not in self._images:
            self._images[name] = pygame.image.load(str(self.assets_dir / name))
        return self._images[name]

    def _icon(self, icon: str) -> pygame.Surface:
        try:
            return self._image(f"icons/{icon}.png")
        except (pygame.error, FileNotFoundError):
            return self._image(f"icons/{DEFAULT_ICON}.png")

    def _text(self, font: pygame.font.Font, text: str, color, pos: tuple[int, int]) -> None:
        self.screen.blit(font.render(text, True, color), pos)

    def render(self, weather: WeatherData, now: time.struct_time | None = None) -> None:
        """Draw a complete frame (without flipping the display)."""
        now = now or time.localtime()
        height = self.screen.get_height()
        icon = self._icon(weather.icon)

        self.screen.blit(self._image(background_file(now)), (0, 0))

        # Header: date and clock
        date_str = time.strftime("%a, %b %d (%d.%m.%Y)", now)
        self._text(self.medium2_font, date_str, WHITE, (13, 23))
        self._text(self.large_font, time.strftime("%H:%M", now), WHITE, (645, 13))
        self._text(self.small_font, time.strftime("%S", now), WHITE, (750, 13))

        # Current weather (left column)
        self.screen.blit(icon, (280, 60))
        self._text(self.small_font, weather.description, WHITE, (300, 140))
        self._text(self.xlarge_font, f"{weather.temp}{DEGREE}", CYAN, (40, 80))
        self._text(self.medium_font, weather.name, CYAN, (40, ROW_BASE))
        self._text(
            self.medium_font, f"Humidity {weather.humidity}%", WHITE, (40, ROW_BASE + ROW_STEP)
        )
        self._text(
            self.medium_font,
            f"Feels like: {weather.feels_like}{DEGREE}",
            WHITE,
            (40, ROW_BASE + 2 * ROW_STEP),
        )

        # Today (right column)
        self._text(self.medium2_font, "Today", GREEN, (421, 80))
        self._text(self.small_font, weather.description, WHITE, (720, 140))
        self.screen.blit(icon, (700, 60))
        rows = [
            f"Temp: {weather.temp_max}{DEGREE} / {weather.temp_min}{DEGREE}",
            format_wind(weather.wind_speed, self.settings.wind_unit, self.settings.temp_unit),
            f"Sunrise: {format_clock_time(weather.sunrise)}",
            f"Sunset: {format_clock_time(weather.sunset)}",
        ]
        for i, row in enumerate(rows, start=-1):
            self._text(self.medium_font, row, WHITE, (421, ROW_BASE + i * ROW_STEP))

        # Separators
        pygame.draw.line(self.screen, WHITE, (0, 53), (800, 53))
        pygame.draw.line(self.screen, WHITE, (400, 69), (400, 270))

        # Footer: status
        if weather.error:
            self._text(self.small_font, weather.error, RED, (10, height - 70))
        if weather.last_updated:
            self._text(
                self.small_font, f"Last updated: {weather.last_updated}", WHITE, (10, height - 30)
            )
