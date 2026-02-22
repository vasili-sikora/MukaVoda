import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from typing import List, Optional

from database.database import DatabaseManager
from database.models import Order, OrderItem
from gui.child_form import ChildForm


class OrderForm(ChildForm):
    def __init__(self, parent, order: Optional[Order] = None):
        super().__init__(parent)

        self.db = DatabaseManager()
        self.result: Optional[Order] = None
        self.items: List[OrderItem] = []
        self.editing_order = order

        if order:
            self.dialog.title(f"Изменить заказ {order.order_number}")
        else:
            self.dialog.title("Создать новый заказ")

        self.create_widgets()

        if order:
            self.load_order_data(order)

    def create_widgets(self):
        title_text = (
            "Изменение заказа" if self.editing_order else "Создание нового заказа"
        )
        bg_color = "#e67e22" if self.editing_order else "#3498db"

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

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(left_frame, text="Меню ресторана", font=("Arial", 12, "bold")).pack(
            anchor=tk.W, pady=(0, 5)
        )

        menu_frame = tk.Frame(left_frame)
        menu_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(menu_frame, text="Выберите блюдо:", font=("Arial", 10)).pack(
            anchor=tk.W
        )

        columns = ("price",)
        self.menu_tree = ttk.Treeview(
            menu_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse",
            height=12,
        )
        self.menu_tree.heading("#0", text="Название")
        self.menu_tree.heading("price", text="Цена")
        self.menu_tree.column("#0", width=260, anchor="w")
        self.menu_tree.column("price", width=90, anchor="e")

        tree_scroll = ttk.Scrollbar(
            menu_frame, orient="vertical", command=self.menu_tree.yview
        )
        self.menu_tree.configure(yscrollcommand=tree_scroll.set)

        self.menu_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.selected_menu = None
        self.menu_tree.bind("<<TreeviewSelect>>", self.on_menu_select)
        self.menu_tree.bind("<Double-1>", lambda e: self.add_item())

        self.load_menu_tree()

        # Количество
        qty_frame = tk.Frame(left_frame)
        qty_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(qty_frame, text="Количество:", font=("Arial", 10)).pack(anchor=tk.W)

        self.qty_spinbox = tk.Spinbox(
            qty_frame, from_=1, to=99, font=("Arial", 10), width=10
        )
        self.qty_spinbox.pack(anchor=tk.W, pady=(5, 0))

        self.btn_add_item = tk.Button(
            left_frame,
            text="Добавить в заказ",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            pady=10,
            command=self.add_item,
        )
        self.btn_add_item.pack(fill=tk.X, pady=(15, 0))

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        tk.Label(right_frame, text="Позиции заказа", font=("Arial", 12, "bold")).pack(
            anchor=tk.W, pady=(0, 5)
        )

        list_frame = tk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.items_listbox = tk.Listbox(
            list_frame, font=("Courier", 10), yscrollcommand=scrollbar.set
        )
        self.items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.items_listbox.yview)

        self.btn_remove_item = tk.Button(
            right_frame,
            text="Удалить позицию",
            font=("Arial", 10),
            bg="#e74c3c",
            fg="white",
            pady=5,
            command=self.remove_item,
            state=tk.DISABLED,
        )
        self.btn_remove_item.pack(fill=tk.X, pady=(10, 0))

        self.total_label = tk.Label(
            right_frame,
            text="ИТОГО: 0.00 BYN",
            font=("Arial", 14, "bold"),
            fg="#2c3e50",
        )
        self.total_label.pack(pady=(15, 0))

        bottom_container = tk.Frame(self.dialog, bg="#ecf0f1")
        bottom_container.pack(fill=tk.X, side=tk.BOTTOM)

        bottom_frame = tk.Frame(bottom_container, bg="#ecf0f1", padx=20, pady=15)
        bottom_frame.grid(row=0, column=0, sticky="ew")

        button_frame = tk.Frame(bottom_container, bg="#ecf0f1")
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        bottom_container.columnconfigure(0, weight=1)

        payment_frame = tk.Frame(bottom_frame, bg="#ecf0f1")
        payment_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            payment_frame,
            text="Способ оплаты:",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
        ).pack(anchor=tk.W)

        self.payment_var = tk.StringVar(value="Наличные")

        payment_options = tk.Frame(payment_frame, bg="#ecf0f1")
        payment_options.pack(anchor=tk.W, pady=(5, 0))

        for method in ["Наличные", "Карта", "Онлайн"]:
            tk.Radiobutton(
                payment_options,
                text=method,
                variable=self.payment_var,
                value=method,
                font=("Arial", 10),
                bg="#ecf0f1",
            ).pack(side=tk.LEFT, padx=(0, 15))

        address_frame = tk.Frame(bottom_frame, bg="#ecf0f1")
        address_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 0))

        tk.Label(
            address_frame,
            text="Адрес доставки (пусто = самовывоз):",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
        ).pack(anchor=tk.W)

        self.address_entry = tk.Entry(address_frame, font=("Arial", 10), width=30)
        self.address_entry.pack(fill=tk.X, pady=(5, 0))

        completion_frame = tk.Frame(bottom_frame, bg="#ecf0f1")
        completion_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 0))

        tk.Label(
            completion_frame,
            text="Время выдачи (пусто = не выдан):",
            font=("Arial", 10, "bold"),
            bg="#ecf0f1",
        ).pack(anchor=tk.W)

        completion_input = tk.Frame(completion_frame, bg="#ecf0f1")
        completion_input.pack(fill=tk.X, pady=(5, 0))

        self.completion_entry = tk.Entry(completion_input, font=("Arial", 10), width=18)
        self.completion_entry.pack(side=tk.LEFT)

        tk.Button(
            completion_input,
            text="Сегодня",
            font=("Arial", 9),
            bg="#3498db",
            fg="white",
            command=self.set_current_day,
        ).pack(side=tk.LEFT, padx=(5, 0))

        tk.Button(
            completion_input,
            text="Завтра",
            font=("Arial", 9),
            bg="#3498db",
            fg="white",
            command=self.set_tomorrow_day,
        ).pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(
            completion_frame,
            text="Формат: ГГГГ-ММ-ДД ЧЧ:ММ",
            font=("Arial", 8),
            bg="#ecf0f1",
            fg="#7f8c8d",
        ).pack(anchor=tk.W)

        tk.Button(
            button_frame,
            text="Отмена",
            font=("Arial", 11),
            bg="#95a5a6",
            fg="white",
            padx=30,
            pady=10,
            command=self.cancel,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        self.btn_save = tk.Button(
            button_frame,
            text="Создать заказ" if not self.editing_order else "Сохранить изменения",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=10,
            command=self.save,
            state=tk.DISABLED,
        )
        self.btn_save.pack(side=tk.RIGHT)

        self.items_listbox.bind("<<ListboxSelect>>", self.on_item_select)

    def set_current_day(self):
        current = datetime.now().strftime("%Y-%m-%d")
        self.completion_entry.delete(0, tk.END)
        self.completion_entry.insert(0, current)

    def set_tomorrow_day(self):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.completion_entry.delete(0, tk.END)
        self.completion_entry.insert(0, tomorrow)

    def add_item(self):
        if not self.selected_menu:
            messagebox.showwarning(
                "Выберите блюдо", "Выберите блюдо (не категорию) в меню слева"
            )
            return

        mi = self.selected_menu  # это MenuItem из БД

        try:
            quantity = int(self.qty_spinbox.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Неверное количество", "Количество должно быть положительным числом"
            )
            return

        item = OrderItem(
            name=mi.name,
            category=mi.category,
            quantity=quantity,
            price=mi.price,
        )

        self.items.append(item)
        self.update_items_display()

        self.menu_tree.selection_remove(self.menu_tree.selection())
        self.selected_menu = None
        self.qty_spinbox.delete(0, tk.END)
        self.qty_spinbox.insert(0, "1")

        self.btn_save.config(state=tk.NORMAL)

    def remove_item(self):
        selection = self.items_listbox.curselection()
        if not selection:
            return

        index = selection[0]

        del self.items[index]

        self.update_items_display()
        if not self.items:
            self.btn_save.config(state=tk.DISABLED)

    def update_items_display(self):
        self.items_listbox.delete(0, tk.END)

        for item in self.items:
            display_text = (
                f"{item.name} x{item.quantity}  {item.calculate_total():.2f} BYN"
            )
            self.items_listbox.insert(tk.END, display_text)

        total = sum(item.calculate_total() for item in self.items)
        self.total_label.config(text=f"ИТОГО: {total:.2f} BYN")

    def on_item_select(self, event):
        """Обработчик выбора позиции в списке"""
        if self.items_listbox.curselection():
            self.btn_remove_item.config(state=tk.NORMAL)
        else:
            self.btn_remove_item.config(state=tk.DISABLED)

    def save(self):
        if not self.items:
            messagebox.showwarning(
                "Пустой заказ", "Добавьте хотя бы одну позицию в заказ"
            )
            return

        if not self.completion_entry.get():
            messagebox.showwarning("Пустое время выдачи", "Введите время выдачи заказа")
            return

        payment_method = self.payment_var.get()

        address = self.address_entry.get().strip()
        delivery_address = address if address else None
        completion_time = self.completion_entry.get().strip()
        if completion_time:
            try:
                datetime.strptime(completion_time, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror(
                    "Неверный формат",
                    "Время выдачи должно быть в формате:\nЧЧ:ММ\n\nНапример: 15:30",
                )
                return

        if self.editing_order:
            self.editing_order.items = self.items.copy()
            self.editing_order.payment_method = payment_method
            self.editing_order.delivery_adress = delivery_address
            self.editing_order.completed_at = completion_time
            self.result = self.editing_order
        else:
            order = Order(
                order_id=None,
                order_number=None,
                items=self.items.copy(),
                created_at=None,
                completed_at=completion_time,
                payment_method=payment_method,
                delivery_adress=delivery_address,
            )
            self.result = order

        self.dialog.destroy()

    def cancel(self):
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Order]:
        self.dialog.wait_window()
        return self.result

    def load_order_data(self, order: Order):
        self.items = order.items.copy()
        self.update_items_display()

        # Загружаем способ оплаты
        self.payment_var.set(order.payment_method)

        # Загружаем адрес
        if order.delivery_adress:
            self.address_entry.insert(0, order.delivery_adress)

        # Загружаем время выдачи
        if order.completed_at:
            self.completion_entry.insert(0, order.completed_at)

        # Активируем кнопку сохранения если есть позиции
        if self.items:
            self.btn_save.config(state=tk.NORMAL)

    def load_menu_tree(self):
        for iid in self.menu_tree.get_children():
            self.menu_tree.delete(iid)

        cat_nodes: dict[str, str] = {}
        self._dish_by_iid = {}

        menu_items = self.db.get_menu()
        menu_items.sort(key=lambda x: (x.category, x.name))

        for mi in menu_items:
            if mi.category not in cat_nodes:
                cat_iid = self.menu_tree.insert(
                    "",
                    "end",
                    text=mi.category,
                    values=("",),
                    open=False,
                )
                cat_nodes[mi.category] = cat_iid

            dish_iid = self.menu_tree.insert(
                cat_nodes[mi.category],
                "end",
                text=mi.name,
                values=(f"{mi.price:.2f} BYN",),
            )
            self._dish_by_iid[dish_iid] = mi

    def on_menu_select(self, event=None):
        sel = self.menu_tree.selection()
        if not sel:
            self.selected_menu = None
            return
        iid = sel[0]
        self.selected_menu = self._dish_by_iid.get(iid)
