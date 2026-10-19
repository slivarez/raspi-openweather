import threading
from unittest import mock

import pytest
import requests

from raspi_openweather.config import Settings
from raspi_openweather.weather import (
    API_URL,
    FixtureClient,
    WeatherClient,
    WeatherData,
    WeatherError,
    WeatherStore,
    parse_weather,
    start_updater,
)

from .conftest import FIXTURE_PATH


def make_response(status=200, payload=None, text=""):
    response = mock.Mock(spec=requests.Response)
    response.status_code = status
    response.ok = 200 <= status < 400
    response.text = text
    if isinstance(payload, Exception):
        response.json.side_effect = payload
    else:
        response.json.return_value = payload
    return response


def make_client(*responses, max_retries=3):
    session = mock.Mock(spec=requests.Session)
    session.get.side_effect = list(responses)
    sleep = mock.Mock()
    settings = Settings(api_key="key", lat="1", lon="2", temp_unit="imperial")
    client = WeatherClient(settings, session, max_retries=max_retries, retry_delay=10, sleep=sleep)
    return client, session, sleep


class TestParseWeather:
    def test_full_payload(self, api_payload):
        data = parse_weather(api_payload, last_updated="now")
        assert data == WeatherData(
            name="Berlin",
            temp=23.2,
            feels_like=23.4,
            humidity=69,
            temp_min=22.8,
            temp_max=24.6,
            description="Clear",
            icon="01d",
            wind_speed=2.68,
            sunrise=1758257237,
            sunset=1758301988,
            last_updated="now",
        )

    def test_empty_payload_uses_defaults(self):
        data = parse_weather({}, last_updated="now")
        assert data == WeatherData(last_updated="now")

    def test_empty_weather_list(self, api_payload):
        api_payload["weather"] = []
        data = parse_weather(api_payload)
        assert (data.description, data.icon) == ("N/A", "01d")

    def test_sets_last_updated(self, api_payload):
        assert parse_weather(api_payload).last_updated


class TestWeatherClient:
    def test_success(self, api_payload):
        client, session, sleep = make_client(make_response(payload=api_payload))
        data = client.fetch()
        assert data.name == "Berlin"
        session.get.assert_called_once_with(
            API_URL,
            params={"appid": "key", "lat": "1", "lon": "2", "units": "imperial"},
            timeout=5,
        )
        sleep.assert_not_called()

    def test_retries_network_errors_with_backoff(self, api_payload):
        client, session, sleep = make_client(
            requests.ConnectionError("down"),
            requests.Timeout("slow"),
            make_response(payload=api_payload),
        )
        assert client.fetch().name == "Berlin"
        assert session.get.call_count == 3
        assert sleep.call_args_list == [mock.call(10), mock.call(20)]

    def test_gives_up_after_max_retries(self):
        client, session, sleep = make_client(*[requests.ConnectionError("down")] * 3)
        with pytest.raises(WeatherError, match=r"after 3 attempts.*down"):
            client.fetch()
        assert session.get.call_count == 3
        # No pointless sleep after the final attempt
        assert sleep.call_count == 2

    def test_http_error_is_not_retried(self):
        client, session, _ = make_client(
            make_response(status=401, payload={"cod": 401, "message": "Invalid API key"})
        )
        with pytest.raises(WeatherError, match="ERROR: 401 Invalid API key"):
            client.fetch()
        session.get.assert_called_once()

    def test_http_error_without_json_body(self):
        client, _, _ = make_client(
            make_response(status=502, payload=ValueError("no json"), text="Bad Gateway")
        )
        with pytest.raises(WeatherError, match="ERROR: 502 Bad Gateway"):
            client.fetch()

    def test_invalid_json(self):
        client, _, _ = make_client(make_response(payload=ValueError("garbage")))
        with pytest.raises(WeatherError, match="invalid JSON"):
            client.fetch()


class TestFixtureClient:
    def test_loads_fixture(self):
        assert FixtureClient(FIXTURE_PATH).fetch().name == "Berlin"

    def test_missing_fixture(self, tmp_path):
        with pytest.raises(WeatherError, match="Cannot load fixture"):
            FixtureClient(tmp_path / "missing.json").fetch()

    def test_invalid_fixture(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{oops")
        with pytest.raises(WeatherError):
            FixtureClient(path).fetch()


class TestWeatherStore:
    def test_initial_placeholder(self):
        data = WeatherStore().get()
        assert data.name == "Unknown"
        assert data.last_updated
        assert not data.error

    def test_update_success(self):
        client = mock.Mock()
        client.fetch.return_value = WeatherData(name="Berlin")
        store = WeatherStore()
        assert store.update(client).name == "Berlin"
        assert store.get().name == "Berlin"

    def test_update_failure_keeps_previous_data(self):
        client = mock.Mock()
        client.fetch.side_effect = [WeatherData(name="Berlin", temp=20), WeatherError("boom")]
        store = WeatherStore()
        store.update(client)
        store.update(client)
        data = store.get()
        assert (data.name, data.temp, data.error) == ("Berlin", 20, "boom")

    def test_success_clears_error(self):
        client = mock.Mock()
        client.fetch.side_effect = [WeatherError("boom"), WeatherData(name="Berlin")]
        store = WeatherStore()
        store.update(client)
        assert store.get().error == "boom"
        store.update(client)
        assert store.get().error == ""


def test_start_updater_refreshes_until_stopped():
    fetched = threading.Event()
    client = mock.Mock()

    def fetch():
        fetched.set()
        return WeatherData(name="Berlin")

    client.fetch.side_effect = fetch
    store = WeatherStore()
    stop = threading.Event()
    thread = start_updater(store, client, interval=60, stop_event=stop)
    assert fetched.wait(timeout=5)
    stop.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert thread.daemon
    assert store.get().name == "Berlin"
    client.fetch.assert_called_once()
