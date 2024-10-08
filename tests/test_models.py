from dataclasses import fields

import pytest

from toggl_api.models import as_dict_custom


@pytest.mark.unit
def test_etters(model_data):
    for model in model_data.values():
        flds = fields(model)
        for fld in flds:
            assert model[fld.name] == getattr(model, fld.name)


@pytest.mark.unit
def test_as_dict_custom(model_data):
    for model in model_data.values():
        assert isinstance(as_dict_custom(model), dict)
