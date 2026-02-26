import tkinter as tk

from database.database import DatabaseManager
from gui.main_window import MainWindow
from services.order_service import OrderService


def main():
    root = tk.Tk()
    db = DatabaseManager()
    order_service = OrderService()
    app = MainWindow(root, db=db, order_service=order_service)

    root.mainloop()


if __name__ == "__main__":
    main()
