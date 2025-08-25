from typing import Any, Dict

from ..models.source_models import EnhancedDataSource


class LegalComplianceChecker:
    @staticmethod
    def check_compliance(source: EnhancedDataSource, content_length: int) -> Dict[str, Any]:
        info: Dict[str, Any] = {"compliant": True, "warnings": [], "required_actions": []}
        if content_length > 10000:
            info["warnings"].append("Large content extraction - verify fair use")
        if source.copyright_status not in ["public_domain", "fair_use", "creative_commons"]:
            info["warnings"].append("Verify copyright permissions")
        if "commercial" in source.usage_rights and source.usage_rights != "commercial_allowed":
            info["warnings"].append("Non-commercial use only")
        if source.institutional_backing:
            info["required_actions"].append(f"Cite: {source.name}")
        return info

