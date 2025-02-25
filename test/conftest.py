import asyncio
from dataclasses import asdict
from datetime import datetime
from asyncio import AbstractEventLoop
from typing import Generator

import pytest_asyncio

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.settings import settings
from app.suggester.suggester_document import SuggesterDocument, SuggesterDTO
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

    users_collection = mongo.db["users"]
    initial_user = {
        "_id": ObjectId("67bd950e6a524a8132db160d"),
        "kakao_id": 1,
        "nickname": "개발 계정",
        "profile_image": "",
        "thumbnail_image": "",
    }
    await users_collection.insert_one(initial_user)


@pytest_asyncio.fixture
def auth_header() -> dict[str, str]:
    """테스트용 JWT 인증 헤더 생성"""
    return {"Authorization": f"Bearer {settings.test_jwt_token}"}


@pytest_asyncio.fixture(scope="function")
async def exists_suggestion() -> SuggesterDocument:
    suggestion_collection = mongo.db["suggester"]

    suggester_dto = SuggesterDTO(
        user_id=ObjectId("67bd950e6a524a8132db160d"),
        tag=["AI", "NLP"],
        suggestion="Test suggestion",
        updated_at=datetime.now(),
        created_at=datetime.now(),
    )

    result = await suggestion_collection.insert_one(asdict(suggester_dto))
    return SuggesterDocument(
        _id=result.inserted_id,  # ✅ 삽입된 ObjectId 사용
        user_id=suggester_dto.user_id,
        tag=suggester_dto.tag,
        suggestion=suggester_dto.suggestion,
        created_at=suggester_dto.created_at,
        updated_at=suggester_dto.updated_at,
    )
