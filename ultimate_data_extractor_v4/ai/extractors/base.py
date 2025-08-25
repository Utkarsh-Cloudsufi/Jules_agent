from abc import ABC, abstractmethod
from typing import List

from ...models.data_models import EnhancedRawDataPoint
from ...models.source_models import ContentType


class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, content: str, query, content_type: ContentType) -> List[EnhancedRawDataPoint]:
        raise NotImplementedError

