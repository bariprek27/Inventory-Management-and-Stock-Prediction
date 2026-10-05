"""
gui/purchases.py
Purchase Management Module:
- Select Supplier, Select Product, Quantity, Purchase Price, Purchase Date
- Multi-item Purchase Order creation
- Atomic transaction: Updates current_stock = current_stock + qty and records in inventory_transactions
- View historical purchase records & inspect line items
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import List, Dict, Any

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView
from database.queries import (
    get_all_suppliers,
    get_all_products,
    get_purchases_list,
    get_purchase_details
)
from services.purchase_service import PurchaseService
from utils.validators import validate_positive_number, validate_positive_int, validate_date_str

class PurchasesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.suppliers_cache = []
        self.products_cache = []
        self.cart_items: List[Dict[str, Any]] = []

        self.build_ui()
        self.load_metadata()
        self.load_purchase_history()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Purchase Management & Stock Inflow", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        # Two Tabs: Create Purchase Order vs Purchase History
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ── TAB 1: New Purchase Order ──
        tab_new = tk.Frame(self.nb, bg=CREAM, padx=15, pady=15)
        self.nb.add(tab_new, text="New Purchase Order")

        # Top form for PO Header & Item Entry
        entry_box = tk.LabelFrame(tab_new, text=" Purchase Details ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=10)
        entry_box.pack(fill="x", pady=(0, 15))

        # Supplier & Date
        tk.Label(entry_box, text="Supplier *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=0, column=0, sticky="w", pady=4)
        self.cb_supp = ttk.Combobox(entry_box, state="readonly", width=25)
        self.cb_supp.grid(row=0, column=1, sticky="w", pady=4, padx=(0, 20))

        tk.Label(entry_box, text="Purchase Date (YYYY-MM-DD) *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=0, column=2, sticky="w", pady=4)
        self.ent_date = ttk.Entry(entry_box, width=15)
        self.ent_date.grid(row=0, column=3, sticky="w", pady=4)
        self.ent_date.insert(0, str(date.today()))

        # Product, Qty, Unit Cost
        tk.Label(entry_box, text="Select Product *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=1, column=0, sticky="w", pady=6)
        self.cb_prod = ttk.Combobox(entry_box, state="readonly", width=25)
        self.cb_prod.grid(row=1, column=1, sticky="w", pady=6, padx=(0, 20))
        self.cb_prod.bind("<<ComboboxSelected>>", self.on_product_picked)

        tk.Label(entry_box, text="Quantity *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=1, column=2, sticky="w", pady=6)
        self.ent_qty = ttk.Entry(entry_box, width=10)
        self.ent_qty.grid(row=1, column=3, sticky="w", pady=6)

        tk.Label(entry_box, text="Purchase Unit Price ($) *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=1, column=4, sticky="w", pady=6, padx=(15, 4))
        self.ent_cost = ttk.Entry(entry_box, width=12)
        self.ent_cost.grid(row=1, column=5, sticky="w", pady=6)

        btn_add_item = ttk.Button(entry_box, text="+ Add To Order", style="Teal.TButton", command=self.add_item_to_order)
        btn_add_item.grid(row=1, column=6, padx=(15, 0), pady=6)

        # Cart Table
        cart_frame = tk.LabelFrame(tab_new, text=" Order Items ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        cart_frame.pack(fill="both", expand=True)

        cart_cols = [
            ("product_id", "Product ID", 70),
            ("product_name", "Product Name", 240),
            ("quantity", "Quantity", 90),
            ("unit_price", "Unit Cost ($)", 110),
            ("line_total", "Total ($)", 120),
        ]
        self.cart_table = TableView(cart_frame, columns=cart_cols)
        self.cart_table.pack(fill="both", expand=True)

        # Bottom Bar: Total & Actions
        bottom_bar = tk.Frame(tab_new, bg=CREAM)
        bottom_bar.pack(fill="x", pady=(12, 0))

        btn_remove_item = ttk.Button(bottom_bar, text="- Remove Selected Item", style="Teal.TButton", command=self.remove_item_from_order)
        btn_remove_item.pack(side="left")

        self.lbl_order_total = tk.Label(bottom_bar, text="Total Amount: $0.00", font=(FONT_SUBHEADER[0], 14, "bold"), bg=CREAM, fg=DARK_TEAL)
        self.lbl_order_total.pack(side="right", padx=(0, 20))

        btn_complete = ttk.Button(bottom_bar, text="✓ Save & Receive Purchase Order", style="Aqua.TButton", command=self.complete_purchase_order)
        btn_complete.pack(side="right", padx=10, ipady=4)

        # ── TAB 2: Purchase History ──
        tab_hist = tk.Frame(self.nb, bg=CREAM, padx=15, pady=15)
        self.nb.add(tab_hist, text="Purchase Order History")

        hist_cols = [
            ("purchase_id", "PO #", 60),
            ("purchase_date", "Date", 110),
            ("supplier_name", "Supplier Name", 220),
            ("total_items", "Items Count", 100),
            ("total_amount", "Total Value ($)", 130),
            ("notes", "Notes", 220),
        ]
        self.hist_table = TableView(tab_hist, columns=hist_cols, on_select=self.on_history_select)
        self.hist_table.pack(fill="both", expand=True, pady=(0, 10))

        # Bottom drilldown for selected purchase
        drill_box = tk.LabelFrame(tab_hist, text=" Line Items for Selected PO ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        drill_box.pack(fill="x")
        
        detail_cols = [
            ("product_id", "Product ID", 80),
            ("product_name", "Product Name", 240),
            ("quantity", "Quantity", 90),
            ("unit_price", "Unit Price ($)", 110),
            ("line_total", "Line Total ($)", 120),
        ]
        self.detail_table = TableView(drill_box, columns=detail_cols)
        self.detail_table.pack(fill="x")

    def load_metadata(self):
        self.suppliers_cache = get_all_suppliers()
        self.cb_supp['values'] = [s['supplier_name'] for s in self.suppliers_cache]

        self.products_cache = get_all_products()
        self.cb_prod['values'] = [f"{p['product_id']}: {p['product_name']}" for p in self.products_cache]

    def on_product_picked(self, event=None):
        selected = self.cb_prod.get()
        if not selected:
            return
        p_id = int(selected.split(":")[0])
        prod = next((p for p in self.products_cache if p['product_id'] == p_id), None)
        if prod:
            self.ent_cost.delete(0, tk.END)
            self.ent_cost.insert(0, str(prod['purchase_price']))

    def add_item_to_order(self):
        prod_selection = self.cb_prod.get()
        qty_str = self.ent_qty.get().strip()
        cost_str = self.ent_cost.get().strip()

        if not prod_selection:
            return messagebox.showwarning("Validation Error", "Please select a product.")

        p_id = int(prod_selection.split(":")[0])
        p_name = prod_selection.split(":", 1)[1].strip()

        ok, err = validate_positive_int(qty_str, "Quantity", allow_zero=False)
        if not ok: return messagebox.showwarning("Validation Error", err)

        ok, err = validate_positive_number(cost_str, "Purchase Unit Price", allow_zero=False)
        if not ok: return messagebox.showwarning("Validation Error", err)

        qty = int(qty_str)
        cost = float(cost_str)

        # Check if product is already in cart, update quantity
        existing = next((item for item in self.cart_items if item['product_id'] == p_id), None)
        if existing:
            existing['quantity'] += qty
            existing['unit_price'] = cost
        else:
            self.cart_items.append({
                "product_id": p_id,
                "product_name": p_name,
                "quantity": qty,
                "unit_price": cost
            })

        self.refresh_cart_view()
        self.ent_qty.delete(0, tk.END)

    def remove_item_from_order(self):
        sel = self.cart_table.get_selected()
        if not sel:
            return messagebox.showwarning("Selection Required", "Select an item to remove.")
        p_id = int(sel[0])
        self.cart_items = [i for i in self.cart_items if i['product_id'] != p_id]
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
        self.lbl_order_total.config(text=f"Total Amount: ${total:,.2f}")

    def complete_purchase_order(self):
        supp_name = self.cb_supp.get()
        p_date = self.ent_date.get().strip()

        if not supp_name:
            return messagebox.showwarning("Validation Error", "Please select a Supplier.")
        
        ok, err = validate_date_str(p_date)
        if not ok: return messagebox.showwarning("Validation Error", err)

        if not self.cart_items:
            return messagebox.showwarning("Empty Order", "Please add at least one product to the purchase order.")

        supp_obj = next((s for s in self.suppliers_cache if s['supplier_name'] == supp_name), None)
        if not supp_obj:
            return messagebox.showwarning("Error", "Invalid supplier selected.")

        try:
            po_id = PurchaseService.process_purchase(
                supplier_id=supp_obj['supplier_id'],
                purchase_date=p_date,
                items=self.cart_items,
                notes=f"PO Received from {supp_name}"
            )
            messagebox.showinfo("Purchase Recorded", f"Purchase Order #{po_id} successfully created!\nInventory stock updated automatically.")
            self.cart_items.clear()
            self.refresh_cart_view()
            self.load_metadata()
            self.load_purchase_history()
            self.nb.select(1) # Switch to history tab
        except Exception as e:
            messagebox.showerror("Transaction Error", f"Failed to record purchase order (Rollback executed):\n{str(e)}")

    def load_purchase_history(self):
        purchases = get_purchases_list()
        rows = [
            (
                p['purchase_id'],
                str(p['purchase_date']),
                p['supplier_name'],
                p['total_items'],
                f"${float(p['total_amount']):,.2f}",
                p['notes'] or ''
            )
            for p in purchases
        ]
        self.hist_table.populate(rows)

    def on_history_select(self, event=None):
        sel = self.hist_table.get_selected()
        if not sel:
            return
        po_id = int(sel[0])
        details = get_purchase_details(po_id)
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
