"""
services/inventory_service.py
Service layer for inventory management, transaction logs, and stock adjustments.
"""
from typing import List, Dict, Any, Optional
from database.queries import (
    get_inventory_view,
    get_inventory_transactions,
    execute_write,
    execute_read_one,
    get_connection
)

class InventoryService:
    @staticmethod
    def get_inventory(category=None, supplier=None, status=None, search=None, sort_by=None) -> List[Dict[str, Any]]:
        return get_inventory_view(category, supplier, status, search, sort_by)

    @staticmethod
    def get_transactions(product_id: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        return get_inventory_transactions(product_id, limit)

    @staticmethod
    def adjust_stock(product_id: int, new_stock: int, notes: str = "Manual Adjustment") -> bool:
        """Manually adjust stock with audit trail in inventory_transactions."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT current_stock FROM products WHERE product_id = %s FOR UPDATE", (product_id,))
            prod = cursor.fetchone()
            if not prod:
                raise ValueError(f"Product ID {product_id} not found.")
            
            old_stock = prod['current_stock']
            diff = new_stock - old_stock
            
            # Update product stock
            cursor.execute("UPDATE products SET current_stock = %s WHERE product_id = %s", (new_stock, product_id))
            
            # Record transaction
            from datetime import date
            cursor.execute("""
                INSERT INTO inventory_transactions (product_id, transaction_type, quantity, transaction_date, notes)
                VALUES (%s, 'ADJUSTMENT', %s, %s, %s)
            """, (product_id, diff, date.today(), f"{notes} (from {old_stock} to {new_stock})"))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
