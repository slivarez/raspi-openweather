"""Application settings and configuration loading."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

#: Directory holding icons, backgrounds and fixtures (the repository root).
ASSETS_DIR = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG_PATH = Path("open_weather.json")

TEMP_UNITS = ("metric", "imperial", "standard")
WIND_UNITS = ("kmph", "mps")


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """User-configurable settings, overridable from the JSON config file."""

    api_key: str = "PUT_YOUR_API_KEY_HERE_OR_MODIFY_JSON_CONFIG"
    lat: str = "52.5244"  # Berlin
    lon: str = "13.4105"  # Berlin
    wind_unit: str = "kmph"  # kmph (km/h) or mps (m/s); ignored for imperial
    temp_unit: str = "metric"  # metric, imperial or standard (Kelvin)

    def __post_init__(self) -> None:
        if self.temp_unit not in TEMP_UNITS:
            raise ConfigError(f"Invalid temp_unit {self.temp_unit!r}, expected one of {TEMP_UNITS}")
        if self.wind_unit not in WIND_UNITS:
            raise ConfigError(f"Invalid wind_unit {self.wind_unit!r}, expected one of {WIND_UNITS}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        """Build settings from a mapping, ignoring (and logging) unknown keys."""
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(data) - known)
        if unknown:
            logger.warning("Ignoring unknown config keys: %s", ", ".join(unknown))
        return replace(cls(), **{k: v for k, v in data.items() if k in known})


def load_settings(path: Path | str = DEFAULT_CONFIG_PATH) -> Settings:
    """Load settings from a JSON file, falling back to defaults for missing keys."""
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise ConfigError(f"Config file {path} not found, see README.md for an example") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file {path} is not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError(f"Config file {path} must contain a JSON object")
    return Settings.from_dict(data)
