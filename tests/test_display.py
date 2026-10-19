import time

import pygame
import pytest

from raspi_openweather.config import Settings
from raspi_openweather.display import SCREEN_SIZE, WHITE, Display
from raspi_openweather.weather import WeatherData

NOON = time.struct_time((2025, 9, 20, 12, 0, 0, 5, 263, -1))


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.Surface(SCREEN_SIZE)
    yield surface
    pygame.quit()


@pytest.fixture
def display(screen):
    return Display(screen, Settings())


def test_render_full_frame(display, screen):
    display.render(WeatherData(name="Berlin", temp=21.5, last_updated="now"), NOON)
    # Horizontal separator line is drawn across the top
    assert screen.get_at((400, 53))[:3] == WHITE


def test_render_with_error(display, screen):
    display.render(WeatherData(error="ERROR: 401 Invalid API key"), NOON)


def test_unknown_icon_falls_back_to_default(display):
    assert display._icon("does-not-exist") is display._icon("01d")


def test_images_are_cached(display):
    assert display._image("background_day.jpg") is display._image("background_day.jpg")


@pytest.mark.parametrize("temp_unit", ["metric", "imperial", "standard"])
def test_render_for_each_unit(screen, temp_unit):
    Display(screen, Settings(temp_unit=temp_unit)).render(WeatherData(), NOON)
