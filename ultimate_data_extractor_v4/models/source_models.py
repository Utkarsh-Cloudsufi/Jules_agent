from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class SourcePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class ContentType(Enum):
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    DOCX = "docx"
    API = "api"


class DataFreshness(Enum):
    REAL_TIME = "real_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    STATIC = "static"


@dataclass
class EnhancedDataSource:
    name: str
    base_url: str
    search_patterns: List[str]
    priority: SourcePriority
    authority: float
    content_types: List[ContentType]
    data_freshness: DataFreshness
    rate_limit: float = 2.0
    requires_auth: bool = False
    api_key_env: Optional[str] = None
    geographic_coverage: Optional[List[str]] = None
    domain_expertise: Optional[List[str]] = None
    peer_reviewed: bool = False
    institutional_backing: bool = False
    copyright_status: str = "fair_use"
    usage_rights: str = "research_educational"
    terms_of_service_url: Optional[str] = None


__all__ = [
    "SourcePriority",
    "ContentType",
    "DataFreshness",
    "EnhancedDataSource",
]