"""
services/reorder_service.py
Dedicated helper service for Reorder Recommendations page.
"""
from typing import List, Dict, Any
from services.forecasting_service import ForecastingService

class ReorderService:
    @staticmethod
    def get_reorder_list(method: str = "Linear Regression") -> List[Dict[str, Any]]:
        return ForecastingService.get_reorder_recommendations(method=method)
