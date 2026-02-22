import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk
from typing import List, Optional

from database.database import DatabaseManager
from database.models import MenuItem, Order, OrderItem
from gui.child_form import ChildForm


class MenuForm(ChildForm):
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

        # Заголовки
        self.menu_table.heading("name", text="Название")
        self.menu_table.heading("category", text="Категория")
        self.menu_table.heading("price", text="Цена")

        # Ширины и выравнивание
        self.menu_table.column("name", width=250, anchor="w")
        self.menu_table.column("category", width=160, anchor="w")
        self.menu_table.column("price", width=90, anchor="e")

        # Скроллбар
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
        name = simpledialog.askstring("Добавить", "Название:", parent=self.dialog)
        if not name:
            return

        category = simpledialog.askstring("Добавить", "Категория:", parent=self.dialog)
        if not category:
            return

        price = simpledialog.askfloat(
            "Добавить", "Цена:", parent=self.dialog, minvalue=0.01
        )
        if price is None:
            return

        try:
            self.db.add_to_menu(
                MenuItem(
                    name=name.strip(), category=category.strip(), price=float(price)
                )
            )
        except sqlite3.IntegrityError as e:
            # например, если нарушили UNIQUE (дубликат)
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

        # Ввод новых значений (с предзаполнением)
        new_name = simpledialog.askstring(
            "Редактирование", "Название:", initialvalue=old_name, parent=self.dialog
        )
        if new_name is None or not new_name.strip():
            return

        new_category = simpledialog.askstring(
            "Редактирование",
            "Категория:",
            initialvalue=old_category,
            parent=self.dialog,
        )
        if new_category is None or not new_category.strip():
            return

        new_price = simpledialog.askfloat(
            "Редактирование",
            "Цена:",
            initialvalue=float(old_price),
            minvalue=0.01,
            parent=self.dialog,
        )
        if new_price is None:
            return

        try:
            self.db.update_menu_item(
                old_name=old_name,
                menu_item=MenuItem(
                    name=new_name.strip(),
                    category=new_category.strip(),
                    price=float(new_price),
                ),
            )
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")
            return

        self.refresh_table()
