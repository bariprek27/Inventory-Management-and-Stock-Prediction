"""
gui/analytics.py
Sales Analysis Module:
- Date Filtering: Start Date and End Date with 'Analyze' button
- Metrics: Revenue, Total Units Sold, Total Orders, Average Daily Sales
- Embedded Matplotlib Charts:
  1. Sales Revenue Trend over Time
  2. Category-wise Revenue Distribution
  3. Top 5 Best-Selling Products
  4. Fast-Moving vs Slow-Moving comparison
- Strict adherence to project color palette:
  #001E23, #007887, #78E6DC, #FAF6EE
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import StatCard, TableView
from services.analytics_service import AnalyticsService
from utils.csv_export import export_dataframe_to_csv

class AnalyticsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)

        self.current_data = None
        self.canvas = None

        self.build_ui()
        self.run_analysis()

    def build_ui(self):
        # Top banner
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Sales Analysis & Performance Analytics", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        btn_export = ttk.Button(top_bar, text="⬇ Export Analysis Data", style="Teal.TButton", command=self.export_analysis)
        btn_export.pack(side="right")

        # ── Date Filter Control Bar ──
        filter_bar = tk.LabelFrame(self, text=" Period Filter ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=12, pady=8)
        filter_bar.pack(fill="x", padx=25, pady=(0, 10))

        tk.Label(filter_bar, text="Start Date (YYYY-MM-DD):", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.ent_start = ttk.Entry(filter_bar, width=13)
        self.ent_start.pack(side="left", padx=(0, 15))
        # Default start date 90 days ago
        default_start = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
        self.ent_start.insert(0, default_start)

        tk.Label(filter_bar, text="End Date (YYYY-MM-DD):", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.ent_end = ttk.Entry(filter_bar, width=13)
        self.ent_end.pack(side="left", padx=(0, 15))
        self.ent_end.insert(0, str(date.today()))

        btn_analyze = ttk.Button(filter_bar, text="🔍 Analyze Period", style="Teal.TButton", command=self.run_analysis)
        btn_analyze.pack(side="left", padx=5)

        # Quick preset buttons
        btn_30d = ttk.Button(filter_bar, text="Last 30 Days", style="Aqua.TButton", command=lambda: self.set_preset_days(30))
        btn_30d.pack(side="left", padx=3)

        btn_90d = ttk.Button(filter_bar, text="Last 90 Days", style="Aqua.TButton", command=lambda: self.set_preset_days(90))
        btn_90d.pack(side="left", padx=3)

        btn_all = ttk.Button(filter_bar, text="All Time", style="Aqua.TButton", command=self.set_all_time)
        btn_all.pack(side="left", padx=3)

        # ── KPI Metrics Row ──
        cards_frame = tk.Frame(self, bg=CREAM)
        cards_frame.pack(fill="x", padx=25, pady=(0, 10))
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="an_card")

        self.kpi_rev = StatCard(cards_frame, "Period Revenue", "$0.00", "Total gross sales")
        self.kpi_rev.grid(row=0, column=0, padx=5, sticky="nsew")

        self.kpi_units = StatCard(cards_frame, "Units Sold", "0", "Total items checked out")
        self.kpi_units.grid(row=0, column=1, padx=5, sticky="nsew")

        self.kpi_orders = StatCard(cards_frame, "Completed Orders", "0", "Number of sale tickets")
        self.kpi_orders.grid(row=0, column=2, padx=5, sticky="nsew")

        self.kpi_daily = StatCard(cards_frame, "Avg Daily Revenue", "$0.00", "Average turnover / day")
        self.kpi_daily.grid(row=0, column=3, padx=5, sticky="nsew")

        # ── Notebook for Visualizations & Product Tables ──
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Tab 1: Charts
        self.tab_charts = tk.Frame(self.nb, bg=CREAM)
        self.nb.add(self.tab_charts, text="Visual Charts (Matplotlib)")

        # Tab 2: Fast & Slow Moving
        tab_movers = tk.Frame(self.nb, bg=CREAM, padx=12, pady=12)
        self.nb.add(tab_movers, text="Fast & Slow Moving Products")

        movers_split = tk.Frame(tab_movers, bg=CREAM)
        movers_split.pack(fill="both", expand=True)

        fast_box = tk.LabelFrame(movers_split, text=" Fast-Moving Products (Top Volume) ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        fast_box.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.tbl_fast = TableView(fast_box, columns=[("id", "ID", 45), ("name", "Product Name", 180), ("cat", "Category", 110), ("units", "Units Sold", 80), ("rev", "Revenue ($)", 90)])
        self.tbl_fast.pack(fill="both", expand=True)

        slow_box = tk.LabelFrame(movers_split, text=" Slow-Moving Products (Lowest Volume) ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        slow_box.pack(side="right", fill="both", expand=True, padx=(8, 0))
        self.tbl_slow = TableView(slow_box, columns=[("id", "ID", 45), ("name", "Product Name", 180), ("cat", "Category", 110), ("units", "Units Sold", 80), ("rev", "Revenue ($)", 90)])
        self.tbl_slow.pack(fill="both", expand=True)

    def set_preset_days(self, days: int):
        self.ent_start.delete(0, tk.END)
        self.ent_start.insert(0, (date.today() - timedelta(days=days)).strftime("%Y-%m-%d"))
        self.ent_end.delete(0, tk.END)
        self.ent_end.insert(0, str(date.today()))
        self.run_analysis()

    def set_all_time(self):
        self.ent_start.delete(0, tk.END)
        self.ent_start.insert(0, "2020-01-01")
        self.ent_end.delete(0, tk.END)
        self.ent_end.insert(0, str(date.today()))
        self.run_analysis()

    def run_analysis(self):
        start = self.ent_start.get().strip()
        end = self.ent_end.get().strip()

        data = AnalyticsService.get_sales_analytics(start_date=start, end_date=end)
        self.current_data = data

        self.kpi_rev.update_value(f"${data['total_revenue']:,.2f}")
        self.kpi_units.update_value(f"{data['total_units']:,}")
        self.kpi_orders.update_value(f"{data['total_orders']:,}")
        self.kpi_daily.update_value(f"${data['avg_daily_sales']:,.2f}")

        # Populate tables
        if data['has_data']:
            fast_rows = [
                (r['product_id'], r['product_name'], r['category_name'], r['units_sold'], f"${float(r['revenue']):,.2f}")
                for _, r in data['fast_moving'].iterrows()
            ]
            self.tbl_fast.populate(fast_rows)

            slow_rows = [
                (r['product_id'], r['product_name'], r['category_name'], r['units_sold'], f"${float(r['revenue']):,.2f}")
                for _, r in data['slow_moving'].iterrows()
            ]
            self.tbl_slow.populate(slow_rows)
        else:
            self.tbl_fast.clear()
            self.tbl_slow.clear()

        # Render Matplotlib plots
        self.render_charts(data)

    def render_charts(self, data):
        # Destroy existing canvas
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(10, 4.8), dpi=100)
        fig.patch.set_facecolor(CREAM)

        if not data['has_data'] or data['daily_trend'].empty:
            ax = fig.add_subplot(111)
            ax.set_facecolor(CREAM)
            ax.text(0.5, 0.5, "No sales data found for the selected time period.",
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=12, color=DARK_TEAL)
            ax.axis('off')
        else:
            # 2x2 Subplots layout
            # 1. Sales Trend over time (Line)
            ax1 = fig.add_subplot(221)
            ax1.set_facecolor(CREAM)
            trend = data['daily_trend']
            ax1.plot(trend['date'], trend['revenue'], color=TEAL, marker='o', markersize=3, linewidth=2, label="Revenue ($)")
            ax1.set_title("Revenue Trend Over Time", fontsize=10, fontweight='bold', color=DARK_TEAL)
            ax1.tick_params(axis='x', rotation=30, labelsize=7, colors=DARK_TEAL)
            ax1.tick_params(axis='y', labelsize=8, colors=DARK_TEAL)
            for spine in ax1.spines.values():
                spine.set_color(TEAL)
            ax1.grid(True, linestyle="--", alpha=0.3, color=DARK_TEAL)

            # 2. Category-Wise Sales (Bar)
            ax2 = fig.add_subplot(222)
            ax2.set_facecolor(CREAM)
            cat_df = data['category_sales']
            if not cat_df.empty:
                bars = ax2.bar(cat_df['category_name'], cat_df['revenue'], color=DARK_TEAL, edgecolor=AQUA, width=0.5)
                ax2.set_title("Category-Wise Revenue", fontsize=10, fontweight='bold', color=DARK_TEAL)
                ax2.tick_params(axis='x', rotation=25, labelsize=8, colors=DARK_TEAL)
                ax2.tick_params(axis='y', labelsize=8, colors=DARK_TEAL)
                for spine in ax2.spines.values():
                    spine.set_color(TEAL)

            # 3. Top 5 Products by Quantity (Horizontal Bar)
            ax3 = fig.add_subplot(223)
            ax3.set_facecolor(CREAM)
            top_df = data['top_products']
            if not top_df.empty:
                ax3.barh(top_df['product_name'], top_df['total_sold'], color=TEAL, edgecolor=DARK_TEAL, height=0.55)
                ax3.set_title("Top 5 Best-Selling Products (Units)", fontsize=10, fontweight='bold', color=DARK_TEAL)
                ax3.tick_params(axis='y', labelsize=8, colors=DARK_TEAL)
                ax3.tick_params(axis='x', labelsize=8, colors=DARK_TEAL)
                ax3.invert_yaxis()
                for spine in ax3.spines.values():
                    spine.set_color(TEAL)

            # 4. Units Sold Over Time (Line with AQUA highlight)
            ax4 = fig.add_subplot(224)
            ax4.set_facecolor(CREAM)
            ax4.plot(trend['date'], trend['units'], color=DARK_TEAL, marker='s', markersize=3, linewidth=1.8, label="Units")
            ax4.fill_between(trend['date'], trend['units'], color=AQUA, alpha=0.35)
            ax4.set_title("Daily Units Sold Volume", fontsize=10, fontweight='bold', color=DARK_TEAL)
            ax4.tick_params(axis='x', rotation=30, labelsize=7, colors=DARK_TEAL)
            ax4.tick_params(axis='y', labelsize=8, colors=DARK_TEAL)
            for spine in ax4.spines.values():
                spine.set_color(TEAL)
            ax4.grid(True, linestyle="--", alpha=0.3, color=DARK_TEAL)

        fig.tight_layout(pad=2.0)
        self.canvas = FigureCanvasTkAgg(fig, master=self.tab_charts)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_analysis(self):
        if not self.current_data or not self.current_data['has_data']:
            return messagebox.showwarning("Export Warning", "No data to export.")
        export_dataframe_to_csv(self.current_data['raw_df'], default_filename="sales_analysis.csv", title="Export Sales Analysis")
