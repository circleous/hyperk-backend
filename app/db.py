from functools import lru_cache
import logging
from typing import AsyncIterator, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.service.virt import Virt
from app.service.virt import VirtMode
from app.settings import get_config

logger = logging.getLogger(__name__)

config = get_config()

async_engine = create_async_engine(
    config.db,
    pool_pre_ping=True,
    echo=True,
)

async_session = async_sessionmaker[AsyncSession](
    bind=async_engine,
    autoflush=False,
    future=True,
)


@lru_cache
def get_virt() -> Virt:
    return Virt(config.libvirt, VirtMode.READ | VirtMode.WRITE)


async def get_session() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    try:
        yield async_session
    except SQLAlchemyError as e:
        logger.exception(e)
