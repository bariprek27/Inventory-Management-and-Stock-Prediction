"""
gui/products.py
Product Management:
- Complete CRUD operations: Add, Edit, Delete, View, Search, Filter
- Fields: Product ID, Name, Category, Supplier, Purchase Price, Selling Price,
  Current Stock, Reorder Level, Safety Stock, Lead Time
- Strict input validation
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView, SearchBar
from database.queries import (
    get_all_products,
    get_all_categories,
    get_all_suppliers,
    add_product,
    update_product,
    delete_product
)
from utils.validators import validate_non_empty, validate_positive_number, validate_positive_int

class ProductsView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.selected_product_id: Optional[int] = None
        self.categories_cache = []
        self.suppliers_cache = []

        self.build_ui()
        self.load_metadata()
        self.load_products()

    def build_ui(self):
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Product Catalog Management", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        content = tk.Frame(self, bg=CREAM)
        content.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ── LEFT PANE: Filter bar & Product Table ──
        left_pane = tk.Frame(content, bg=CREAM)
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Filter bar
        filter_box = tk.Frame(left_pane, bg=CREAM)
        filter_box.pack(fill="x", pady=(0, 10))

        tk.Label(filter_box, text="Category:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_filter_cat = ttk.Combobox(filter_box, state="readonly", width=14)
        self.cb_filter_cat.pack(side="left", padx=(0, 10))
        self.cb_filter_cat.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        tk.Label(filter_box, text="Supplier:", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(side="left", padx=(0, 4))
        self.cb_filter_supp = ttk.Combobox(filter_box, state="readonly", width=16)
        self.cb_filter_supp.pack(side="left", padx=(0, 10))
        self.cb_filter_supp.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        search_bar = SearchBar(filter_box, on_search=self.filter_by_search, placeholder="Search by name or ID...")
        search_bar.pack(side="right")

        columns = [
            ("product_id", "ID", 45),
            ("product_name", "Product Name", 170),
            ("category_name", "Category", 110),
            ("supplier_name", "Supplier", 130),
            ("purchase_price", "Cost ($)", 75),
            ("selling_price", "Sell ($)", 75),
            ("current_stock", "Stock", 65),
            ("reorder_level", "Reorder", 65),
            ("safety_stock", "Safety", 60),
        ]
        self.table = TableView(left_pane, columns=columns, on_select=self.on_product_select)
        self.table.pack(fill="both", expand=True)

        # ── RIGHT PANE: Add / Edit Product Form ──
        right_pane = tk.Frame(content, bg=CREAM, width=380)
        right_pane.pack(side="right", fill="both", padx=(5, 0))
        right_pane.pack_propagate(False)

        form_frame = tk.LabelFrame(right_pane, text=" Product Form ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=12)
        form_frame.pack(fill="both", expand=True)

        # Form fields
        fields = [
            ("Product Name *", "ent_name"),
            ("Category *", "cb_cat"),
            ("Supplier *", "cb_supp"),
            ("Purchase Price ($) *", "ent_buy_price"),
            ("Selling Price ($) *", "ent_sell_price"),
            ("Current Stock *", "ent_stock"),
            ("Reorder Level *", "ent_reorder"),
            ("Safety Stock *", "ent_safety")
        ]

        for i, (label_txt, widget_name) in enumerate(fields):
            tk.Label(form_frame, text=label_txt, font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).grid(row=i, column=0, sticky="w", pady=4)
            if widget_name == "cb_cat":
                w = ttk.Combobox(form_frame, state="readonly")
            elif widget_name == "cb_supp":
                w = ttk.Combobox(form_frame, state="readonly")
            else:
                w = ttk.Entry(form_frame)
            w.grid(row=i, column=1, sticky="ew", pady=4)
            setattr(self, widget_name, w)

        form_frame.grid_columnconfigure(1, weight=1)

        # Buttons
        btn_box = tk.Frame(form_frame, bg=CREAM)
        btn_box.grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(15, 0))

        self.btn_save = ttk.Button(btn_box, text="Save / Update", style="Teal.TButton", command=self.save_product)
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_delete = ttk.Button(btn_box, text="Delete", style="Teal.TButton", command=self.delete_current_product)
        self.btn_delete.pack(side="left", expand=True, fill="x", padx=4)

        self.btn_clear = ttk.Button(btn_box, text="Clear", style="Aqua.TButton", command=self.clear_form)
        self.btn_clear.pack(side="left", expand=True, fill="x", padx=(4, 0))

    def load_metadata(self):
        self.categories_cache = get_all_categories()
        cat_names = ["All"] + [c['category_name'] for c in self.categories_cache]
        self.cb_filter_cat['values'] = cat_names
        self.cb_filter_cat.set("All")
        self.cb_cat['values'] = [c['category_name'] for c in self.categories_cache]

        self.suppliers_cache = get_all_suppliers()
        supp_names = ["All"] + [s['supplier_name'] for s in self.suppliers_cache]
        self.cb_filter_supp['values'] = supp_names
        self.cb_filter_supp.set("All")
        self.cb_supp['values'] = [s['supplier_name'] for s in self.suppliers_cache]

    def load_products(self, category_id: Optional[int] = None, supplier_id: Optional[int] = None, search: Optional[str] = None):
        prods = get_all_products(category_id=category_id, supplier_id=supplier_id, search=search)
        rows = [
            (
                p['product_id'],
                p['product_name'],
                p['category_name'],
                p['supplier_name'],
                f"${float(p['purchase_price']):.2f}",
                f"${float(p['selling_price']):.2f}",
                p['current_stock'],
                p['reorder_level'],
                p['safety_stock']
            )
            for p in prods
        ]
        self.table.populate(rows)

    def apply_filters(self):
        cat_name = self.cb_filter_cat.get()
        supp_name = self.cb_filter_supp.get()

        cat_id = None
        if cat_name != "All":
            cat_obj = next((c for c in self.categories_cache if c['category_name'] == cat_name), None)
            if cat_obj: cat_id = cat_obj['category_id']

        supp_id = None
        if supp_name != "All":
            supp_obj = next((s for s in self.suppliers_cache if s['supplier_name'] == supp_name), None)
            if supp_obj: supp_id = supp_obj['supplier_id']

        self.load_products(category_id=cat_id, supplier_id=supp_id)

    def filter_by_search(self, term: str):
        self.load_products(search=term)

    def on_product_select(self, event=None):
        sel = self.table.get_selected()
        if not sel:
            return
        p_id = int(sel[0])
        self.selected_product_id = p_id

        # Populate form
        prods = get_all_products()
        p = next((x for x in prods if x['product_id'] == p_id), None)
        if not p:
            return

        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, p['product_name'])

        self.cb_cat.set(p['category_name'])
        self.cb_supp.set(p['supplier_name'])

        self.ent_buy_price.delete(0, tk.END)
        self.ent_buy_price.insert(0, str(p['purchase_price']))

        self.ent_sell_price.delete(0, tk.END)
        self.ent_sell_price.insert(0, str(p['selling_price']))

        self.ent_stock.delete(0, tk.END)
        self.ent_stock.insert(0, str(p['current_stock']))

        self.ent_reorder.delete(0, tk.END)
        self.ent_reorder.insert(0, str(p['reorder_level']))

        self.ent_safety.delete(0, tk.END)
        self.ent_safety.insert(0, str(p['safety_stock']))

    def save_product(self):
        name = self.ent_name.get().strip()
        cat_name = self.cb_cat.get()
        supp_name = self.cb_supp.get()
        buy_str = self.ent_buy_price.get().strip()
        sell_str = self.ent_sell_price.get().strip()
        stock_str = self.ent_stock.get().strip()
        reorder_str = self.ent_reorder.get().strip()
        safety_str = self.ent_safety.get().strip()

        ok, err = validate_non_empty(name, "Product Name")
        if not ok: return messagebox.showwarning("Validation Error", err)

        cat_obj = next((c for c in self.categories_cache if c['category_name'] == cat_name), None)
        if not cat_obj: return messagebox.showwarning("Validation Error", "Please select a valid Category.")

        supp_obj = next((s for s in self.suppliers_cache if s['supplier_name'] == supp_name), None)
        if not supp_obj: return messagebox.showwarning("Validation Error", "Please select a valid Supplier.")

        for val, fld in [(buy_str, "Purchase Price"), (sell_str, "Selling Price")]:
            ok, err = validate_positive_number(val, fld)
            if not ok: return messagebox.showwarning("Validation Error", err)

        for val, fld in [(stock_str, "Current Stock"), (reorder_str, "Reorder Level"), (safety_str, "Safety Stock")]:
            ok, err = validate_positive_int(val, fld)
            if not ok: return messagebox.showwarning("Validation Error", err)

        buy_price = float(buy_str)
        sell_price = float(sell_str)
        stock = int(stock_str)
        reorder = int(reorder_str)
        safety = int(safety_str)

        try:
            if self.selected_product_id:
                update_product(self.selected_product_id, name, cat_obj['category_id'], supp_obj['supplier_id'],
                               buy_price, sell_price, stock, reorder, safety)
                messagebox.showinfo("Success", f"Product '{name}' updated successfully.")
            else:
                add_product(name, cat_obj['category_id'], supp_obj['supplier_id'],
                            buy_price, sell_price, stock, reorder, safety)
                messagebox.showinfo("Success", f"Product '{name}' added successfully.")

            self.clear_form()
            self.load_products()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save product:\n{str(e)}")

    def delete_current_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("Selection Required", "Please select a product from the list to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            try:
                delete_product(self.selected_product_id)
                messagebox.showinfo("Deleted", "Product deleted successfully.")
                self.clear_form()
                self.load_products()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete product (check if it has sales or purchase history):\n{str(e)}")

    def clear_form(self):
        self.selected_product_id = None
        self.ent_name.delete(0, tk.END)
        self.cb_cat.set("")
        self.cb_supp.set("")
        self.ent_buy_price.delete(0, tk.END)
        self.ent_sell_price.delete(0, tk.END)
        self.ent_stock.delete(0, tk.END)
        self.ent_reorder.delete(0, tk.END)
        self.ent_safety.delete(0, tk.END)
