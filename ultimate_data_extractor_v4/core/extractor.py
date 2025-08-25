import statistics
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ..core.query import UltimateSearchEngine
from ..infrastructure.metrics import PerformanceTracker
from ..models.data_models import EnhancedSearchResult


class Aggregator:
    def __init__(self, groq_api_key: str):
        if not groq_api_key:
            raise ValueError("Groq API key is required")
        self.search_engine = UltimateSearchEngine(groq_api_key)
        self.performance_tracker = PerformanceTracker()

    async def extract(self, query) -> Dict[str, Any]:
        start = time.time()
        try:
            search_results = await self.search_engine.search(query)
            analysis = await self._analyze(search_results)
            processing_time = time.time() - start
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
                        "metadata": p.metadata,
                    }
                    for r in search_results
                    for p in r.data_points
                ],
                "search_analytics": analysis,
                "processing_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "processing_time_seconds": round(processing_time, 2),
                    "model": "llama3-8b-8192",
                    "aggregator_version": "4.0_modular",
                    "total_sources_attempted": len({r.source for r in search_results}),
                    "successful_extractions": len([r for r in search_results if r.data_points]),
                    "total_data_points": sum(len(r.data_points) for r in search_results),
                    "average_confidence": self._average_confidence(search_results),
                    "content_types_processed": list({r.content_type.value for r in search_results}),
                },
                "performance_metrics": self.performance_tracker.get_summary(),
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
            return output
        except Exception as e:
            return self._error(query, str(e))

    def _average_confidence(self, search_results: List[EnhancedSearchResult]) -> float:
        vals: List[float] = []
        for r in search_results:
            for p in r.data_points:
                vals.append(p.extraction_confidence)
        return statistics.mean(vals) if vals else 0.0

    async def _analyze(self, search_results: List[EnhancedSearchResult]) -> Dict[str, Any]:
        if not search_results:
            return {"total_results": 0, "analysis": "No results found"}
        from collections import defaultdict

        source_breakdown = defaultdict(lambda: {"data_points": 0, "avg_confidence": 0, "content_types": set(), "authority": 0})
        all_conf: List[float] = []
        content_type_counts = defaultdict(int)
        error_summary = defaultdict(int)
        for r in search_results:
            sb = source_breakdown[r.source]
            sb["data_points"] += len(r.data_points)
            sb["authority"] = r.source_authority or 0
            sb["content_types"].add(r.content_type.value)
            pcs = [p.extraction_confidence for p in r.data_points]
            all_conf.extend(pcs)
            if pcs:
                sb["avg_confidence"] = statistics.mean(pcs)
            content_type_counts[r.content_type.value] += 1
            for e in r.errors_encountered:
                error_summary[e] += 1
        for v in source_breakdown.values():
            v["content_types"] = list(v["content_types"])
        return {
            "total_results": len(search_results),
            "results_with_data": len([r for r in search_results if r.data_points]),
            "total_data_points": sum(len(r.data_points) for r in search_results),
            "average_extraction_accuracy": statistics.mean(all_conf) if all_conf else 0,
            "source_breakdown": dict(source_breakdown),
            "content_type_distribution": dict(content_type_counts),
            "error_summary": dict(error_summary),
        }

    def _error(self, query, error: str) -> Dict[str, Any]:
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

