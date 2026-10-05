"""
gui/login.py
Desktop login screen with username, password, authentication via MySQL and bcrypt.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from database.queries import get_user_by_username
from utils.security import verify_password, CurrentUser
from gui.theme import DARK_TEAL, TEAL, AQUA, CREAM, FONT_TITLE, FONT_SUBHEADER, FONT_BODY, FONT_BODY_BOLD

class LoginWindow:
    def __init__(self, root: tk.Tk, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("StockWise - Login")
        self.root.geometry("450x520")
        self.root.minsize(400, 480)
        self.root.configure(bg=CREAM)

        # Center on screen
        self.center_window()
        self.build_ui()

    def center_window(self):
        self.root.update_idletasks()
        w = 450
        h = 520
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def build_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg=DARK_TEAL, height=110)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title = tk.Label(header, text="StockWise", font=(FONT_TITLE[0], 22, "bold"), bg=DARK_TEAL, fg=AQUA)
        title.pack(pady=(22, 2))
        subtitle = tk.Label(header, text="Desktop Inventory & Stock Forecasting System", font=FONT_BODY, bg=DARK_TEAL, fg=CREAM)
        subtitle.pack()

        # Login card container
        card = tk.Frame(self.root, bg=CREAM, padx=30, pady=25)
        card.pack(fill="both", expand=True)

        card_title = tk.Label(card, text="Account Sign In", font=FONT_SUBHEADER, bg=CREAM, fg=DARK_TEAL)
        card_title.pack(anchor="w", pady=(0, 20))

        # Username Field
        lbl_user = tk.Label(card, text="Username", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL)
        lbl_user.pack(anchor="w", pady=(0, 4))
        self.ent_user = ttk.Entry(card, width=32, font=FONT_BODY)
        self.ent_user.pack(fill="x", pady=(0, 15), ipady=4)
        self.ent_user.focus_set()

        # Password Field
        lbl_pass = tk.Label(card, text="Password", font=FONT_BODY_BOLD, bg=CREAM, fg=DARK_TEAL)
        lbl_pass.pack(anchor="w", pady=(0, 4))
        self.ent_pass = ttk.Entry(card, width=32, show="•", font=FONT_BODY)
        self.ent_pass.pack(fill="x", pady=(0, 20), ipady=4)
        self.ent_pass.bind("<Return>", lambda e: self.handle_login())

        # Buttons frame
        btn_frame = tk.Frame(card, bg=CREAM)
        btn_frame.pack(fill="x", pady=(10, 0))

        self.btn_login = ttk.Button(btn_frame, text="Login", style="Teal.TButton", command=self.handle_login)
        self.btn_login.pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=4)

        self.btn_clear = ttk.Button(btn_frame, text="Clear", style="Aqua.TButton", command=self.clear_fields)
        self.btn_clear.pack(side="right", expand=True, fill="x", padx=(6, 0), ipady=4)

        # Default Demo Credentials hint
        hint_box = tk.Frame(card, bg=CREAM, highlightbackground=TEAL, highlightthickness=1, padx=10, pady=8)
        hint_box.pack(fill="x", side="bottom", pady=(20, 0))
        lbl_hint_title = tk.Label(hint_box, text="Default Demo Accounts:", font=FONT_BODY_BOLD, bg=CREAM, fg=TEAL)
        lbl_hint_title.pack(anchor="w")
        lbl_hint_1 = tk.Label(hint_box, text="• Admin: admin / admin123", font=FONT_BODY, bg=CREAM, fg=DARK_TEAL)
        lbl_hint_1.pack(anchor="w")
        lbl_hint_2 = tk.Label(hint_box, text="• Staff: staff / staff123", font=FONT_BODY, bg=CREAM, fg=DARK_TEAL)
        lbl_hint_2.pack(anchor="w")

    def handle_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation Error", "Please provide both username and password.")
            return

        try:
            user = get_user_by_username(username)
            if not user:
                messagebox.showerror("Login Failed", "Invalid username or password.")
                return

            if verify_password(password, user['password_hash']):
                CurrentUser.set_user(user['user_id'], user['username'], user['name'], user['role'])
                self.on_login_success()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Unable to authenticate against MySQL:\n{str(e)}")

    def clear_fields(self):
        self.ent_user.delete(0, tk.END)
        self.ent_pass.delete(0, tk.END)
        self.ent_user.focus_set()
