"""
gui/sales.py
Sales Management Module:
- Product Search & Selection
- Real-time stock availability check
- Add to Cart, Remove from Cart, Dynamic Total calculation
- Complete Sale with ACID Transaction:
  Reduces stock, logs inventory transaction, stores sale & sale_items
- Sale Receipt & Transaction History
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import List, Dict, Any

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView, SearchBar
from database.queries import (
    get_all_products,
    get_sales_list,
    get_sale_details
)
from services.sales_service import SalesService
from utils.security import CurrentUser
from utils.validators import validate_positive_int

class SalesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.products_cache = []
        self.cart_items: List[Dict[str, Any]] = []

        self.build_ui()
        self.load_products()
        self.load_sales_history()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Sales Management & Outflow POS", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ── TAB 1: New Sale (POS Terminal) ──
        tab_pos = tk.Frame(self.nb, bg=CREAM, padx=15, pady=15)
        self.nb.add(tab_pos, text="New Sale Terminal")

        # Split: Left side Available Products Catalog, Right side Shopping Cart & Checkout
        pos_split = tk.Frame(tab_pos, bg=CREAM)
        pos_split.pack(fill="both", expand=True)

        # ── LEFT: Product Catalog Picker ──
        catalog_box = tk.LabelFrame(pos_split, text=" Available Stock Catalog ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        catalog_box.pack(side="left", fill="both", expand=True, padx=(0, 12))

        search_bar = SearchBar(catalog_box, on_search=self.filter_products, placeholder="Search product...")
        search_bar.pack(fill="x", pady=(0, 8))

        cat_cols = [
            ("product_id", "ID", 45),
            ("product_name", "Product Name", 170),
            ("category_name", "Category", 100),
            ("current_stock", "In Stock", 65),
            ("selling_price", "Price ($)", 75),
        ]
        self.catalog_table = TableView(catalog_box, columns=cat_cols, on_select=self.on_catalog_select)
        self.catalog_table.pack(fill="both", expand=True)

        # Add to cart bar below catalog
        add_bar = tk.Frame(catalog_box, bg=CREAM)
        add_bar.pack(fill="x", pady=(10, 0))

        tk.Label(add_bar, text="Selected:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.lbl_selected_prod = tk.Label(add_bar, text="None", font=FONT_BODY, bg=CREAM, fg=TEAL)
        self.lbl_selected_prod.pack(side="left", padx=(0, 15))

        tk.Label(add_bar, text="Qty:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.ent_qty = ttk.Entry(add_bar, width=8)
        self.ent_qty.pack(side="left", padx=(0, 10))
        self.ent_qty.insert(0, "1")
        self.ent_qty.bind("<Return>", lambda e: self.add_to_cart())

        btn_add = ttk.Button(add_bar, text="+ Add to Cart", style="Teal.TButton", command=self.add_to_cart)
        btn_add.pack(side="left")

        # ── RIGHT: Active Cart & Checkout ──
        cart_box = tk.LabelFrame(pos_split, text=" Current Sale Cart ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=12, pady=10)
        cart_box.pack(side="right", fill="both", expand=True)

        cart_cols = [
            ("product_id", "ID", 45),
            ("product_name", "Product", 170),
            ("quantity", "Qty", 55),
            ("unit_price", "Unit ($)", 75),
            ("line_total", "Total ($)", 85),
        ]
        self.cart_table = TableView(cart_box, columns=cart_cols)
        self.cart_table.pack(fill="both", expand=True)

        cart_bottom = tk.Frame(cart_box, bg=CREAM)
        cart_bottom.pack(fill="x", pady=(10, 0))

        btn_remove = ttk.Button(cart_bottom, text="- Remove Item", style="Teal.TButton", command=self.remove_from_cart)
        btn_remove.pack(side="left")

        btn_clear_cart = ttk.Button(cart_bottom, text="Clear Cart", style="Aqua.TButton", command=self.clear_cart)
        btn_clear_cart.pack(side="left", padx=6)

        self.lbl_grand_total = tk.Label(cart_box, text="Grand Total: $0.00", font=(FONT_SUBHEADER[0], 16, "bold"), bg=CREAM, fg=DARK_TEAL)
        self.lbl_grand_total.pack(anchor="e", pady=(12, 4))

        btn_complete_sale = ttk.Button(cart_box, text="⚡ Complete Sale & Update Stock", style="Teal.TButton", command=self.complete_sale)
        btn_complete_sale.pack(fill="x", ipady=6, pady=(4, 0))

        # ── TAB 2: Sales History & Receipts ──
        tab_hist = tk.Frame(self.nb, bg=CREAM, padx=15, pady=15)
        self.nb.add(tab_hist, text="Sales History & Receipts")

        hist_cols = [
            ("sale_id", "Sale #", 60),
            ("sale_date", "Date", 110),
            ("cashier_name", "Handled By", 160),
            ("total_items", "Items Count", 100),
            ("total_amount", "Total Revenue ($)", 130),
        ]
        self.hist_table = TableView(tab_hist, columns=hist_cols, on_select=self.on_sale_select)
        self.hist_table.pack(fill="both", expand=True, pady=(0, 10))

        detail_box = tk.LabelFrame(tab_hist, text=" Line Items for Selected Sale ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        detail_box.pack(fill="x")

        sale_item_cols = [
            ("product_id", "Product ID", 80),
            ("product_name", "Product Name", 240),
            ("quantity", "Quantity Sold", 100),
            ("unit_price", "Selling Price ($)", 110),
            ("line_total", "Subtotal ($)", 120),
        ]
        self.detail_table = TableView(detail_box, columns=sale_item_cols)
        self.detail_table.pack(fill="x")

    def load_products(self, search: str = ""):
        self.products_cache = get_all_products(search=search)
        rows = [
            (
                p['product_id'],
                p['product_name'],
                p['category_name'],
                p['current_stock'],
                f"${float(p['selling_price']):.2f}"
            )
            for p in self.products_cache
        ]
        self.catalog_table.populate(rows)

    def filter_products(self, query: str):
        self.load_products(search=query)

    def on_catalog_select(self, event=None):
        sel = self.catalog_table.get_selected()
        if not sel:
            return
        self.lbl_selected_prod.config(text=f"[{sel[0]}] {sel[1]} (Stock: {sel[3]})")
        self.ent_qty.focus_set()

    def add_to_cart(self):
        sel = self.catalog_table.get_selected()
        if not sel:
            return messagebox.showwarning("Selection Required", "Please select a product from the catalog table.")

        p_id = int(sel[0])
        p_name = sel[1]
        available_stock = int(sel[3])
        price = float(sel[4].replace("$", ""))

        qty_str = self.ent_qty.get().strip()
        ok, err = validate_positive_int(qty_str, "Quantity", allow_zero=False)
        if not ok: return messagebox.showwarning("Validation Error", err)
        qty = int(qty_str)

        # Check existing cart quantity
        current_cart_qty = sum(item['quantity'] for item in self.cart_items if item['product_id'] == p_id)
        if (current_cart_qty + qty) > available_stock:
            return messagebox.showerror(
                "Insufficient Stock",
                f"Cannot sell {current_cart_qty + qty} units of '{p_name}'.\nOnly {available_stock} units currently available in inventory."
            )

        existing = next((item for item in self.cart_items if item['product_id'] == p_id), None)
        if existing:
            existing['quantity'] += qty
        else:
            self.cart_items.append({
                "product_id": p_id,
                "product_name": p_name,
                "quantity": qty,
                "unit_price": price
            })

        self.refresh_cart_view()

    def remove_from_cart(self):
        sel = self.cart_table.get_selected()
        if not sel:
            return messagebox.showwarning("Selection Required", "Select an item from the cart to remove.")
        p_id = int(sel[0])
        self.cart_items = [i for i in self.cart_items if i['product_id'] != p_id]
        self.refresh_cart_view()

    def clear_cart(self):
        self.cart_items.clear()
        self.refresh_cart_view()

    def refresh_cart_view(self):
        rows = [
            (
                item['product_id'],
                item['product_name'],
                item['quantity'],
                f"${item['unit_price']:.2f}",
                f"${(item['quantity'] * item['unit_price']):.2f}"
            )
            for item in self.cart_items
        ]
        self.cart_table.populate(rows)
        total = sum(i['quantity'] * i['unit_price'] for i in self.cart_items)
        self.lbl_grand_total.config(text=f"Grand Total: ${total:,.2f}")

    def complete_sale(self):
        if not self.cart_items:
            return messagebox.showwarning("Empty Cart", "No items added to the sale.")

        # Determine user id
        user_id = CurrentUser.user_id or 1
        today_str = str(date.today())

        try:
            sale_id = SalesService.process_sale(user_id=user_id, sale_date=today_str, items=self.cart_items)
            total = sum(i['quantity'] * i['unit_price'] for i in self.cart_items)
            messagebox.showinfo(
                "Sale Completed",
                f"Sale #{sale_id} processed successfully!\nTotal: ${total:,.2f}\nInventory stock has been deducted atomically."
            )
            self.clear_cart()
            self.load_products()
            self.load_sales_history()
            self.nb.select(1) # Switch to history
        except Exception as e:
            messagebox.showerror("Transaction Failed", f"Sale processing failed:\n{str(e)}")

    def load_sales_history(self):
        sales = get_sales_list()
        rows = [
            (
                s['sale_id'],
                str(s['sale_date']),
                s['cashier_name'] or 'Staff',
                s['total_items'],
                f"${float(s['total_amount']):,.2f}"
            )
            for s in sales
        ]
        self.hist_table.populate(rows)

    def on_sale_select(self, event=None):
        sel = self.hist_table.get_selected()
        if not sel:
            return
        sale_id = int(sel[0])
        details = get_sale_details(sale_id)
        rows = [
            (
                item['product_id'],
                item['product_name'],
                item['quantity'],
                f"${float(item['unit_price']):.2f}",
                f"${float(item['line_total']):.2f}"
            )
            for item in details['items']
        ]
        self.detail_table.populate(rows)
