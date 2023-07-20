from http import HTTPStatus
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Path
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.authentication import requires

from app.db import get_session
from app.db import get_virt
from app.models.instances import Instance
from app.models.instances import InstanceSchema
from app.models.users import User
from app.models.users import UserSchema
from app.settings import Config
from app.settings import get_config

from .schemas import InstanceCreateRequest
from .schemas import InstanceListResponse
from .schemas import InstanceStateRequest
from .schemas import InstanceStateResponse
from .schemas import InstanceUpdateNameRequest
from .schemas import InstanceUpdateNameResponse
from .use_cases import InstanceDetail
from .use_cases import InstanceList
from .use_cases import InstanceUpdateName
from .use_cases import InstanceUpdateState

router = APIRouter(prefix="/instances", tags=["instance"])


@router.get("", response_model=InstanceListResponse)
async def list_instances(
        request: Request,
        use_case: InstanceList = Depends(InstanceList),
) -> InstanceListResponse:
    return InstanceListResponse(instances=[
        instance async for instance in use_case.execute(request.scope["user"])
    ])


@router.get("/{instance_id}", response_model=InstanceSchema)
async def get_instance(
        request: Request,
        instance_id: UUID = Path(description="id of instance"),
        use_case: InstanceDetail = Depends(InstanceDetail),
) -> InstanceSchema:
    instance = await use_case.execute(instance_id, request.scope["user"])
    return instance


@router.put("/{instance_id}", response_model=InstanceUpdateNameResponse)
async def update_instance_name(
    request: Request,
    data: InstanceUpdateNameRequest,
    instance_id: UUID = Path(description="id of instance"),
    use_case: InstanceUpdateName = Depends(InstanceUpdateName),
) -> InstanceUpdateNameResponse:
    instance = await use_case.execute(
        instance_id,
        data.name,
        request.scope["user"],
    )
    return InstanceUpdateNameResponse(id=instance.id, name=instance.name)


@router.post("/{instance_id}/state")
async def update_state(
    data: InstanceStateRequest,
    instance_id: UUID = Path(description="id of instance"),
    use_case: InstanceUpdateState = Depends(InstanceUpdateState),
) -> InstanceStateResponse:
    return await use_case.execute(instance_id, data.state)


@router.post("/create")
async def create_instance(
    request: Request,
    data: InstanceCreateRequest,
    config: Annotated[Config, Depends(get_config)],
    task: BackgroundTasks,
) -> JSONResponse:
    base_image = config.images.get(data.os)
    if base_image is None:
        raise HTTPException(HTTPStatus.BAD_REQUEST, "Invalid OS type")

    if any(c.isspace() for c in data.name):
        raise HTTPException(HTTPStatus.BAD_REQUEST,
                            "Name can't contain whitespace")

    task.add_task(
        createvm,
        user=request.scope["user"],
        name=data.name,
        vcpu=data.vcpu,
        ram=f"{data.ram}{data.ram_unit}",
        size=data.size,
        os=data.os,
        new_password=data.root_password,
        hostname=data.hostname,
    )

    return JSONResponse(
        content={"status": "accepted"},
        status_code=HTTPStatus.ACCEPTED,
    )


async def createvm(
    user: UserSchema,
    name: str,
    vcpu: int,
    ram: str,
    size: int,
    os: str,
    new_password: str,
    hostname: Optional[str] = None,
) -> None:
    import subprocess

    if hostname is None:
        hostname = str(name)

    subprocess.check_call([
        "./createvm.py",
        "--name",
        str(name),
        "--vcpu",
        str(vcpu),
        "--ram",
        str(ram),
        "--size",
        f"{size}G",
        "--os",
        str(os),
        "--new-password",
        str(new_password),
        "--hostname",
        hostname,
    ])

    virt = get_virt()

    domain = virt.get_vm_by_name(name)

    session_maker = await get_session().__anext__()

    async with session_maker() as session:
        user_obj = await User.get_by_id(session, user.id)
        if not user_obj:
            return

        await Instance.create(
            session,
            UUID(str(domain.UUIDString())),
            name,
            user_obj,
        )

        await session.flush()
