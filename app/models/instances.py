from __future__ import annotations

from ipaddress import ip_address
from typing import Literal, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import ConfigDict, BaseModel
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy import Uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from .users import User

from .base import Base


class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[UUID] = mapped_column(
        "id",
        Uuid(as_uuid=True, native_uuid=False),
        nullable=False,
        unique=True,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column("name", String(length=64), nullable=True)

    user_id: Mapped[int] = mapped_column("user_id",
                                         ForeignKey("users.id"),
                                         nullable=False)

    user: Mapped[User] = relationship("User", back_populates="instances")

    @classmethod
    async def get_by_id(cls, session: AsyncSession,
                        id: UUID) -> Optional[Instance]:
        stmt = select(cls).where(cls.id == id).options(selectinload(cls.user))
        return await session.scalar(stmt)

    @classmethod
    async def create(cls, session: AsyncSession, id: UUID, name: str,
                     user: User) -> Instance:
        instance = Instance(id=id, name=name, user_id=user.id)
        session.add(instance)
        await session.commit()
        await session.refresh(instance)

        new = await cls.get_by_id(session, id)
        if not new:
            raise RuntimeError("Instance not created")
        return new

    async def update_name(self, session: AsyncSession, name: str) -> None:
        self.name = name
        await session.flush()

    async def delete(self, session: AsyncSession) -> None:
        await session.delete(self)
        await session.flush()


class InstanceSchema(BaseModel):
    id: UUID
    name: str
    ip: Optional[str] = None
    ram: str
    vcpu: int
    state: Literal["running", "off", "paused"]
    model_config = ConfigDict(from_attributes=True)
