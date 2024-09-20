"""This module contains classes for interacting with Azure DevOps"""

from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from json import dumps

from requests import Response, get, patch, post

from alexlib.api.objects import (
    AgentBase,
    ApiObject,
    ClientBase,
)
from alexlib.core import chkenv, show_dict

ORG_INITIALS = chkenv("ORG_INITIALS")
ADO_PROJECT = chkenv("ADO_PROJECT")
ADO_TEAM = chkenv("ADO_TEAM")

SEP = "\\"
TIMEFRAMES = ["past", "current", "future"]
OPS = ["<", "==", ">"]
PROGRESS_STATES = ["planning", "inprogress", "completed"]
WORKITEM_ATTR_MAP = {
    "title": "System.Title",
    "description": "Microsoft.VSTS.Common.DescriptionHTML",
    "acceptance_criteria": "Microsoft.VSTS.Common.AcceptanceCriteria",
    "area": "System.AreaPath",
    "iteration": "System.IterationPath",
    "status": f"{ORG_INITIALS}.Status",
    "targeted_release": f"{ORG_INITIALS}.TargetedRelease",
    "qa_effort": "Custom.QAEffort",
    "dev_effort": "Custom.DevEffort",
    "assigned_to": "System.AssignedTo",
    "created_by": "System.CreatedBy",
    "created_date": "System.CreatedDate",
    "changed_by": "System.ChangedBy",
    "changed_date": "System.ChangedDate",
    "priority": "Microsoft.VSTS.Common.Priority",
    "tags": "System.Tags",
    "workitem_type": "System.WorkItemType",
    "id": "System.Id",
    "url": "System.Url",
    "remaining_work": "Microsoft.VSTS.Scheduling.RemainingWork",
    "original_estimate": "Microsoft.VSTS.Scheduling.OriginalEstimate",
    "completed_work": "Microsoft.VSTS.Scheduling.CompletedWork",
}
POST_HEADER = {"Content-Type": "application/json-patch+json"}
PATCH_HEADER = {"Content-Type": "application/json-patch+json"}
GET_HEADER = {"Content-Type": "application/json"}
ADO_BASE_URL = "https://dev.azure.com"
ADO_API_URL = f"{ADO_BASE_URL}/{ORG_INITIALS}/{ADO_PROJECT}/_apis"


def mk_area_path(project: str, team: str) -> str:
    """Returns an area path"""
    return SEP.join([project, "Team", team])


@dataclass
class DevOpsPath(str):
    """Base class for all DevOps paths"""

    sep: str = field(default=SEP, repr=False)

    @property
    def parts(self) -> list[str]:
        """Returns a list of path parts"""
        return self.split(self.sep)

    @property
    def name(self) -> str:
        """Returns the last part of the path"""
        return self.parts[-1]

    @classmethod
    def from_env(cls, env: str, **kwargs):
        """Returns a DevOpsPath object from an environment variable"""
        return cls(chkenv(env, **kwargs))

    @classmethod
    def area_from_env(cls, **kwargs):
        """Returns a DevOpsPath object from an environment variable"""
        return cls.from_env("ADO_AREA_PATH", **kwargs)

    @classmethod
    def iteration_from_env(cls, **kwargs):
        """Returns a DevOpsPath object from an environment variable"""
        return cls.from_env("ADO_ITERATION_PATH", **kwargs)


@dataclass
class DevOpsObject(ApiObject):
    """Base class for all DevOps objects"""

    url: str = field(default=None, repr=False)
    path: DevOpsPath = field(default=None, repr=False)


@dataclass
class DevOpsAgent(AgentBase, DevOpsObject):
    """Base class for all DevOps agents"""


@dataclass
class WorkItem(DevOpsObject):
    """Base class for all DevOps Product Backlog Items"""

    title: str = field(default=None)
    description: str = field(default=None)
    acceptance_criteria: str = field(default=None)
    area: DevOpsPath = field(default_factory=DevOpsPath.area_from_env)
    iteration: DevOpsPath = field(default_factory=DevOpsPath.iteration_from_env)
    status: str = field(default=None)
    targeted_release: str = field(default=None)
    qa_effort: float = field(default=None)
    dev_effort: float = field(default=None)
    assigned_to: DevOpsAgent = field(default=None, repr=False)
    created_by: DevOpsAgent = field(default=None, repr=False)
    created_date: datetime = field(default=None, repr=False)
    changed_by: DevOpsAgent = field(default=None, repr=False)
    changed_date: datetime = field(default=None, repr=False)
    priority: int = field(default=None, repr=False)
    tags: list[str] = field(default_factory=list, repr=False)
    workitem_type: str = field(default=None, repr=False)
    remaining_work: float = field(default=0.0, repr=False)
    original_estimate: float = field(default=0.0, repr=False)
    completed_work: float = field(default=0.0, repr=False)
    startdate: datetime = field(default=None, repr=False)
    finishdate: datetime = field(default=None, repr=False)
    timeframe: str = field(default=None, repr=False)


