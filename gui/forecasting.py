"""
gui/forecasting.py
Stock Forecasting Module:
- Forecast Methods: Moving Average & Linear Regression (Scikit-learn)
- Forecast Periods: 7 Days, 14 Days, 30 Days
- Output metrics: Current Stock, Predicted Daily Demand, Expected Demand,
  Estimated Days Until Stock-Out, Risk Assessment, Reorder Recommendation
- Interactive Product Demand Plot: Historical Sales vs. Forecasted Demand
- All Product Forecasting Results Treeview Table
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
from gui.widgets import TableView
from database.queries import get_all_products
from services.forecasting_service import ForecastingService
from utils.csv_export import export_records_to_csv

class ForecastingView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.products_cache = []
        self.forecast_results: List[Dict[str, Any]] = []
        self.canvas = None

        self.build_ui()
        self.load_products()
        self.generate_forecast()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Stock Forecasting & Predictive Intelligence", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        btn_export = ttk.Button(top_bar, text="⬇ Export Forecast Results", style="Teal.TButton", command=self.export_forecast)
        btn_export.pack(side="right")

        # ── Control Parameter Bar ──
        param_bar = tk.LabelFrame(self, text=" Forecasting Parameters ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=8)
        param_bar.pack(fill="x", padx=25, pady=(0, 10))

        # Model Selector
        tk.Label(param_bar, text="Forecast Method:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_method = ttk.Combobox(param_bar, state="readonly", width=18, values=["Linear Regression", "Moving Average"])
        self.cb_method.set("Linear Regression")
        self.cb_method.pack(side="left", padx=(0, 15))

        # Forecast Horizon
        tk.Label(param_bar, text="Forecast Horizon:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_period = ttk.Combobox(param_bar, state="readonly", width=12, values=["7 Days", "14 Days", "30 Days"])
        self.cb_period.set("7 Days")
        self.cb_period.pack(side="left", padx=(0, 15))

        # Focus Product Picker
        tk.Label(param_bar, text="Inspect Product:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_prod = ttk.Combobox(param_bar, state="readonly", width=25)
        self.cb_prod.pack(side="left", padx=(0, 15))
        self.cb_prod.bind("<<ComboboxSelected>>", self.on_product_inspect)

        btn_run = ttk.Button(param_bar, text="⚡ Generate Forecast", style="Aqua.TButton", command=self.generate_forecast)
        btn_run.pack(side="left", padx=5)

        # ── Split Section: Top Detail & Chart, Bottom Comprehensive Table ──
        upper_split = tk.Frame(self, bg=CREAM)
        upper_split.pack(fill="x", padx=25, pady=(0, 10))

        # Left Info Card: Single Product Forecast Summary
        self.summary_box = tk.LabelFrame(upper_split, text=" Product Forecast Diagnostics ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=14, pady=10, width=380, height=230)
        self.summary_box.pack(side="left", fill="both", padx=(0, 10))
        self.summary_box.pack_propagate(False)

        self.lbl_pname = tk.Label(self.summary_box, text="Product: -", font=FONT_BODY_BOLD, bg=CREAM, fg=TEAL, anchor="w")
        self.lbl_pname.pack(fill="x", pady=1)

        self.lbl_stock = tk.Label(self.summary_box, text="Current Stock: -", font=FONT_BODY, bg=CREAM, fg=DARK_TEAL, anchor="w")
        self.lbl_stock.pack(fill="x", pady=1)

        self.lbl_demand = tk.Label(self.summary_box, text="Predicted Daily Demand: -", font=FONT_BODY, bg=CREAM, fg=DARK_TEAL, anchor="w")
        self.lbl_demand.pack(fill="x", pady=1)

        self.lbl_horizon = tk.Label(self.summary_box, text="Forecast Period: -", font=FONT_BODY, bg=CREAM, fg=DARK_TEAL, anchor="w")
        self.lbl_horizon.pack(fill="x", pady=1)

        self.lbl_stockout = tk.Label(self.summary_box, text="Estimated Stock-Out: -", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL, anchor="w")
        self.lbl_stockout.pack(fill="x", pady=1)

        self.lbl_reorder = tk.Label(self.summary_box, text="Recommendation: -", font=FONT_BODY_BOLD, bg=CREAM, fg=TEAL, anchor="w")
        self.lbl_reorder.pack(fill="x", pady=2)

        # Right Chart: Matplotlib Historical vs Forecast
        self.chart_box = tk.LabelFrame(upper_split, text=" Historical Sales vs Forecasted Demand ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=8, pady=5)
        self.chart_box.pack(side="right", fill="both", expand=True)

        # ── Lower Table: Forecast for All Products ──
        table_box = tk.LabelFrame(self, text=" All Inventory Forecast Results & Stock-Out Estimation ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        table_box.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        fc_cols = [
            ("product_id", "ID", 45),
            ("product_name", "Product Name", 170),
            ("current_stock", "Current Stock", 90),
            ("pred_demand", "Pred Daily Demand", 120),
            ("days_left", "Days Until Stock-Out", 140),
            ("reorder_level", "Reorder Level", 90),
            ("recom_qty", "Recommended Qty", 120),
            ("risk", "Stock Risk Level", 110),
            ("recommendation", "Recommendation", 170),
        ]
        self.table = TableView(table_box, columns=fc_cols, on_select=self.on_table_row_select)
        self.table.pack(fill="both", expand=True)

    def load_products(self):
        self.products_cache = get_all_products()
        prod_items = [f"{p['product_id']}: {p['product_name']}" for p in self.products_cache]
        self.cb_prod['values'] = prod_items
        if prod_items:
            self.cb_prod.set(prod_items[0])

    def get_period_days(self) -> int:
        p = self.cb_period.get()
        if "14" in p: return 14
        if "30" in p: return 30
        return 7

    def generate_forecast(self):
        method = self.cb_method.get()
        days = self.get_period_days()

        try:
            self.forecast_results = ForecastingService.generate_all_forecasts(method=method, forecast_days=days)
            rows = [
                (
                    r['product_id'],
                    r['product_name'],
                    r['current_stock'],
                    f"{r['predicted_daily_demand']:.2f} units",
                    f"{r['days_left']} days" if isinstance(r['days_left'], (int, float)) else r['days_left'],
                    r['reorder_level'],
                    r['recommended_qty'],
                    r['risk'],
                    r['recommendation']
                )
                for r in self.forecast_results
            ]
            self.table.populate(rows)

            # Update selected product view
            self.on_product_inspect()

        except Exception as e:
            messagebox.showerror("Forecasting Error", f"Failed to compute stock forecast:\n{str(e)}")

    def on_product_inspect(self, event=None):
        selected = self.cb_prod.get()
        if not selected or not self.forecast_results:
            return
        p_id = int(selected.split(":")[0])
        res = next((r for r in self.forecast_results if r['product_id'] == p_id), None)
        if not res:
            return

        self.update_single_product_display(res)

    def on_table_row_select(self, event=None):
        sel = self.table.get_selected()
        if not sel:
            return
        p_id = int(sel[0])
        # Find item in cb_prod
        for val in self.cb_prod['values']:
            if val.startswith(f"{p_id}:"):
                self.cb_prod.set(val)
                break
        res = next((r for r in self.forecast_results if r['product_id'] == p_id), None)
        if res:
            self.update_single_product_display(res)

    def update_single_product_display(self, res: Dict[str, Any]):
        self.lbl_pname.config(text=f"Product: {res['product_name']}")
        self.lbl_stock.config(text=f"Current Stock: {res['current_stock']} units")
        self.lbl_demand.config(text=f"Predicted Daily Demand: {res['predicted_daily_demand']} units")
        self.lbl_horizon.config(text=f"Forecast Horizon: {res['forecast_period']} days (Exp: {res['expected_demand']} units)")
        
        days_str = f"{res['days_left']} days" if isinstance(res['days_left'], (int, float)) else res['days_left']
        self.lbl_stockout.config(text=f"Days Until Stock-Out: {days_str}")
        self.lbl_reorder.config(text=f"Action: {res['recommendation']} ({res['recommended_qty']} units)")

        # Render Chart
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(6.5, 2.3), dpi=100)
        fig.patch.set_facecolor(CREAM)
        ax = fig.add_subplot(111)
        ax.set_facecolor(CREAM)

        hist_dates = res.get('hist_dates', [])
        hist_vals = res.get('hist_values', [])
        fc_dates = res.get('forecast_dates', [])
        fc_vals = res.get('forecast_values', [])

        if hist_dates and hist_vals:
            ax.plot(hist_dates, hist_vals, color=DARK_TEAL, marker='o', markersize=3, label="Historical Sales", linewidth=1.5)
            
            # Connect last hist to first forecast
            combined_dates = [hist_dates[-1]] + fc_dates
            combined_vals = [hist_vals[-1]] + fc_vals
            ax.plot(combined_dates, combined_vals, color=TEAL, linestyle='--', marker='s', markersize=4, label="Forecast Demand", linewidth=2)
            ax.fill_between(combined_dates, combined_vals, color=AQUA, alpha=0.3)
        else:
            ax.text(0.5, 0.5, "Insufficient sales history to render plot.", horizontalalignment='center', verticalalignment='center', color=DARK_TEAL)

        ax.set_title(f"Demand Trajectory: {res['product_name']}", fontsize=10, fontweight='bold', color=DARK_TEAL)
        ax.tick_params(axis='x', rotation=30, labelsize=7, colors=DARK_TEAL)
        ax.tick_params(axis='y', labelsize=8, colors=DARK_TEAL)
        for spine in ax.spines.values():
            spine.set_color(TEAL)
        ax.legend(facecolor=CREAM, edgecolor=TEAL, fontsize=8)
        ax.grid(True, linestyle=":", alpha=0.4, color=TEAL)

        fig.tight_layout(pad=1.2)
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_box)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_forecast(self):
        if not self.forecast_results:
            return messagebox.showwarning("Export Warning", "No forecast data available to export.")
        export_records_to_csv(self.forecast_results, default_filename="stock_forecast.csv", title="Export Stock Forecast")
