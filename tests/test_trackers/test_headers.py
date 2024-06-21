from datetime import datetime, timezone

import pytest

from toggl_api import TrackerBody


@pytest.mark.unit()
def test_format_body(get_workspace_id):
    body = TrackerBody(get_workspace_id)
    assert isinstance(body.format_body(get_workspace_id), dict)


@pytest.mark.unit()
def test_start_date(get_workspace_id):
    d = datetime.now(tz=timezone.utc)
    body = TrackerBody(get_workspace_id, start=d)
    b_format = body.format_body(get_workspace_id)
    assert isinstance(b_format["start"], str)
    assert b_format.get("start_date") is None
    body.start_date = d.date()
    b_format = body.format_body(get_workspace_id)
    assert b_format.get("start_date") is None
    body.start = None
    b_format = body.format_body(get_workspace_id)
    assert b_format.get("start") is None
    assert isinstance(b_format["start_date"], str)


@pytest.mark.unit()
def test_tags(get_workspace_id):
    tags = ["tag1", "tag2"]
    body = TrackerBody(get_workspace_id, tags=tags)
    b_format = body.format_body(get_workspace_id)
    assert b_format.get("tags") == tags
    assert b_format.get("tag_ids") is None
    assert b_format.get("tag_action") is None

    body.tag_ids = [1, 2]
    body.tag_action = "add"
    b_format = body.format_body(get_workspace_id)
    assert b_format.get("tags") == tags
    assert b_format.get("tag_ids") == [1, 2]
    assert b_format.get("tag_action") == "add"

    body.tag_ids = []
    body.tags = []
    body.tag_action = None
    b_format = body.format_body(get_workspace_id)
    assert b_format.get("tags") is None
    assert b_format.get("tag_ids") is None
    assert b_format.get("tag_action") is None

    body = TrackerBody(get_workspace_id, tags=tags)
    body.tag_action = "remove"

    b_format = body.format_body(get_workspace_id)
    assert b_format.get("tags") == tags
    assert b_format.get("tag_ids") is None
    assert b_format.get("tag_action") == "remove"


@pytest.mark.integration()
def test_body_usage(tracker_object, user_object, create_body):
    assert True
