import tkinter as tk
from tkinter import messagebox

from services.errors import AppError


class BaseForm:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)

        self.dialog.geometry("950x800")
        self.dialog.resizable(False, False)

        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.center_window()

    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def run(self, func):
        try:
            return func()
        except AppError as e:
            messagebox.showerror("Ошибка", str(e), parent=self.dialog)
            return None
