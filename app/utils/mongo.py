from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.settings import settings

client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.db_name]


async def set_indexes() -> None:
    from app.user.user_collection import UserCollection
    from app.suggester.suggester_collection import SuggesterCollection

    await UserCollection.set_index()
    await SuggesterCollection.set_index()
