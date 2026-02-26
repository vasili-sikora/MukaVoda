from dataclasses import dataclass
from datetime import datetime


@dataclass
class MenuItem:
    name: str
    category: str
    price: float

    def __str__(self) -> str:
        return f"{self.name}({self.category}): {self.price}"


@dataclass
class OrderItem(MenuItem):
    quantity: int

    def calculate_total(self) -> float:
        return self.price * self.quantity

    def __str__(self) -> str:
        return super().__str__() + f"*{self.quantity} = {self.calculate_total()}"


class Order:
    def __init__(
        self,
        order_id: int | None,
        order_number: str | None,
        items: list[OrderItem],
        created_at: str | None,
        completed_at: str,
        payment_method: str,
        delivery_adress: str | None,
    ):
        self.order_id = order_id
        self.order_number = order_number or self._generate_order_number()

        self.items = items if items else []

        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.completed_at = completed_at

        self.payment_method = payment_method
        self.delivery_adress = delivery_adress

    def calculate_total(self):
        return sum(item.calculate_total() for item in self.items)

    def __str__(self) -> str:
        return f"{self.order_number}: {self.items}, {self.created_at}, {self.completed_at}, {self.payment_method}, {self.delivery_adress}"

    def __repr__(self) -> str:
        return (
            f"Order("
            f"id={self.order_id}, "
            f"number={self.order_number}, "
            f"items={len(self.items)}, "
            f"total={self.calculate_total():.2f} BYN, "
            f"created_at={self.created_at}, "
            f"completed_at={self.completed_at}, "
            f"payment_method={self.payment_method}, "
            f"delivery_adress={self.delivery_adress}"
            f")"
        )

    def add_item(self, item: OrderItem):
        self.items.append(item)

    def remove_item(self, ind: int):
        if 0 <= ind < len(self.items):
            removed = self.items.pop(ind)
            print(f"Удалена {removed} позиция")
        else:
            print("Не удалось удалить позицию")

    def remove_all_items(self):
        self.items.clear()

    def _generate_order_number(self) -> str:
        return f"#{datetime.now().strftime('%Y%m%d%H%M%S')}"
