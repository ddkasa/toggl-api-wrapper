from dataclasses import dataclass, field

import pytest

from toggl_api import TogglTracker
from toggl_api.meta import BaseBody, TogglEndpoint


@pytest.mark.unit
@pytest.mark.parametrize(
    ("body", "status_code", "expected"),
    [
        ({"status": "OK"}, 200, True),
        (None, 401, False),
        (None, 501, False),
    ],
)
def test_api_status(body, status_code, expected, httpx_mock):
    httpx_mock.add_response(json=body, status_code=status_code)
    assert TogglEndpoint.api_status() is expected


@pytest.mark.unit
def test_headers(meta_object):
    assert meta_object.HEADERS == {"content-type": "application/json"}


@pytest.mark.unit
def test_model_parameter(meta_object):
    assert meta_object.MODEL is TogglTracker


@pytest.mark.unit
def test_process_models(meta_object, get_test_data, meta_object_sqlite):
    models = [meta_object.MODEL.from_kwargs(**i) for i in get_test_data]
    assert meta_object.process_models(get_test_data) == models
    assert all(isinstance(model, meta_object.MODEL) for model in models)
    assert meta_object_sqlite.process_models(get_test_data) == models
    assert all(isinstance(model, meta_object_sqlite.MODEL) for model in models)


@dataclass()
class BodyTest(BaseBody):
    parameter: str = field(metadata={"endpoints": frozenset(("generic_endpoint",))})


@pytest.mark.parametrize(
    ("parameter", "endpoint", "expected"),
    [
        ("parameter", "generic_endpoint", True),
        pytest.param(
            "random_parameter",
            "wdwad",
            False,
            marks=pytest.mark.xfail(
                reason="Raises KeyError if parameter is not found.",
                raises=KeyError,
            ),
        ),
        ("parameter", "generic_endpoint_two", False),
    ],
)
@pytest.mark.unit
def test_base_body(parameter, endpoint, expected):
    assert BodyTest._verify_endpoint_parameter(parameter, endpoint) is expected  # noqa: SLF001
