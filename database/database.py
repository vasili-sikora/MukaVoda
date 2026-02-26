import sqlite3
from datetime import datetime
from typing import Optional

from .models import MenuItem, Order, OrderItem


class DatabaseManager:
    def __init__(self, db_path: str = "data/restaurant.db"):
        self.db_path = db_path

        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        return conn

    def init_database(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                delivery_adress TEXT,
                total_price REAL NOT NULL DEFAULT 0
                )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                price REAL NOT NULL CHECK(price > 0),
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_number
            ON orders(order_number)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_created
            ON orders(created_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_items_order_id
            ON order_items(order_id)
        """)

        conn.commit()
        conn.close()

        print("База данных инициализирована")

    def add_order(self, order: Order) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        total_price = getattr(order, "total_price", None)
        if total_price is None:
            total_price = order.calculate_total()

        cursor.execute(
            """
            INSERT INTO orders(
                order_number, created_at, completed_at,
                payment_method, delivery_adress, total_price
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order.order_number,
                order.created_at,
                order.completed_at,
                order.payment_method,
                order.delivery_adress,
                float(total_price),
            ),
        )

        order_id = cursor.lastrowid

        for item in order.items:
            cursor.execute(
                """
                INSERT INTO order_items (
                    order_id, item_name, category, quantity, price
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (order_id, item.name, item.category, item.quantity, item.price),
            )

        conn.commit()
        conn.close()

        print(f"Заказ {order.order_number} сохранен с ID={order_id}")

    def get_order(self, order_id: int) -> Optional[Order]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        cursor.execute(
            "SELECT * FROM order_items WHERE order_id=?",
            (order_id,),
        )

        items: list[OrderItem] = []
        for item_row in cursor.fetchall():
            items.append(
                OrderItem(
                    name=item_row["item_name"],
                    category=item_row["category"],
                    quantity=item_row["quantity"],
                    price=item_row["price"],
                )
            )

        order = Order(
            order_id=row["id"],
            order_number=row["order_number"],
            items=items,
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            payment_method=row["payment_method"],
            delivery_adress=row["delivery_adress"],
        )

        setattr(order, "total_price", row["total_price"])

        conn.close()
        print(f"Заказ {order.order_number} успешно загружен")
        return order

    def get_all_orders(self, limit: int = 50) -> list[Order]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM orders
            ORDER BY completed_at DESC
            LIMIT ?""",
            (limit,),
        )

        order_ids = [row["id"] for row in cursor.fetchall()]
        conn.close()

        orders = []
        for order_id in order_ids:
            order = self.get_order(order_id)
            if order:
                orders.append(order)

        print("Все заказы успешно загружены")
        return orders

    def update_order(self, order: Order) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        # Берём итог, рассчитанный в GUI/сервисе (со скидкой/ручной суммой),
        # иначе — считаем по позициям.
        total_price = getattr(order, "total_price", None)
        if total_price is None:
            total_price = order.calculate_total()

        cursor.execute(
            """
            UPDATE orders SET
                order_number = ?,
                completed_at = ?,
                payment_method = ?,
                delivery_adress = ?,
                total_price = ?
            WHERE id = ?
            """,
            (
                order.order_number,
                order.completed_at,
                order.payment_method,
                order.delivery_adress,
                float(total_price),
                order.order_id,
            ),
        )

        if cursor.rowcount == 0:
            conn.close()
            print("Не найдено заказов")
            return

        cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order.order_id,))

        for item in order.items:
            cursor.execute(
                """
                INSERT INTO order_items (
                    order_id, item_name, category, quantity, price
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (order.order_id, item.name, item.category, item.quantity, item.price),
            )

        conn.commit()
        conn.close()

        print(f"Заказ {order.order_number} обновлен")

    def delete_order(self, order_id: int) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        if deleted:
            print(f"Заказ с ID={order_id} удален")
        else:
            print(f"Заказ с ID={order_id} не найден")

    # DEBUG
    def delete_all_orders(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM orders")

        conn.commit()
        conn.close()
        print("Все заказы удалены")

    def get_shift_total(self, date: str) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT SUM(total_price) as total
            FROM orders
            WHERE DATE(completed_at) = ?
        """,
            (date,),
        )

        result = cursor.fetchone()
        conn.close()

        return result["total"] if result["total"] else 0.0

    def get_today_total(self) -> float:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_shift_total(today)

    def get_menu(self) -> list[MenuItem]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM menu")

        menu_items: list[MenuItem] = []
        for row in cursor:
            menu_items.append(
                MenuItem(
                    name=row["name"],
                    category=row["category"],
                    price=row["price"],
                )
            )

        conn.close()
        return menu_items

    def add_to_menu(self, menu_item: MenuItem) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO menu (name, category, price) VALUES (?, ?, ?)",
            (menu_item.name, menu_item.category, menu_item.price),
        )

        conn.commit()
        conn.close()

        print("Позиция успешно добавлена в меню")

    def delete_from_menu(self, name: str) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM menu WHERE name = ?", (name,))

        conn.commit()
        conn.close()

        print("Позиция успешно удалена из меню")

    # DEBUG
    def delete_all_menu(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM menu")

        conn.commit()
        conn.close()

    def update_menu_item(self, old_name: str, menu_item: MenuItem) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
                UPDATE menu
                SET name = ?, category = ?, price = ?
                WHERE name = ?
                """,
            (menu_item.name, menu_item.category, menu_item.price, old_name),
        )

        conn.commit()
        conn.close()
