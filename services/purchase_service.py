"""
services/purchase_service.py
Service layer for purchases and restocking.
"""
from typing import List, Dict, Any
from database.queries import record_purchase_transaction, get_purchases_list, get_purchase_details

class PurchaseService:
    @staticmethod
    def process_purchase(supplier_id: int, purchase_date: str, items: List[Dict[str, Any]], notes: str = "") -> int:
        if not items:
            raise ValueError("No purchase items provided.")
        return record_purchase_transaction(supplier_id, purchase_date, items, notes)

    @staticmethod
    def get_recent_purchases(limit: int = 150) -> List[Dict[str, Any]]:
        return get_purchases_list(limit)

    @staticmethod
    def get_purchase(purchase_id: int) -> Dict[str, Any]:
        return get_purchase_details(purchase_id)
