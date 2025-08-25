from typing import List

from ..models.source_models import (
    ContentType,
    DataFreshness,
    EnhancedDataSource,
    SourcePriority,
)


class SourceFactory:
    def create_all_sources(self) -> List[EnhancedDataSource]:
        sources: List[EnhancedDataSource] = []
        sources.extend(self._critical_sources())
        sources.extend(self._high_value_sources())
        sources.extend(self._general_sources())
        return sources

    def _critical_sources(self) -> List[EnhancedDataSource]:
        return [
            EnhancedDataSource(
                name="World Bank Open Data",
                base_url="https://data.worldbank.org",
                search_patterns=["https://data.worldbank.org/search?q={query}"],
                priority=SourcePriority.CRITICAL,
                authority=0.98,
                content_types=[ContentType.HTML, ContentType.API],
                data_freshness=DataFreshness.QUARTERLY,
                requires_auth=False,
                geographic_coverage=["Global"],
                domain_expertise=["development", "economics"],
                peer_reviewed=True,
                institutional_backing=True,
            ),
        ]

    def _high_value_sources(self) -> List[EnhancedDataSource]:
        return [
            EnhancedDataSource(
                name="International Energy Agency",
                base_url="https://www.iea.org",
                search_patterns=["https://www.iea.org/search?q={query}"],
                priority=SourcePriority.HIGH,
                authority=0.97,
                content_types=[ContentType.HTML, ContentType.EXCEL],
                data_freshness=DataFreshness.MONTHLY,
                geographic_coverage=["Global"],
                domain_expertise=["energy", "statistics"],
                peer_reviewed=True,
                institutional_backing=True,
            ),
        ]

    def _general_sources(self) -> List[EnhancedDataSource]:
        return [
            EnhancedDataSource(
                name="Our World in Data",
                base_url="https://ourworldindata.org",
                search_patterns=["https://ourworldindata.org/search?q={query}"],
                priority=SourcePriority.MEDIUM,
                authority=0.87,
                content_types=[ContentType.HTML, ContentType.CSV],
                data_freshness=DataFreshness.MONTHLY,
                geographic_coverage=["Global"],
                domain_expertise=["development data"],
            ),
        ]

