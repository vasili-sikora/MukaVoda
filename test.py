from database import database
from database.models import MenuItem

db = database.DatabaseManager("data/test.py")

db.delete_all_menu()

db.add_to_menu(MenuItem(name="Кока-Кола 0.25л", category="Холодные напитки", price=2.0))

print(db.get_menu())

db.delete_from_menu("Кока-Кола 0.25л")

print(db.get_menu())
