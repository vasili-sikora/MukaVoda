import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from database.database import DatabaseManager
from database.models import MenuItem
from gui.child_form import BaseForm


class MenuForm(BaseForm):
    CATEGORIES = ["Пицца", "Хот-дог", "Закуски", "Соусы", "Напитки"]

    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.items: list[MenuItem] = []

        self.dialog.title("Просмотр меню")

        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        title_text = "Просмотр меню"
        bg_color = "#e67e22"

        header = tk.Label(
            self.dialog,
            text=title_text,
            font=("Arial", 16, "bold"),
            bg=bg_color,
            fg="white",
            pady=15,
        )
        header.pack(fill=tk.X)

        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "category", "price")

        self.menu_table = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=12,
        )

        self.menu_table.heading("name", text="Название")
        self.menu_table.heading("category", text="Категория")
        self.menu_table.heading("price", text="Цена")

        self.menu_table.column("name", width=250, anchor="w")
        self.menu_table.column("category", width=160, anchor="w")
        self.menu_table.column("price", width=90, anchor="e")

        y_scroll = ttk.Scrollbar(
            main_frame, orient="vertical", command=self.menu_table.yview
        )
        self.menu_table.configure(yscrollcommand=y_scroll.set)

        self.menu_table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Treeview", rowheight=26)

        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        btn_frame.columnconfigure(0, weight=1)

        add_btn = ttk.Button(
            btn_frame, text="Добавить в меню", command=self.add_menu_item
        )
        edit_btn = ttk.Button(
            btn_frame, text="Редактировать", command=self.edit_selected_item
        )
        edit_btn.pack(side=tk.LEFT, padx=(10, 0))
        del_btn = ttk.Button(
            btn_frame, text="Удалить из меню", command=self.delete_selected_item
        )

        add_btn.pack(side=tk.LEFT)
        del_btn.pack(side=tk.LEFT, padx=(10, 0))

    def refresh_table(self):
        for iid in self.menu_table.get_children():
            self.menu_table.delete(iid)

        self.items = self.db.get_menu()

        for item in self.items:
            self.menu_table.insert(
                "", "end", values=(item.name, item.category, f"{item.price:.2f}")
            )

    def add_menu_item(self):
        res = self._open_item_dialog("Добавить позицию")
        if not res["ok"]:
            return

        try:
            self.db.add_to_menu(
                MenuItem(
                    name=res["name"],
                    category=res["category"],
                    price=res["price"],
                )
            )
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить позицию:\n{e}")
            return

        self.refresh_table()
        messagebox.showinfo("Готово", "Позиция добавлена в меню")

    def delete_selected_item(self):
        selected = self.menu_table.selection()
        if not selected:
            messagebox.showwarning("Удаление", "Выберите строку в таблице")
            return

        iid = selected[0]
        values = self.menu_table.item(iid, "values")  # ("name","category","price")
        name = values[0]

        if not messagebox.askyesno("Удаление", f"Удалить '{name}' из меню?"):
            return

        self.db.delete_from_menu(name)
        self.refresh_table()

    def edit_selected_item(self):
        selected = self.menu_table.selection()
        if not selected:
            messagebox.showwarning("Редактирование", "Выберите позицию в таблице")
            return

        iid = selected[0]
        old_name, old_category, old_price = self.menu_table.item(iid, "values")

        res = self._open_item_dialog(
            "Редактировать позицию",
            name=old_name,
            category=old_category,
            price=float(old_price),
        )
        if not res["ok"]:
            return

        try:
            self.db.update_menu_item(
                old_name=old_name,
                menu_item=MenuItem(
                    name=res["name"],
                    category=res["category"],
                    price=res["price"],
                ),
            )
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")
            return

        self.refresh_table()

    def _open_item_dialog(
        self,
        title: str,
        name: str = "",
        category: str = "Пицца",
        price: float | None = None,
    ):
        dlg = tk.Toplevel(self.dialog)
        dlg.title(title)
        dlg.transient(self.dialog)
        dlg.grab_set()

        frm = tk.Frame(dlg, padx=12, pady=12)
        frm.pack(fill=tk.BOTH, expand=True)

        tk.Label(frm, text="Название:").grid(row=0, column=0, sticky="w")
        name_var = tk.StringVar(value=name)
        name_entry = tk.Entry(frm, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, sticky="ew", pady=4)

        tk.Label(frm, text="Категория:").grid(row=1, column=0, sticky="w")
        cat_var = tk.StringVar(
            value=category if category in self.CATEGORIES else self.CATEGORIES[0]
        )
        cat_combo = ttk.Combobox(
            frm, textvariable=cat_var, values=self.CATEGORIES, state="readonly"
        )
        cat_combo.grid(row=1, column=1, sticky="ew", pady=4)

        tk.Label(frm, text="Цена:").grid(row=2, column=0, sticky="w")
        price_var = tk.StringVar(value="" if price is None else f"{price:.2f}")
        price_entry = tk.Entry(frm, textvariable=price_var, width=12)
        price_entry.grid(row=2, column=1, sticky="w", pady=4)

        frm.columnconfigure(1, weight=1)

        result = {"ok": False, "name": None, "category": None, "price": None}

        def on_ok():
            n = name_var.get().strip()
            if not n:
                messagebox.showerror(
                    "Ошибка", "Название не должно быть пустым", parent=dlg
                )
                return

            try:
                p = float(price_var.get().replace(",", "."))
                if p <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Ошибка", "Цена должна быть числом > 0", parent=dlg
                )
                return

            result["ok"] = True
            result["name"] = n
            result["category"] = cat_var.get()
            result["price"] = p
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btns = tk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="Отмена", command=on_cancel).pack(side=tk.RIGHT)
        ttk.Button(btns, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(0, 8))

        name_entry.focus_set()

        dlg.update_idletasks()
        parent = self.dialog
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        dw, dh = dlg.winfo_width(), dlg.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        dlg.geometry(f"+{x}+{y}")

        dlg.wait_window()
        return result
