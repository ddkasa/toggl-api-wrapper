from datetime import datetime, timedelta, timezone

import pytest

from toggl_api import TrackerBody


@pytest.mark.unit
def test_format_body(get_workspace_id):
    body = TrackerBody(get_workspace_id)
    assert isinstance(body.format("add", workspace_id=get_workspace_id), dict)


@pytest.mark.unit
def test_start_time(get_workspace_id):
    d = datetime.now(tz=timezone.utc)
    body = TrackerBody(start=d)
    b_format = body.format("add", workspace_id=get_workspace_id)
    assert isinstance(b_format["start"], str)


@pytest.mark.unit
def test_tags(get_workspace_id):
    tags = ["tag1", "tag2"]
    body = TrackerBody(get_workspace_id, tags=tags)
    b_format = body.format("add", workspace_id=get_workspace_id)
    assert b_format.get("tags") == tags
    assert b_format.get("tag_ids") is None
    assert b_format.get("tag_action") is None

    body.tag_ids = [1, 2]
    body.tag_action = "add"
    b_format = body.format("add", workspace_id=get_workspace_id)
    assert b_format.get("tags") == tags
    assert b_format.get("tag_ids") == [1, 2]
    assert b_format.get("tag_action") == "add"

    body.tag_ids = []
    body.tags = []
    body.tag_action = None
    b_format = body.format("add", workspace_id=get_workspace_id)
    assert b_format.get("tags") is None
    assert b_format.get("tag_ids") is None
    assert b_format.get("tag_action") is None

    body = TrackerBody("add", tags=tags)
    body.tag_action = "remove"

    b_format = body.format("add", workspace_id=get_workspace_id)
    assert b_format.get("tags") == tags
    assert b_format.get("tag_ids") is None
    assert b_format.get("tag_action") == "remove"


@pytest.mark.unit
def test_tracker_body_iter(faker):
    body = TrackerBody(faker.name(), tags=[faker.name()])
    assert body.format("") == {**body}

    body["description"] = (name := faker.name())
    assert body.description == name

    del body["description"]
    assert body.description is None

    del body["tags"]
    assert body.tags == []


@pytest.mark.unit
def test_timedelta_conversion(number):
    body = TrackerBody(duration=timedelta(seconds=(value := number.randint(50, 200))))

    fmt = body.format("add")
    assert fmt["duration"] == value