@dataclass
class DevOpsClient(DevOpsObject, ClientBase):
    """A class to handle Azure DevOps API Requests"""

    host: str
    org: str
    project: str
    token: str = field(repr=False)
    api_version: str = field(default="7.0", repr=False)
    area: DevOpsPath = field(default_factory=DevOpsPath.area_from_env)
    iteration: DevOpsPath = field(default_factory=DevOpsPath.iteration_from_env)

    @classmethod
    def from_envs(cls) -> "DevOpsClient":
        """Returns a DevOpsClient object from environment variables"""
        envs = [chkenv(f"ado_{x}".upper()) for x in ["host", "org", "project", "token"]]
        kwenvs = {x: chkenv(f"ado_{x}".upper()) for x in ["api_version"]}
        return cls(*envs, **kwenvs)

    @cached_property
    def api_part(self) -> dict:
        """Returns a dictionary with the API version"""
        return {"api-version": self.api_version}

    @property
    def org_path(self) -> str:
        """Returns the organization path"""
        return "/".join(
            [
                self.host,
                self.org,
            ]
        )

    @property
    def project_path(self) -> str:
        """Returns the project path"""
        proj = self.project.replace(" ", "%20")
        return "/".join(
            [
                self.org_path,
                proj,
            ]
        )

    @property
    def org_api_path(self) -> str:
        """Returns the organization API path"""
        return self.org_path + "/_apis"

    @property
    def project_api_path(self) -> str:
        """Returns the project API path"""
        return self.project_path + "/_apis"

    @staticmethod
    def fmt_uri_kwargs(kwargs: dict[str, str]) -> str:
        """Returns a string of URI kwargs"""
        return "?" + "&".join([f"{k}={v}" for k, v in kwargs.items()])

    @staticmethod
    def mk_uri(
        api_path: str,
        resource_path: str,
        kwargs: dict[str:str] = None,
    ) -> str:
        """Returns a URI"""
        ret = "/".join(
            [
                api_path,
                resource_path,
            ]
        )
        if kwargs:
            ret += DevOpsClient.fmt_uri_kwargs(kwargs)
        return ret

    def mk_team_iterations_uri(self, team: str) -> str:
        """Returns a URI for team iterations"""
        team_api_path = self.project_path + f"/{team}/_apis"
        return DevOpsClient.mk_uri(
            team_api_path, "work/teamsettings/iterations", kwargs=self.api_part
        )

    def get_team_iterations(self, team: str) -> dict:
        """Returns a dictionary of team iterations"""
        return self.get_response(self.mk_team_iterations_uri(team)).json()["value"]

    @property
    def last_sprint_query_id(self) -> str:
        """Returns the last sprint query ID"""
        return chkenv("ADO_LAST_SPRINT_QUERY_ID")

    @property
    def new_tasks_query_id(self) -> str:
        """Returns the new tasks query ID"""
        return chkenv("ADO_NEW_TASKS_CREATED_TODAY_QUERY_ID")

    @property
    def my_hours_query_id(self) -> str:
        """Returns the my hours query ID"""
        return chkenv("ADO_MY_HOURS_QUERY_ID")

    def mk_query_uri(self, query_id: str) -> str:
        """Returns a URI for a query"""
        return DevOpsClient.mk_uri(
            self.project_api_path,
            f"wit/wiql/{query_id}",
            kwargs=self.api_part,
        )

    def get_response(self, uri: str) -> Response:
        """Returns a response object"""
        resp = get(uri, auth=self.basic_auth, headers=GET_HEADER)
        if resp.status_code == 200:
            return resp
        msg = ", ".join([f"code={resp.status_code}", f"url={resp.url}"])
        raise ConnectionError(msg)

    def get_workitems(self, query_id: str) -> list[str]:
        """Returns a list of workitem IDs"""
        resp = self.get_response(self.mk_query_uri(query_id))
        return [x["id"] for x in resp.json()["workItems"]]

    @cached_property
    def last_sprint_workitems(self) -> dict:
        """Returns a dictionary of workitems in the last sprint"""
        return self.get_workitems(self.last_sprint_query_id)

    @cached_property
    def my_hours_workitems(self) -> dict:
        """Returns a dictionary of workitems in the last sprint"""
        return self.get_workitems(self.my_hours_query_id)

    @property
    def all_projects_uri(self) -> dict:
        """Returns a URI for all projects"""
        return DevOpsClient.mk_uri(
            self.org_api_path,
            "projects",
            kwargs=self.api_part,
        )

    @cached_property
    def all_projects(self) -> dict:
        """Returns a dictionary of all projects"""
        return self.get_response(self.all_projects_uri).json()["value"]

    @cached_property
    def all_project_names(self) -> list[str]:
        """Returns a list of all project names"""
        return [x["name"] for x in self.all_projects]

    @cached_property
    def all_project_ids(self) -> list[str]:
        """Returns a list of all project IDs"""
        return [x["id"] for x in self.all_projects]

    @property
    def all_teams_uri(self) -> dict:
        """Returns a URI for all teams"""
        return DevOpsClient.mk_uri(
            self.org_api_path,
            "teams",
            kwargs=self.api_part,
        )

    @cached_property
    def all_teams(self) -> dict:
        """Returns a dictionary of all teams"""
        return self.get_response(self.all_teams_uri).json()["value"]

    @cached_property
    def all_team_names(self) -> list[str]:
        """Returns a list of all team names"""
        return [x["name"] for x in self.all_teams]

    @cached_property
    def all_team_ids(self) -> list[str]:
        """Returns a list of all team IDs"""
        return [x["id"] for x in self.all_teams]

    @cached_property
    def team_projects(self) -> dict:
        """Returns a dictionary of team projects"""
        return {
            x: [y["projectName"] for y in self.all_teams if y["name"] == x][0]
            for x in self.all_team_names
        }

    @cached_property
    def project_teams(self) -> dict:
        """Returns a dictionary of project teams"""
        return {
            x: [y["name"] for y in self.all_teams if y["projectName"] == x]
            for x in self.all_project_names
        }

    @cached_property
    def team_iterations(self) -> dict:
        """Returns a dictionary of team iterations"""
        teams = self.project_teams[self.project]
        iters = {x: self.get_team_iterations(x) for x in teams}
        return {k: [DevOpsPath(y) for y in v] for k, v in iters.items() if v}

    @property
    def my_team(self) -> str:
        """Returns the name of my team"""
        return chkenv("ADO_TEAM")

    @cached_property
    def my_team_iterations(self) -> dict:
        """Returns a dictionary of my team iterations"""
        return self.get_team_iterations(self.my_team)

    @cached_property
    def workitem_relationship_types(self) -> dict:
        """Returns a dictionary of workitem relationship types"""
        uri = DevOpsClient.mk_uri(
            self.org_api_path,
            "wit/workitemrelationtypes",
            kwargs=self.api_part,
        )
        return self.get_response(uri).json()["value"]

    @cached_property
    def workitem_relationship_map(self) -> dict:
        """Returns a dictionary of workitem relationship types"""
        return {x["name"]: x["referenceName"] for x in self.workitem_relationship_types}

    @cached_property
    def relationship_workitem_map(self) -> dict:
        """Returns a dictionary of workitem relationship types"""
        return {v: k for k, v in self.workitem_relationship_map.items()}

    def add_relationship(
        self, workitem_id: int, rel_id: int, rel_type: str = "Child"
    ) -> Response:
        """Adds a relationship between two workitems"""
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
        uri = DevOpsClient.mk_uri(
            self.project_api_path,
            f"wit/workitems/{workitem_id}",
            kwargs=self.api_part,
        )
        payload = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": rel_code,
                    "url": f"{self.org_api_path}/wit/workitems/{rel_id}",
                    "attributes": {
                        "comment": "".join(
                            [
                                "adding relationship ",
                                rel_type,
                                f"({rel_id})",
                                " -> ",
                                rev_type,
                                f"({workitem_id})",
                            ]
                        )
                    },
                },
            }
        ]
        return patch(uri, auth=self.basic_auth, headers=PATCH_HEADER, json=payload)

    def create_task(
        self,
        title: str,
        workitem_id: int = None,
        description: str = None,
    ) -> dict:
        """Creates a task"""
        hasworkitem = workitem_id is not None
        uri = DevOpsClient.mk_uri(
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
        if self.iteration:
            payload.append(
                {
                    "op": "add",
                    "path": "/fields/System.IterationPath",
                    "value": self.iteration,
                }
            )
        if self.area:
            payload.append(
                {
                    "op": "add",
                    "path": "/fields/System.AreaPath",
                    "value": self.area,
                }
            )
        if description and hasworkitem:
            description = f"{description} | PBI = {workitem_id}"
        if description:
            payload.append(
                {
                    "op": "add",
                    "path": "/fields/System.Description",
                    "value": description,
                }
            )
        show_dict(payload)
        resp = post(uri, auth=self.basic_auth, headers=POST_HEADER, data=dumps(payload))
        stat200 = resp.status_code == 200
        if stat200 and workitem_id is not None:
            resp = self.add_relationship(
                workitem_id=workitem_id,
                rel_id=resp.json()["id"],
            )
        if stat200:
            return resp
        raise ConnectionError(f"{resp.status_code} - {resp.text}")
