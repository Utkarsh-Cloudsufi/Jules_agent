from typing import List

from ..models.source_models import (
    ContentType,
    DataFreshness,
    EnhancedDataSource,
    SourcePriority,
)
from .factory import SourceFactory


class SourceRegistry:
    def __init__(self) -> None:
        self.factory = SourceFactory()
        self.sources = self.factory.create_all_sources()

    def get_sources_by_priority(self, max_sources: int = 50) -> List[EnhancedDataSource]:
        return sorted(self.sources, key=lambda s: (s.priority.value, -s.authority))[:max_sources]

