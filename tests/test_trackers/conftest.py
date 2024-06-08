from datetime import datetime, timedelta, timezone

import pytest

from toggl_api import TrackerBody


@pytest.fixture(scope="module")
def create_body(get_workspace_id, faker):
    start = datetime.now(tz=timezone.utc)
    delta = timedelta(hours=1)
    return TrackerBody(
        get_workspace_id,
        faker.sentence(nb_words=3),
        project_id=1,
        start=datetime.now(tz=timezone.utc) - delta,
        duration=delta,
        stop=start + delta,
        tags=[faker.word() for _ in range(3)],
    )
