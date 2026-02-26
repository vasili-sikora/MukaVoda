from datetime import datetime

from services.errors import ValidationError


class OrderService:
    def validate_completion_time(self, text: str) -> str:
        text = text.strip()
        if not text:
            raise ValidationError("Время выдачи обязательно.")

        try:
            datetime.strptime(text, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValidationError("Вркемя выдачи: формат ГГГГ-ММ-ДД ЧЧ:ММ")

        return text

    def calc_items_total(self, items) -> float:
        return sum(item.calculate_total() for item in items)

    def calc_total(
        self, items_total: float, discount_percent: float, manual_total: float | None
    ) -> float:
        if manual_total is not None:
            if manual_total <= 0:
                raise ValidationError("Цена должна быть больше 0")
            return round(float(manual_total), 2)
