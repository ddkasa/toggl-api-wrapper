"""Async report endpoints classes."""

from abc import abstractmethod
from datetime import date
from typing import Any, ClassVar, Literal, cast

from httpx import URL, AsyncClient, BasicAuth, Response

from toggl_api import TogglProject, TogglWorkspace
from toggl_api.meta import RequestMethod
from toggl_api.reports import (
    PaginatedResult,
    PaginationOptions,
    ReportBody,
    ReportFormats,
    _validate_extension,
)
from toggl_api.utility import format_iso

from ._async_endpoint import TogglAsyncEndpoint


class AsyncReportEndpoint(TogglAsyncEndpoint[Any]):
    """Abstract baseclass for the async report endpoints that overrides BASE_ENDPOINT."""

    BASE_ENDPOINT: ClassVar[URL] = URL(
        "https://api.track.toggl.com/reports/api/v3/",
    )

    def __init__(
        self,
        workspace_id: TogglWorkspace | int,
        auth: BasicAuth,
        *,
        client: AsyncClient | None = None,
        timeout: int = 10,
        re_raise: bool = False,
        retries: int = 3,
    ) -> None:
        super().__init__(
            auth,
            client=client,
            timeout=timeout,
            re_raise=re_raise,
            retries=retries,
        )
        self.workspace_id = workspace_id if isinstance(workspace_id, int) else workspace_id.id

    @abstractmethod
    async def search_time_entries(
        self,
        body: ReportBody,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...

    @abstractmethod
    async def export_report(
        self,
        body: ReportBody,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...

    # REFACTOR: More concrete function signatures.


class AsyncSummaryReportEndpoint(AsyncReportEndpoint):
    """Summary reports endpoints.

    [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports)
    """

    async def project_summary(
        self,
        project: TogglProject | int,
        start_date: date | str,
        end_date: date | str,
    ) -> dict[str, int]:
        """Return a specific projects summary within the parameters provided.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-load-project-summary)

        Args:
            project: Project to retrieve summaries about.
            start_date: The date to gather project summary data from.
            end_date: The date to gather project summary data to.

        Returns:
            A list of dictionary with the summary data.
        """
        response = await self.request(
            f"{self.endpoint}/projects/{project.id if isinstance(project, TogglProject) else project}/summary",
            method=RequestMethod.POST,
            body={
                "start_date": format_iso(start_date),
                "end_date": format_iso(end_date),
            },
        )

        return cast("dict[str, int]", response)

    async def project_summaries(
        self,
        start_date: date | str,
        end_date: date | str,
    ) -> list[dict[str, int]]:
        """Return a summary of user projects according to parameters provided.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-list-project-users)

        Args:
            start_date: The date to gather project summaries from.
            end_date: The date to gather project summaries data to.

        Returns:
            A list of dictionary with the summary data.
        """
        response = await self.request(
            f"{self.endpoint}/projects/summary",
            method=RequestMethod.POST,
            body={
                "start_date": format_iso(start_date),
                "end_date": format_iso(end_date),
            },
        )

        return cast("list[dict[str, int]]", response)

    async def search_time_entries(
        self,
        body: ReportBody,
    ) -> list[dict[str, int]]:
        """Return a list of time entries within the parameters specified.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-search-time-entries)

        Args:
            body: Body parameters to filter time entries by.

        Returns:
            A list of dictionaries with the filtered tracker data.
        """
        response = await self.request(
            f"{self.endpoint}/summary/time_entries",
            method=RequestMethod.POST,
            body=body.format(
                "summary_time_entries",
                workspace_id=self.workspace_id,
            ),
        )
        return cast("list[dict[str, int]]", response)

    async def export_report(
        self,
        body: ReportBody,
        extension: ReportFormats,
        *,
        collapse: bool = False,
    ) -> bytes:
        """Download summary report in the specified in the specified format: csv or pdf.

        [Official Documentation](https://engineering.toggl.com/docs/reports/summary_reports#post-export-summary-report)

        Args:
            body: Body parameters to filter the report by.
            extension: What format to use for the report. CSV or PDF.
            collapse: Whether collapse others. Inserted into body.

        Raises:
            InvalidExtensionError: If extension is not pdf or csv.

        Returns:
            A format ready to be saved as a file or used for further processing.
        """
        _validate_extension(extension)

        response = await self.request(
            f"{self.endpoint}/summary/time_entries.{extension}",
            method=RequestMethod.POST,
            body=body.format(
                f"summary_report_{extension}",
                workspace_id=self.workspace_id,
                collapse=collapse,
            ),
            raw=True,
        )

        return cast("Response", response).content

    @property
    def endpoint(self) -> str:
        return f"workspace/{self.workspace_id}"


class AsyncDetailedReportEndpoint(AsyncReportEndpoint):
    """Detailed reports endpoint.

    [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports)
    """

    @staticmethod
    def _paginate(
        request: Response,
        *,
        raw: bool = False,
    ) -> PaginatedResult[Any]:
        return PaginatedResult(
            request.content if raw else request.json(),
            request.headers.get("x-next-id"),
            request.headers.get("x-next-row-number"),
        )

    @staticmethod
    def _paginate_body(
        body: dict[str, Any],
        pagination: PaginationOptions,
    ) -> dict[str, Any]:
        body["page_size"] = pagination.page_size
        if pagination.next_id is not None and pagination.next_row is not None:
            body["first_id"] = pagination.next_id
            body["first_row_number"] = pagination.next_row

        return body

    async def search_time_entries(
        self,
        body: ReportBody,
        pagination: PaginationOptions | None = None,
        *,
        hide_amounts: bool = False,
    ) -> PaginatedResult[list[dict[str, Any]]]:
        """Return time entries for detailed report according to the given filters.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-search-time-entries)

        Args:
            body: JSON body with filters for time entries.
            pagination: Pagination options containing page size, next_id and next_row.
            hide_amounts: Whether amounts should be hidden.

        Returns:
            Data with pagination information if required.
        """
        pagination = pagination or PaginationOptions()

        response = await self.request(
            self.endpoint,
            body=self._paginate_body(
                body.format(
                    "detail_search_time",
                    workspace_id=self.workspace_id,
                    hide_amounts=hide_amounts,
                ),
                pagination,
            ),
            method=RequestMethod.POST,
            raw=True,
        )

        return self._paginate(cast("Response", response))

    async def export_report(
        self,
        body: ReportBody,
        extension: ReportFormats,
        pagination: PaginationOptions | None = None,
        *,
        hide_amounts: bool = False,
    ) -> PaginatedResult[bytes]:
        """Download detailed report in pdf or csv format.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-export-detailed-report)

        Args:
            body: JSON body for formatting and filtering the report.
            extension: Format of the exported report. PDF or CSV.
            pagination: Pagination options containing page size, next_id and next_row.
            hide_amounts: Whether amounts should be hidden.

        Raises:
            InvalidExtensionError: If extension is not pdf or csv.
            HTTPStatusError: If the request is not a success.

        Returns:
            Report ready to be saved or further processed in python.
        """
        _validate_extension(extension)

        pagination = pagination or PaginationOptions()

        response = await self.request(
            f"{self.endpoint}.{extension}",
            body=self._paginate_body(
                body.format(
                    f"detail_report_{extension}",
                    workspace_id=self.workspace_id,
                    hide_amounts=hide_amounts,
                ),
                pagination,
            ),
            method=RequestMethod.POST,
            raw=True,
        )
        return self._paginate(cast("Response", response), raw=True)

    async def totals_report(
        self,
        body: ReportBody,
        *,
        granularity: Literal["day", "week", "month"] = "day",
        with_graph: bool = False,
    ) -> dict[str, int]:
        """Return totals sums for detailed report.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-load-totals-detailed-report)

        Args:
            body: JSON body for filtering the report.
            granularity: Totals granularity, optional, overrides resolution values.
            with_graph: Whether Graph information should be loaded.

        Returns:
            With the totals relevant to the provided filters.
        """
        response = await self.request(
            f"{self.endpoint}/totals",
            body=body.format(
                "detail_totals",
                workspace_id=self.workspace_id,
                granularity=granularity,
                with_graph=with_graph,
            ),
            method=RequestMethod.POST,
        )

        return cast("dict[str, int]", response)

    @property
    def endpoint(self) -> str:
        return f"workspace/{self.workspace_id}/search/time_entries"


class AsyncWeeklyReportEndpoint(AsyncReportEndpoint):
    """Weekly reports endpoint.

    [Official Documentation](https://engineering.toggl.com/docs/reports/weekly_reports)
    """

    async def search_time_entries(
        self,
        body: ReportBody,
    ) -> list[dict[str, Any]]:
        """Return time entries for weekly report according to the given filters.

        [Official Documentation](https://engineering.toggl.com/docs/reports/detailed_reports#post-search-time-entries)

        Args:
            body: JSON body for filtering time entries.

        Returns:
            A List of time entries filted by the formatted body.
        """
        response = await self.request(
            self.endpoint,
            body=body.format(
                "weekly_time_entries",
                workspace_id=self.workspace_id,
            ),
            method=RequestMethod.POST,
        )

        return cast("list[dict[str, Any]]", response)

    async def export_report(
        self,
        body: ReportBody,
        extension: ReportFormats,
    ) -> bytes:
        """Download weekly report in pdf or csv format.

        [Official Documentation](https://engineering.toggl.com/docs/reports/weekly_reports#post-export-weekly-report)

        Args:
            body: JSON body for filtering time entries.
            extension: extension: Format of the exported report. PDF or CSV.

        Raises:
            InvalidExtensionError: If extension is not pdf or csv.

        Returns:
            Report ready to be saved or further processed in python.
        """
        _validate_extension(extension)
        response = await self.request(
            f"{self.endpoint}.{extension}",
            body=body.format(
                f"weekly_report_{extension}",
                workspace_id=self.workspace_id,
            ),
            method=RequestMethod.POST,
            raw=True,
        )
        return cast("Response", response).content

    @property
    def endpoint(self) -> str:
        return f"workspace/{self.workspace_id}/weekly/time_entries"
