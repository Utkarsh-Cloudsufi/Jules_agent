import json
import re
from typing import Any, Dict, List

from ..validators import AntiHallucinationValidator
from .base import BaseExtractor
from ...models.data_models import EnhancedRawDataPoint
from ...models.source_models import ContentType


try:
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover
    Groq = None  # type: ignore


class GroqExtractor(BaseExtractor):
    def __init__(self, api_key: str, model: str = "llama3-8b-8192") -> None:
        self.model = model
        self.validator = AntiHallucinationValidator()
        self.client = None
        if Groq and api_key:
            try:
                self.client = Groq(api_key=api_key)  # type: ignore
            except Exception:
                self.client = None

    async def extract(self, content: str, query, content_type: ContentType) -> List[EnhancedRawDataPoint]:
        if not self.client:
            return self._regex_extract(content, content_type)
        try:
            prompt = self._build_prompt(content, query, content_type)
            resp = self.client.chat.completions.create(  # type: ignore
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.05,
                max_tokens=1500,
            )
            content_out = resp.choices[0].message.content.strip()  # type: ignore
            data = self._parse_json_response(content_out)
            points: List[EnhancedRawDataPoint] = []
            for p in data.get("data_points", []):
                if p.get("value") is None:
                    continue
                point = EnhancedRawDataPoint(
                    value=p.get("value"),
                    context=p.get("context", ""),
                    source_url="",
                    source_name="",
                    extraction_confidence=float(p.get("confidence", 0.5)),
                    raw_text=p.get("raw_text", ""),
                    content_type=content_type,
                    methodology_notes=p.get("methodology", ""),
                    metadata={"extraction_method": "ai_llm"},
                )
                score = self.validator.verify_data_existence(point, content)
                point.extraction_confidence *= score
                if point.extraction_confidence > 0.1:
                    points.append(point)
            return points
        except Exception:
            return self._regex_extract(content, content_type)

    def _regex_extract(self, text: str, content_type: ContentType) -> List[EnhancedRawDataPoint]:
        nums = re.findall(r"[-+]?\d*[\.,]?\d+%?", text)[:5]
        points: List[EnhancedRawDataPoint] = []
        for n in nums:
            points.append(
                EnhancedRawDataPoint(
                    value=n,
                    context=text[:120],
                    source_url="",
                    source_name="",
                    extraction_confidence=0.3,
                    raw_text=n,
                    content_type=content_type,
                    metadata={"extraction_method": "regex_fallback"},
                )
            )
        return points

    def _build_prompt(self, content: str, query, content_type: ContentType) -> str:
        add_terms = ", ".join(query.additional_terms or [])
        date_constraint = ""
        if query.date_from or query.date_to:
            date_constraint = f"\nDATE: {query.date_from or 'any'} to {query.date_to or 'any'}"
        return (
            f"EXTRACT RAW NUMERICAL DATA (no synthesis)\n"
            f"Query: {query.query}\nEntity: {query.entity_context or 'n/a'}\nRegion: {query.region_context or 'n/a'}\n"
            f"Metric: {query.metric_context or 'n/a'}\nTerms: {add_terms}{date_constraint}\n"
            f"CONTENT_TYPE: {content_type.value}\n"
            f"CONTENT:\n{content[:8000]}\n\n"
            "Return JSON with {'data_points': [{'value','context','confidence','raw_text','methodology'}]}"
        )

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        try:
            if response.strip().startswith("{"):
                return json.loads(response)
        except Exception:
            pass
        try:
            if "```json" in response:
                s = response.find("```json") + 7
                e = response.find("```", s)
                return json.loads(response[s:e].strip())
        except Exception:
            pass
        try:
            start = response.find("{")
            if start != -1:
                brace = 0
                for i, ch in enumerate(response[start:], start):
                    if ch == "{":
                        brace += 1
                    elif ch == "}":
                        brace -= 1
                        if brace == 0:
                            return json.loads(response[start : i + 1])
        except Exception:
            pass
        return {"data_points": []}

