"""This module contains all the API objects used in the library"""
from dataclasses import dataclass, field
from datetime import datetime, tzinfo
from functools import cached_property

from requests.auth import HTTPBasicAuth

from alexlib.core import chkenv

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


@dataclass
class ApiObject:
    """Base class for all API objects"""

    id: str = field(default=None)
    name: str = field(default=None)

    def __repr__(self) -> str:
        """Returns a string representation of the object"""
        return f"{self.__class__.__name__}({self.name})"

    @property
    def now(self) -> datetime:
        """Returns current time"""
        return datetime.now()

    @cached_property
    def tzinfo(self) -> tzinfo:
        """Returns current timezone"""
        return self.now.tzinfo

    @classmethod
    def from_dict(cls, d: dict):
        """Creates an instance from a dictionary"""
        d = {k: v for k, v in d.items() if not isinstance(v, dict)}
        _ = [d.update(v) for v in d.values() if isinstance(v, dict)]
        return cls(**d)


@dataclass
class AgentBase(ApiObject):
    """Base class for all API agents"""

    email: str = field(default=None)


@dataclass
class ClientBase(ApiObject):
    """Base class for all API clients"""

    host: str = field(default=None)
    token: str = field(default=None, repr=False)

    @cached_property
    def basic_auth(self) -> HTTPBasicAuth:
        """Returns basic authentication object"""
        return HTTPBasicAuth("", self.token)
