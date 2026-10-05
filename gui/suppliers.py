"""
gui/suppliers.py
Supplier Management:
- CRUD operations for suppliers
- Fields: ID, Name, Phone, Email, Address, Lead Time
- View supplier's catalog of products
- View supplier's past purchase order history
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView, SearchBar
from database.queries import (
    get_all_suppliers,
    add_supplier,
    update_supplier,
    delete_supplier,
    get_supplier_products,
    get_supplier_purchase_history
)
from utils.validators import validate_non_empty, validate_phone, validate_email, validate_positive_int

class SuppliersView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.selected_supplier_id: Optional[int] = None

        self.build_ui()
        self.load_suppliers()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Supplier Management", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        content = tk.Frame(self, bg=CREAM)
        content.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ── LEFT PANE: List & Search ──
        left_pane = tk.Frame(content, bg=CREAM)
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 15))

        search_bar = SearchBar(left_pane, on_search=self.filter_suppliers, placeholder="Search supplier name, phone...")
        search_bar.pack(fill="x", pady=(0, 10))

        columns = [
            ("supplier_id", "ID", 50),
            ("supplier_name", "Supplier Name", 170),
            ("phone", "Phone", 110),
            ("email", "Email", 160),
            ("lead_time", "Lead Time (Days)", 110),
            ("total_products", "Products", 70),
        ]
        self.table = TableView(left_pane, columns=columns, on_select=self.on_supplier_select)
        self.table.pack(fill="both", expand=True)

        # ── RIGHT PANE: Details Form + Tabs for Products/History ──
        right_pane = tk.Frame(content, bg=CREAM, width=420)
        right_pane.pack(side="right", fill="both", padx=(5, 0))
        right_pane.pack_propagate(False)

        form_frame = tk.LabelFrame(right_pane, text=" Supplier Information ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=10)
        form_frame.pack(fill="x", pady=(0, 10))

        # Name
        tk.Label(form_frame, text="Supplier Name *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=0, column=0, sticky="w", pady=2)
        self.ent_name = ttk.Entry(form_frame)
        self.ent_name.grid(row=0, column=1, sticky="ew", pady=2)

        # Phone
        tk.Label(form_frame, text="Phone", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=1, column=0, sticky="w", pady=2)
        self.ent_phone = ttk.Entry(form_frame)
        self.ent_phone.grid(row=1, column=1, sticky="ew", pady=2)

        # Email
        tk.Label(form_frame, text="Email", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=2, column=0, sticky="w", pady=2)
        self.ent_email = ttk.Entry(form_frame)
        self.ent_email.grid(row=2, column=1, sticky="ew", pady=2)

        # Lead Time
        tk.Label(form_frame, text="Lead Time (Days) *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=3, column=0, sticky="w", pady=2)
        self.ent_lead = ttk.Entry(form_frame)
        self.ent_lead.grid(row=3, column=1, sticky="ew", pady=2)

        # Address
        tk.Label(form_frame, text="Address", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=4, column=0, sticky="nw", pady=2)
        self.txt_address = tk.Text(form_frame, height=3, font=FONT_BODY, bg=CREAM, fg=DARK_TEAL, highlightbackground=TEAL, highlightthickness=1)
        self.txt_address.grid(row=4, column=1, sticky="ew", pady=2)

        form_frame.grid_columnconfigure(1, weight=1)

        # Buttons
        btn_box = tk.Frame(form_frame, bg=CREAM)
        btn_box.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.btn_save = ttk.Button(btn_box, text="Save / Update", style="Teal.TButton", command=self.save_supplier)
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_delete = ttk.Button(btn_box, text="Delete", style="Teal.TButton", command=self.delete_current_supplier)
        self.btn_delete.pack(side="left", expand=True, fill="x", padx=4)

        self.btn_clear = ttk.Button(btn_box, text="Clear", style="Aqua.TButton", command=self.clear_form)
        self.btn_clear.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Bottom notebook: Supplier's Products & Purchase History
        nb = ttk.Notebook(right_pane)
        nb.pack(fill="both", expand=True, pady=(5, 0))

        # Tab 1: Products
        tab_prod = tk.Frame(nb, bg=CREAM)
        nb.add(tab_prod, text="Supplied Products")
        prod_cols = [
            ("product_id", "ID", 40),
            ("product_name", "Product", 150),
            ("current_stock", "Stock", 50),
            ("purchase_price", "Cost", 60),
        ]
        self.tbl_prods = TableView(tab_prod, columns=prod_cols)
        self.tbl_prods.pack(fill="both", expand=True)

        # Tab 2: Purchase History
        tab_hist = tk.Frame(nb, bg=CREAM)
        nb.add(tab_hist, text="Purchase History")
        hist_cols = [
            ("purchase_id", "PO #", 50),
            ("purchase_date", "Date", 90),
            ("total_amount", "Total", 80),
            ("items_count", "Items", 60),
        ]
        self.tbl_hist = TableView(tab_hist, columns=hist_cols)
        self.tbl_hist.pack(fill="both", expand=True)

    def load_suppliers(self, search_query: str = ""):
        suppliers = get_all_suppliers()
        if search_query:
            q = search_query.lower()
            suppliers = [s for s in suppliers if q in s['supplier_name'].lower() or q in (s['phone'] or '').lower() or q in (s['email'] or '').lower()]

        rows = [
            (
                s['supplier_id'],
                s['supplier_name'],
                s['phone'] or '',
                s['email'] or '',
                s['lead_time'],
                s['total_products']
            )
            for s in suppliers
        ]
        self.table.populate(rows)

    def filter_suppliers(self, query: str):
        self.load_suppliers(query)

    def on_supplier_select(self, event=None):
        sel = self.table.get_selected()
        if not sel:
            return
        s_id = int(sel[0])
        self.selected_supplier_id = s_id

        # Populate form
        suppliers = get_all_suppliers()
        s_data = next((s for s in suppliers if s['supplier_id'] == s_id), None)
        if not s_data:
            return

        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, s_data['supplier_name'])

        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, s_data['phone'] or '')

        self.ent_email.delete(0, tk.END)
        self.ent_email.insert(0, s_data['email'] or '')

        self.ent_lead.delete(0, tk.END)
        self.ent_lead.insert(0, str(s_data['lead_time']))

        self.txt_address.delete("1.0", tk.END)
        self.txt_address.insert("1.0", s_data['address'] or '')

        # Load supplier products
        prods = get_supplier_products(s_id)
        p_rows = [(p['product_id'], p['product_name'], p['current_stock'], f"${float(p['purchase_price']):.2f}") for p in prods]
        self.tbl_prods.populate(p_rows)

        # Load supplier purchase history
        purchases = get_supplier_purchase_history(s_id)
        hist_rows = [(p['purchase_id'], str(p['purchase_date']), f"${float(p['total_amount']):.2f}", p['items_count']) for p in purchases]
        self.tbl_hist.populate(hist_rows)

    def save_supplier(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        lead_str = self.ent_lead.get().strip()
        address = self.txt_address.get("1.0", tk.END).strip()

        ok, err = validate_non_empty(name, "Supplier Name")
        if not ok:
            messagebox.showwarning("Validation Error", err)
            return

        ok, err = validate_positive_int(lead_str, "Lead Time", allow_zero=False)
        if not ok:
            messagebox.showwarning("Validation Error", err)
            return
        lead_time = int(lead_str)

        ok, err = validate_email(email)
        if not ok:
            messagebox.showwarning("Validation Error", err)
            return

        ok, err = validate_phone(phone)
        if not ok:
            messagebox.showwarning("Validation Error", err)
            return

        try:
            if self.selected_supplier_id:
                update_supplier(self.selected_supplier_id, name, phone, email, address, lead_time)
                messagebox.showinfo("Success", f"Supplier '{name}' updated successfully.")
            else:
                add_supplier(name, phone, email, address, lead_time)
                messagebox.showinfo("Success", f"Supplier '{name}' registered successfully.")

            self.clear_form()
            self.load_suppliers()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save supplier:\n{str(e)}")

    def delete_current_supplier(self):
        if not self.selected_supplier_id:
            messagebox.showwarning("Selection Required", "Please select a supplier from the list to delete.")
            return

        sel = self.table.get_selected()
        if sel and int(sel[5]) > 0:
            messagebox.showerror("Cannot Delete", f"This supplier is linked to {sel[5]} active products. Delete or reassign products first.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this supplier?"):
            try:
                delete_supplier(self.selected_supplier_id)
                messagebox.showinfo("Deleted", "Supplier removed successfully.")
                self.clear_form()
                self.load_suppliers()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete supplier:\n{str(e)}")

    def clear_form(self):
        self.selected_supplier_id = None
        self.ent_name.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.ent_email.delete(0, tk.END)
        self.ent_lead.delete(0, tk.END)
        self.txt_address.delete("1.0", tk.END)
        self.tbl_prods.clear()
        self.tbl_hist.clear()
