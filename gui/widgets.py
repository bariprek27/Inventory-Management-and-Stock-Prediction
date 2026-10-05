"""
gui/widgets.py
Reusable GUI widgets:
- StatCard: Metrics card with title, value, subtitle
- ActionButton: Consistent styled buttons
- TableView: Configured ttk.Treeview with scrollbars and sort support
- SearchBar: Input bar with search and reset triggers
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Tuple, Optional
from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_SUBHEADER, FONT_STAT_NUM, FONT_SMALL

class StatCard(tk.Frame):
    """Modern Metric Display Card conforming to the 4-color palette."""
    def __init__(self, parent, title: str, initial_value: str = "0", subtitle: str = "", width: int = 180, height: int = 100):
        super().__init__(parent, bg=CREAM, highlightbackground=TEAL, highlightthickness=1.5, bd=0, padx=14, pady=10)
        self.pack_propagate(False)
        self.configure(width=width, height=height)

        self.title_lbl = tk.Label(self, text=title, font=FONT_SUBHEADER, bg=CREAM, fg=TEAL, anchor="w")
        self.title_lbl.pack(fill="x", side="top")

        self.val_var = tk.StringVar(value=initial_value)
        self.val_lbl = tk.Label(self, textvariable=self.val_var, font=FONT_STAT_NUM, bg=CREAM, fg=DARK_TEAL, anchor="w")
        self.val_lbl.pack(fill="x", expand=True)

        if subtitle:
            self.sub_lbl = tk.Label(self, text=subtitle, font=FONT_SMALL, bg=CREAM, fg=DARK_TEAL, anchor="w")
            self.sub_lbl.pack(fill="x", side="bottom")

    def update_value(self, val: str):
        self.val_var.set(val)


class TableView(tk.Frame):
    """Standardized Treeview with vertical & horizontal scrollbars and auto-formatting."""
    def __init__(self, parent, columns: List[Tuple[str, str, int]], on_select: Optional[Callable] = None):
        super().__init__(parent, bg=CREAM)
        self.col_keys = [c[0] for c in columns]
        
        self.tree = ttk.Treeview(self, columns=self.col_keys, show="headings", selectmode="browse")
        
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        for col_id, col_text, col_width in columns:
            self.tree.heading(col_id, text=col_text, anchor="center", 
                              command=lambda c=col_id: self.sort_column(c, False))
            self.tree.column(col_id, width=col_width, minwidth=col_width//2, anchor="center")

        if on_select:
            self.tree.bind("<<TreeviewSelect>>", on_select)

    def populate(self, rows: List[tuple], tags_map: Optional[dict] = None):
        """Clear and refill table."""
        self.clear()
        for row in rows:
            tag = ""
            if tags_map:
                # check custom tagging for status
                status_val = str(row[-1] if len(row) > 0 else "")
                tag = tags_map.get(status_val, "")
            self.tree.insert("", "end", values=row, tags=(tag,) if tag else ())

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_selected(self) -> Optional[tuple]:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0], "values")

    def sort_column(self, col: str, reverse: bool):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            # Numeric sorting attempt
            l.sort(key=lambda t: float(t[0].replace('$', '').replace(',', '')), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))


class SearchBar(tk.Frame):
    """Reusable search bar with Entry and Search/Reset Buttons."""
    def __init__(self, parent, on_search: Callable[[str], None], placeholder: str = "Search..."):
        super().__init__(parent, bg=CREAM)
        self.on_search = on_search

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=28)
        self.entry.pack(side="left", padx=(0, 6), ipady=3)
        self.entry.bind("<Return>", lambda e: self.do_search())

        self.btn_search = ttk.Button(self, text="Search", style="Teal.TButton", command=self.do_search)
        self.btn_search.pack(side="left", padx=2)

        self.btn_reset = ttk.Button(self, text="Reset", style="Teal.TButton", command=self.do_reset)
        self.btn_reset.pack(side="left", padx=2)

    def do_search(self):
        self.on_search(self.var.get().strip())

    def do_reset(self):
        self.var.set("")
        self.on_search("")
