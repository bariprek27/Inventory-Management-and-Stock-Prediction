"""
database/seed_data.py
Populates the stockwise MySQL database with realistic sample data:
- At least 8 Suppliers
- At least 6 Categories
- At least 30 Products (with high/low demand, low stock, out of stock, overstock)
- 2 Users: Admin & Staff (bcrypt hashed passwords)
- 50+ Purchase Orders & Line Items
- 250+ Realistic Sales Orders & Line Items spanning the last 90 days
- Full Inventory Transactions audit history
"""
import os
import sys
import random
from datetime import date, timedelta
import bcrypt

# Ensure root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')

def seed_database():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    print("Beginning database seeding...")

    try:
        # Disable foreign keys temporarily for clean wipe
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        tables = [
            "forecasts", "inventory_transactions", "sale_items", "sales",
            "purchase_items", "purchases", "products", "suppliers", "categories", "users"
        ]
        for tbl in tables:
            cursor.execute(f"TRUNCATE TABLE {tbl};")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # 1. Users
        users = [
            ("System Admin", "admin", hash_pw("admin123"), "admin"),
            ("Inventory Staff", "staff", hash_pw("staff123"), "staff"),
        ]
        for u in users:
            cursor.execute("INSERT INTO users (name, username, password_hash, role) VALUES (%s, %s, %s, %s)", u)
        print("✓ Created Users (admin, staff)")

        # 2. Categories (6 categories)
        categories = [
            ("Electronics", "Smart gadgets, computer components, accessories and consumer electronics"),
            ("Office Stationery", "Paper products, pens, desk organizers, notebooks and writing instruments"),
            ("Pantry & Beverages", "Coffee, teas, packaged snacks and commercial pantry replenishment"),
            ("Safety & PPE", "Protective equipment, high-vis vests, work gloves, first-aid gear"),
            ("Packaging & Shipping", "Cardboard boxes, shipping tape, bubble wrap, thermal mailing labels"),
            ("Hardware & Tools", "Hand tools, measuring tapes, fasteners, maintenance hardware"),
        ]
        cat_ids = {}
        for c in categories:
            cursor.execute("INSERT INTO categories (category_name, description) VALUES (%s, %s)", c)
            cat_ids[c[0]] = cursor.lastrowid
        print(f"✓ Created {len(categories)} Categories")

        # 3. Suppliers (8 suppliers with varied lead times)
        suppliers = [
            ("Apex Electronics Ltd", "+1 555-0101", "orders@apexelectronics.com", "102 Silicon Valley Pkwy, CA", 5),
            ("Nova Hardware Supplies", "+1 555-0102", "sales@novahardware.com", "84 Industrial Way, OH", 12),
            ("Pacific Paper & Print", "+1 555-0103", "contact@pacificpaper.com", "45 Harbor View Rd, WA", 4),
            ("GreenLeaf Pantry Goods", "+1 555-0104", "supply@greenleaf.com", "12 Farmstead Ave, OR", 3),
            ("Vanguard Safety Equipment", "+1 555-0105", "orders@vanguardppe.com", "77 Iron Works Dr, PA", 10),
            ("PackSmart Logistics Co", "+1 555-0106", "support@packsmart.com", "300 Depot Blvd, IL", 6),
            ("TechCore Distribution", "+1 555-0107", "distro@techcore.com", "91 Innovation Blvd, TX", 8),
            ("Standard Supply Hub", "+1 555-0108", "wholesale@standardsupply.com", "150 Commercial St, NY", 7),
        ]
        supp_ids = {}
        for s in suppliers:
            cursor.execute("""
                INSERT INTO suppliers (supplier_name, phone, email, address, lead_time)
                VALUES (%s, %s, %s, %s, %s)
            """, s)
            supp_ids[s[0]] = cursor.lastrowid
        print(f"✓ Created {len(suppliers)} Suppliers")

        # 4. Products (32 products covering various states: high demand, low demand, low stock, out of stock, overstock)
        raw_products = [
            # Electronics
            ("Wireless Ergonomic Mouse", "Electronics", "Apex Electronics Ltd", 18.50, 34.99, 12, 15, 8),      # Low stock
            ("Mechanical Keyboard RGB", "Electronics", "Apex Electronics Ltd", 45.00, 89.99, 0, 10, 5),        # Out of stock
            ("USB-C Multiport Dock", "Electronics", "TechCore Distribution", 28.00, 59.99, 45, 12, 6),
            ("Bluetooth Headset Pro", "Electronics", "TechCore Distribution", 35.00, 74.99, 22, 10, 5),
            ("27-inch 4K Monitor", "Electronics", "Apex Electronics Ltd", 180.00, 299.99, 8, 10, 4),           # Low stock
            ("High-Speed HDMI Cable 2m", "Electronics", "TechCore Distribution", 4.20, 12.99, 180, 25, 15),    # Overstock
            
            # Office Stationery
            ("Executive A5 Notebook", "Office Stationery", "Pacific Paper & Print", 3.50, 8.99, 85, 20, 10),
            ("Gel Ink Pen 0.7mm (Box of 12)", "Office Stationery", "Pacific Paper & Print", 6.00, 14.50, 5, 25, 15), # Low stock
            ("Heavy Duty Desktop Stapler", "Office Stationery", "Pacific Paper & Print", 9.20, 18.99, 30, 8, 4),
            ("Sticky Notes Neon (12-Pack)", "Office Stationery", "Pacific Paper & Print", 5.10, 11.99, 65, 15, 8),
            ("A4 Copy Paper 80gsm (Ream)", "Office Stationery", "Pacific Paper & Print", 4.50, 9.50, 120, 30, 15),
            ("Filing Folder Pack of 25", "Office Stationery", "Pacific Paper & Print", 7.80, 16.50, 0, 12, 6),   # Out of stock

            # Pantry & Beverages
            ("Organic Medium Roast Coffee 1kg", "Pantry & Beverages", "GreenLeaf Pantry Goods", 11.50, 22.99, 28, 10, 5),
            ("English Breakfast Tea (100 Bags)", "Pantry & Beverages", "GreenLeaf Pantry Goods", 5.20, 12.50, 4, 15, 8), # Low stock
            ("Raw Sugar Sachets (Box 500)", "Pantry & Beverages", "GreenLeaf Pantry Goods", 8.00, 16.00, 40, 10, 5),
            ("Sparkling Spring Water (Pack 24)", "Pantry & Beverages", "GreenLeaf Pantry Goods", 9.50, 19.99, 55, 15, 8),
            ("Mixed Nut Snack Packs (Box 30)", "Pantry & Beverages", "GreenLeaf Pantry Goods", 14.00, 28.00, 2, 12, 6), # Critical Low
            ("Oat Milk Barista Edition 1L", "Pantry & Beverages", "GreenLeaf Pantry Goods", 2.10, 4.50, 90, 20, 10),

            # Safety & PPE
            ("Heavy Duty Work Gloves (Pair)", "Safety & PPE", "Vanguard Safety Equipment", 4.50, 11.00, 75, 20, 10),
            ("Safety Glasses Anti-Scratch", "Safety & PPE", "Vanguard Safety Equipment", 3.20, 8.50, 6, 25, 15), # Low stock
            ("High-Visibility Safety Vest", "Safety & PPE", "Vanguard Safety Equipment", 5.50, 13.99, 0, 15, 8),  # Out of stock
            ("Industrial First Aid Kit Large", "Safety & PPE", "Vanguard Safety Equipment", 32.00, 65.00, 14, 5, 3),
            ("N95 Particulate Respirator 20pk", "Safety & PPE", "Vanguard Safety Equipment", 12.00, 24.99, 110, 30, 15),

            # Packaging & Shipping
            ("Corrugated Box 12x12x12 (Pack 25)", "Packaging & Shipping", "PackSmart Logistics Co", 16.00, 32.50, 42, 15, 8),
            ("Heavy Duty Packing Tape 6-Rolls", "Packaging & Shipping", "PackSmart Logistics Co", 8.50, 18.99, 3, 20, 10), # Critical Low
            ("Bubble Cushioning Roll 100ft", "Packaging & Shipping", "PackSmart Logistics Co", 14.00, 29.99, 35, 10, 5),
            ("Self-Adhesive Shipping Labels 500", "Packaging & Shipping", "PackSmart Logistics Co", 9.00, 19.50, 220, 35, 20), # Overstock
            ("Poly Mailers 10x13 (Pack 100)", "Packaging & Shipping", "PackSmart Logistics Co", 11.00, 22.00, 50, 15, 8),

            # Hardware & Tools
            ("Laser Measuring Tool 50m", "Hardware & Tools", "Nova Hardware Supplies", 26.00, 54.99, 18, 6, 3),
            ("Steel Tape Measure 8m / 26ft", "Hardware & Tools", "Nova Hardware Supplies", 6.50, 14.99, 45, 12, 6),
            ("Cordless Drill Bit Set 40-Piece", "Hardware & Tools", "Nova Hardware Supplies", 15.00, 34.50, 0, 8, 4), # Out of stock
            ("Adjustable Wrench 10-inch", "Hardware & Tools", "Standard Supply Hub", 8.00, 17.50, 28, 10, 5),
        ]

        product_id_map = {}
        for p in raw_products:
            name, cat_name, supp_name, buy_p, sell_p, stock, reorder, safety = p
            c_id = cat_ids[cat_name]
            s_id = supp_ids[supp_name]
            cursor.execute("""
                INSERT INTO products (product_name, category_id, supplier_id, purchase_price, selling_price, current_stock, reorder_level, safety_stock)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, c_id, s_id, buy_p, sell_p, stock, reorder, safety))
            product_id_map[name] = cursor.lastrowid
        print(f"✓ Created {len(raw_products)} Products with diverse stock statuses")

        # 5. Purchase Orders (60 realistic historical purchases spanning past 120 days)
        print("Generating 60 historical purchase orders...")
        start_date = date.today() - timedelta(days=120)
        po_dates = [start_date + timedelta(days=int(i * 1.9)) for i in range(60)]

        prod_list = list(product_id_map.items()) # [(name, id), ...]
        
        for po_idx, po_date in enumerate(po_dates):
            # Pick a supplier
            supp_name = random.choice(list(supp_ids.keys()))
            supp_id = supp_ids[supp_name]
            
            # Select 1 to 4 products supplied by this vendor or general
            num_items = random.randint(1, 4)
            items_to_add = random.sample(prod_list, num_items)
            
            # Calculate total
            po_lines = []
            po_total = 0.0
            for p_name, p_id in items_to_add:
                qty = random.randint(15, 60)
                # Find cost
                p_cost = next(p[3] for p in raw_products if p[0] == p_name)
                line_total = qty * p_cost
                po_total += line_total
                po_lines.append((p_id, qty, p_cost))

            cursor.execute("""
                INSERT INTO purchases (supplier_id, purchase_date, total_amount, notes)
                VALUES (%s, %s, %s, %s)
            """, (supp_id, po_date, round(po_total, 2), f"Routine stock replenishment PO #{po_idx+1}"))
            po_id = cursor.lastrowid

            for p_id, qty, unit_cost in po_lines:
                cursor.execute("""
                    INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                """, (po_id, p_id, qty, unit_cost))

                cursor.execute("""
                    INSERT INTO inventory_transactions (product_id, transaction_type, quantity, transaction_date, reference_id, notes)
                    VALUES (%s, 'PURCHASE', %s, %s, %s, %s)
                """, (p_id, qty, po_date, po_id, f"Received from PO #{po_id}"))

        print("✓ Created 60 Purchase Orders with line items and inventory transactions")

        # 6. Sales Orders (280 sales spanning the last 90 days for realistic ML forecasting)
        print("Generating 280 sales transactions across 90 days for demand forecasting...")
        sales_start = date.today() - timedelta(days=90)
        user_ids = [1, 2] # admin or staff cashier

        for sale_idx in range(280):
            # Distribute dates across last 90 days, with higher density in recent days
            days_ago = int((90 - 1) * (1 - (sale_idx / 280.0) ** 0.8))
            sale_date = date.today() - timedelta(days=days_ago)

            cashier = random.choice(user_ids)
            
            # High demand items get picked more often
            # We assign weights: items 0, 1, 6, 7, 12, 13, 24, 25 have higher popularity
            weights = [3.5 if i in [0, 2, 6, 7, 9, 10, 12, 13, 18, 23, 24, 26] else 1.0 for i in range(len(prod_list))]
            num_sale_items = random.randint(1, 3)
            chosen_indices = random.choices(range(len(prod_list)), weights=weights, k=num_sale_items)
            chosen_prods = [prod_list[idx] for idx in set(chosen_indices)]

            sale_lines = []
            sale_total = 0.0
            for p_name, p_id in chosen_prods:
                qty = random.randint(1, 8)
                sell_p = next(p[4] for p in raw_products if p[0] == p_name)
                line_total = qty * sell_p
                sale_total += line_total
                sale_lines.append((p_id, qty, sell_p))

            cursor.execute("""
                INSERT INTO sales (user_id, sale_date, total_amount)
                VALUES (%s, %s, %s)
            """, (cashier, sale_date, round(sale_total, 2)))
            sale_id = cursor.lastrowid

            for p_id, qty, price in sale_lines:
                cursor.execute("""
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                """, (sale_id, p_id, qty, price))

                cursor.execute("""
                    INSERT INTO inventory_transactions (product_id, transaction_type, quantity, transaction_date, reference_id, notes)
                    VALUES (%s, 'SALE', %s, %s, %s, %s)
                """, (p_id, -qty, sale_date, sale_id, f"Sold on Ticket #{sale_id}"))

        print("✓ Created 280 Sales Records across 90 days with audit movements")

        conn.commit()
        print("\n=======================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("Accounts available:")
        print("  - Admin: admin / admin123")
        print("  - Staff: staff / staff123")
        print("=======================================================\n")

    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_database()
