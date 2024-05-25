from dataclasses import fields

import pytest

from toggl_api.modules.models import TogglClass, TogglClient, TogglProject, TogglTag, TogglTracker, TogglWorkspace


class ModelTest(TogglClass):
    def from_kwargs(self, **kwargs) -> TogglClass:
        return self(
            id=kwargs["id"],
            name=kwargs["name"],
        )


@pytest.fixture(scope="module")
def model_data(get_workspace_id):
    workspace = TogglWorkspace(get_workspace_id, "test_workspace")

    client = TogglClient(1, "test_client", workspace)
    project = TogglProject(
        1,
        "test_project",
        workspace,
        color="#000000",
        client=client,
        active=True,
    )
    tag = TogglTag(1, "test_tag", workspace)
    return {
        "workspace": workspace,
        "model": ModelTest(1, "test_model"),
        "client": client,
        "project": project,
        "track": TogglTracker(
            1,
            "test_tracker",
            workspace,
            start="2020-01-01T00:00:00Z",
            duration=3600,
            stop="2020-01-01T01:00:00Z",
            project=project,
            tags=[tag],
        ),
        "tag": tag,
    }


@pytest.mark.unit()
def test_etters(model_data: TogglClass):
    for model in model_data.values():
        flds = fields(model)
        for fld in flds:
            assert model[fld.name] == getattr(model, fld.name)
