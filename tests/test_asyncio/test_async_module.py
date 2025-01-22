import importlib
import sys
from unittest import mock

import pytest


@pytest.mark.unit
@pytest.mark.parametrize(
    "module",
    [
        "sqlalchemy",
        "greenlet",
    ],
)
def test_module_reqs(module):
    with mock.patch.dict(sys.modules):
        sys.modules[module] = None

        with pytest.raises(SystemExit):  # noqa: PT012
            if "toggl_api.asyncio" in sys.modules:
                importlib.reload(sys.modules["toggl_api.asyncio"])
            else:
                importlib.import_module("toggl_api.asyncio")  # pragma: no cover
