from typing import Optional

from aiogram.types import ContentType


class MediaIdStorage:
    def __init__(self):
        self.cache = {}

    async def get_media_id(self,
                           path: Optional[str],
                           type: ContentType) -> Optional[int]:
        if not path:
            return None
        return self.cache.get((path, type))

    async def save_media_id(self,
                            path: Optional[str],
                            type: ContentType,
                            media_id: str) -> None:
        if not path:
            return None
        self.cache[(path, type)] = media_id
