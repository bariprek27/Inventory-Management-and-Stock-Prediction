"""
gui/categories.py
Category Management:
- Add, Edit, Delete categories
- Search & View associated products
- Form validation and SQL foreign key safety
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD
from gui.widgets import TableView, SearchBar
from database.queries import (
    get_all_categories,
    add_category,
    update_category,
    delete_category,
    execute_read
)
from utils.validators import validate_non_empty

class CategoriesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CREAM)
        self.selected_category_id: Optional[int] = None
        
        self.build_ui()
        self.load_categories()

    def build_ui(self):
        # Header
        top_bar = tk.Frame(self, bg=CREAM)
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        title_lbl = tk.Label(top_bar, text="Category Management", font=FONT_TITLE, bg=CREAM, fg=DARK_TEAL)
        title_lbl.pack(side="left")

        # Main splitter: Left side table, Right side form & category products
        content = tk.Frame(self, bg=CREAM)
        content.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # ── LEFT PANE: List & Search ──
        left_pane = tk.Frame(content, bg=CREAM)
        left_pane.pack(side="left", fill="both", expand=True, padx=(0, 15))

        search_bar = SearchBar(left_pane, on_search=self.filter_categories, placeholder="Search categories...")
        search_bar.pack(fill="x", pady=(0, 10))

        columns = [
            ("category_id", "ID", 60),
            ("category_name", "Category Name", 180),
            ("description", "Description", 240),
            ("product_count", "Total Products", 100),
        ]
        self.table = TableView(left_pane, columns=columns, on_select=self.on_category_select)
        self.table.pack(fill="both", expand=True)

        # ── RIGHT PANE: Form & Products In Category ──
        right_pane = tk.Frame(content, bg=CREAM, width=380)
        right_pane.pack(side="right", fill="both", padx=(10, 0))
        right_pane.pack_propagate(False)

        form_frame = tk.LabelFrame(right_pane, text=" Category Details ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=15, pady=12)
        form_frame.pack(fill="x", pady=(0, 15))

        # Name
        tk.Label(form_frame, text="Category Name *", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(anchor="w")
        self.ent_name = ttk.Entry(form_frame)
        self.ent_name.pack(fill="x", pady=(2, 10), ipady=3)

        # Description
        tk.Label(form_frame, text="Description", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL).pack(anchor="w")
        self.txt_desc = tk.Text(form_frame, height=4, font=FONT_BODY, bg=CREAM, fg=DARK_TEAL, highlightbackground=TEAL, highlightthickness=1)
        self.txt_desc.pack(fill="x", pady=(2, 12))

        # Buttons
        btn_box = tk.Frame(form_frame, bg=CREAM)
        btn_box.pack(fill="x")

        self.btn_save = ttk.Button(btn_box, text="Save / Update", style="Teal.TButton", command=self.save_category)
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_delete = ttk.Button(btn_box, text="Delete", style="Teal.TButton", command=self.delete_current_category)
        self.btn_delete.pack(side="left", expand=True, fill="x", padx=4)

        self.btn_clear = ttk.Button(btn_box, text="Clear", style="Aqua.TButton", command=self.clear_form)
        self.btn_clear.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Associated Products sub-table
        sub_frame = tk.LabelFrame(right_pane, text=" Products in Selected Category ", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL, padx=10, pady=8)
        sub_frame.pack(fill="both", expand=True)

        prod_cols = [
            ("product_id", "ID", 50),
            ("product_name", "Product Name", 160),
            ("current_stock", "Stock", 60),
            ("selling_price", "Price", 70)
        ]
        self.prod_table = TableView(sub_frame, columns=prod_cols)
        self.prod_table.pack(fill="both", expand=True)

    def load_categories(self, search_query: str = ""):
        cats = get_all_categories()
        if search_query:
            q = search_query.lower()
            cats = [c for c in cats if q in c['category_name'].lower() or q in (c['description'] or '').lower()]
            
        rows = [
            (
                c['category_id'],
                c['category_name'],
                c['description'] or '',
                c['product_count']
            )
            for c in cats
        ]
        self.table.populate(rows)

    def filter_categories(self, query: str):
        self.load_categories(query)

    def on_category_select(self, event=None):
        sel = self.table.get_selected()
        if not sel:
            return
        cat_id = int(sel[0])
        self.selected_category_id = cat_id

        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, sel[1])
        
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", sel[2])

        # Load associated products
        prods = execute_read(
            "SELECT product_id, product_name, current_stock, selling_price FROM products WHERE category_id = %s",
            (cat_id,)
        )
        prod_rows = [(p['product_id'], p['product_name'], p['current_stock'], f"${float(p['selling_price']):.2f}") for p in prods]
        self.prod_table.populate(prod_rows)

    def save_category(self):
        name = self.ent_name.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()

        ok, err = validate_non_empty(name, "Category Name")
        if not ok:
            messagebox.showwarning("Validation Error", err)
            return

        try:
            if self.selected_category_id:
                update_category(self.selected_category_id, name, desc)
                messagebox.showinfo("Success", f"Category '{name}' updated successfully.")
            else:
                add_category(name, desc)
                messagebox.showinfo("Success", f"Category '{name}' created successfully.")

            self.clear_form()
            self.load_categories()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save category:\n{str(e)}")

    def delete_current_category(self):
        if not self.selected_category_id:
            messagebox.showwarning("Selection Required", "Please select a category from the table to delete.")
            return

        # Check if category contains products
        sel = self.table.get_selected()
        if sel and int(sel[3]) > 0:
            messagebox.showerror("Cannot Delete", f"This category has {sel[3]} assigned products. Reassign or delete those products first.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this category?"):
            try:
                delete_category(self.selected_category_id)
                messagebox.showinfo("Deleted", "Category deleted successfully.")
                self.clear_form()
                self.load_categories()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete category:\n{str(e)}")

    def clear_form(self):
        self.selected_category_id = None
        self.ent_name.delete(0, tk.END)
        self.txt_desc.delete("1.0", tk.END)
        self.prod_table.clear()
