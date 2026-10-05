"""
database/queries.py
Centralized SQL queries executing parameterized statements and demonstrating DBMS concepts:
- JOIN, GROUP BY, HAVING, ORDER BY
- Transactions with commit/rollback
- Subqueries and Aggregations
- Views integration
"""
from typing import List, Dict, Any, Optional, Tuple
from mysql.connector import Error
from database.connection import get_connection

def execute_read(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return rows as list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()

def execute_read_one(query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    """Execute a SELECT query and return single row dict or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        return result
    finally:
        cursor.close()
        conn.close()

def execute_write(query: str, params: Optional[Tuple] = None) -> int:
    """Execute INSERT/UPDATE/DELETE query with autocommit/commit. Returns lastrowid or affected rows."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        rowcount = cursor.rowcount
        return last_id if last_id > 0 else rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────────────────────────
def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT user_id, name, username, password_hash, role FROM users WHERE username = %s"
    return execute_read_one(sql, (username,))

def create_user(name: str, username: str, password_hash: str, role: str = 'staff') -> int:
    sql = "INSERT INTO users (name, username, password_hash, role) VALUES (%s, %s, %s, %s)"
    return execute_write(sql, (name, username, password_hash, role))

# ─────────────────────────────────────────────────────────────
# CATEGORIES QUERIES
# ─────────────────────────────────────────────────────────────
def get_all_categories() -> List[Dict[str, Any]]:
    sql = """
        SELECT c.category_id, c.category_name, c.description,
               COUNT(p.product_id) AS product_count
        FROM categories c
        LEFT JOIN products p ON c.category_id = p.category_id
        GROUP BY c.category_id, c.category_name, c.description
        ORDER BY c.category_name ASC
    """
    return execute_read(sql)

def add_category(name: str, description: str) -> int:
    sql = "INSERT INTO categories (category_name, description) VALUES (%s, %s)"
    return execute_write(sql, (name, description))

def update_category(category_id: int, name: str, description: str) -> int:
    sql = "UPDATE categories SET category_name = %s, description = %s WHERE category_id = %s"
    return execute_write(sql, (name, description, category_id))

def delete_category(category_id: int) -> int:
    sql = "DELETE FROM categories WHERE category_id = %s"
    return execute_write(sql, (category_id,))

# ─────────────────────────────────────────────────────────────
# SUPPLIERS QUERIES
# ─────────────────────────────────────────────────────────────
def get_all_suppliers() -> List[Dict[str, Any]]:
    sql = """
        SELECT s.supplier_id, s.supplier_name, s.phone, s.email, s.address, s.lead_time,
               COUNT(DISTINCT p.product_id) AS total_products,
               COUNT(DISTINCT pu.purchase_id) AS total_purchases
        FROM suppliers s
        LEFT JOIN products p ON s.supplier_id = p.supplier_id
        LEFT JOIN purchases pu ON s.supplier_id = pu.supplier_id
        GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email, s.address, s.lead_time
        ORDER BY s.supplier_name ASC
    """
    return execute_read(sql)

def add_supplier(name: str, phone: str, email: str, address: str, lead_time: int) -> int:
    sql = """
        INSERT INTO suppliers (supplier_name, phone, email, address, lead_time)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_write(sql, (name, phone, email, address, lead_time))

def update_supplier(supplier_id: int, name: str, phone: str, email: str, address: str, lead_time: int) -> int:
    sql = """
        UPDATE suppliers
        SET supplier_name = %s, phone = %s, email = %s, address = %s, lead_time = %s
        WHERE supplier_id = %s
    """
    return execute_write(sql, (name, phone, email, address, lead_time, supplier_id))

def delete_supplier(supplier_id: int) -> int:
    sql = "DELETE FROM suppliers WHERE supplier_id = %s"
    return execute_write(sql, (supplier_id,))

def get_supplier_products(supplier_id: int) -> List[Dict[str, Any]]:
    sql = """
        SELECT product_id, product_name, current_stock, purchase_price, selling_price
        FROM products WHERE supplier_id = %s ORDER BY product_name
    """
    return execute_read(sql, (supplier_id,))

def get_supplier_purchase_history(supplier_id: int) -> List[Dict[str, Any]]:
    sql = """
        SELECT p.purchase_id, p.purchase_date, p.total_amount, p.notes,
               COUNT(pi.purchase_item_id) as items_count
        FROM purchases p
        LEFT JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
        WHERE p.supplier_id = %s
        GROUP BY p.purchase_id, p.purchase_date, p.total_amount, p.notes
        ORDER BY p.purchase_date DESC
    """
    return execute_read(sql, (supplier_id,))

# ─────────────────────────────────────────────────────────────
# PRODUCTS QUERIES
# ─────────────────────────────────────────────────────────────
def get_all_products(category_id: Optional[int] = None, supplier_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = """
        SELECT p.product_id, p.product_name, p.category_id, c.category_name,
               p.supplier_id, s.supplier_name, p.purchase_price, p.selling_price,
               p.current_stock, p.reorder_level, p.safety_stock, s.lead_time,
               (p.current_stock * p.purchase_price) AS stock_value
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE 1=1
    """
    params = []
    if category_id:
        sql += " AND p.category_id = %s"
        params.append(category_id)
    if supplier_id:
        sql += " AND p.supplier_id = %s"
        params.append(supplier_id)
    if search:
        sql += " AND (p.product_name LIKE %s OR CAST(p.product_id AS CHAR) LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term])
    sql += " ORDER BY p.product_id ASC"
    return execute_read(sql, tuple(params))

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT p.*, c.category_name, s.supplier_name, s.lead_time
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.product_id = %s
    """
    return execute_read_one(sql, (product_id,))

def add_product(name: str, category_id: int, supplier_id: int, purchase_price: float,
                selling_price: float, stock: int, reorder_level: int, safety_stock: int) -> int:
    sql = """
        INSERT INTO products 
        (product_name, category_id, supplier_id, purchase_price, selling_price, current_stock, reorder_level, safety_stock)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_write(sql, (name, category_id, supplier_id, purchase_price, selling_price, stock, reorder_level, safety_stock))

def update_product(product_id: int, name: str, category_id: int, supplier_id: int, purchase_price: float,
                   selling_price: float, stock: int, reorder_level: int, safety_stock: int) -> int:
    sql = """
        UPDATE products 
        SET product_name = %s, category_id = %s, supplier_id = %s,
            purchase_price = %s, selling_price = %s, current_stock = %s,
            reorder_level = %s, safety_stock = %s
        WHERE product_id = %s
    """
    return execute_write(sql, (name, category_id, supplier_id, purchase_price, selling_price, stock, reorder_level, safety_stock, product_id))

def delete_product(product_id: int) -> int:
    sql = "DELETE FROM products WHERE product_id = %s"
    return execute_write(sql, (product_id,))

# ─────────────────────────────────────────────────────────────
# INVENTORY TRANSACTIONS & VIEW QUERIES
# ─────────────────────────────────────────────────────────────
def get_inventory_view(category_filter=None, supplier_filter=None, status_filter=None, search=None, sort_by=None) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM v_inventory_overview WHERE 1=1"
    params = []
    if category_filter and category_filter != "All":
        sql += " AND category_name = %s"
        params.append(category_filter)
    if supplier_filter and supplier_filter != "All":
        sql += " AND supplier_name = %s"
        params.append(supplier_filter)
    if status_filter and status_filter != "All":
        sql += " AND stock_status = %s"
        params.append(status_filter)
    if search:
        sql += " AND (product_name LIKE %s OR CAST(product_id AS CHAR) LIKE %s)"
        term = f"%{search}%"
        params.extend([term, term])
        
    if sort_by == "Stock Quantity (Asc)":
        sql += " ORDER BY current_stock ASC"
    elif sort_by == "Stock Quantity (Desc)":
        sql += " ORDER BY current_stock DESC"
    elif sort_by == "Stock Value":
        sql += " ORDER BY stock_value DESC"
    elif sort_by == "Product Name":
        sql += " ORDER BY product_name ASC"
    else:
        sql += " ORDER BY product_id ASC"
        
    return execute_read(sql, tuple(params))

def get_inventory_transactions(product_id: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
    sql = """
        SELECT it.transaction_id, it.product_id, p.product_name, it.transaction_type,
               it.quantity, it.transaction_date, it.reference_id, it.notes, it.created_at
        FROM inventory_transactions it
        JOIN products p ON it.product_id = p.product_id
        WHERE 1=1
    """
    params = []
    if product_id:
        sql += " AND it.product_id = %s"
        params.append(product_id)
    sql += " ORDER BY it.transaction_date DESC, it.transaction_id DESC LIMIT %s"
    params.append(limit)
    return execute_read(sql, tuple(params))

# ─────────────────────────────────────────────────────────────
# PURCHASES & SALES WITH ACID TRANSACTIONS
# ─────────────────────────────────────────────────────────────
def record_purchase_transaction(supplier_id: int, purchase_date: str, items: List[Dict[str, Any]], notes: str = "") -> int:
    """
    ACID Transaction:
    1. Insert into purchases
    2. Insert into purchase_items
    3. Update product current_stock (+quantity)
    4. Insert into inventory_transactions (PURCHASE)
    Commit if all succeed, Rollback on any failure.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        total_amount = sum(item['quantity'] * item['unit_price'] for item in items)
        
        # 1. purchases table
        sql_pur = "INSERT INTO purchases (supplier_id, purchase_date, total_amount, notes) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_pur, (supplier_id, purchase_date, total_amount, notes))
        purchase_id = cursor.lastrowid
        
        # 2, 3, 4 per item
        sql_item = "INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)"
        sql_stock = "UPDATE products SET current_stock = current_stock + %s WHERE product_id = %s"
        sql_trans = """
            INSERT INTO inventory_transactions (product_id, transaction_type, quantity, transaction_date, reference_id, notes)
            VALUES (%s, 'PURCHASE', %s, %s, %s, %s)
        """
        
        for item in items:
            p_id = item['product_id']
            qty = item['quantity']
            price = item['unit_price']
            
            cursor.execute(sql_item, (purchase_id, p_id, qty, price))
            cursor.execute(sql_stock, (qty, p_id))
            cursor.execute(sql_trans, (p_id, qty, purchase_date, purchase_id, f"Purchase #{purchase_id}"))
            
        conn.commit()
        return purchase_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def record_sale_transaction(user_id: int, sale_date: str, items: List[Dict[str, Any]]) -> int:
    """
    ACID Transaction:
    1. Validate current stock >= item quantity (FOR UPDATE locking)
    2. Insert into sales
    3. Insert into sale_items
    4. Update product current_stock (-quantity)
    5. Insert into inventory_transactions (SALE)
    Commit if all succeed, Rollback on any failure.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Validate stock availability with row lock
        for item in items:
            p_id = item['product_id']
            qty = item['quantity']
            cursor.execute("SELECT product_name, current_stock FROM products WHERE product_id = %s FOR UPDATE", (p_id,))
            prod = cursor.fetchone()
            if not prod:
                raise ValueError(f"Product ID {p_id} not found.")
            if prod['current_stock'] < qty:
                raise ValueError(f"Insufficient stock for '{prod['product_name']}'. Available: {prod['current_stock']}, Requested: {qty}")

        total_amount = sum(item['quantity'] * item['unit_price'] for item in items)
        
        # 1. sales table
        sql_sale = "INSERT INTO sales (user_id, sale_date, total_amount) VALUES (%s, %s, %s)"
        cursor.execute(sql_sale, (user_id, sale_date, total_amount))
        sale_id = cursor.lastrowid
        
        # 2, 3, 4 per item
        sql_item = "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)"
        sql_stock = "UPDATE products SET current_stock = current_stock - %s WHERE product_id = %s"
        sql_trans = """
            INSERT INTO inventory_transactions (product_id, transaction_type, quantity, transaction_date, reference_id, notes)
            VALUES (%s, 'SALE', %s, %s, %s, %s)
        """
        
        for item in items:
            p_id = item['product_id']
            qty = item['quantity']
            price = item['unit_price']
            
            cursor.execute(sql_item, (sale_id, p_id, qty, price))
            cursor.execute(sql_stock, (qty, p_id))
            cursor.execute(sql_trans, (p_id, -qty, sale_date, sale_id, f"Sale #{sale_id}"))
            
        conn.commit()
        return sale_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_purchases_list(limit: int = 150) -> List[Dict[str, Any]]:
    sql = """
        SELECT p.purchase_id, p.supplier_id, s.supplier_name, p.purchase_date, p.total_amount, p.notes,
               COUNT(pi.purchase_item_id) as total_items
        FROM purchases p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        LEFT JOIN purchase_items pi ON p.purchase_id = pi.purchase_id
        GROUP BY p.purchase_id, p.supplier_id, s.supplier_name, p.purchase_date, p.total_amount, p.notes
        ORDER BY p.purchase_date DESC, p.purchase_id DESC
        LIMIT %s
    """
    return execute_read(sql, (limit,))

def get_purchase_details(purchase_id: int) -> Dict[str, Any]:
    header = execute_read_one("""
        SELECT p.purchase_id, p.supplier_id, s.supplier_name, p.purchase_date, p.total_amount, p.notes
        FROM purchases p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.purchase_id = %s
    """, (purchase_id,))
    
    items = execute_read("""
        SELECT pi.purchase_item_id, pi.product_id, pr.product_name, pi.quantity, pi.unit_price,
               (pi.quantity * pi.unit_price) AS line_total
        FROM purchase_items pi
        JOIN products pr ON pi.product_id = pr.product_id
        WHERE pi.purchase_id = %s
    """, (purchase_id,))
    
    return {"header": header, "items": items}

def get_sales_list(limit: int = 150) -> List[Dict[str, Any]]:
    sql = """
        SELECT s.sale_id, s.user_id, u.name as cashier_name, s.sale_date, s.total_amount,
               COUNT(si.sale_item_id) as total_items
        FROM sales s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN sale_items si ON s.sale_id = si.sale_id
        GROUP BY s.sale_id, s.user_id, u.name, s.sale_date, s.total_amount
        ORDER BY s.sale_date DESC, s.sale_id DESC
        LIMIT %s
    """
    return execute_read(sql, (limit,))

def get_sale_details(sale_id: int) -> Dict[str, Any]:
    header = execute_read_one("""
        SELECT s.sale_id, s.user_id, u.name as cashier_name, s.sale_date, s.total_amount
        FROM sales s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.sale_id = %s
    """, (sale_id,))
    
    items = execute_read("""
        SELECT si.sale_item_id, si.product_id, pr.product_name, si.quantity, si.unit_price,
               (si.quantity * si.unit_price) AS line_total
        FROM sale_items si
        JOIN products pr ON si.product_id = pr.product_id
        WHERE si.sale_id = %s
    """, (sale_id,))
    
    return {"header": header, "items": items}

# ─────────────────────────────────────────────────────────────
# DASHBOARD METRICS QUERIES
# ─────────────────────────────────────────────────────────────
def get_dashboard_metrics() -> Dict[str, Any]:
    """Retrieve all dynamic statistics required for Dashboard Cards."""
    sql = """
        SELECT
            (SELECT COUNT(*) FROM products) AS total_products,
            (SELECT COUNT(*) FROM suppliers) AS total_suppliers,
            (SELECT COALESCE(SUM(current_stock * purchase_price), 0) FROM products) AS current_stock_value,
            (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE sale_date = CURDATE()) AS today_sales,
            (SELECT COALESCE(SUM(total_amount), 0) FROM sales 
             WHERE YEAR(sale_date) = YEAR(CURDATE()) AND MONTH(sale_date) = MONTH(CURDATE())) AS monthly_sales,
            (SELECT COUNT(*) FROM products WHERE current_stock <= reorder_level AND current_stock > 0) AS low_stock_count,
            (SELECT COUNT(*) FROM products WHERE current_stock = 0) AS out_of_stock_count
    """
    row = execute_read_one(sql)
    return row or {}
