import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

from database.database import DatabaseManager
from database.models import Order, OrderItem
from gui.menu_form import MenuForm


class MainWindow:
    """Главное окно приложения"""

    def __init__(self, root: tk.Tk):
        """
        Инициализация главного окна.

        Параметры:
            root: Корневое окно Tkinter
        """
        self.root = root
        self.root.title("MukaVoda")
        self.root.geometry("1280x720")

        # База данных
        self.db = DatabaseManager()

        # Текущий выбранный заказ
        self.selected_order: Optional[Order] = None

        # Создаем интерфейс
        self.create_widgets()

        # Загружаем заказы
        self.refresh_orders()

    def create_widgets(self):
        """Создает все виджеты интерфейса"""

        # ====================================================================
        # ЗАГОЛОВОК
        # ====================================================================
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🍕 Система управления заказами",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white",
        )
        title_label.pack(pady=15)

        # ====================================================================
        # ПАНЕЛЬ КНОПОК
        # ====================================================================
        button_frame = tk.Frame(self.root, bg="#ecf0f1", height=80)
        button_frame.pack(fill=tk.X)
        button_frame.pack_propagate(False)

        # Кнопка "Создать заказ"
        self.btn_create = tk.Button(
            button_frame,
            text="➕ Создать заказ",
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

        # Кнопка "Удалить заказ"
        self.btn_delete = tk.Button(
            button_frame,
            text="🗑️ Удалить заказ",
            font=("Arial", 12),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=10,
            command=self.delete_order,
            state=tk.DISABLED,
        )
        self.btn_delete.pack(side=tk.LEFT, padx=10, pady=15)

        # Кнопка "Обновить"
        self.btn_refresh = tk.Button(
            button_frame,
            text="🔄 Обновить",
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
            text="🔄 Посмотреть меню",
            font=("Arial", 12),
            bg="#95a5a6",
            fg="white",
            padx=20,
            pady=10,
            command=self.show_menu,
        )
        self.btn_show_menu.pack(side=tk.LEFT, padx=10, pady=15)

        # Метка выручки
        self.revenue_label = tk.Label(
            button_frame,
            text="Выручка за сегодня: 0.00 BYN",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50",
        )
        self.revenue_label.pack(side=tk.RIGHT, padx=20, pady=15)

        # ====================================================================
        # ТАБЛИЦА ЗАКАЗОВ
        # ====================================================================
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создаем Treeview (таблицу)
        columns = ("Номер", "Создан", "Время выдачи", "Оплата", "Доставка", "Стоимость")

        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=15
        )

        # Настраиваем колонки
        self.tree.heading("Номер", text="Номер заказа")
        self.tree.heading("Создан", text="Создан")
        self.tree.heading("Время выдачи", text="Время выдачи")
        self.tree.heading("Оплата", text="Оплата")
        self.tree.heading("Доставка", text="Доставка")
        self.tree.heading("Стоимость", text="Стоимость")

        # Ширина колонок
        self.tree.column("Номер", width=150)
        self.tree.column("Создан", width=150)
        self.tree.column("Время выдачи", width=150)
        self.tree.column("Оплата", width=120)
        self.tree.column("Доставка", width=200)
        self.tree.column("Стоимость", width=120)

        # Скроллбар
        scrollbar = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Размещаем таблицу и скроллбар
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Обработчик выбора строки
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Двойной клик - просмотр деталей
        self.tree.bind("<Double-1>", self.view_order_details)

        # ====================================================================
        # СТАТУС БАР
        # ====================================================================
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
        """Обновляет список заказов из БД"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загружаем заказы из БД
        orders = self.db.get_all_orders(limit=100)

        # Заполняем таблицу
        for order in orders:
            # Доставка
            delivery = (
                order.delivery_adress if order.delivery_adress else "🏪 Самовывоз"
            )

            # Время выдачи
            completion = order.completed_at if order.completed_at else "—"

            # Добавляем строку
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

        # Обновляем выручку
        self.update_revenue()

        # Обновляем статус
        self.status_label.config(text=f"Загружено заказов: {len(orders)}")

    def update_revenue(self):
        """Обновляет отображение выручки за сегодня"""
        total = self.db.get_today_total()
        self.revenue_label.config(text=f"Выручка за сегодня: {total:.2f} BYN")

    def on_select(self, event):
        """Обработчик выбора заказа в таблице"""
        selected = self.tree.selection()

        if selected:
            # Включаем кнопки
            self.btn_edit.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)

            # Получаем ID заказа из тегов
            item = selected[0]
            tags = self.tree.item(item, "tags")
            if tags:
                order_id = int(tags[0])
                self.selected_order = self.db.get_order(order_id)
        else:
            # Отключаем кнопки
            self.btn_edit.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
            self.selected_order = None

    def create_order(self):
        """Создает новый заказ"""
        from gui.order_form import OrderForm

        # Показываем форму
        form = OrderForm(self.root)
        order = form.show()

        # Если заказ создан
        if order:
            # Сохраняем в БД
            self.db.add_order(order)

            # Обновляем список
            self.refresh_orders()

            # Показываем сообщение
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

        # Показываем форму с данными заказа
        form = OrderForm(self.root, order=self.selected_order)
        updated_order = form.show()

        # Если заказ изменен
        if updated_order:
            # Обновляем в БД
            self.db.update_order(updated_order)

            # Обновляем список
            self.refresh_orders()

            # Показываем сообщение
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

        # Подтверждение
        result = messagebox.askyesno(
            "Удалить заказ",
            f"Вы уверены, что хотите удалить заказ {self.selected_order.order_number}?\n\n"
            f"Это действие нельзя отменить!",
        )

        if result:
            order_number = self.selected_order.order_number

            # Удаляем из БД
            self.db.delete_order(self.selected_order.order_id)

            # Обновляем список
            self.refresh_orders()

            self.status_label.config(text=f"Заказ {order_number} удален")

    def view_order_details(self, event):
        """Показывает детали заказа при двойном клике"""
        if not self.selected_order:
            return

        # Формируем текст с деталями
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

        # Показываем в диалоге
        messagebox.showinfo("Детали заказа", details)

    def show_menu(self):
        menu_form = MenuForm(self.root)
