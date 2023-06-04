import logging
from typing import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.service.virt import Virt
from app.service.virt import VirtMode
from app.settings import config

logger = logging.getLogger(__name__)

async_engine = create_async_engine(
    config.db,
    pool_pre_ping=True,
    echo=True,
)

async_session = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    future=True,
)

virtmanager = Virt(config.libvirt, VirtMode.READ | VirtMode.WRITE)


async def get_session() -> AsyncIterator[async_sessionmaker]:
    try:
        yield async_session
    except SQLAlchemyError as e:
        logger.exception(e)
