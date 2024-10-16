from datetime import date, datetime, timezone

import pytest

from toggl_api.utility import format_iso, get_workspace, parse_iso, requires


@pytest.mark.unit
def test_format_iso():
    iso = format_iso(datetime.now(tz=timezone.utc))
    assert isinstance(iso, str)
    assert isinstance(format_iso(iso), str)
    assert isinstance(format_iso(date.today()), str)  # noqa: DTZ011


@pytest.mark.unit
def test_parse_iso():
    iso = parse_iso("2020-01-01T01:01:01Z")
    assert isinstance(iso, datetime)
    assert (
        datetime(
            year=2020,
            month=1,
            day=1,
            hour=1,
            minute=1,
            second=1,
            tzinfo=timezone.utc,
        )
        == iso
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("data", "result"),
    [
        ({"wid": 1}, 1),
        ({"workspace_id": 25}, 25),
        ({"workspace_id": 25, "wid": 1}, 25),
        ({}, KeyError),
    ],
)
def test_get_workspace(data, result):
    if type(result) is type and issubclass(result, Exception):
        with pytest.raises(result) as excinfo:
            get_workspace(data)
        assert isinstance(excinfo.value, result)
    else:
        assert get_workspace(data) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    "module",
    [
        "sqlalchemy",
        pytest.param("numpy", marks=pytest.mark.xfail(ImportError, reason="NumPy is not a required dependency.")),
        "httpx",
    ],
)
def test_requires_decorator(module, monkeypatch):
    @requires(module)
    def test(a):
        return a

    assert test(module) == module
