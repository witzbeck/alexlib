from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cached_property
from alexlib.__init__ import dotenv

from requests import Response, get
from requests.auth import HTTPBasicAuth

from alexlib.core import chkenv, get_local_tz, show_dict

dotenv


@dataclass
class AzureDevOpsClient:
    host: str
    org: str
    project: str
    token: str = field(repr=False)
    api_version: str = field(default="7.0", repr=False)

    @property
    def org_initials(self) -> str:
        return self.org[:3].capitalize()

    @property
    def basic(self) -> HTTPBasicAuth:
        return HTTPBasicAuth("", self.token)

    @classmethod
    def from_envs(
        cls,
        envs: list[str] = [
            "host",
            "org",
            "project",
            "token",
        ],
        kwenvs: list[str] = [
            "api_version",
        ],
    ):
        envs = [chkenv(f"ado_{x}".upper()) for x in envs]
        kwenvs = {x: chkenv(f"ado_{x}".upper()) for x in kwenvs}
        return cls(*envs, **kwenvs)

    @property
    def api_part(self) -> dict:
        return {"api-version": self.api_version}

    @property
    def org_path(self) -> str:
        return "/".join([
            self.host,
            self.org,
        ])

    @property
    def project_path(self) -> str:
        return "/".join([
            self.org_path,
            self.project,
        ])

    @property
    def org_api_path(self) -> str:
        return self.org_path + "/_apis"

    @property
    def project_api_path(self) -> str:
        return self.project_path + "/_apis"

    @staticmethod
    def fmt_uri_kwargs(
        kwargs: dict[str, str]
    ) -> str:
        return "?" + "&".join([
            f"{k}={v}"
            for k, v in kwargs.items()
        ])

    @staticmethod
    def mk_uri(
        api_path: str,
        resource_path: str,
        kwargs: dict[str:str] = None,
    ) -> str:
        ret = "/".join([
            api_path,
            resource_path,
        ])
        if kwargs:
            ret += AzureDevOpsClient.fmt_uri_kwargs(kwargs)
        return ret

    def mk_team_iterations_uri(self, team: str) -> str:
        team_api_path = self.project_path + f"/{team}/_apis"
        return AzureDevOpsClient.mk_uri(
            team_api_path,
            "work/teamsettings/iterations",
            kwargs=self.api_part
        )

    def get_team_iterations(self, team: str) -> dict:
        return self.get_response(
            self.mk_team_iterations_uri(team)
        ).json()["value"]

    @property
    def last_sprint_query_id(self) -> str:
        return chkenv("ADO_LAST_SPRINT_QUERY_ID")

    @property
    def my_hours_query_id(self) -> str:
        return chkenv("ADO_MY_HOURS_QUERY_ID")

    def mk_query_uri(self, query_id: str) -> str:
        return AzureDevOpsClient.mk_uri(
            self.project_api_path,
            f"wit/wiql/{query_id}",
            kwargs=self.api_part,
        )

    def get_response(self, uri: str) -> Response:
        resp = get(uri, auth=self.basic)
        if resp.status_code == 200:
            return resp
        else:
            msg = ", ".join([
                f"code={resp.status_code}",
                f"url={resp.url}"
            ])
            raise ConnectionError(msg)

    def get_workitems(self, query_id: str) -> list[str]:
        resp = self.get_response(self.mk_query_uri(query_id))
        return [x["id"] for x in resp.json()["workItems"]]

    @cached_property
    def last_sprint_workitems(self) -> dict:
        return self.get_workitems(self.last_sprint_query_id)

    @cached_property
    def my_hours_workitems(self) -> dict:
        return self.get_workitems(self.my_hours_query_id)

    @property
    def all_projects_uri(self) -> dict:
        return AzureDevOpsClient.mk_uri(
            self.org_api_path,
            "projects",
            kwargs=self.api_part,
        )

    @cached_property
    def all_projects(self) -> dict:
        return self.get_response(self.all_projects_uri).json()["value"]

    @cached_property
    def all_project_names(self) -> list[str]:
        return [x["name"] for x in self.all_projects]

    @cached_property
    def all_project_ids(self) -> list[str]:
        return [x["id"] for x in self.all_projects]

    @property
    def all_teams_uri(self) -> dict:
        return AzureDevOpsClient.mk_uri(
            self.org_api_path,
            "teams",
            kwargs=self.api_part,
        )

    @cached_property
    def all_teams(self) -> dict:
        return self.get_response(self.all_teams_uri).json()["value"]

    @cached_property
    def all_team_names(self) -> list[str]:
        return [x["name"] for x in self.all_teams]

    @cached_property
    def all_team_ids(self) -> list[str]:
        return [x["id"] for x in self.all_teams]

    @cached_property
    def team_projects(self) -> dict:
        return {
            x: [
                y["projectName"] for y in self.all_teams
                if y["name"] == x
            ][0]
            for x in self.all_team_names
        }

    @cached_property
    def project_teams(self) -> dict:
        return {
            x: [
                y["name"] for y in self.all_teams
                if y["projectName"] == x
            ]
            for x in self.all_project_names
        }

    @cached_property
    def team_iterations(self) -> dict:
        teams = self.project_teams[self.project]
        iters = {
            x: self.get_team_iterations(x)
            for x in teams
        }
        return {k: v for k, v in iters.items() if v}

    @property
    def my_team(self) -> str:
        return chkenv("ADO_TEAM")

    @cached_property
    def my_team_iterations(self) -> dict:
        return self.get_team_iterations(self.my_team)

