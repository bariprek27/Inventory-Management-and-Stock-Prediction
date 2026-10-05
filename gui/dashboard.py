"""
gui/dashboard.py
Dashboard screen featuring:
- Dynamic stat cards: Total Products, Total Suppliers, Current Stock Value,
  Today's Sales, Monthly Sales, Low Stock Products, Out of Stock, Forecasted Stock Risk
- Quick Action Buttons: Sales Analysis, Inventory Analysis, Stock Forecast, Reorder Recommendations, Reports
- Recent Activity Feed & Stock Alert table
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import StatCard, TableView
from database.queries import get_dashboard_metrics, get_inventory_view
from services.forecasting_service import ForecastingService

class DashboardView(tk.Frame):
    def __init__(self, parent, nav_callback: Callable[[str], None]):
        super().__init__(parent, bg=CREAM)
        self.nav_callback = nav_callback
        
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        # Top banner with title and refresh button
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Dashboard Overview", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        btn_refresh = ttk.Button(top_bar, text="⟳ Refresh Dashboard", style="Teal.TButton", command=self.refresh_data)
        btn_refresh.pack(side="right")

        # ─── STAT CARDS GRID (8 Cards) ───────────────────────────
        cards_frame = tk.Frame(self, bg=CREAM)
        cards_frame.pack(fill="x", padx=20, pady=5)
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="card")

        self.card_products = StatCard(cards_frame, "Total Products", "0", "Catalog registered")
        self.card_products.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_suppliers = StatCard(cards_frame, "Total Suppliers", "0", "Active vendors")
        self.card_suppliers.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_stock_value = StatCard(cards_frame, "Current Stock Value", "$0.00", "Cost valuation")
        self.card_stock_value.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        self.card_today_sales = StatCard(cards_frame, "Today's Sales", "$0.00", "Daily revenue")
        self.card_today_sales.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")

        self.card_month_sales = StatCard(cards_frame, "Monthly Sales", "$0.00", "Current month")
        self.card_month_sales.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")

        self.card_low_stock = StatCard(cards_frame, "Low Stock Products", "0", "Below reorder level")
        self.card_low_stock.grid(row=1, column=1, padx=6, pady=6, sticky="nsew")

        self.card_out_of_stock = StatCard(cards_frame, "Out of Stock", "0", "Zero inventory units")
        self.card_out_of_stock.grid(row=1, column=2, padx=6, pady=6, sticky="nsew")

        self.card_forecast_risk = StatCard(cards_frame, "Forecasted Stock Risk", "0", "Predicted shortage")
        self.card_forecast_risk.grid(row=1, column=3, padx=6, pady=6, sticky="nsew")

        # ─── QUICK ACTION BUTTONS BAR (Mandatory Section 7 & 38) ───
        action_bar = tk.LabelFrame(self, text=" Analytical Control Center ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=10)
        action_bar.pack(fill="x", padx=25, pady=15)

        for col_idx in range(5):
            action_bar.grid_columnconfigure(col_idx, weight=1, uniform="act")

        btn_sales_an = ttk.Button(action_bar, text="📊 Sales Analysis", style="Teal.TButton", 
                                  command=lambda: self.nav_callback("Analytics"))
        btn_sales_an.grid(row=0, column=0, padx=6, pady=4, sticky="nsew", ipady=4)

        btn_inv_an = ttk.Button(action_bar, text="📦 Inventory Analysis", style="Teal.TButton", 
                                command=lambda: self.nav_callback("Inventory"))
        btn_inv_an.grid(row=0, column=1, padx=6, pady=4, sticky="nsew", ipady=4)

        btn_stock_fc = ttk.Button(action_bar, text="📈 Stock Forecast", style="Aqua.TButton", 
                                  command=lambda: self.nav_callback("Forecasting"))
        btn_stock_fc.grid(row=0, column=2, padx=6, pady=4, sticky="nsew", ipady=4)

        btn_reorder = ttk.Button(action_bar, text="⚠️ Reorder Recommendations", style="Aqua.TButton", 
                                 command=lambda: self.nav_callback("Reorder"))
        btn_reorder.grid(row=0, column=3, padx=6, pady=4, sticky="nsew", ipady=4)

        btn_reports = ttk.Button(action_bar, text="📄 Reports & Export", style="Teal.TButton", 
                                 command=lambda: self.nav_callback("Reports"))
        btn_reports.grid(row=0, column=4, padx=6, pady=4, sticky="nsew", ipady=4)

        # ─── ATTENTION ITEMS / LOW STOCK PREVIEW TABLE ─────────────
        alert_frame = tk.LabelFrame(self, text=" Critical Stock Watchlist (Low / Out of Stock) ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=12, pady=10)
        alert_frame.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        columns = [
            ("product_id", "ID", 60),
            ("product_name", "Product Name", 220),
            ("category_name", "Category", 130),
            ("current_stock", "Current Stock", 100),
            ("reorder_level", "Reorder Level", 100),
            ("supplier_name", "Supplier", 180),
            ("stock_status", "Status", 120),
        ]
        self.table = TableView(alert_frame, columns=columns)
        self.table.pack(fill="both", expand=True)

    def refresh_data(self):
        try:
            m = get_dashboard_metrics()
            
            self.card_products.update_value(str(m.get('total_products', 0)))
            self.card_suppliers.update_value(str(m.get('total_suppliers', 0)))
            
            stock_val = float(m.get('current_stock_value', 0.0))
            self.card_stock_value.update_value(f"${stock_val:,.2f}")
            
            today_sales = float(m.get('today_sales', 0.0))
            self.card_today_sales.update_value(f"${today_sales:,.2f}")
            
            monthly_sales = float(m.get('monthly_sales', 0.0))
            self.card_month_sales.update_value(f"${monthly_sales:,.2f}")
            
            self.card_low_stock.update_value(str(m.get('low_stock_count', 0)))
            self.card_out_of_stock.update_value(str(m.get('out_of_stock_count', 0)))

            # Calculate forecasted risk dynamically
            risk_count = ForecastingService.get_forecasted_risk_count()
            self.card_forecast_risk.update_value(str(risk_count))

            # Populate Critical Watchlist (Low stock + Out of Stock)
            items = get_inventory_view()
            critical_items = [
                (
                    item['product_id'],
                    item['product_name'],
                    item['category_name'],
                    item['current_stock'],
                    item['reorder_level'],
                    item['supplier_name'],
                    item['stock_status']
                )
                for item in items
                if item['stock_status'] in ['Out of Stock', 'Low Stock']
            ]
            self.table.populate(critical_items)
            
        except Exception as e:
            messagebox.showerror("Dashboard Error", f"Failed to refresh dashboard stats:\n{str(e)}")
