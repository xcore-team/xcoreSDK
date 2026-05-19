"""
mongodb.py — Base repository for MongoDB plugins (Motor async driver).

Usage:
    class UserRepo(BaseMongoRepository):
        collection_name = "users"

    repo = UserRepo(db=adapter.db)
    user = await repo.get_by_id("64a1f2...")
    all_users = await repo.get_all({"active": True})
"""

from __future__ import annotations

from abc import ABC
from typing import Any, List, Optional


class BaseMongoRepository(ABC):
    """
    Generic async repository for MongoDB via Motor.

    Set `collection_name` on the subclass.
    Pass a Motor `AsyncIOMotorDatabase` as `db`.
    """

    collection_name: str = ""

    def __init__(self, db: Any) -> None:
        if not self.collection_name:
            raise ValueError(
                f"{self.__class__.__name__} must define `collection_name`"
            )
        self._col = db[self.collection_name]

    def _oid(self, id: str) -> Any:
        from bson import ObjectId

        return ObjectId(id)

    async def get_by_id(self, id: str) -> Optional[dict]:
        return await self._col.find_one({"_id": self._oid(id)})

    async def get_all(self, filter: dict | None = None, limit: int = 0) -> List[dict]:
        cursor = self._col.find(filter or {})
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=None)

    async def find_one(self, filter: dict) -> Optional[dict]:
        return await self._col.find_one(filter)

    async def create(self, data: dict) -> dict:
        result = await self._col.insert_one(data)
        data["_id"] = result.inserted_id
        return data

    async def update(self, id: str, data: dict) -> Optional[dict]:
        await self._col.update_one({"_id": self._oid(id)}, {"$set": data})
        return await self.get_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self._col.delete_one({"_id": self._oid(id)})
        return result.deleted_count > 0

    async def count(self, filter: dict | None = None) -> int:
        return await self._col.count_documents(filter or {})

    async def exists(self, filter: dict) -> bool:
        return await self._col.count_documents(filter, limit=1) > 0
