"""
main.py
StockWise Application Entrypoint:
- App Window setup & Theme styling
- Session Management (Login screen -> Central Dashboard)
- Left Sidebar Navigation (Dark Teal #001E23) with Active Teal buttons (#007887)
- Central Content switching (Cream #FAF6EE background)
- Role-based permissions (Admin vs Staff)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_pool, test_connection
from gui.theme import setup_ttk_styles, DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.login import LoginWindow
from gui.dashboard import DashboardView
from gui.products import ProductsView
from gui.categories import CategoriesView
from gui.suppliers import SuppliersView
from gui.purchases import PurchasesView
from gui.sales import SalesView
from gui.inventory import InventoryView
from gui.analytics import AnalyticsView
from gui.forecasting import ForecastingView
from gui.reorder import ReorderView
from gui.reports import ReportsView
from utils.security import CurrentUser

class StockWiseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("StockWise - Desktop Inventory Management & Stock Forecasting System")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)
        self.root.configure(bg=CREAM)

        setup_ttk_styles(self.root)

        self.current_nav_button = None
        self.nav_buttons = {}
        self.active_view = None

        # Check DB connection
        self.check_database()

        # Start with Login Screen
        self.show_login()

    def check_database(self):
        try:
            init_pool()
            if not test_connection():
                print("Warning: Database ping failed. Verify MySQL service is running and 'stockwise' DB exists.")
        except Exception as e:
            print(f"DB Pool Initialization Warning: {e}")

    def show_login(self):
        # Clear root
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.withdraw() # Hide main app window while login dialog is up
        login_top = tk.Toplevel(self.root)
        
        def on_success():
            login_top.destroy()
            self.root.deiconify()
            self.build_main_app()

        def on_cancel():
            login_top.destroy()
            self.root.destroy()
            sys.exit(0)

        login_top.protocol("WM_DELETE_WINDOW", on_cancel)
        LoginWindow(login_top, on_login_success=on_success)

    def build_main_app(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # ── TOP HEADER (Dark Teal) ──
        header = tk.Frame(self.root, bg=DARK_TEAL, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        brand_lbl = tk.Label(header, text="StockWise System", font=(FONT_TITLE[0], 15, "bold"), bg=DARK_TEAL, fg=AQUA)
        brand_lbl.pack(side="left", padx=20)

        role_badge = f"Logged in as: {CurrentUser.name} ({CurrentUser.role.upper()})"
        user_lbl = tk.Label(header, text=role_badge, font=FONT_BODY_BOLD, bg=DARK_TEAL, fg=CREAM)
        user_lbl.pack(side="right", padx=20)

        # ── MAIN LAYOUT: Sidebar (Left) + Content (Center) ──
        container = tk.Frame(self.root, bg=CREAM)
        container.pack(fill="both", expand=True)

        # ── SIDEBAR (Dark Teal) ──
        self.sidebar = tk.Frame(container, bg=DARK_TEAL, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Navigation items: label, key, admin_only
        nav_items = [
            ("📊 Dashboard", "Dashboard", False),
            ("📦 Products", "Products", False),
            ("📁 Categories", "Categories", False),
            ("🏭 Suppliers", "Suppliers", False),
            ("📥 Purchases", "Purchases", False),
            ("🛒 Sales (POS)", "Sales", False),
            ("📋 Inventory", "Inventory", False),
            ("📈 Sales Analysis", "Analytics", False),
            ("🔮 Forecasting", "Forecasting", False),
            ("⚠️ Reorder Advice", "Reorder", False),
            ("📄 Reports & CSV", "Reports", False),
        ]

        tk.Label(self.sidebar, text="MAIN MENU", font=(FONT_BODY_BOLD[0], 9), bg=DARK_TEAL, fg=TEAL, anchor="w").pack(fill="x", padx=16, pady=(15, 6))

        for label_text, key, admin_only in nav_items:
            # Check permissions
            if admin_only and not CurrentUser.is_admin():
                continue

            btn = ttk.Button(
                self.sidebar,
                text=label_text,
                style="Nav.TButton",
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=2, padx=8)
            self.nav_buttons[key] = btn

        # Logout at bottom
        logout_btn = ttk.Button(
            self.sidebar,
            text="🚪 Logout",
            style="Nav.TButton",
            command=self.logout
        )
        logout_btn.pack(side="bottom", fill="x", pady=(0, 15), padx=8)

        # ── CENTRAL CONTENT AREA (Cream) ──
        self.content_frame = tk.Frame(container, bg=CREAM)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Default to Dashboard
        self.navigate_to("Dashboard")

    def navigate_to(self, view_name: str):
        # Update Nav Button Highlight
        if self.current_nav_button and self.current_nav_button in self.nav_buttons.values():
            self.current_nav_button.configure(style="Nav.TButton")

        btn = self.nav_buttons.get(view_name)
        if btn:
            btn.configure(style="NavActive.TButton")
            self.current_nav_button = btn

        # Clear active view
        if self.active_view:
            self.active_view.destroy()

        # Instantiate requested view
        if view_name == "Dashboard":
            self.active_view = DashboardView(self.content_frame, nav_callback=self.navigate_to)
        elif view_name == "Products":
            self.active_view = ProductsView(self.content_frame)
        elif view_name == "Categories":
            self.active_view = CategoriesView(self.content_frame)
        elif view_name == "Suppliers":
            self.active_view = SuppliersView(self.content_frame)
        elif view_name == "Purchases":
            self.active_view = PurchasesView(self.content_frame)
        elif view_name == "Sales":
            self.active_view = SalesView(self.content_frame)
        elif view_name == "Inventory":
            self.active_view = InventoryView(self.content_frame)
        elif view_name == "Analytics":
            self.active_view = AnalyticsView(self.content_frame)
        elif view_name == "Forecasting":
            self.active_view = ForecastingView(self.content_frame)
        elif view_name == "Reorder":
            self.active_view = ReorderView(self.content_frame, nav_callback=self.navigate_to)
        elif view_name == "Reports":
            self.active_view = ReportsView(self.content_frame)
        else:
            self.active_view = DashboardView(self.content_frame, nav_callback=self.navigate_to)

        self.active_view.pack(fill="both", expand=True)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            CurrentUser.clear()
            self.show_login()


def main():
    root = tk.Tk()
    app = StockWiseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
