from __future__ import annotations

import warnings

from .meta import RequestMethod, TogglCachedEndpoint
from .models import TogglTag


class TagEndpoint(TogglCachedEndpoint):
    def collect(
        self,
        *,
        refresh: bool = False,
    ) -> list[TogglTag]:
        return self.request("", refresh=refresh)  # type: ignore[return-value]

    def get_tags(
        self,
        *,
        refresh: bool = False,
    ) -> list[TogglTag]:
        warnings.warn("Deprecated in favour of 'collect' method.", DeprecationWarning, stacklevel=1)
        return self.collect(refresh=refresh)

    def add(self, name: str) -> TogglTag:
        return self.request(
            "",
            body={"name": name},
            method=RequestMethod.POST,
            refresh=True,
        )  # type: ignore[return-value]

    def create_tag(self, name: str) -> TogglTag:
        warnings.warn("Deprecated in favour of 'add' method.", DeprecationWarning, stacklevel=1)
        return self.add(name)

    def edit(
        self,
        tag: TogglTag,
    ) -> TogglTag:
        """Sets the name of the tag based on the tag object."""
        return self.request(
            f"/{tag.id}",
            body={"name": tag.name},
            method=RequestMethod.PUT,
            refresh=True,
        )  # type: ignore[return-value]

    def update_tag(self, tag: TogglTag) -> TogglTag:
        warnings.warn("Deprecated in favour of 'edit' method.", DeprecationWarning, stacklevel=1)
        return self.edit(tag)

    def delete(self, tag: TogglTag, **kwargs) -> None:
        """Deletes a tag based on its ID."""
        self.request(f"/{tag.id}", method=RequestMethod.DELETE, refresh=True)
        self.cache.delete_entries(tag)
        self.cache.commit()

    def delete_tag(self, tag: TogglTag, **kwargs) -> None:
        warnings.warn("Deprecated in favour of 'delete' method.", DeprecationWarning, stacklevel=1)
        return self.delete(tag, **kwargs)

    @property
    def endpoint(self) -> str:
        return f"workspaces/{self.workspace_id}/tags"

    @property
    def model(self) -> type[TogglTag]:
        return TogglTag
