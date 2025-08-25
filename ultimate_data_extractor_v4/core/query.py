import asyncio
import statistics
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote, urlparse

from ..ai.extractors.groq_extractor import GroqExtractor
from ..infrastructure.cache import CacheManager
from ..infrastructure.metrics import PerformanceTracker
from ..models.data_models import EnhancedRawDataPoint, EnhancedSearchResult
from ..models.source_models import ContentType, DataFreshness, EnhancedDataSource
from ..sources.fetcher import Fetcher
from ..sources.registry import SourceRegistry


class UltimateSearchEngine:
    def __init__(self, groq_api_key: str):
        self.source_registry = SourceRegistry()
        self.data_extractor = GroqExtractor(groq_api_key)
        self.cache_manager = CacheManager()
        self.performance_tracker = PerformanceTracker()

    async def search(self, query) -> List[EnhancedSearchResult]:
        sources = self.source_registry.get_sources_by_priority(max_sources=query.max_sources)
        searches_per_source = {"basic": 1, "standard": 2, "extensive": 3, "exhaustive": 4}.get(query.search_depth, 3)
        all_results: List[EnhancedSearchResult] = []
        max_concurrent = {"basic": 8, "standard": 12, "extensive": 16, "exhaustive": 20}.get(query.search_depth, 16)
        semaphore = asyncio.Semaphore(max_concurrent)

        async with Fetcher(max_concurrent=max_concurrent) as fetcher:
            tasks: List[asyncio.Task] = []
            variations = self._generate_intelligent_variations(query)
            for source in sources:
                for vq in variations[:searches_per_source]:
                    tasks.append(asyncio.create_task(self._search_single_source(source, vq, query, semaphore, fetcher)))

            try:
                results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=query.max_processing_time)
            except asyncio.TimeoutError:
                results = []

        for r in results:
            if isinstance(r, list):
                all_results.extend(r)
        processed_results = await self._process_results(all_results, query)
        self.performance_tracker.record_extraction(
            accuracy=self._calculate_average_confidence(processed_results),
            response_time=0.0,
            source="ultimate_search",
            success=len(processed_results) > 0,
        )
        return processed_results

    def _generate_intelligent_variations(self, query) -> List[str]:
        v: List[str] = [query.query]
        if query.entity_context:
            v.extend([f"{query.entity_context} {query.query}", f"{query.query} {query.entity_context}"])
        if query.region_context:
            v.extend([f"{query.query} {query.region_context}", f"{query.region_context} {query.query}"])
        if query.metric_context:
            v.extend([f"{query.metric_context} {query.query}", f"{query.query} {query.metric_context} data"])
        for term in (query.additional_terms or [])[:3]:
            v.extend([f"{query.query} {term}", f"{term} {query.query}"])
        return list(dict.fromkeys(v))

    async def _search_single_source(self, source: EnhancedDataSource, search_query: str, query, semaphore: asyncio.Semaphore, fetcher: Fetcher) -> List[EnhancedSearchResult]:
        async with semaphore:
            results: List[EnhancedSearchResult] = []
            for pattern in source.search_patterns:
                url = pattern.format(query=quote(search_query))
                try:
                    cache_key = self.cache_manager.get_cache_key(url, search_query) if query.enable_caching else None
                    if cache_key:
                        cached = self.cache_manager.get(cache_key, ttl_hours=self._get_cache_ttl(source))
                        if cached:
                            results.extend(cached)
                            continue
                    fetch = await fetcher.fetch_content(url, source)
                    if not fetch or not fetch.get("success"):
                        results.append(
                            EnhancedSearchResult(
                                query=search_query,
                                source=source.name,
                                url=url,
                                title="Fetch Failed",
                                content="",
                                data_points=[],
                                content_type=ContentType.HTML,
                                errors_encountered=[(fetch or {}).get("error", "Unknown error")],
                                blocked_by_paywall=(fetch or {}).get("blocked_by_paywall", False),
                                rate_limited=(fetch or {}).get("rate_limited", False),
                            )
                        )
                        continue
                    content = fetch["content"]
                    ctype: ContentType = fetch.get("content_type", ContentType.HTML)
                    if not content:
                        continue
                    extracted = await self.data_extractor.extract(content if isinstance(content, str) else str(content), query, ctype)
                    if extracted:
                        for p in extracted:
                            p.source_url = url
                            p.source_name = source.name
                            p.source_credibility = source.authority
                            p.peer_reviewed = source.peer_reviewed
                            if source.data_freshness != DataFreshness.STATIC:
                                p.data_freshness_days = self._freshness_days(source.data_freshness)
                        result = EnhancedSearchResult(
                            query=search_query,
                            source=source.name,
                            url=url,
                            title=fetch.get("title", "Data Source Content"),
                            content=(content if isinstance(content, str) else f"{ctype.value} bytes: {len(content)}")[:3000],
                            data_points=extracted,
                            content_type=ctype,
                            extraction_accuracy=self._calculate_extraction_accuracy(extracted),
                            content_completeness=min((len(content) if isinstance(content, str) else len(content)) / 5000, 1.0),
                            source_authority=source.authority,
                        )
                        results.append(result)
                        if query.enable_caching and cache_key:
                            self.cache_manager.set(cache_key, [result])
                except Exception:
                    continue
            return results

    def _get_cache_ttl(self, source: EnhancedDataSource) -> int:
        mapping = {
            DataFreshness.REAL_TIME: 1,
            DataFreshness.DAILY: 6,
            DataFreshness.WEEKLY: 24,
            DataFreshness.MONTHLY: 168,
            DataFreshness.QUARTERLY: 720,
            DataFreshness.ANNUALLY: 2160,
            DataFreshness.STATIC: 8760,
        }
        return mapping.get(source.data_freshness, 24)

    @staticmethod
    def _freshness_days(freshness: DataFreshness) -> int:
        mapping = {
            DataFreshness.REAL_TIME: 0,
            DataFreshness.DAILY: 1,
            DataFreshness.WEEKLY: 7,
            DataFreshness.MONTHLY: 30,
            DataFreshness.QUARTERLY: 90,
            DataFreshness.ANNUALLY: 365,
            DataFreshness.STATIC: 999,
        }
        return mapping.get(freshness, 30)

    @staticmethod
    def _calculate_extraction_accuracy(data_points: List[EnhancedRawDataPoint]) -> float:
        if not data_points:
            return 0.0
        return sum(p.extraction_confidence for p in data_points) / len(data_points)

    @staticmethod
    def _calculate_average_confidence(results: List[EnhancedSearchResult]) -> float:
        vals: List[float] = []
        for r in results:
            for p in r.data_points:
                vals.append(p.extraction_confidence)
        return statistics.mean(vals) if vals else 0.0

    async def _process_results(self, all_results: List[EnhancedSearchResult], query) -> List[EnhancedSearchResult]:
        if not all_results:
            return []
        with_data = [r for r in all_results if r.data_points]
        if not with_data:
            return all_results[:10]
        unique = await self._deduplicate_results(with_data)
        filtered = self._apply_quality_filters(unique, query)
        ranked = self._rank_results(filtered, query)
        diverse = self._ensure_source_diversity(ranked)
        return diverse

    async def _deduplicate_results(self, results: List[EnhancedSearchResult]) -> List[EnhancedSearchResult]:
        seen: Set[str] = set()
        unique: List[EnhancedSearchResult] = []
        for r in results:
            domain = urlparse(r.url).netloc
            values = [str(p.value) for p in r.data_points[:5]]
            signature = f"{domain}_{r.title[:50]}_{'_'.join(values)}"
            sig_hash = str(abs(hash(signature)))
            if sig_hash not in seen:
                seen.add(sig_hash)
                unique.append(r)
        return unique

    @staticmethod
    def _apply_quality_filters(results: List[EnhancedSearchResult], query) -> List[EnhancedSearchResult]:
        out: List[EnhancedSearchResult] = []
        for r in results:
            if getattr(query, "min_source_authority", 0) and r.source_authority and r.source_authority < query.min_source_authority:
                continue
            if getattr(query, "require_peer_reviewed", False) and not any(p.peer_reviewed for p in r.data_points):
                continue
            if r.data_points:
                avg_conf = statistics.mean(p.extraction_confidence for p in r.data_points)
                if avg_conf < 0.2:
                    continue
            out.append(r)
        return out

    @staticmethod
    def _rank_results(results: List[EnhancedSearchResult], query) -> List[EnhancedSearchResult]:
        def score(r: EnhancedSearchResult) -> float:
            s = 0.0
            if r.source_authority:
                s += r.source_authority * 0.30
            s += min(len(r.data_points) / 10.0, 0.25)
            if r.extraction_accuracy:
                s += r.extraction_accuracy * 0.20
            if r.content_completeness:
                s += r.content_completeness * 0.15
            terms = query.query.lower().split()
            txt = r.content.lower()
            rel = sum(1 for t in terms if t in txt) / max(len(terms), 1)
            s += rel * 0.10
            return min(s, 1.0)

        return sorted(results, key=score, reverse=True)

    @staticmethod
    def _ensure_source_diversity(results: List[EnhancedSearchResult], max_per_source: int = 5) -> List[EnhancedSearchResult]:
        out: List[EnhancedSearchResult] = []
        counts: Dict[str, int] = {}
        for r in results:
            counts[r.source] = counts.get(r.source, 0) + 1
            if counts[r.source] <= max_per_source:
                out.append(r)
        return out[:50]

