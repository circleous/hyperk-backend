from http import HTTPStatus
from typing import Annotated, AsyncIterator
from uuid import UUID
from uuid import uuid4

from fastapi import Depends
from fastapi import HTTPException
import libvirt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.db import virtmanager
from app.models import Instance
from app.models import InstanceSchema
from app.models import User
from app.models import UserSchema

from .schemas import InstanceCreateRequest

AsyncSessionMaker = Annotated[async_sessionmaker, Depends(get_session)]


def transform_domain(domain: libvirt.virDomain) -> InstanceSchema:
    name = domain.name()
    uuid = UUID(domain.UUIDString())
    state, _ = domain.state()
    if state == libvirt.VIR_DOMAIN_RUNNING:
        state = "running"
        vcpu = domain.maxVcpus()
        ram = domain.maxMemory()
        iface = list(
            domain.interfaceAddresses(
                libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE).items())
        if len(iface) > 0:
            _, val = iface[0]
            ip = val["addrs"][0]["addr"]
    else:
        ram = -1
        vcpu = -1
        ip = ""
        state = "off"
    return InstanceSchema(id=uuid,
                          name=name,
                          ip=ip,
                          vcpu=vcpu,
                          ram=ram,
                          state=state)


class InstanceList:

    def __init__(
        self,
        session: AsyncSessionMaker,
    ) -> None:
        self.dbsession = session

    async def execute(self, user: UserSchema) -> AsyncIterator[InstanceSchema]:
        domains = virtmanager.get_vms()
        for domain in domains:
            yield transform_domain(domain)


class InstanceDetail:

    def __init__(
        self,
        session: AsyncSessionMaker,
    ) -> None:
        self.dbsession = session

    async def execute(self, id: UUID, user: UserSchema) -> InstanceSchema:
        domain = virtmanager.conn.lookupByUUID(id.bytes)
        return transform_domain(domain)


class InstanceUpdateName:

    def __init__(
        self,
        session: AsyncSessionMaker,
    ) -> None:
        self.dbsession = session

    async def execute(self, id: UUID, new_name: str,
                      user: UserSchema) -> Instance:
        async with self.dbsession() as session:
            instance = await Instance.get_by_id(session, id)
            user_obj = await User.get_by_id(session, user.id)
            if not instance:
                raise HTTPException(HTTPStatus.NOT_FOUND, "Invalid Instance ID")
            if instance.user_id != user.id and not user_obj.is_admin:
                raise HTTPException(HTTPStatus.UNAUTHORIZED,
                                    "Invalid Instance ID")
            await instance.update_name(session, new_name)
            await session.refresh(instance)
        return InstanceSchema.from_orm(instance)
