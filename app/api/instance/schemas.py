from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models import InstanceSchema


class InstanceListResponse(BaseModel):
    instances: list[InstanceSchema]


class InstanceUpdateNameRequest(InstanceSchema):
    pass


class InstanceUpdateNameResponse(BaseModel):
    id: UUID
    name: str


class InstanceStateRequest(BaseModel):
    state: Literal["start", "poweroff", "pause"]


class InstanceStateResponse(BaseModel):
    state: Literal["start", "poweroff", "pause"]


class InstanceCreateRequest(BaseModel):
    name: str
    os: str
    vcpu: int
    ram: int
    ram_unit: Literal["KiB", "MiB", "GiB"]
    size: int
    root_password: str
    hostname: Optional[str] = None


class InstanceCreateResponse(BaseModel):
    jobid: UUID


class InstanceJobStatusResponse(BaseModel):
    status: Literal["QUEUED", "PROCESSING", "COMPLETED"]
