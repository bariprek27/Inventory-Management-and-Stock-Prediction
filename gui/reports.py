"""
gui/reports.py
Reports & Data Export Module:
- Product Report
- Supplier Report
- Inventory Report
- Sales Report
- Purchase Report
- Forecast Report
- Generated dynamically from MySQL and exported to CSV via Pandas
"""
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView
from database.queries import (
    get_all_products,
    get_all_suppliers,
    get_inventory_view,
    get_sales_list,
    get_purchases_list,
    execute_read
)
from services.forecasting_service import ForecastingService
from utils.csv_export import export_records_to_csv, export_dataframe_to_csv

class ReportsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.current_report_data = []

        self.build_ui()
        self.load_report("Inventory Report")

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Business Reports & CSV Exporter", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        btn_csv = ttk.Button(top_bar, text="⬇ Export Current Report to CSV", style="Teal.TButton", command=self.export_current_report)
        btn_csv.pack(side="right")

        # ── Report Selector Bar ──
        ctrl_bar = tk.LabelFrame(self, text=" Select Report Type ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=8)
        ctrl_bar.pack(fill="x", padx=25, pady=(0, 15))

        reports = [
            "Product Report",
            "Supplier Report",
            "Inventory Report",
            "Sales Report",
            "Purchase Report",
            "Forecast Report"
        ]

        tk.Label(ctrl_bar, text="Report Category:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 6))
        self.cb_report = ttk.Combobox(ctrl_bar, state="readonly", width=22, values=reports)
        self.cb_report.set("Inventory Report")
        self.cb_report.pack(side="left", padx=(0, 15))
        self.cb_report.bind("<<ComboboxSelected>>", lambda e: self.load_report(self.cb_report.get()))

        btn_run = ttk.Button(ctrl_bar, text="Generate Report", style="Aqua.TButton", command=lambda: self.load_report(self.cb_report.get()))
        btn_run.pack(side="left", padx=5)

        # ── Display Container ──
        self.table_container = tk.Frame(self, bg=CREAM)
        self.table_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        self.table = None

    def load_report(self, report_type: str):
        if self.table:
            self.table.destroy()

        try:
            if report_type == "Product Report":
                data = get_all_products()
                self.current_report_data = data
                cols = [
                    ("product_id", "ID", 50),
                    ("product_name", "Product Name", 180),
                    ("category_name", "Category", 120),
                    ("supplier_name", "Supplier", 150),
                    ("purchase_price", "Cost ($)", 80),
                    ("selling_price", "Sell ($)", 80),
                    ("current_stock", "Stock", 70),
                    ("reorder_level", "Reorder Level", 90),
                    ("safety_stock", "Safety Stock", 80),
                ]
                self.table = TableView(self.table_container, columns=cols)
                self.table.pack(fill="both", expand=True)
                rows = [
                    (p['product_id'], p['product_name'], p['category_name'], p['supplier_name'],
                     f"${float(p['purchase_price']):.2f}", f"${float(p['selling_price']):.2f}",
                     p['current_stock'], p['reorder_level'], p['safety_stock'])
                    for p in data
                ]
                self.table.populate(rows)

            elif report_type == "Supplier Report":
                data = get_all_suppliers()
                self.current_report_data = data
                cols = [
                    ("supplier_id", "ID", 50),
                    ("supplier_name", "Supplier Name", 180),
                    ("phone", "Phone", 110),
                    ("email", "Email", 160),
                    ("lead_time", "Lead Time (Days)", 110),
                    ("total_products", "Total Products", 90),
                    ("total_purchases", "Total POs", 80),
                ]
                self.table = TableView(self.table_container, columns=cols)
                self.table.pack(fill="both", expand=True)
                rows = [
                    (s['supplier_id'], s['supplier_name'], s['phone'] or '', s['email'] or '',
                     s['lead_time'], s['total_products'], s['total_purchases'])
                    for s in data
                ]
                self.table.populate(rows)

            elif report_type == "Inventory Report":
                data = get_inventory_view()
                self.current_report_data = data
                cols = [
                    ("product_id", "ID", 50),
                    ("product_name", "Product Name", 180),
                    ("category_name", "Category", 110),
                    ("current_stock", "Stock", 70),
                    ("reorder_level", "Reorder", 70),
                    ("safety_stock", "Safety", 70),
                    ("stock_value", "Stock Value ($)", 110),
                    ("supplier_name", "Supplier", 150),
                    ("stock_status", "Status", 110),
                ]
                self.table = TableView(self.table_container, columns=cols)
                self.table.pack(fill="both", expand=True)
                rows = [
                    (i['product_id'], i['product_name'], i['category_name'], i['current_stock'],
                     i['reorder_level'], i['safety_stock'], f"${float(i['stock_value']):,.2f}",
                     i['supplier_name'], i['stock_status'])
                    for i in data
                ]
                self.table.populate(rows)

            elif report_type == "Sales Report":
                data = get_sales_list(limit=500)
                self.current_report_data = data
                cols = [
                    ("sale_id", "Sale #", 60),
                    ("sale_date", "Date", 110),
                    ("cashier_name", "Cashier", 160),
                    ("total_items", "Items Sold", 90),
                    ("total_amount", "Revenue ($)", 120),
                ]
                self.table = TableView(self.table_container, columns=cols)
                self.table.pack(fill="both", expand=True)
                rows = [
                    (s['sale_id'], str(s['sale_date']), s['cashier_name'], s['total_items'], f"${float(s['total_amount']):,.2f}")
                    for s in data
                ]
                self.table.populate(rows)

            elif report_type == "Purchase Report":
                data = get_purchases_list(limit=500)
                self.current_report_data = data
                cols = [
                    ("purchase_id", "PO #", 60),
                    ("purchase_date", "Date", 110),
                    ("supplier_name", "Supplier", 180),
                    ("total_items", "Items", 80),
                    ("total_amount", "Cost Value ($)", 120),
                    ("notes", "Notes", 220),
                ]
                self.table = TableView(self.table_container, columns=cols)
                self.table.pack(fill="both", expand=True)
                rows = [
                    (p['purchase_id'], str(p['purchase_date']), p['supplier_name'], p['total_items'],
                     f"${float(p['total_amount']):,.2f}", p['notes'] or '')
                    for p in data
                ]
                self.table.populate(rows)

            elif report_type == "Forecast Report":
                data = ForecastingService.generate_all_forecasts()
                self.current_report_data = data
                cols = [
                    ("product_id", "ID", 45),
                    ("product_name", "Product Name", 170),
                    ("current_stock", "Stock", 65),
                    ("pred_demand", "Pred Demand/Day", 110),
                    ("days_left", "Days Left", 100),
                    ("required_stock", "Required Stock", 100),
                    ("recom_qty", "Order Qty", 90),
                    ("risk", "Risk", 100),
                    ("recommendation", "Recommendation", 160),
                ]
                self.table = TableView(self.table_container, columns=cols)
                self.table.pack(fill="both", expand=True)
                rows = [
                    (r['product_id'], r['product_name'], r['current_stock'], f"{r['predicted_daily_demand']:.2f}",
                     str(r['days_left']), r['required_stock'], r['recommended_qty'], r['risk'], r['recommendation'])
                    for r in data
                ]
                self.table.populate(rows)

        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate {report_type}:\n{str(e)}")

    def export_current_report(self):
        rep = self.cb_report.get().lower().replace(" ", "_")
        filename = f"{rep}.csv"
        export_records_to_csv(self.current_report_data, default_filename=filename, title=f"Export {self.cb_report.get()}")