@dataclass
class ProductBacklogItem:
    id: int
    client: AzureDevOpsClient = field(
        default_factory=AzureDevOpsClient.from_envs,
        repr=False,
    )

    @property
    def resource_path(self) -> str:
        return self.client.workitem_path

    @cached_property
    def tz(self) -> timezone:
        return get_local_tz()

    @property
    def now(self) -> datetime:
        return datetime.now(tz=self.tz)

    @property
    def url(self) -> str:
        return "/".join([
            self.auth.api_path,
            "wit/workitems",
            str(self.id),
        ]) + self.client.api_part

    @classmethod
    def from_env(cls, env: str = "ADO_PBI_ID", **kwargs):
        return cls(chkenv(env, astype=int), **kwargs)

    def get_json(self) -> dict:
        return get(self.url, auth=self.auth.basic).json()

    @cached_property
    def fields(self) -> dict:
        return self.get_json()["fields"]

    @property
    def title(self) -> str:
        return self.fields["System.Title"]

    @property
    def description(self) -> str:
        return self.fields["Microsoft.VSTS.Common.DescriptionHTML"]

    @property
    def acceptance_criteria(self) -> str:
        return self.fields["Microsoft.VSTS.Common.AcceptanceCriteria"]

    @property
    def area_path(self) -> str:
        return self.fields["System.AreaPath"]

    @property
    def area_parts(self) -> list[str]:
        return self.area_path.split("\\")

    @property
    def area(self) -> str:
        return self.area_parts[-1]

    @property
    def iteration_path(self) -> str:
        return self.fields["System.IterationPath"]

    @property
    def iteration_parts(self) -> str:
        return self.iteration_path.split("\\")

    @property
    def iteration(self) -> str:
        return self.iteration_parts[-1]

    @property
    def status(self) -> str:
        return self.fields[f"{self.client.org_initials}.Status"]

    @property
    def targeted_release(self) -> str:
        return self.fields[f"{self.client.org_initials}.TargetedRelease"]

    @property
    def qa_effort(self) -> float:
        try:
            return float(self.fields["Custom.QAEffort"])
        except TypeError:
            return 0.

    @property
    def dev_effort(self) -> float:
        try:
            return float(self.fields["Custom.DevEffort"])
        except TypeError:
            return 0.

    @property
    def work_item_type(self) -> str:
        return self.fields["System.WorkItemType"]

    @property
    def state(self) -> str:
        return self.fields["System.State"]

    @property
    def assigned_to(self) -> str:
        return self.fields["System.AssignedTo"]

    @property
    def assigned_to_name(self) -> str:
        return self.assigned_to["displayName"]

    @property
    def assigned_to_id(self) -> str:
        return self.assigned_to["id"]

    @property
    def assigned_to_email(self) -> str:
        return self.assigned_to["uniqueName"]

    @property
    def created_date(self) -> datetime:
        return datetime.fromisoformat(
            self.fields["System.CreatedDate"]).replace(
            tzinfo=self.tz
        )

    @property
    def days_since_created(self) -> int:
        return (self.now - self.created_date).days

    @property
    def created_by(self) -> str:
        return self.fields["System.CreatedBy"]

    @property
    def created_by_name(self) -> str:
        return self.created_by["displayName"]

    @property
    def created_by_id(self) -> str:
        return self.created_by["id"]

    @property
    def created_by_email(self) -> str:
        return self.created_by["uniqueName"]

    @property
    def changed_date(self) -> datetime:
        return datetime.fromisoformat(
            self.fields["System.ChangedDate"]).replace(
            tzinfo=self.tz
        )

    @property
    def days_since_changed(self) -> int:
        return (self.now - self.changed_date).days

    @property
    def changed_by(self) -> str:
        return self.fields["System.ChangedBy"]

    @property
    def changed_by_name(self) -> str:
        return self.changed_by["displayName"]

    @property
    def changed_by_id(self) -> str:
        return self.changed_by["id"]

    @property
    def changed_by_email(self) -> str:
        return self.changed_by["uniqueName"]

    @property
    def remaining_work(self) -> float:
        return float(self.fields["Microsoft.VSTS.Scheduling.RemainingWork"])

    @property
    def original_estimate(self) -> float:
        return float(self.fields["Microsoft.VSTS.Scheduling.OriginalEstimate"])

    @property
    def completed_work(self) -> float:
        return float(self.fields["Microsoft.VSTS.Scheduling.CompletedWork"])


if __name__ == "__main__":
    client = AzureDevOpsClient.from_envs()
    """
    pbi = ProductBacklogItem.from_env()
    pbis = [
        ProductBacklogItem(x, auth=pbi.auth)
        for x in pbi.auth.last_sprint_workitems
    ]
    show_dict(client.project_teams)
    print(client.all_projects_uri)
    print(client.all_teams_uri)
    show_dict(client.project_teams)
    """
    show_dict(client.my_team_iterations)
