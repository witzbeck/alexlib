from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import cached_property
from alexlib.__init__ import dotenv

from requests import Response, get
from requests.auth import HTTPBasicAuth

from alexlib.core import chkenv, get_local_tz

dotenv


@dataclass
class AdoAuth:
    host: str
    org: str
    project: str
    token: str = field(repr=False)
    api_version: str = field(default="7.0", repr=False)

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
    def api_part(self) -> str:
        return f"?api-version={self.api_version}"

    @property
    def api_path(self) -> str:
        return "/".join([
            self.host,
            self.org,
            self.project,
            "_apis",
        ])

    def mk_url(
        self,
        resource_path: str,
        kwparts: list[str] = [],
    ) -> str:
        return "/".join([
            self.api_path,
            resource_path,
        ]) + "".join(kwparts)

    @property
    def last_sprint_query_id(self) -> str:
        return chkenv("ADO_LAST_SPRINT_QUERY_ID")

    @property
    def last_sprint_url(self) -> str:
        return self.mk_url(
            f"wit/wiql/{self.last_sprint_query_id}",
            kwparts=[self.api_part],
        )

    def get_response(self, url: str) -> Response:
        resp = get(url, auth=self.basic)
        if resp.status_code == 200:
            return resp
        else:
            msg = ", ".join([
                f"code={resp.status_code}",
                f"url={resp.url}"
            ])
            raise ConnectionError(msg)

    @property
    def last_sprint_workitems(self) -> list[str]:
        resp = self.get_response(self.last_sprint_url)
        return [x["id"] for x in resp.json()["workItems"]]

    @property
    def workitems(self) -> dict:
        url = self.mk_url(self.workitem_path, kwparts=[self.api_part])
        return self.get_response(url)

    @property
    def org_initials(self) -> str:
        return self.org[:3].capitalize()


@dataclass
class ProductBacklogItem:
    id: int
    auth: AdoAuth = field(
        default_factory=AdoAuth.from_envs,
        repr=False,
    )

    @property
    def resource_path(self) -> str:
        return self.auth.workitem_path

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
        ]) + self.auth.api_part

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
    def area(self) -> str:
        return self.area_path.split("\\")[-1]

    @property
    def iteration_path(self) -> str:
        return self.fields["System.IterationPath"]

    @property
    def iteration(self) -> str:
        return self.iteration_path.split("\\")[-1]

    @property
    def status(self) -> str:
        return self.fields[f"{self.auth.org_initials}.Status"]

    @property
    def targeted_release(self) -> str:
        return self.fields[f"{self.auth.org_initials}.TargetedRelease"]

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
    pbi = ProductBacklogItem.from_env()
    auth = AdoAuth.from_envs()
    pbis = [
        ProductBacklogItem(x, auth=pbi.auth)
        for x in pbi.auth.last_sprint_workitems
    ]
