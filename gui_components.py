import tkinter as tk
from tkinter import simpledialog, messagebox

def ask_for_access_name(remote_id):
    root = tk.Tk()
    root.withdraw()
    name = simpledialog.askstring("Nome do Acesso", f"Novo acesso detectado:\nID: {remote_id}\nInforme o nome para esse acesso:")
    root.destroy()
    return name
