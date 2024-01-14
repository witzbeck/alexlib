from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cached_property
from json import dumps

from requests import Response, get, post, patch
from requests.auth import HTTPBasicAuth

from alexlib.__init__ import dotenv
from alexlib.core import chkenv, get_local_tz, show_dict

dotenv


@dataclass
class AzureDevOpsObject:
    id: str = field(repr=False)
    name: str = field()
    path: str = field()
    url: str = field(repr=False)
    startdate: datetime = field(default=None, repr=False)
    finishdate: datetime = field(default=None, repr=False)
    timeframe: str = field(default=None, repr=False)
    sep: str = field(default="\\", repr=False)

    def __post_init__(self) -> None:
        if self.startdate is not None:
            self.startdate = datetime.fromisoformat(self.startdate)
        if self.finishdate is not None:
            self.finishdate = datetime.fromisoformat(self.finishdate)

    @cached_property
    def path_parts(self) -> list[str]:
        return self.path.split(self.sep)

    @cached_property
    def timeframes(self) -> list[str]:
        return ["past", "current", "future"]

    @cached_property
    def ops(self) -> list[str]:
        return ["<", "==", ">"]

    @property
    def progress_states(self) -> list[str]:
        return ["planning", "inprogress", "completed"]

    @property
    def hastime(self) -> bool:
        return self.startdate is not None and self.finishdate is not None

    @property
    def usetime(self) -> datetime:
        if not self.hastime:
            raise ValueError("Object has no start or finish date")
        elif self.finishdate is not None:
            ret = self.finishdate
        elif self.startdate is not None:
            ret = self.startdate
        return ret

    def istimeframe(self, timeframe: str, op: str) -> bool:
        if timeframe not in self.timeframes and not op:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        elif op not in self.ops and not timeframe:
            raise ValueError(f"Invalid operator: {op}")
        elif timeframe:
            ret = self.timeframe == timeframe
        else:
            ret = exec("self.timeframe 'eval(op)' timeframe")
        return ret

    @cached_property
    def ispast(self) -> bool:
        if self.timeframe:
            ret = self.timeframe == "past"
        else:
            ret = self.usetime < datetime.now()
        return ret

    @cached_property
    def isfuture(self) -> bool:
        if self.timeframe:
            ret = self.timeframe == "future"
        else:
            ret = self.usetime > datetime.now()
        return ret

    @cached_property
    def iscurrent(self) -> bool:
        if self.timeframe:
            ret = self.timeframe == "current"
        else:
            ret = self.usetime == datetime.now().date()
        return ret

    @classmethod
    def from_dict(cls, d: dict):
        d = {k: v for k, v in d.items() if not isinstance(v, dict)}
        [
            d.update(v)
            for v in d.values()
            if isinstance(v, dict)
        ]
        return cls(**d)


@dataclass
class Iteration(AzureDevOpsObject):
    def __post_init__(self) -> None:
        return super().__post_init__()


