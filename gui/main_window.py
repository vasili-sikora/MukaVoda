import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from database.database import DatabaseManager
from database.models import Order
from gui.child_form import BaseForm
from gui.menu_form import MenuForm


class MainWindow(BaseForm):
    def __init__(self, root: tk.Tk, db: DatabaseManager):
        self.root = root
        self.db = db

        self.root.title("MukaVoda")
        self.root.geometry("1280x720")

        self.selected_order: Optional[Order] = None

        self.create_widgets()

        self.refresh_orders()

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="Система управления заказами",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        title_label.pack(pady=15)

        button_frame = tk.Frame(self.root, bg="#ecf0f1", height=80)
        button_frame.pack(fill=tk.X)
        button_frame.pack_propagate(False)

        self.btn_create = tk.Button(
            button_frame,
            text="Создать заказ",
            font=("Arial", 12),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
            command=self.create_order,
        )
        self.btn_create.pack(side=tk.LEFT, padx=10, pady=15)

        # Кнопка "Изменить заказ"
        self.btn_edit = tk.Button(
            button_frame,
            text="Изменить заказ",
            font=("Arial", 12),
            bg="#e67e22",
            fg="white",
            padx=20,
            pady=10,
            command=self.edit_order,
            state=tk.DISABLED,
        )
        self.btn_edit.pack(side=tk.LEFT, padx=10, pady=15)

        self.btn_delete = tk.Button(
            button_frame,
            text="Удалить заказ",
            font=("Arial", 12),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=10,
            command=self.delete_order,
            state=tk.DISABLED,
        )
        self.btn_delete.pack(side=tk.LEFT, padx=10, pady=15)

        self.btn_refresh = tk.Button(
            button_frame,
            text="Обновить",
            font=("Arial", 12),
            bg="#95a5a6",
            fg="white",
            padx=20,
            pady=10,
            command=self.refresh_orders,
        )
        self.btn_refresh.pack(side=tk.LEFT, padx=10, pady=15)

        self.btn_show_menu = tk.Button(
            button_frame,
            text="Посмотреть меню",
            font=("Arial", 12),
            bg="#95a5a6",
            fg="white",
            padx=20,
            pady=10,
            command=self.show_menu,
        )
        self.btn_show_menu.pack(side=tk.LEFT, padx=10, pady=15)

        self.revenue_label = tk.Label(
            button_frame,
            text="Выручка за сегодня: 0.00 BYN",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50",
        )
        self.revenue_label.pack(side=tk.RIGHT, padx=20, pady=15)

        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Номер", "Создан", "Время выдачи", "Оплата", "Доставка", "Стоимость")

        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=15
        )

        self.tree.heading("Номер", text="Номер заказа")
        self.tree.heading("Создан", text="Создан")
        self.tree.heading("Время выдачи", text="Время выдачи")
        self.tree.heading("Оплата", text="Оплата")
        self.tree.heading("Доставка", text="Доставка")
        self.tree.heading("Стоимость", text="Стоимость")

        self.tree.column("Номер", width=150)
        self.tree.column("Создан", width=150)
        self.tree.column("Время выдачи", width=150)
        self.tree.column("Оплата", width=120)
        self.tree.column("Доставка", width=200)
        self.tree.column("Стоимость", width=120)

        scrollbar = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.tree.bind("<Double-1>", self.view_order_details)

        status_frame = tk.Frame(self.root, bg="#34495e", height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame,
            text="Готов к работе",
            font=("Arial", 10),
            bg="#34495e",
            fg="white",
            anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=5)

    def refresh_orders(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        orders = self.db.get_all_orders(limit=100)

        for order in orders:
            delivery = order.delivery_adress if order.delivery_adress else "Самовывоз"

            completion = order.completed_at if order.completed_at else "—"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    order.order_number,
                    order.created_at,
                    completion,
                    order.payment_method,
                    delivery,
                    f"{order.calculate_total():.2f} BYN",
                ),
                tags=(str(order.order_id),),  # Сохраняем ID в тегах
            )

        self.update_revenue()

        self.status_label.config(text=f"Загружено заказов: {len(orders)}")

    def update_revenue(self):
        """Обновляет отображение выручки за сегодня"""
        total = self.db.get_today_total()
        self.revenue_label.config(text=f"Выручка за сегодня: {total:.2f} BYN")

    def on_select(self, event):
        """Обработчик выбора заказа в таблице"""
        selected = self.tree.selection()

        if selected:
            self.btn_edit.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)

            item = selected[0]
            tags = self.tree.item(item, "tags")
            if tags:
                order_id = int(tags[0])
                self.selected_order = self.db.get_order(order_id)
        else:
            self.btn_edit.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.selected_order = None

    def create_order(self):
        """Создает новый заказ"""
        from gui.order_form import OrderForm

        form = OrderForm(self.root)
        order = form.show()

        if order:
            self.db.add_order(order)

            self.refresh_orders()

            messagebox.showinfo(
                "Заказ создан",
                f"Заказ {order.order_number} успешно создан!\n\n"
                f"Позиций: {len(order.items)}\n"
                f"Сумма: {order.calculate_total():.2f} BYN",
            )

            self.status_label.config(text=f"Создан заказ {order.order_number}")

    def edit_order(self):
        """Открывает форму редактирования заказа"""
        if not self.selected_order:
            return

        from gui.order_form import OrderForm

        form = OrderForm(self.root, order=self.selected_order)
        updated_order = form.show()

        if updated_order:
            self.db.update_order(updated_order)

            self.refresh_orders()

            messagebox.showinfo(
                "Заказ обновлен",
                f"Заказ {updated_order.order_number} успешно обновлен!",
            )

            self.status_label.config(
                text=f"Обновлен заказ {updated_order.order_number}"
            )

    def delete_order(self):
        """Удаляет заказ"""
        if not self.selected_order:
            return

        result = messagebox.askyesno(
            "Удалить заказ",
            f"Вы уверены, что хотите удалить заказ {self.selected_order.order_number}?\n\n"
            f"Это действие нельзя отменить!",
        )

        if result:
            order_number = self.selected_order.order_number

            self.db.delete_order(self.selected_order.order_id)

            self.refresh_orders()

            self.status_label.config(text=f"Заказ {order_number} удален")

    def view_order_details(self, event):
        if not self.selected_order:
            return

        details = f"Заказ: {self.selected_order.order_number}\n"
        details += f"Создан: {self.selected_order.created_at}\n"

        if self.selected_order.completed_at:
            details += f"Время выдачи: {self.selected_order.completed_at}\n"
        else:
            details += "Статус: В работе\n"

        details += f"Оплата: {self.selected_order.payment_method}\n"

        if self.selected_order.delivery_adress:
            details += f"Адрес: {self.selected_order.delivery_adress}\n"
        else:
            details += "Самовывоз\n"

        details += "\nПозиции:\n"
        for i, item in enumerate(self.selected_order.items, 1):
            details += f"  {i}. {item.name} x{item.quantity} - {item.calculate_total():.2f} BYN\n"

        details += f"\nИТОГО: {self.selected_order.calculate_total():.2f} BYN"

        messagebox.showinfo("Детали заказа", details)

    def show_menu(self):
        menu_form = MenuForm(self.root)
