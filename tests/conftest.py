import os

# Let pygame run without a real display or audio device.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import json

import pytest

from raspi_openweather.config import ASSETS_DIR

FIXTURE_PATH = ASSETS_DIR / "fixtures" / "weather.json"


@pytest.fixture
def api_payload():
    with FIXTURE_PATH.open() as f:
        return json.load(f)
