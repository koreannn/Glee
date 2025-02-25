import asyncio
from asyncio import AbstractEventLoop
from typing import Generator

import pytest_asyncio

from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.settings import settings
from app.utils import mongo  # 기존 MongoDB 설정을 임포트


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db() -> None:
    """테스트용 MongoDB 연결"""
    client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(settings.test_mongo_uri)
    test_db = client["test_db"]

    # 기존 MongoDB 설정을 테스트용 DB로 변경
    mongo.db = test_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db() -> None:
    for collection_name in await mongo.db.list_collection_names():
        await mongo.db[collection_name].drop()
