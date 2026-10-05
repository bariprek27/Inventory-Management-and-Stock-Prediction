"""
gui/reorder.py
Reorder Recommendations Page:
- Dedicated module displaying products that require replenishment
- Columns: Product, Current Stock, Predicted Daily Demand, Supplier, Lead Time, Safety Stock, Recommended Quantity, Priority
- Filtering by Critical Products / Priority
- One-click trigger to generate Purchase Order draft
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Callable

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView
from services.reorder_service import ReorderService
from utils.csv_export import export_records_to_csv

class ReorderView(tk.Frame):
    def __init__(self, parent, nav_callback: Callable[[str], None]):
        super().__init__(parent, bg=CREAM)
        self.nav_callback = nav_callback
        self.reorder_items: List[Dict[str, Any]] = []

        self.build_ui()
        self.load_reorders()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Intelligent Reorder Recommendations", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        btn_export = ttk.Button(top_bar, text="⬇ Export Recommendations", style="Teal.TButton", command=self.export_data)
        btn_export.pack(side="right", padx=(6, 0))

        btn_refresh = ttk.Button(top_bar, text="⟳ Recalculate", style="Aqua.TButton", command=self.load_reorders)
        btn_refresh.pack(side="right")

        # ── Filter Bar ──
        filter_bar = tk.LabelFrame(self, text=" Filter & Sort Priority ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=8)
        filter_bar.pack(fill="x", padx=25, pady=(0, 10))

        tk.Label(filter_bar, text="Priority Filter:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_prio = ttk.Combobox(filter_bar, state="readonly", width=14, values=["All At-Risk", "Critical Only", "High Only", "Medium Only"])
        self.cb_prio.set("All At-Risk")
        self.cb_prio.pack(side="left", padx=(0, 15))
        self.cb_prio.bind("<<ComboboxSelected>>", lambda e: self.filter_display())

        # Formula Explainer Note
        formula_lbl = tk.Label(
            filter_bar, 
            text="Formula: Required Stock = (Predicted Demand × Lead Time) + Safety Stock | Reorder Qty = Required - Current Stock",
            font=FONT_BODY, bg=CREAM, fg=TEAL
        )
        formula_lbl.pack(side="right")

        # ── Recommendations Table ──
        table_frame = tk.Frame(self, bg=CREAM)
        table_frame.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        columns = [
            ("product_id", "ID", 45),
            ("product_name", "Product Name", 180),
            ("current_stock", "Current Stock", 90),
            ("pred_demand", "Pred Daily Demand", 120),
            ("supplier_name", "Supplier", 170),
            ("lead_time", "Lead Time (Days)", 110),
            ("safety_stock", "Safety Stock", 85),
            ("recom_qty", "Recommended Qty", 120),
            ("priority", "Replenishment Priority", 140),
        ]
        self.table = TableView(table_frame, columns=columns)
        self.table.pack(fill="both", expand=True)

        # Bottom Bar: Direct Action to PO module
        bottom_bar = tk.Frame(self, bg=CREAM)
        bottom_bar.pack(fill="x", padx=25, pady=(0, 15))

        btn_create_po = ttk.Button(
            bottom_bar,
            text="➜ Proceed to Purchase Orders Module",
            style="Teal.TButton",
            command=lambda: self.nav_callback("Purchases")
        )
        btn_create_po.pack(side="right", ipady=4)

    def load_reorders(self):
        try:
            self.reorder_items = ReorderService.get_reorder_list()
            self.filter_display()
        except Exception as e:
            messagebox.showerror("Reorder Service Error", f"Failed to compute reorder list:\n{str(e)}")

    def filter_display(self):
        crit = self.cb_prio.get()
        filtered = self.reorder_items
        if crit == "Critical Only":
            filtered = [r for r in filtered if r['priority'] == "Critical" or r['risk'] == "Out of Stock"]
        elif crit == "High Only":
            filtered = [r for r in filtered if r['priority'] == "High"]
        elif crit == "Medium Only":
            filtered = [r for r in filtered if r['priority'] == "Medium" or r['risk'] == "Moderate Risk"]

        rows = [
            (
                r['product_id'],
                r['product_name'],
                r['current_stock'],
                f"{r['predicted_daily_demand']:.2f} / day",
                r['supplier_name'],
                f"{r['lead_time']} days",
                r['safety_stock'],
                f"{r['recommended_qty']} units",
                r['priority']
            )
            for r in filtered
        ]
        self.table.populate(rows)

    def export_data(self):
        if not self.reorder_items:
            return messagebox.showwarning("Export Warning", "No reorder recommendations to export.")
        export_records_to_csv(self.reorder_items, default_filename="reorder_recommendations.csv", title="Export Reorder Recommendations")
