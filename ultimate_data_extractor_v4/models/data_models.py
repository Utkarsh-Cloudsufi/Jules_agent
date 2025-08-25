from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .source_models import ContentType


@dataclass
class EnhancedRawDataPoint:
    value: Any
    context: str
    source_url: str
    source_name: str
    extraction_confidence: float
    raw_text: str
    publication_date: Optional[datetime] = None
    data_freshness_days: Optional[int] = None
    source_credibility: Optional[float] = None
    peer_reviewed: Optional[bool] = None
    is_partial_data: Optional[bool] = None
    methodology_notes: Optional[str] = None
    content_type: Optional[ContentType] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None
    copyright_status: Optional[str] = None
    usage_rights: Optional[str] = None
    required_attribution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancedSearchResult:
    query: str
    source: str
    url: str
    title: str
    content: str
    data_points: List[EnhancedRawDataPoint]
    content_type: ContentType
    errors_encountered: List[str] = field(default_factory=list)
    blocked_by_paywall: bool = False
    rate_limited: bool = False
    requires_authentication: bool = False
    content_language: Optional[str] = None
    extraction_accuracy: Optional[float] = None
    content_completeness: Optional[float] = None
    source_authority: Optional[float] = None
    search_timestamp: datetime = field(default_factory=datetime.now)
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            self.content_hash = str(abs(hash(self.content)))[:12]


__all__ = [
    "EnhancedRawDataPoint",
    "EnhancedSearchResult",
]