from __future__ import annotations

from typing import AsyncIterator, Optional

from pydantic import ConfigDict, BaseModel
from sqlalchemy import Boolean
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base
from .instances import Instance


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column("id",
                                    autoincrement=True,
                                    nullable=False,
                                    unique=True,
                                    primary_key=True)

    username: Mapped[str] = mapped_column("username",
                                          String(length=64),
                                          nullable=False,
                                          unique=True)

    realname: Mapped[str] = mapped_column("realname",
                                          String(length=64),
                                          nullable=True)

    is_admin: Mapped[bool] = mapped_column("is_admin",
                                           Boolean(),
                                           nullable=False)

    instances: Mapped[list[Instance]] = relationship(
        "Instance",
        back_populates="user",
        order_by=Instance.name,
    )

    @classmethod
    async def get_by_id(cls, session: AsyncSession, uid: int) -> Optional[User]:
        stmt = select(cls).where(cls.id == uid)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def get_by_username(cls, session: AsyncSession,
                              username: str) -> Optional[User]:
        stmt = select(cls).where(cls.username == username)
        return await session.scalar(stmt.order_by(cls.id))

    @classmethod
    async def create(cls, session: AsyncSession, username: str, realname: str,
                     is_admin: bool) -> User:
        user = User(username=username, realname=realname, is_admin=is_admin)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        new = await cls.get_by_id(session, user.id)
        if not new:
            raise RuntimeError("User not created")
        return new

    async def get_instances(self,
                            session: AsyncSession) -> AsyncIterator[Instance]:
        stmt = select(Instance).where(Instance.user_id == self.id)
        stream = await session.stream_scalars(stmt.order_by(Instance.id))
        async for row in stream:
            yield row


class UserSchema(BaseModel):
    id: int
    username: str
    realname: str
    model_config = ConfigDict(from_attributes=True)
