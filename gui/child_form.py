import tkinter as tk


class ChildForm:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)

        self.dialog.geometry("950x750")
        self.dialog.resizable(False, False)

        self.dialog.transient(parent)
        self.dialog.grab_set()
