"""
services/sales_service.py
Service layer for sales transactions and cart processing.
"""
from typing import List, Dict, Any
from database.queries import record_sale_transaction, get_sales_list, get_sale_details

class SalesService:
    @staticmethod
    def process_sale(user_id: int, sale_date: str, items: List[Dict[str, Any]]) -> int:
        if not items:
            raise ValueError("Cart is empty. Please add items to complete sale.")
        return record_sale_transaction(user_id, sale_date, items)

    @staticmethod
    def get_recent_sales(limit: int = 150) -> List[Dict[str, Any]]:
        return get_sales_list(limit)

    @staticmethod
    def get_sale(sale_id: int) -> Dict[str, Any]:
        return get_sale_details(sale_id)
