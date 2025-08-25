from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EnhancedQueryInput:
    query: str
    entity_context: Optional[str] = None
    region_context: Optional[str] = None
    metric_context: Optional[str] = None
    additional_terms: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    languages: Optional[List[str]] = None
    include_pdfs: bool = True
    include_excel: bool = True
    include_csv: bool = True
    include_apis: bool = True
    exclude_regions: Optional[List[str]] = None
    specific_countries: Optional[List[str]] = None
    max_sources: int = 50
    # Keep as string to avoid breaking existing usage; can be Enum later
    search_depth: str = "extensive"
    require_peer_reviewed: bool = False
    min_source_authority: float = 0.3
    max_processing_time: int = 600
    enable_caching: bool = True
    parallel_extraction: bool = True


__all__ = [
    "EnhancedQueryInput",
]