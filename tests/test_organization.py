import sys
import time
from string import ascii_lowercase

import pytest

from toggl_api import OrganizationEndpoint, TogglOrganization


@pytest.fixture
def org_object(config_setup, get_json_cache):
    return OrganizationEndpoint(config_setup, get_json_cache)


@pytest.mark.unit
def test_model(faker, number):
    name = faker.name()
    mid = number.randint(5, sys.maxsize)
    model = TogglOrganization(mid, name)

    assert model.id == mid
    assert name == model.name


@pytest.mark.integration
def test_collect_org(org_object: OrganizationEndpoint):
    collection = org_object.collect(refresh=True)
    assert isinstance(collection, list)

    collection = org_object.collect()
    assert isinstance(collection, list)


@pytest.mark.integration
def test_get_org(org_object: OrganizationEndpoint, organization_id, request):
    org = org_object.get(organization_id, refresh=True)
    assert isinstance(org, TogglOrganization)
    assert org.id == organization_id
    assert org.name == "Do-Not-Delete"

    org = org_object.get(org)
    assert isinstance(org, TogglOrganization)
    assert org.id == organization_id
    assert org.name == "Do-Not-Delete"


@pytest.mark.integration
@pytest.mark.dependency
def test_add_org(org_object: OrganizationEndpoint, faker, request, number):
    name = "".join(number.choices(ascii_lowercase, k=number.randint(141, 300)))
    with pytest.raises(ValueError, match="Max organization name length is 140!"):
        org_object.add(name)

    name = faker.name().replace(" ", "-")
    org = org_object.add(name)
    assert isinstance(org, TogglOrganization)
    assert org.name == name

    request.config.cache.set("org", {"name": org.name, "id": org.id})


# NOTE: Orgs might take a bit to create so reruns are enabled.
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.dependency(depends=["test_add_org"])
@pytest.mark.flaky(rerun_except="httpx.HTTPStatusError", reruns=5)
def test_edit_org(org_object: OrganizationEndpoint, faker, request):
    cache = request.config.cache.get("org", {})
    with pytest.raises(ValueError, match="The organization name need at least have one letter!"):
        org_object.edit(cache["id"], "")
    name = faker.name().replace("", "-")

    time.sleep(10)

    edit = org_object.edit(cache["id"], name)
    assert isinstance(edit, TogglOrganization)
    assert edit.name == name
    request.config.cache.set("org", {"name": edit.name, "id": edit.id})


# NOTE: API can be slow in deleting the organization so reruns are enabled.
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.dependency(depends=["test_edit_org"])
@pytest.mark.flaky(only_rerun=["AssertionError", "httpx.HTTPStatusError"], reruns=5)
def test_delete_org(org_object: OrganizationEndpoint, faker, request):
    cache = request.config.cache.get("org", {})
    org_object.delete(cache["id"])
    time.sleep(10)
    assert org_object.get(cache["id"], refresh=True) is None
