import tkinter as tk

from database.database import DatabaseManager
from gui.main_window import MainWindow


def main():
    root = tk.Tk()
    db = DatabaseManager()
    app = MainWindow(root, db=db)

    root.mainloop()


if __name__ == "__main__":
    main()