@dataclass
class AzureDevOpsClient:
    host: str
    org: str
    project: str
    token: str = field(repr=False)
    api_version: str = field(default="7.0", repr=False)
    sep: str = field(default="\\", repr=False)

    @property
    def org_initials(self) -> str:
        return self.org[:3].capitalize()

    @cached_property
    def team(self) -> str:
        return chkenv("ADO_TEAM")

    @cached_property
    def area_path(self) -> str:
        return self.sep.join([
            self.project,
            "Team",
            self.team,
        ])

    @cached_property
    def iteration_path(self) -> str:
        return chkenv("ADO_ITERATION_PATH")

    @property
    def basic(self) -> HTTPBasicAuth:
        return HTTPBasicAuth("", self.token)

    @cached_property
    def header_map(self) -> dict:
        return {
            "get": {"Content-Type": "application/json"},
            "post": {"Content-Type": "application/json-patch+json"},
            "patch": {"Content-Type": "application/json-patch+json"},
        }

    @property
    def post_headers(self) -> dict:
        return self.header_map["post"]

    @property
    def patch_headers(self) -> dict:
        return self.header_map["patch"]

    @property
    def get_headers(self) -> dict:
        return self.header_map["get"]

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
        proj = self.project.replace(" ", "%20")
        return "/".join([
            self.org_path,
            proj,
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
    def new_tasks_query_id(self) -> str:
        return chkenv("ADO_NEW_TASKS_CREATED_TODAY_QUERY_ID")

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
        return {
            k: [Iteration.from_dict(y) for y in v]
            for k, v in iters.items() if v
        }

    @property
    def my_team(self) -> str:
        return chkenv("ADO_TEAM")

    @cached_property
    def my_team_iterations(self) -> dict:
        return self.get_team_iterations(self.my_team)

    @cached_property
    def workitem_relationship_types(self) -> dict:
        uri = AzureDevOpsClient.mk_uri(
            self.org_api_path,
            "wit/workitemrelationtypes",
            kwargs=self.api_part,
        )
        return self.get_response(uri).json()["value"]

    @cached_property
    def workitem_relationship_map(self) -> dict:
        return {
            x["name"]: x["referenceName"]
            for x in self.workitem_relationship_types
        }

    @cached_property
    def relationship_workitem_map(self) -> dict:
        return {
            v: k
            for k, v in self.workitem_relationship_map.items()
        }

    def add_relationship(
        self,
        workitem_id: int,
        rel_id: int,
        rel_type: str = "Child"
    ) -> Response:
        rel_code = self.workitem_relationship_map[rel_type]
        isforward = rel_code.endswith("Forward")
        isreverse = rel_code.endswith("Reverse")
        isrelated = rel_code.endswith("Related")
        hasrev = isforward or isreverse or isrelated
        if isforward:
            rev_code = rel_code.replace("Forward", "Reverse")
        elif isreverse:
            rev_code = rel_code.replace("Reverse", "Forward")
        elif isrelated:
            rev_code = rel_code
        if hasrev:
            rev_type = self.relationship_workitem_map[rev_code]
        uri = AzureDevOpsClient.mk_uri(
            self.project_api_path,
            f"wit/workitems/{workitem_id}",
            kwargs=self.api_part,
        )
        payload = [{
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": rel_code,
                "url": f"{self.org_api_path}/wit/workitems/{rel_id}",
                "attributes": {
                    "comment": "".join([
                        "adding relationship ",
                        rel_type,
                        f"({rel_id})",
                        " -> ",
                        rev_type,
                        f"({workitem_id})",
                    ])
                }
            }
        }]
        return patch(
            uri,
            auth=self.basic,
            headers=self.patch_headers,
            json=payload
        )

    def create_task(
        self,
        title: str,
        workitem_id: int = None,
        description: str = None,
    ) -> dict:
        hasworkitem = workitem_id is not None
        uri = AzureDevOpsClient.mk_uri(
            self.project_api_path,
            "wit/workitems/$task",
            kwargs=self.api_part,
        )
        payload = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title,
            },
        ]
        if self.iteration_path:
            payload.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.iteration_path,
            })
        if self.area_path:
            payload.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": self.area_path,
            })
        if description and hasworkitem:
            description = f"{description} | PBI = {workitem_id}"
        if description:
            payload.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": description,
            })
        show_dict(payload)
        resp = post(
            uri,
            auth=self.basic,
            headers=self.post_headers,
            data=dumps(payload)
        )
        stat200 = resp.status_code == 200
        if stat200 and workitem_id is not None:
            resp = self.add_relationship(
                workitem_id=workitem_id,
                rel_id=resp.json()["id"],
            )
        if stat200:
            return resp
        else:
            raise ConnectionError(f"{resp.status_code} - {resp.text}")


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
        return self.area_path.split(self.sep)

    @property
    def area(self) -> str:
        return self.area_parts[-1]

    @property
    def _iteration_path(self) -> str:
        return "System.IterationPath"

    @cached_property
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
