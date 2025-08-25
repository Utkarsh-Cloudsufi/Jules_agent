"""
FastAPI server for Ultimate Pure Data Extractor v4-style API over v3 engine.

Endpoints:
- POST /api/v4/extract
- GET  /api/v4/health
- GET  /api/v4/sources
- GET  /api/v4/metrics

Requires:
- GROQ_API_KEY (for full AI extraction; without it, service returns 503 on extract)
- API_SECRET_KEY (HTTP Bearer token; defaults to 'demo-key')
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ultimate_pure_extractor import (
    EnhancedQueryInput,
    UltimatePureDataAggregator,
    ComprehensiveSourceRegistry,
)


class ExtractRequestV4(BaseModel):
    query: str = Field("", description="Query text")
    entity_context: Optional[str] = None
    region_context: Optional[str] = None
    metric_context: Optional[str] = None
    additional_terms: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search_depth: str = "extensive"
    max_sources: int = 50
    languages: Optional[List[str]] = None
    include_pdfs: bool = True
    include_excel: bool = True
    include_csv: bool = True
    include_apis: bool = True
    require_peer_reviewed: bool = False
    min_source_authority: float = 0.3
    specific_countries: Optional[List[str]] = None
    exclude_regions: Optional[List[str]] = None
    max_processing_time: int = 600
    enable_caching: bool = True


app = FastAPI(
    title="Ultimate Pure Data Extractor v4 API",
    description="v4-style API backed by the v3 Ultimate engine",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


class AppState:
    aggregator: Optional[UltimatePureDataAggregator] = None
    registry: Optional[ComprehensiveSourceRegistry] = None
    metrics: Dict[str, Any] = {
        "total_requests": 0,
        "successful_extractions": 0,
        "last_request_ts": None,
    }


state = AppState()


@app.on_event("startup")
async def on_startup() -> None:
    state.registry = ComprehensiveSourceRegistry()
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            state.aggregator = UltimatePureDataAggregator(groq_key)
        except Exception:
            state.aggregator = None


@app.on_event("shutdown")
async def on_shutdown() -> None:
    return


def _require_api_key(credentials: HTTPAuthorizationCredentials) -> None:
    secret = os.getenv("API_SECRET_KEY", "demo-key")
    if not credentials or credentials.credentials != secret:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.post("/api/v4/extract")
async def extract_v4(
    query_request: ExtractRequestV4,
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    _require_api_key(credentials)

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise HTTPException(status_code=503, detail="Service requires GROQ_API_KEY")

    if state.aggregator is None:
        try:
            state.aggregator = UltimatePureDataAggregator(groq_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize aggregator: {e}")

    q = EnhancedQueryInput(
        query=query_request.query,
        entity_context=query_request.entity_context,
        region_context=query_request.region_context,
        metric_context=query_request.metric_context,
        additional_terms=query_request.additional_terms or [],
        date_from=query_request.date_from,
        date_to=query_request.date_to,
        languages=query_request.languages,
        include_pdfs=query_request.include_pdfs,
        include_excel=query_request.include_excel,
        include_csv=query_request.include_csv,
        include_apis=query_request.include_apis,
        exclude_regions=query_request.exclude_regions,
        specific_countries=query_request.specific_countries,
        max_sources=query_request.max_sources,
        search_depth=query_request.search_depth,
        require_peer_reviewed=query_request.require_peer_reviewed,
        min_source_authority=query_request.min_source_authority,
        max_processing_time=query_request.max_processing_time,
        enable_caching=query_request.enable_caching,
    )

    state.metrics["total_requests"] += 1
    state.metrics["last_request_ts"] = datetime.now(timezone.utc).isoformat()

    try:
        result = await state.aggregator.extract_ultimate_data(q)  # type: ignore[arg-type]
        if result and not result.get("error"):
            state.metrics["successful_extractions"] += 1
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Processing timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v4/health")
async def health_v4() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "version": "4.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "groq_ready": bool(os.getenv("GROQ_API_KEY")),
        "available_sources": len(state.registry.sources) if state.registry else 0,  # type: ignore[attr-defined]
    }


@app.get("/api/v4/sources")
async def sources_v4() -> Dict[str, Any]:
    if not state.registry:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    items: List[Dict[str, Any]] = []
    for s in state.registry.sources:  # type: ignore[attr-defined]
        items.append(
            {
                "name": s.name,
                "authority": s.authority,
                "priority": s.priority.name,
                "content_types": [ct.value for ct in s.content_types],
                "data_freshness": s.data_freshness.value,
                "geographic_coverage": s.geographic_coverage,
                "peer_reviewed": s.peer_reviewed,
                "requires_auth": s.requires_auth,
            }
        )
    return {"total_sources": len(items), "sources": items}


@app.get("/api/v4/metrics")
async def metrics_v4() -> Dict[str, Any]:
    perf = None
    cache = None
    if state.aggregator:
        perf = state.aggregator.performance_tracker.get_summary()
        cache = state.aggregator.search_engine.cache_manager.cache_stats  # type: ignore[attr-defined]
    return {
        "api_metrics": state.metrics,
        "aggregator_performance": perf or {},
        "cache_stats": cache or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

