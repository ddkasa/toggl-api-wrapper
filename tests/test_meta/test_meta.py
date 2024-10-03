import httpx
import pytest

from toggl_api.modules.meta import RequestMethod
from toggl_api.modules.meta.base_endpoint import TogglEndpoint
from toggl_api.modules.models import TogglTracker


@pytest.mark.integration
def test_api_status():
    assert isinstance(TogglEndpoint.api_status(), bool)


@pytest.mark.unit
def test_headers(meta_object):
    assert {"content-type": "application/json"} == meta_object.HEADERS


@pytest.mark.unit
@pytest.mark.parametrize(
    ("method", "expected"),
    [
        (RequestMethod.GET, httpx.Client().get),
        (RequestMethod.POST, httpx.Client().post),
        (RequestMethod.PUT, httpx.Client().put),
        (RequestMethod.DELETE, httpx.Client().delete),
        (RequestMethod.PATCH, httpx.Client().patch),
    ],
)
def test_get_method(meta_object, method, expected):
    method = meta_object.method(method)
    assert method.__name__ == expected.__name__
    assert method.__class__ == expected.__class__


@pytest.mark.unit
def test_model_parameter(meta_object):
    assert meta_object.model == TogglTracker


@pytest.mark.unit
def test_endpoint(meta_object):
    assert isinstance(meta_object.endpoint, str)


@pytest.mark.unit
def test_process_models(meta_object, get_test_data, meta_object_sqlite):
    models = [meta_object.model.from_kwargs(**i) for i in get_test_data]
    assert meta_object.process_models(get_test_data) == models
    assert all(isinstance(model, meta_object.model) for model in models)
    assert meta_object_sqlite.process_models(get_test_data) == models
    assert all(isinstance(model, meta_object_sqlite.model) for model in models)
