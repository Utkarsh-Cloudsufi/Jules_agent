import statistics
from collections import defaultdict
from typing import Any, Dict


class PerformanceTracker:
    def __init__(self) -> None:
        self.metrics: Dict[str, Any] = {
            "extraction_accuracy": [],
            "response_times": [],
            "total_requests": 0,
            "successful_extractions": 0,
            "error_rates": defaultdict(int),
        }

    def record_extraction(self, accuracy: float, response_time: float, source: str, success: bool = True) -> None:
        self.metrics["extraction_accuracy"].append(accuracy)
        self.metrics["response_times"].append(response_time)
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_extractions"] += 1
        else:
            self.metrics["error_rates"][source] += 1

    def get_summary(self) -> Dict[str, Any]:
        return {
            "avg_accuracy": statistics.mean(self.metrics["extraction_accuracy"]) if self.metrics["extraction_accuracy"] else 0,
            "avg_response_time": statistics.mean(self.metrics["response_times"]) if self.metrics["response_times"] else 0,
            "success_rate": self.metrics["successful_extractions"] / max(self.metrics["total_requests"], 1),
            "total_extractions": self.metrics["total_requests"],
            "error_summary": dict(self.metrics["error_rates"]),
        }

