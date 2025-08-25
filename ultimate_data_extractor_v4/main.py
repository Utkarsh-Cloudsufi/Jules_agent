import os
from typing import Any, Dict, List, Optional

from .core.extractor import Aggregator
from .models.query_models import QueryInput


async def extract_ultimate_pure_data(
    query_text: str,
    entity_context: Optional[str] = None,
    region_context: Optional[str] = None,
    metric_context: Optional[str] = None,
    additional_terms: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search_depth: str = "extensive",
    max_sources: int = 50,
    languages: Optional[List[str]] = None,
    include_pdfs: bool = True,
    include_excel: bool = True,
    include_csv: bool = True,
    include_apis: bool = True,
    require_peer_reviewed: bool = False,
    min_source_authority: float = 0.3,
    specific_countries: Optional[List[str]] = None,
    exclude_regions: Optional[List[str]] = None,
    max_processing_time: int = 600,
    enable_caching: bool = True,
    groq_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API key required")
    query = QueryInput(
        query=query_text,
        entity_context=entity_context,
        region_context=region_context,
        metric_context=metric_context,
        additional_terms=additional_terms or [],
        date_from=date_from,
        date_to=date_to,
        search_depth=search_depth,  # type: ignore[arg-type]
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
    aggregator = Aggregator(api_key)
    return await aggregator.extract(query)

