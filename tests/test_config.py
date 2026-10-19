import json

import pytest

from raspi_openweather.config import ConfigError, Settings, load_settings


def write_config(tmp_path, data):
    path = tmp_path / "open_weather.json"
    path.write_text(json.dumps(data) if not isinstance(data, str) else data)
    return path


def test_defaults():
    settings = Settings()
    assert settings.temp_unit == "metric"
    assert settings.wind_unit == "kmph"


def test_load_overrides_defaults(tmp_path):
    path = write_config(tmp_path, {"api_key": "secret", "lat": "1.0", "lon": "2.0"})
    settings = load_settings(path)
    assert settings.api_key == "secret"
    assert (settings.lat, settings.lon) == ("1.0", "2.0")
    assert settings.temp_unit == "metric"


def test_unknown_keys_are_ignored(tmp_path, caplog):
    path = write_config(tmp_path, {"api_key": "secret", "colour": "blue"})
    settings = load_settings(path)
    assert settings.api_key == "secret"
    assert "colour" in caplog.text


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_settings(tmp_path / "missing.json")


def test_invalid_json(tmp_path):
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_settings(write_config(tmp_path, "{not json"))


def test_non_object_json(tmp_path):
    with pytest.raises(ConfigError, match="JSON object"):
        load_settings(write_config(tmp_path, [1, 2]))


@pytest.mark.parametrize("key", ["temp_unit", "wind_unit"])
def test_invalid_units(tmp_path, key):
    with pytest.raises(ConfigError, match=key):
        load_settings(write_config(tmp_path, {key: "furlongs"}))
