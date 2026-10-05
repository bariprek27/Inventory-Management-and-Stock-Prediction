"""
gui/theme.py
Design System & Tokens:
- Dark Teal: #001E23
- Teal:      #007887
- Aqua:      #78E6DC
- Cream:     #FAF6EE
Strict adherence to project colors and modern typography.
"""
import tkinter as tk
from tkinter import ttk

# Strict Project Color Palette
DARK_TEAL = "#001E23"
TEAL      = "#007887"
AQUA      = "#78E6DC"
CREAM     = "#FAF6EE"

# Typography
FONT_FAMILY = "Segoe UI"
FONT_TITLE  = (FONT_FAMILY, 18, "bold")
FONT_HEADER = (FONT_FAMILY, 14, "bold")
FONT_SUBHEADER = (FONT_FAMILY, 12, "bold")
FONT_BODY   = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL  = (FONT_FAMILY, 9)
FONT_STAT_NUM = (FONT_FAMILY, 20, "bold")

def setup_ttk_styles(root: tk.Tk):
    """Configure modern ttk styles based strictly on the 4 color tokens."""
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Root background
    root.configure(bg=CREAM)

    # General Frames
    style.configure("Cream.TFrame", background=CREAM)
    style.configure("DarkTeal.TFrame", background=DARK_TEAL)
    style.configure("Card.TFrame", background=CREAM, relief="solid", borderwidth=1)

    # General Labels
    style.configure("Cream.TLabel", background=CREAM, foreground=DARK_TEAL, font=FONT_BODY)
    style.configure("CreamTitle.TLabel", background=CREAM, foreground=DARK_TEAL, font=FONT_TITLE)
    style.configure("CreamHeader.TLabel", background=CREAM, foreground=DARK_TEAL, font=FONT_HEADER)
    style.configure("DarkTeal.TLabel", background=DARK_TEAL, foreground=CREAM, font=FONT_BODY)
    style.configure("DarkTealTitle.TLabel", background=DARK_TEAL, foreground=AQUA, font=FONT_TITLE)
    
    # Stat Card Labels
    style.configure("CardTitle.TLabel", background=CREAM, foreground=TEAL, font=FONT_SUBHEADER)
    style.configure("CardValue.TLabel", background=CREAM, foreground=DARK_TEAL, font=FONT_STAT_NUM)
    style.configure("CardSub.TLabel", background=CREAM, foreground=TEAL, font=FONT_SMALL)

    # Primary Action Buttons (Teal)
    style.configure(
        "Teal.TButton",
        background=TEAL,
        foreground=CREAM,
        font=FONT_BODY_BOLD,
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Teal.TButton",
        background=[('active', DARK_TEAL), ('pressed', DARK_TEAL)],
        foreground=[('active', AQUA)]
    )

    # Accent Highlight Buttons (Aqua)
    style.configure(
        "Aqua.TButton",
        background=AQUA,
        foreground=DARK_TEAL,
        font=FONT_BODY_BOLD,
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Aqua.TButton",
        background=[('active', TEAL), ('pressed', TEAL)],
        foreground=[('active', CREAM)]
    )

    # Sidebar Nav Buttons (Dark Teal base, Teal hover)
    style.configure(
        "Nav.TButton",
        background=DARK_TEAL,
        foreground=CREAM,
        font=(FONT_FAMILY, 11, "bold"),
        anchor="w",
        padding=(16, 10),
        borderwidth=0
    )
    style.map(
        "Nav.TButton",
        background=[('active', TEAL), ('pressed', TEAL)],
        foreground=[('active', AQUA)]
    )

    style.configure(
        "NavActive.TButton",
        background=TEAL,
        foreground=AQUA,
        font=(FONT_FAMILY, 11, "bold"),
        anchor="w",
        padding=(16, 10),
        borderwidth=0
    )

    # Treeview Styles
    style.configure(
        "Treeview",
        background=CREAM,
        foreground=DARK_TEAL,
        fieldbackground=CREAM,
        font=FONT_BODY,
        rowheight=26,
        borderwidth=1,
        relief="solid"
    )
    style.map(
        "Treeview",
        background=[('selected', TEAL)],
        foreground=[('selected', CREAM)]
    )
    style.configure(
        "Treeview.Heading",
        background=TEAL,
        foreground=CREAM,
        font=FONT_BODY_BOLD,
        padding=(8, 6),
        relief="flat"
    )
    style.map(
        "Treeview.Heading",
        background=[('active', DARK_TEAL)]
    )

    # Entry and Combobox
    style.configure(
        "TEntry",
        fieldbackground=CREAM,
        foreground=DARK_TEAL,
        insertcolor=DARK_TEAL,
        padding=5
    )
    style.configure(
        "TCombobox",
        fieldbackground=CREAM,
        background=TEAL,
        foreground=DARK_TEAL,
        padding=4
    )
    style.map(
        "TCombobox",
        fieldbackground=[('readonly', CREAM)],
        selectbackground=[('readonly', TEAL)],
        selectforeground=[('readonly', CREAM)]
    )

    # Scrollbars
    style.configure("Vertical.TScrollbar", background=TEAL, troughcolor=CREAM, arrowcolor=DARK_TEAL)
    style.configure("Horizontal.TScrollbar", background=TEAL, troughcolor=CREAM, arrowcolor=DARK_TEAL)
