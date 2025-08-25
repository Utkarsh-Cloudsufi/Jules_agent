from typing import Any

from ..models.data_models import EnhancedRawDataPoint


class AntiHallucinationValidator:
    @staticmethod
    def verify_data_existence(data_point: EnhancedRawDataPoint, original_content: str) -> float:
        try:
            raw_text = (data_point.raw_text or "").lower()
            content_lower = (original_content or "").lower()
            if raw_text and raw_text in content_lower:
                return 1.0
            value_str = str(data_point.value).lower()
            if value_str and value_str in content_lower:
                return 0.9
            context_words = (data_point.context or "").lower().split()
            if not context_words:
                return 0.0
            matches = sum(1 for w in context_words if w in content_lower)
            return min(matches / max(len(context_words), 1), 0.8)
        except Exception:
            return 0.0

