"""
gui/inventory.py
Inventory Management & Audit Log:
- View all inventory items with dynamic status: Healthy, Low Stock, Out of Stock, Overstock
- Search by Product Name / ID
- Filters: Category, Supplier, Stock Status
- Sorting: Stock Quantity (Asc/Desc), Stock Value, Product Name
- Inventory Transaction History audit trail (PURCHASE, SALE, ADJUSTMENT)
- Manual stock adjustment dialog with audit reason
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView, SearchBar
from database.queries import (
    get_all_categories,
    get_all_suppliers,
    get_inventory_view,
    get_inventory_transactions
)
from services.inventory_service import InventoryService
from utils.csv_export import export_records_to_csv

class InventoryView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.categories_cache = []
        self.suppliers_cache = []

        self.build_ui()
        self.load_metadata()
        self.load_inventory()
        self.load_transactions()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Central Inventory Tracking & Auditing", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        btn_export = ttk.Button(top_bar, text="⬇ Export to CSV", style="Teal.TButton", command=self.export_inventory)
        btn_export.pack(side="right", padx=(6, 0))

        btn_adjust = ttk.Button(top_bar, text="⚙ Adjust Stock", style="Aqua.TButton", command=self.open_stock_adjustment)
        btn_adjust.pack(side="right")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ── TAB 1: Real-time Stock Levels ──
        tab_stock = tk.Frame(self.nb, bg=CREAM, padx=15, pady=15)
        self.nb.add(tab_stock, text="Current Stock Levels")

        # Filters and search bar
        filter_bar = tk.Frame(tab_stock, bg=CREAM)
        filter_bar.pack(fill="x", pady=(0, 10))

        # Category Filter
        tk.Label(filter_bar, text="Category:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_cat = ttk.Combobox(filter_bar, state="readonly", width=13)
        self.cb_cat.pack(side="left", padx=(0, 10))
        self.cb_cat.bind("<<ComboboxSelected>>", lambda e: self.load_inventory())

        # Supplier Filter
        tk.Label(filter_bar, text="Supplier:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_supp = ttk.Combobox(filter_bar, state="readonly", width=14)
        self.cb_supp.pack(side="left", padx=(0, 10))
        self.cb_supp.bind("<<ComboboxSelected>>", lambda e: self.load_inventory())

        # Status Filter
        tk.Label(filter_bar, text="Status:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_status = ttk.Combobox(filter_bar, state="readonly", width=13, values=["All", "Healthy", "Low Stock", "Out of Stock", "Overstock"])
        self.cb_status.set("All")
        self.cb_status.pack(side="left", padx=(0, 10))
        self.cb_status.bind("<<ComboboxSelected>>", lambda e: self.load_inventory())

        # Sort By
        tk.Label(filter_bar, text="Sort By:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_sort = ttk.Combobox(filter_bar, state="readonly", width=16, values=["Product Name", "Stock Quantity (Asc)", "Stock Quantity (Desc)", "Stock Value"])
        self.cb_sort.set("Product Name")
        self.cb_sort.pack(side="left", padx=(0, 15))
        self.cb_sort.bind("<<ComboboxSelected>>", lambda e: self.load_inventory())

        # Search Bar
        search_bar = SearchBar(filter_bar, on_search=self.filter_by_search, placeholder="Search product...")
        search_bar.pack(side="right")

        stock_cols = [
            ("product_id", "ID", 45),
            ("product_name", "Product Name", 180),
            ("category_name", "Category", 110),
            ("current_stock", "Stock", 65),
            ("reorder_level", "Reorder", 65),
            ("safety_stock", "Safety", 60),
            ("stock_value", "Stock Value ($)", 110),
            ("supplier_name", "Supplier", 150),
            ("stock_status", "Status", 110),
        ]
        self.stock_table = TableView(tab_stock, columns=stock_cols)
        self.stock_table.pack(fill="both", expand=True)

        # ── TAB 2: Inventory Transactions History ──
        tab_tx = tk.Frame(self.nb, bg=CREAM, padx=15, pady=15)
        self.nb.add(tab_tx, text="Stock Movement Audit Trail")

        tx_bar = tk.Frame(tab_tx, bg=CREAM)
        tx_bar.pack(fill="x", pady=(0, 10))
        tk.Label(tx_bar, text="Recent Inventory Transactions (Inflow / Outflow / Adjustments)", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL).pack(side="left")
        btn_refresh_tx = ttk.Button(tx_bar, text="⟳ Refresh Log", style="Teal.TButton", command=self.load_transactions)
        btn_refresh_tx.pack(side="right")

        tx_cols = [
            ("transaction_id", "Tx ID", 60),
            ("transaction_date", "Date", 100),
            ("product_name", "Product Name", 220),
            ("transaction_type", "Type", 110),
            ("quantity", "Quantity Change", 120),
            ("reference_id", "Reference ID", 100),
            ("notes", "Audit Notes", 260),
        ]
        self.tx_table = TableView(tab_tx, columns=tx_cols)
        self.tx_table.pack(fill="both", expand=True)

    def load_metadata(self):
        self.categories_cache = get_all_categories()
        self.cb_cat['values'] = ["All"] + [c['category_name'] for c in self.categories_cache]
        self.cb_cat.set("All")

        self.suppliers_cache = get_all_suppliers()
        self.cb_supp['values'] = ["All"] + [s['supplier_name'] for s in self.suppliers_cache]
        self.cb_supp.set("All")

    def load_inventory(self, search: Optional[str] = None):
        cat = self.cb_cat.get()
        supp = self.cb_supp.get()
        stat = self.cb_status.get()
        sort_by = self.cb_sort.get()

        items = get_inventory_view(
            category_filter=cat,
            supplier_filter=supp,
            status_filter=stat,
            search=search,
            sort_by=sort_by
        )
        rows = [
            (
                item['product_id'],
                item['product_name'],
                item['category_name'],
                item['current_stock'],
                item['reorder_level'],
                item['safety_stock'],
                f"${float(item['stock_value']):,.2f}",
                item['supplier_name'],
                item['stock_status']
            )
            for item in items
        ]
        self.stock_table.populate(rows)

    def filter_by_search(self, term: str):
        self.load_inventory(search=term)

    def load_transactions(self):
        txs = get_inventory_transactions(limit=300)
        rows = [
            (
                t['transaction_id'],
                str(t['transaction_date']),
                t['product_name'],
                t['transaction_type'],
                f"{t['quantity']:+d}", # + or - prefix
                t['reference_id'] or '-',
                t['notes'] or ''
            )
            for t in txs
        ]
        self.tx_table.populate(rows)

    def open_stock_adjustment(self):
        sel = self.stock_table.get_selected()
        if not sel:
            return messagebox.showwarning("Selection Required", "Please select a product from the table to adjust stock.")

        p_id = int(sel[0])
        p_name = sel[1]
        curr_stock = int(sel[3])

        new_val = simpledialog.askinteger(
            "Adjust Stock Quantity",
            f"Product: {p_name}\nCurrent Stock: {curr_stock}\nEnter New Physical Count:",
            minvalue=0,
            initialvalue=curr_stock
        )
        if new_val is None:
            return

        reason = simpledialog.askstring("Adjustment Reason", "Enter reason for stock adjustment (e.g. Physical inventory count, damaged goods):")
        if not reason:
            reason = "Manual audit adjustment"

        try:
            InventoryService.adjust_stock(p_id, new_val, notes=reason)
            messagebox.showinfo("Success", f"Stock for '{p_name}' adjusted from {curr_stock} to {new_val}.")
            self.load_inventory()
            self.load_transactions()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust stock:\n{str(e)}")

    def export_inventory(self):
        items = get_inventory_view(
            category_filter=self.cb_cat.get(),
            supplier_filter=self.cb_supp.get(),
            status_filter=self.cb_status.get(),
            sort_by=self.cb_sort.get()
        )
        export_records_to_csv(items, default_filename="inventory_status.csv", title="Export Inventory Status")
