from http import HTTPStatus
from typing import Annotated, AsyncIterator
from uuid import UUID

from fastapi import Depends
from fastapi import HTTPException
import libvirt
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

import app.db
from app.db import get_session
from app.db import get_virt
from app.models import Instance
from app.models import InstanceSchema
from app.models import User
from app.models import UserSchema
from app.service.virt import Virt

from .schemas import InstanceCreateRequest
from .schemas import InstanceStateResponse

AsyncSessionMaker = Annotated[async_sessionmaker[AsyncSession],
                              Depends(get_session)]


def transform_domain(domain: libvirt.virDomain) -> InstanceSchema:
    name = domain.name()
    uuid = UUID(domain.UUIDString())
    state, max_mem, mem, vcpu, time = domain.info()
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
            ip = ""
    else:
        ram = int(max_mem)
        vcpu = int(vcpu)
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
        virt: Annotated[Virt, Depends(get_virt)],
    ) -> None:
        self.dbsession = session
        self.virt = virt

    async def execute(self, user: UserSchema) -> AsyncIterator[InstanceSchema]:
        domains = self.virt.get_vms()
        for domain in domains:
            yield transform_domain(domain)


class InstanceDetail:

    def __init__(
        self,
        session: AsyncSessionMaker,
        virt: Annotated[Virt, Depends(get_virt)],
    ) -> None:
        self.dbsession = session
        self.virt = virt

    async def execute(self, id: UUID, user: UserSchema) -> InstanceSchema:
        domain = self.virt.conn.lookupByUUID(id.bytes)
        return transform_domain(domain)


class InstanceUpdateName:

    def __init__(
        self,
        session: AsyncSessionMaker,
    ) -> None:
        self.dbsession = session

    async def execute(self, id: UUID, new_name: str,
                      user: UserSchema) -> InstanceSchema:
        async with self.dbsession() as session:
            instance = await Instance.get_by_id(session, id)
            user_obj = await User.get_by_id(session, user.id)
            if not instance or not user_obj:
                raise HTTPException(HTTPStatus.NOT_FOUND, "Invalid Instance ID")
            if instance.user_id != user.id and not user_obj.is_admin:
                raise HTTPException(HTTPStatus.UNAUTHORIZED,
                                    "Invalid Instance ID")
            await instance.update_name(session, new_name)
            await session.refresh(instance)
        return InstanceSchema.from_orm(instance)


class InstanceUpdateState:

    def __init__(
        self,
        session: AsyncSessionMaker,
        virt: Annotated[Virt, Depends(get_virt)],
    ) -> None:
        self.dbsession = session
        self.virt = virt

    async def execute(self, id: UUID, state: str) -> InstanceStateResponse:
        dom = self.virt.get_vm_by_id(id)

        if dom is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, "Invalid Instance ID")

        if state == "start":
            dom.create()
        elif state == "poweroff":
            dom.destroy()
        elif state == "pause":
            dom.managedSave()
        else:
            raise HTTPException(HTTPStatus.BAD_REQUEST, "Unhandled state")

        return InstanceStateResponse(state=state)