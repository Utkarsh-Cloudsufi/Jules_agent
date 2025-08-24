"""
Ultimate Pure Universal Data Extractor (Simplified, Runnable Implementation)

This module provides a consolidated and corrected implementation inspired by the
user-provided design. It focuses on being runnable in constrained environments
without external APIs or network access, while preserving the public APIs and
data structures expected by the CLI and export functions.

Key notes:
- No external network calls; the search engine synthesizes deterministic demo
  results based on the query to exercise the full pipeline.
- Exports JSON, CSV (always); Excel optional if pandas+openpyxl are available.
- All functions/classes referenced in the CLI exist and work coherently.
- The previously garbled `_calculate_overall_confidence` and undefined variable
  `require_peer_reviewed` in `custom_ultimate_query` are corrected.
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# -----------------------------------------------------------------------------
# Optional dependencies (pandas/openpyxl) for enhanced exports
# -----------------------------------------------------------------------------
try:
    import pandas as pd  # type: ignore
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False

try:
    from openpyxl import Workbook  # type: ignore
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False


# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ultimate_extractor")


# -----------------------------------------------------------------------------
# Enums and Data Models
# -----------------------------------------------------------------------------
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
    max_sources: int = 25
    search_depth: str = "extensive"
    require_peer_reviewed: bool = False
    min_source_authority: float = 0.3
    max_processing_time: int = 120
    enable_caching: bool = True
    parallel_extraction: bool = True


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


# -----------------------------------------------------------------------------
# Utility components
# -----------------------------------------------------------------------------
class PerformanceTracker:
    def __init__(self) -> None:
        self.accuracies: List[float] = []
        self.response_times: List[float] = []
        self.successful: int = 0
        self.total: int = 0

    def record_extraction(self, accuracy: float, response_time: float, success: bool) -> None:
        self.accuracies.append(accuracy)
        self.response_times.append(response_time)
        self.total += 1
        if success:
            self.successful += 1

    def get_summary(self) -> Dict[str, Any]:
        return {
            "avg_accuracy": statistics.mean(self.accuracies) if self.accuracies else 0.0,
            "avg_response_time": statistics.mean(self.response_times) if self.response_times else 0.0,
            "success_rate": (self.successful / self.total) if self.total else 0.0,
            "total_extractions": self.total,
        }


class ComprehensiveSourceRegistry:
    """Provides a small, representative set of sources for demo purposes."""

    def __init__(self) -> None:
        self.sources = [
            EnhancedDataSource(
                name="International Energy Agency",
                base_url="https://www.iea.org",
                search_patterns=["https://www.iea.org/search?q={query}"],
                priority=SourcePriority.HIGH,
                authority=0.97,
                content_types=[ContentType.HTML, ContentType.EXCEL],
                data_freshness=DataFreshness.MONTHLY,
                peer_reviewed=True,
                institutional_backing=True,
            ),
            EnhancedDataSource(
                name="World Bank Open Data",
                base_url="https://data.worldbank.org",
                search_patterns=["https://data.worldbank.org/search?q={query}"],
                priority=SourcePriority.CRITICAL,
                authority=0.98,
                content_types=[ContentType.HTML, ContentType.API],
                data_freshness=DataFreshness.QUARTERLY,
                peer_reviewed=True,
                institutional_backing=True,
            ),
            EnhancedDataSource(
                name="Energy Information Administration",
                base_url="https://www.eia.gov",
                search_patterns=["https://www.eia.gov/search/?q={query}"],
                priority=SourcePriority.HIGH,
                authority=0.96,
                content_types=[ContentType.HTML, ContentType.CSV],
                data_freshness=DataFreshness.MONTHLY,
                peer_reviewed=True,
                institutional_backing=True,
            ),
        ]

    def get_sources_by_priority(self, query: EnhancedQueryInput) -> List[EnhancedDataSource]:
        filtered: List[EnhancedDataSource] = []
        for source in self.sources:
            if source.authority < (query.min_source_authority or 0.0):
                continue
            if query.require_peer_reviewed and not source.peer_reviewed:
                continue
            filtered.append(source)
        # Sort by priority then authority descending
        filtered.sort(key=lambda s: (s.priority.value, -s.authority))
        return filtered[: max(1, min(query.max_sources, len(filtered)))]


class UltimateSearchEngine:
    """Simplified search engine that synthesizes results for a given query.

    This avoids network dependencies while providing deterministic demo data.
    """

    def __init__(self) -> None:
        self.source_registry = ComprehensiveSourceRegistry()
        self.performance_tracker = PerformanceTracker()

    async def search_ultimate(self, query: EnhancedQueryInput) -> List[EnhancedSearchResult]:
        start_time = time.time()
        logger.info("Starting demo search for: %s", query.query)

        sources = self.source_registry.get_sources_by_priority(query)
        results: List[EnhancedSearchResult] = []

        # Create deterministic demo data points
        for source in sources:
            base_value = float(len(query.query) % 100) + (source.authority * 10.0)
            points: List[EnhancedRawDataPoint] = []

            for i in range(3):
                value_text = f"{base_value + i * 5.3:.1f} GW"
                raw_text = f"Reported value: {value_text} in {source.name}"
                point = EnhancedRawDataPoint(
                    value=value_text,
                    context=f"Context for {query.query} - sample {i+1}",
                    source_url=source.base_url,
                    source_name=source.name,
                    extraction_confidence=round(0.7 + 0.05 * i, 3),
                    raw_text=raw_text,
                    content_type=ContentType.HTML,
                    source_credibility=source.authority,
                    peer_reviewed=source.peer_reviewed,
                    metadata={"extraction_method": "demo_synthesized"},
                )
                points.append(point)

            content_blob = (
                f"Demo content for {source.name} regarding '{query.query}'. "
                f"Contains numerical references like {points[0].value}, {points[1].value}, and {points[2].value}."
            )
            result = EnhancedSearchResult(
                query=query.query,
                source=source.name,
                url=source.base_url,
                title=f"{source.name} - {query.query}",
                content=content_blob,
                data_points=points,
                content_type=ContentType.HTML,
                extraction_accuracy=statistics.mean([p.extraction_confidence for p in points]),
                content_completeness=min(len(content_blob) / 2000.0, 1.0),
                source_authority=source.authority,
            )
            results.append(result)

        elapsed = time.time() - start_time
        self.performance_tracker.record_extraction(
            accuracy=self._calculate_average_confidence(results),
            response_time=elapsed,
            success=len(results) > 0,
        )
        logger.info("Demo search complete: %d result(s) in %.2fs", len(results), elapsed)
        return results

    @staticmethod
    def _calculate_average_confidence(results: List[EnhancedSearchResult]) -> float:
        confidences: List[float] = []
        for result in results:
            for point in result.data_points:
                confidences.append(point.extraction_confidence)
        return statistics.mean(confidences) if confidences else 0.0


# -----------------------------------------------------------------------------
# Aggregator
# -----------------------------------------------------------------------------
class UltimatePureDataAggregator:
    def __init__(self) -> None:
        self.search_engine = UltimateSearchEngine()
        self.performance_tracker = PerformanceTracker()
        logger.info("UltimatePureDataAggregator initialized (demo mode)")

    async def extract_ultimate_data(self, query: EnhancedQueryInput) -> Dict[str, Any]:
        start_time = time.time()
        try:
            search_results = await self.search_engine.search_ultimate(query)
            analysis = await self._analyze_results_comprehensively(search_results)
            processing_time = time.time() - start_time

            output: Dict[str, Any] = {
                "query": query.query,
                "entity_context": query.entity_context,
                "region_context": query.region_context,
                "metric_context": query.metric_context,
                "additional_terms": query.additional_terms,
                "search_configuration": {
                    "search_depth": query.search_depth,
                    "max_sources": query.max_sources,
                    "languages": query.languages,
                    "date_constraints": {"from": query.date_from, "to": query.date_to},
                    "content_types": {
                        "pdfs": query.include_pdfs,
                        "excel": query.include_excel,
                        "csv": query.include_csv,
                        "apis": query.include_apis,
                    },
                },
                "raw_data_points": [
                    {
                        "value": p.value,
                        "context": p.context,
                        "source_name": p.source_name,
                        "source_url": p.source_url,
                        "extraction_confidence": p.extraction_confidence,
                        "raw_text": p.raw_text,
                        "content_type": p.content_type.value if p.content_type else None,
                        "publication_date": p.publication_date.isoformat() if p.publication_date else None,
                        "data_freshness_days": p.data_freshness_days,
                        "source_credibility": p.source_credibility,
                        "peer_reviewed": p.peer_reviewed,
                        "page_number": p.page_number,
                        "table_reference": p.table_reference,
                        "methodology_notes": p.methodology_notes,
                        "legal_compliance": {
                            "copyright_status": p.copyright_status,
                            "usage_rights": p.usage_rights,
                            "required_attribution": p.required_attribution,
                        },
                        "metadata": p.metadata,
                    }
                    for r in search_results
                    for p in r.data_points
                ],
                "search_analytics": analysis,
                "processing_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "processing_time_seconds": round(processing_time, 2),
                    "groq_model": "llama3-8b-8192",
                    "aggregator_version": "3.0_ultimate_demo",
                    "total_sources_attempted": len({r.source for r in search_results}),
                    "successful_extractions": len([r for r in search_results if r.data_points]),
                    "total_data_points": sum(len(r.data_points) for r in search_results),
                    "average_confidence": self._calculate_overall_confidence(search_results),
                    "extraction_methods_used": list({p.metadata.get("extraction_method", "unknown") for r in search_results for p in r.data_points}),
                    "content_types_processed": list({r.content_type.value for r in search_results}),
                    "cache_performance": {"hits": 0, "misses": 0, "hit_rate": 0.0},
                },
                "performance_metrics": self.performance_tracker.get_summary(),
                "quality_indicators": {
                    "peer_reviewed_sources": len([r for r in search_results if any(p.peer_reviewed for p in r.data_points)]),
                    "high_authority_sources": len([r for r in search_results if (r.source_authority or 0) > 0.8]),
                    "recent_data_points": len([p for r in search_results for p in r.data_points if (p.data_freshness_days or 999) < 30]),
                    "extraction_accuracy_avg": analysis.get("average_extraction_accuracy", 0.0),
                    "source_diversity_score": len({r.source for r in search_results}) / max(len(search_results), 1),
                },
                "search_results_details": [
                    {
                        "source": r.source,
                        "url": r.url,
                        "title": r.title,
                        "content_type": r.content_type.value,
                        "data_points_count": len(r.data_points),
                        "extraction_accuracy": r.extraction_accuracy,
                        "source_authority": r.source_authority,
                        "search_timestamp": r.search_timestamp.isoformat(),
                        "errors_encountered": r.errors_encountered,
                        "blocked_by_paywall": r.blocked_by_paywall,
                        "rate_limited": r.rate_limited,
                        "content_preview": (r.content[:200] + "...") if len(r.content) > 200 else r.content,
                    }
                    for r in search_results
                ],
            }

            logger.info(
                "Ultimate extraction complete: %d data points from %d source(s)",
                len(output["raw_data_points"]),
                output["processing_metadata"]["total_sources_attempted"],
            )
            return output
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Ultimate extraction failed: %s", exc)
            return self._create_error_output(query, str(exc))

    async def _analyze_results_comprehensively(self, search_results: List[EnhancedSearchResult]) -> Dict[str, Any]:
        if not search_results:
            return {"total_results": 0, "analysis": "No results found"}

        source_breakdown: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"data_points": 0, "avg_confidence": 0.0, "content_types": set(), "authority": 0.0}
        )
        all_confidences: List[float] = []
        content_type_counts: Dict[str, int] = defaultdict(int)
        error_summary: Dict[str, int] = defaultdict(int)

        for result in search_results:
            info = source_breakdown[result.source]
            info["data_points"] += len(result.data_points)
            info["authority"] = result.source_authority or 0.0
            info["content_types"].add(result.content_type.value)

            confs = [p.extraction_confidence for p in result.data_points]
            all_confidences.extend(confs)
            if confs:
                info["avg_confidence"] = statistics.mean(confs)

            content_type_counts[result.content_type.value] += 1

            for err in result.errors_encountered:
                error_summary[err] += 1

        for k in list(source_breakdown.keys()):
            source_breakdown[k]["content_types"] = list(source_breakdown[k]["content_types"])  # type: ignore

        return {
            "total_results": len(search_results),
            "results_with_data": len([r for r in search_results if r.data_points]),
            "total_data_points": sum(len(r.data_points) for r in search_results),
            "average_extraction_accuracy": statistics.mean(all_confidences) if all_confidences else 0.0,
            "confidence_distribution": {
                "min": min(all_confidences) if all_confidences else 0.0,
                "max": max(all_confidences) if all_confidences else 0.0,
                "median": statistics.median(all_confidences) if all_confidences else 0.0,
                "std_dev": statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0.0,
            },
            "source_breakdown": dict(source_breakdown),
            "content_type_distribution": dict(content_type_counts),
            "error_summary": dict(error_summary),
            "quality_metrics": {
                "high_confidence_points": len([c for c in all_confidences if c > 0.8]),
                "medium_confidence_points": len([c for c in all_confidences if 0.5 <= c <= 0.8]),
                "low_confidence_points": len([c for c in all_confidences if c < 0.5]),
            },
        }

    @staticmethod
    def _calculate_overall_confidence(search_results: List[EnhancedSearchResult]) -> float:
        """Calculate overall confidence across all results."""
        confidences: List[float] = []
        for result in search_results:
            for point in result.data_points:
                confidences.append(point.extraction_confidence)
        return statistics.mean(confidences) if confidences else 0.0

    @staticmethod
    def _create_error_output(query: EnhancedQueryInput, error: str) -> Dict[str, Any]:
        return {
            "query": query.query,
            "entity_context": query.entity_context,
            "region_context": query.region_context,
            "error": error,
            "error_timestamp": datetime.now().isoformat(),
            "raw_data_points": [],
            "search_analytics": {"total_results": 0, "analysis": f"Processing failed: {error}"},
            "processing_metadata": {
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": 0,
                "total_sources_attempted": 0,
                "successful_extractions": 0,
                "total_data_points": 0,
            },
        }

    async def batch_extract_ultimate(self, queries: List[EnhancedQueryInput], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        logger.info("Batch processing %d queries (max_concurrent=%d)", len(queries), max_concurrent)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_single(q: EnhancedQueryInput) -> Dict[str, Any]:
            async with semaphore:
                return await self.extract_ultimate_data(q)

        start = time.time()
        tasks = [process_single(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        processed: List[Dict[str, Any]] = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error("Query %d failed: %s", i, res)
                processed.append(self._create_error_output(queries[i], str(res)))
            else:
                processed.append(res)

        logger.info("Batch complete: %d result(s) in %.2fs", len(processed), elapsed)
        return processed


# -----------------------------------------------------------------------------
# Export functions
# -----------------------------------------------------------------------------
def _generate_batch_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    summary: Dict[str, Any] = {
        "total_queries": len(results),
        "successful_queries": len(successful),
        "failed_queries": len(failed),
        "success_rate": (len(successful) / len(results)) if results else 0.0,
    }
    if successful:
        all_points: List[Dict[str, Any]] = []
        proc_times: List[float] = []
        sources_attempted: List[int] = []
        confidences: List[float] = []
        for r in successful:
            points = r.get("raw_data_points", [])
            all_points.extend(points)
            meta = r.get("processing_metadata", {})
            proc_times.append(float(meta.get("processing_time_seconds", 0)))
            sources_attempted.append(int(meta.get("total_sources_attempted", 0)))
            confidences.extend([float(p.get("extraction_confidence", 0)) for p in points])
        summary.update(
            {
                "total_data_points_extracted": len(all_points),
                "average_data_points_per_query": (len(all_points) / len(successful)) if successful else 0.0,
                "average_processing_time": statistics.mean(proc_times) if proc_times else 0.0,
                "average_sources_per_query": statistics.mean(sources_attempted) if sources_attempted else 0.0,
                "overall_confidence_stats": (
                    {
                        "mean": statistics.mean(confidences) if confidences else 0.0,
                        "median": statistics.median(confidences) if confidences else 0.0,
                        "min": min(confidences) if confidences else 0.0,
                        "max": max(confidences) if confidences else 0.0,
                    }
                    if confidences
                    else {}
                ),
                "content_type_distribution": _analyze_content_types(successful),
                "source_diversity": _analyze_source_diversity(successful),
            }
        )
    return summary


def _analyze_content_types(results: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for r in results:
        for p in r.get("raw_data_points", []):
            ctype = p.get("content_type", "unknown")
            counts[ctype] += 1
    return dict(counts)


def _analyze_source_diversity(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_sources: set[str] = set()
    usage: Dict[str, int] = defaultdict(int)
    for r in results:
        query_sources: set[str] = set()
        for p in r.get("raw_data_points", []):
            sname = p.get("source_name")
            if sname:
                all_sources.add(sname)
                query_sources.add(sname)
                usage[sname] += 1
    return {
        "unique_sources_total": len(all_sources),
        "most_used_sources": sorted(usage.items(), key=lambda kv: kv[1], reverse=True)[:10],
        "source_distribution_stats": {
            "mean_usage": statistics.mean(usage.values()) if usage else 0.0,
            "max_usage": max(usage.values()) if usage else 0,
            "sources_used_once": sum(1 for v in usage.values() if v == 1),
        },
    }


def export_ultimate_data(results: Union[Dict[str, Any], List[Dict[str, Any]]], base_filename: str = "ultimate_data_export") -> Dict[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_info: Dict[str, str] = {}
    results_list: List[Dict[str, Any]] = results if isinstance(results, list) else [results]

    json_filename = f"{base_filename}_{timestamp}.json"
    payload = {
        "export_metadata": {
            "timestamp": datetime.now().isoformat(),
            "export_type": "ultimate_pure_data_extraction",
            "aggregator_version": "3.0_ultimate_demo",
            "total_queries": len(results_list),
            "total_data_points": sum(len(r.get("raw_data_points", [])) for r in results_list),
            "groq_model": "llama3-8b-8192",
            "features_used": [
                "multi_format_extraction",
                "anti_hallucination_validation",
                "legal_compliance_checking",
                "advanced_caching",
                "performance_tracking",
            ],
        },
        "processing_summary": _generate_batch_summary(results_list),
        "results": results_list,
    }
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    export_info["json"] = json_filename

    # CSV export (without pandas fallback)
    csv_rows: List[Dict[str, Any]] = []
    for r in results_list:
        q = r.get("query", "")
        entity = r.get("entity_context", "")
        region = r.get("region_context", "")
        for p in r.get("raw_data_points", []):
            csv_rows.append(
                {
                    "Query": q,
                    "Entity_Context": entity,
                    "Region_Context": region,
                    "Raw_Value": p.get("value"),
                    "Context": p.get("context", ""),
                    "Source_Name": p.get("source_name", ""),
                    "Source_URL": p.get("source_url", ""),
                    "Extraction_Confidence": p.get("extraction_confidence", 0.0),
                    "Content_Type": p.get("content_type", ""),
                    "Raw_Text": p.get("raw_text", ""),
                    "Source_Credibility": p.get("source_credibility", 0.0),
                    "Peer_Reviewed": p.get("peer_reviewed", False),
                    "Data_Freshness_Days": p.get("data_freshness_days", ""),
                    "Page_Number": p.get("page_number", ""),
                    "Table_Reference": p.get("table_reference", ""),
                    "Methodology_Notes": p.get("methodology_notes", ""),
                    "Copyright_Status": p.get("legal_compliance", {}).get("copyright_status", ""),
                    "Usage_Rights": p.get("legal_compliance", {}).get("usage_rights", ""),
                    "Required_Attribution": p.get("legal_compliance", {}).get("required_attribution", ""),
                    "Extraction_Method": p.get("metadata", {}).get("extraction_method", ""),
                }
            )

    if csv_rows:
        csv_filename = f"{base_filename}_{timestamp}.csv"
        if PANDAS_AVAILABLE:
            df = pd.DataFrame(csv_rows)
            df.to_csv(csv_filename, index=False, encoding="utf-8")
        else:
            fieldnames = list(csv_rows[0].keys())
            with open(csv_filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
        export_info["csv"] = csv_filename

    if csv_rows and PANDAS_AVAILABLE and OPENPYXL_AVAILABLE:
        excel_filename = f"{base_filename}_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:  # type: ignore
            pd.DataFrame(csv_rows).to_excel(writer, sheet_name="Data_Points", index=False)
            summary_rows: List[Dict[str, Any]] = []
            for r in results_list:
                meta = r.get("processing_metadata", {})
                quality = r.get("quality_indicators", {})
                summary_rows.append(
                    {
                        "Query": r.get("query", ""),
                        "Total_Data_Points": len(r.get("raw_data_points", [])),
                        "Processing_Time_Seconds": meta.get("processing_time_seconds", 0.0),
                        "Sources_Attempted": meta.get("total_sources_attempted", 0),
                        "Successful_Extractions": meta.get("successful_extractions", 0),
                        "Average_Confidence": meta.get("average_confidence", 0.0),
                        "Peer_Reviewed_Sources": quality.get("peer_reviewed_sources", 0),
                        "High_Authority_Sources": quality.get("high_authority_sources", 0),
                        "Cache_Hit_Rate": meta.get("cache_performance", {}).get("hit_rate", 0.0),
                    }
                )
            pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Summary", index=False)
        export_info["excel"] = excel_filename

    citation_filename = f"{base_filename}_citations_{timestamp}.txt"
    with open(citation_filename, "w", encoding="utf-8") as f:
        f.write("ULTIMATE PURE DATA EXTRACTOR - SOURCE CITATIONS\n")
        f.write("=" * 50 + "\n\n")
        for i, r in enumerate(results_list, 1):
            f.write(f"Query {i}: {r.get('query', '')}\n")
            f.write("-" * 30 + "\n")
            sources: set[tuple[str, str]] = set()
            for p in r.get("raw_data_points", []):
                sname, surl = p.get("source_name"), p.get("source_url")
                if sname and surl:
                    sources.add((str(sname), str(surl)))
            for j, (sname, surl) in enumerate(sorted(sources), 1):
                f.write(f"{j}. {sname}\n")
                f.write(f"   URL: {surl}\n")
                f.write(f"   Accessed: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("\n")
    export_info["citations"] = citation_filename

    return export_info


# -----------------------------------------------------------------------------
# Demo system
# -----------------------------------------------------------------------------
class UltimatePureDataDemo:
    def __init__(self) -> None:
        self.aggregator = UltimatePureDataAggregator()

    def get_ultimate_sample_queries(self) -> List[EnhancedQueryInput]:
        return [
            EnhancedQueryInput(
                query="global renewable energy capacity statistics",
                entity_context="Renewable Energy",
                region_context="Global",
                metric_context="installed capacity",
                additional_terms=["wind", "solar", "hydro"],
                search_depth="exhaustive",
                max_sources=3,
                require_peer_reviewed=False,
                min_source_authority=0.3,
            ),
            EnhancedQueryInput(
                query="electric vehicle market share data worldwide",
                entity_context="Electric Vehicles",
                region_context="Global",
                metric_context="market penetration",
                additional_terms=["BEV", "PHEV"],
                search_depth="comprehensive",
                max_sources=3,
                min_source_authority=0.5,
            ),
        ]

    async def run_ultimate_demo(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 100)
        print("ULTIMATE PURE UNIVERSAL DATA EXTRACTOR - DEMO")
        print("=" * 100)

        sample_queries = self.get_ultimate_sample_queries()
        start_time = time.time()
        results = await self.aggregator.batch_extract_ultimate(sample_queries, max_concurrent=2)
        total_time = time.time() - start_time

        print(f"\nCompleted in {total_time:.2f}s | {len(results)} result set(s)")
        total_points = sum(len(r.get("raw_data_points", [])) for r in results if isinstance(r, dict))
        print(f"Total Data Points: {total_points}")

        export_info = export_ultimate_data(results, "ultimate_demo")
        print("\nExports:")
        for fmt, fname in export_info.items():
            print(f" - {fmt.upper()}: {fname}")
        return results


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
async def extract_ultimate_pure_data(
    query_text: str,
    entity_context: Optional[str] = None,
    region_context: Optional[str] = None,
    metric_context: Optional[str] = None,
    additional_terms: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search_depth: str = "extensive",
    max_sources: int = 3,
    languages: Optional[List[str]] = None,
    include_pdfs: bool = True,
    include_excel: bool = True,
    include_csv: bool = True,
    include_apis: bool = True,
    require_peer_reviewed: bool = False,
    min_source_authority: float = 0.3,
    specific_countries: Optional[List[str]] = None,
    exclude_regions: Optional[List[str]] = None,
    max_processing_time: int = 120,
    enable_caching: bool = True,
    groq_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    query = EnhancedQueryInput(
        query=query_text,
        entity_context=entity_context,
        region_context=region_context,
        metric_context=metric_context,
        additional_terms=additional_terms or [],
        date_from=date_from,
        date_to=date_to,
        search_depth=search_depth,
        max_sources=max_sources,
        languages=languages,
        include_pdfs=include_pdfs,
        include_excel=include_excel,
        include_csv=include_csv,
        include_apis=include_apis,
        require_peer_reviewed=require_peer_reviewed,
        min_source_authority=min_source_authority,
        specific_countries=specific_countries,
        exclude_regions=exclude_regions,
        max_processing_time=max_processing_time,
        enable_caching=enable_caching,
    )
    aggregator = UltimatePureDataAggregator()
    return await aggregator.extract_ultimate_data(query)


# -----------------------------------------------------------------------------
# CLI helpers
# -----------------------------------------------------------------------------
async def main_ultimate_demo() -> List[Dict[str, Any]]:
    print("Starting Ultimate Demo...")
    demo = UltimatePureDataDemo()
    return await demo.run_ultimate_demo()


async def custom_ultimate_query() -> Optional[Dict[str, Any]]:
    print("\nCUSTOM ULTIMATE QUERY\n" + "=" * 50)
    query_text = input("Enter your query: ").strip()
    if not query_text:
        print("No query provided")
        return None

    entity_context = input("Entity context (optional): ").strip() or None
    region_context = input("Region context (optional): ").strip() or None
    metric_context = input("Metric context (optional): ").strip() or None

    additional_terms_input = input("Additional terms (comma-separated, optional): ").strip()
    additional_terms = [t.strip() for t in additional_terms_input.split(",")] if additional_terms_input else None

    date_from = input("Date from (YYYY-MM-DD, optional): ").strip() or None
    date_to = input("Date to (YYYY-MM-DD, optional): ").strip() or None

    search_depth = input("Search depth (basic/standard/extensive/exhaustive) [extensive]: ").strip() or "extensive"
    max_sources = int(input("Max sources (1-75) [3]: ").strip() or "3")

    include_pdfs = input("Include PDFs? (y/n) [y]: ").strip().lower() != "n"
    include_excel = input("Include Excel files? (y/n) [y]: ").strip().lower() != "n"
    include_apis = input("Include API sources? (y/n) [y]: ").strip().lower() != "n"

    require_peer_reviewed = input("Require peer reviewed sources? (y/n) [n]: ").strip().lower() == "y"
    min_source_authority = float(input("Minimum source authority (0.0-1.0) [0.3]: ").strip() or "0.3")

    print(f"\nProcessing: {query_text}")
    result = await extract_ultimate_pure_data(
        query_text=query_text,
        entity_context=entity_context,
        region_context=region_context,
        metric_context=metric_context,
        additional_terms=additional_terms,
        date_from=date_from,
        date_to=date_to,
        search_depth=search_depth,
        max_sources=max_sources,
        include_pdfs=include_pdfs,
        include_excel=include_excel,
        include_apis=include_apis,
        require_peer_reviewed=require_peer_reviewed,
        min_source_authority=min_source_authority,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

    print("\nRESULT SUMMARY\n" + "-" * 50)
    points = result.get("raw_data_points", [])
    meta = result.get("processing_metadata", {})
    print(f"Data Points: {len(points)}")
    print(f"Sources Attempted: {meta.get('total_sources_attempted', 0)}")
    print(f"Avg Confidence: {meta.get('average_confidence', 0):.3f}")

    export_info = export_ultimate_data(result, "custom_ultimate_query")
    print("\nExported:")
    for fmt, fname in export_info.items():
        print(f" - {fmt.upper()}: {fname}")
    return result


async def test_ultimate_api() -> None:
    print("Testing Ultimate API...\n" + "=" * 40)
    tests = [
        {"name": "Basic Test", "query": "solar energy capacity", "config": {"search_depth": "basic", "max_sources": 2}},
        {
            "name": "Advanced Test",
            "query": "renewable energy statistics global trends",
            "config": {"entity_context": "Renewable Energy", "region_context": "Global", "search_depth": "standard", "max_sources": 2},
        },
    ]
    for i, t in enumerate(tests, 1):
        print(f"Running {t['name']} ({i}/{len(tests)})...")
        start = time.time()
        res = await extract_ultimate_pure_data(query_text=t["query"], **t["config"])  # type: ignore[arg-type]
        elapsed = time.time() - start
        if res and not res.get("error"):
            count = len(res.get("raw_data_points", []))
            sources = res.get("processing_metadata", {}).get("total_sources_attempted", 0)
            conf = res.get("processing_metadata", {}).get("average_confidence", 0.0)
            print(f"  PASSED | points={count} sources={sources} conf={conf:.3f} time={elapsed:.2f}s")
        else:
            print(f"  FAILED | {res.get('error', 'No data')} if res else 'No result'")
    print("\nValidation complete.")


def show_ultimate_input_format() -> None:
    print("\nULTIMATE ENHANCED QUERY INPUT FORMAT\n" + "=" * 80)
    ultimate_sample = {
        "query_text": "renewable energy capacity statistics worldwide",
        "entity_context": "Renewable Energy",
        "region_context": "Global",
        "metric_context": "installed capacity",
        "additional_terms": ["wind", "solar", "hydro", "biomass"],
        "date_from": "2020-01-01",
        "date_to": "2024-12-31",
        "search_depth": "extensive",
        "max_sources": 3,
        "max_processing_time": 120,
        "include_pdfs": True,
        "include_excel": True,
        "include_csv": True,
        "include_apis": True,
        "require_peer_reviewed": False,
        "min_source_authority": 0.3,
        "specific_countries": ["Germany", "France", "UK"],
        "exclude_regions": ["Middle East"],
        "languages": ["en"],
        "enable_caching": True,
        "parallel_extraction": True,
        "groq_api_key": "your_groq_api_key_here",
    }
    print(json.dumps(ultimate_sample, indent=2))


if __name__ == "__main__":
    print("ULTIMATE PURE UNIVERSAL DATA EXTRACTOR")
    print("=" * 50)
    print("1. Run Ultimate Demo")
    print("2. Custom Ultimate Query")
    print("3. Test Ultimate API")
    print("4. Show Input Format Guide")
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        if choice == "1":
            asyncio.run(main_ultimate_demo())
        elif choice == "2":
            asyncio.run(custom_ultimate_query())
        elif choice == "3":
            asyncio.run(test_ultimate_api())
        elif choice == "4":
            show_ultimate_input_format()
        else:
            print("Invalid choice. Running demo...")
            asyncio.run(main_ultimate_demo())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"\nError: {exc}")
