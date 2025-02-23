from dataclasses import dataclass

from bson import ObjectId


@dataclass(kw_only=True)
class BaseDocument:
    _id: ObjectId

    @property
    def id(self) -> ObjectId:
        return self._id
