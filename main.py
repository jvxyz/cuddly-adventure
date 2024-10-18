import time
import os
import sys
import subprocess
import win32com.client
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk
from tkinter import Frame, Button
from PIL import Image, ImageTk
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

interface_path = os.path.join(project_root, 'interface')
sys.path.append(interface_path)

hidden_accesses_file = os.path.join(project_root, 'hidden_accesses.json')

try:
    from firebase_service import load_saved_accesses, save_access, delete_access, iniciar_listener
    from log_reader import tail_log_file
    from duplicate_resolver import find_duplicate_names, resolve_duplicates
    from gui_components import ask_for_access_name
except ModuleNotFoundError as e:
    print(f"Erro ao importar módulo: {e}")
    sys.exit(1)

log_file_path = r'C:\ProgramData\AnyDesk\ad_svc.trace'
shortcut_path = r'C:\Projeto Acesso AnyDesk\atalhos_anydesk\1695790049.lnk'

# Load icons if available
icon_open = icon_hide = icon_view_hidden = icon_start = icon_stop = icon_view = None

if __name__ == "__main__":
    root = tk.Tk()
    try:
        icon_open = ImageTk.PhotoImage(Image.open("open_icon.png").resize((24, 24), Image.Resampling.LANCZOS))
    except FileNotFoundError:
        print("open_icon.png not found. Continuing without icon.")
    try:
        icon_hide = ImageTk.PhotoImage(Image.open("hide_icon.png").resize((24, 24), Image.Resampling.LANCZOS))
    except FileNotFoundError:
        print("hide_icon.png not found. Continuing without icon.")
    try:
        icon_view_hidden = ImageTk.PhotoImage(Image.open("view_hidden_icon.png").resize((24, 24), Image.Resampling.LANCZOS))
    except FileNotFoundError:
        print("view_hidden_icon.png not found. Continuing without icon.")
    try:
        icon_start = ImageTk.PhotoImage(Image.open("start_icon.png").resize((24, 24), Image.Resampling.LANCZOS))
    except FileNotFoundError:
        print("start_icon.png not found. Continuing without icon.")
    try:
        icon_stop = ImageTk.PhotoImage(Image.open("stop_icon.png").resize((24, 24), Image.Resampling.LANCZOS))
    except FileNotFoundError:
        print("stop_icon.png not found. Continuing without icon.")
    try:
        icon_view = ImageTk.PhotoImage(Image.open("view_icon.png").resize((24, 24), Image.Resampling.LANCZOS))
    except FileNotFoundError:
        print("view_icon.png not found. Continuing without icon.")

# Load hidden accesses from file
hidden_accesses = {}
if os.path.exists(hidden_accesses_file):
    with open(hidden_accesses_file, 'r') as f:
        hidden_accesses = json.load(f)

def save_hidden_accesses():
    with open(hidden_accesses_file, 'w') as f:
        json.dump(hidden_accesses, f)

def abrir_anydesk(remote_id):
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        comando = f'"{shortcut_path}" {remote_id}'
        subprocess.Popen(comando, shell=True)
    except Exception as e:
        messagebox.showerror("Erro ao abrir AnyDesk", str(e))

def validar_remote_id(remote_id):
    return remote_id.isdigit() and len(remote_id) >= 9

def process_logs(log_lines, saved_accesses, root):
    for line in log_lines:
        if 'app.session' in line and 'Connecting to "' in line:
            remote_id = line.split('"')[1]
            if not validar_remote_id(remote_id):
                continue
            if remote_id in saved_accesses:
                continue

            name = ask_for_access_name(remote_id)
            if not name:
                continue

            duplicate_name_ids = [rid for rid, n in saved_accesses.items() if n == name]
            if duplicate_name_ids:
                duplicates = {name: duplicate_name_ids + [remote_id]}
                resolve_duplicates(duplicates, saved_accesses, delete_access, save_access)
            else:
                save_access(remote_id, name)
                saved_accesses[remote_id] = name

last_position = 0

def monitor_anydesk_log(log_path, saved_accesses, tree, root):
    global last_position
    log_lines, last_position = tail_log_file(log_path, last_position)
    
    if log_lines:
        process_logs(log_lines, saved_accesses, root)
        update_treeview(tree, saved_accesses)
    
    tree.after(10000, monitor_anydesk_log, log_path, saved_accesses, tree, root)

def update_treeview(tree, saved_accesses):
    tree.delete(*tree.get_children())
    for remote_id, name in saved_accesses.items():
        if remote_id not in hidden_accesses:
            tree.insert("", "end", values=(remote_id, name))

def iniciar_interface():
    root.title("Monitoramento de Acessos AnyDesk")
    root.geometry("600x380")
    root.configure(bg="#f0f0f0")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", padding=6, relief="flat", background="#f0f0f0", borderwidth=0)
    style.configure("TLabel", background="#f0f0f0")
    style.configure("TFrame", background="#f0f0f0")

    search_frame = ttk.Frame(root)
    search_frame.grid(row=0, column=0, pady=10, padx=10, sticky=(tk.W, tk.E))
    search_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    ttk.Label(search_frame, text="Buscar ID ou Nome:").grid(row=0, column=0, padx=5)
    search_entry = ttk.Entry(search_frame, width=30)
    search_entry.grid(row=0, column=1, padx=5)
    button_open_anydesk = ttk.Button(search_frame, text="" if icon_open else "Abrir AnyDesk", image=icon_open, compound=None if icon_open else tk.LEFT, command=lambda: abrir_anydesk(search_entry.get()))
    button_open_anydesk.grid(row=0, column=2, padx=5)
    button_open_anydesk.grid_remove()
    button_view_hidden = ttk.Button(search_frame, text="" if icon_view_hidden else "Ver Acessos Ocultos", image=icon_view_hidden, compound=None if icon_view_hidden else tk.LEFT, command=lambda: mostrar_acessos_ocultos())
    button_view_hidden.grid(row=0, column=3, padx=5)
    if hidden_accesses:
        button_view_hidden.grid()
    else:
        button_view_hidden.grid_remove()
    ttk.Button(search_frame, text="" if icon_hide else "Ocultar Acesso", image=icon_hide, compound=None if icon_hide else tk.LEFT, command=lambda: ocultar_selecionado(tree)).grid(row=0, column=4, padx=5)

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=1, column=0, padx=10, pady=10, sticky=(tk.N, tk.S, tk.E, tk.W))
    root.grid_propagate(True)
    frame.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    tree = ttk.Treeview(frame, columns=("ID", "Nome"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Nome", text="Nome")
    tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    saved_accesses = load_saved_accesses()
    update_treeview(tree, saved_accesses)

    def on_key_release(event):
        query = search_entry.get().strip().lower()
        if validar_remote_id(query):
                button_open_anydesk.grid()
        else:
                button_open_anydesk.grid_remove()
        resultados = [(id, name) for id, name in saved_accesses.items() if query in id.lower() or query in name.lower()]
        tree.delete(*tree.get_children())
        for remote_id, name in resultados:
            if remote_id not in hidden_accesses:
                tree.insert("", "end", values=(remote_id, name))

    def hide_access(remote_id):
        if remote_id in saved_accesses:
            hidden_accesses[remote_id] = saved_accesses.pop(remote_id)
            save_hidden_accesses()
            update_treeview(tree, saved_accesses)

    def ocultar_selecionado(tree):
        selected_item = tree.focus()
        if not selected_item:
                messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para ocultar.")
                return
        item_values = tree.item(selected_item, 'values')
        hide_access(item_values[0])
        if hidden_accesses:
                button_view_hidden.grid()
        else:
                button_view_hidden.grid_remove()
        if not selected_item:
                messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para ocultar.")
                return
        item_values = tree.item(selected_item, 'values')
        hide_access(item_values[0])
        if hidden_accesses:
                button_view_hidden.grid()
        else:
                button_view_hidden.grid_remove()
        if not selected_item:
                messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para ocultar.")
                return
        item_values = tree.item(selected_item, 'values')
        hide_access(item_values[0])
        if hidden_accesses:
                button_view_hidden.grid()
        if not selected_item:
            messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para ocultar.")
            return
        item_values = tree.item(selected_item, 'values')
        hide_access(item_values[0])

    def mostrar_acessos_ocultos():
        ocultos_window = tk.Toplevel(root)
        ocultos_window.title("Acessos Ocultos")
        ocultos_window.configure(bg="#f0f0f0")
        ocultos_tree = ttk.Treeview(ocultos_window, columns=("ID", "Nome"), show="headings")
        ocultos_tree.heading("ID", text="ID")
        ocultos_tree.heading("Nome", text="Nome")
        ocultos_tree.pack(fill=tk.BOTH, expand=True)

        for remote_id, name in hidden_accesses.items():
            ocultos_tree.insert("", "end", values=(remote_id, name))

        def restaurar_selecionado():
            selected_item = ocultos_tree.focus()
            if not selected_item:
                        messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para restaurar.")
                        return
            item_values = ocultos_tree.item(selected_item, 'values')
            remote_id = item_values[0]
            if remote_id in hidden_accesses:
                        saved_accesses[remote_id] = hidden_accesses.pop(remote_id)
                        save_hidden_accesses()
                        update_treeview(tree, saved_accesses)
                        ocultos_tree.delete(selected_item)
            if not hidden_accesses:
                        button_view_hidden.grid_remove()
            if not selected_item:
                        messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para restaurar.")
                        return
            item_values = ocultos_tree.item(selected_item, 'values')
            remote_id = item_values[0]
            if remote_id in hidden_accesses:
                        saved_accesses[remote_id] = hidden_accesses.pop(remote_id)
                        save_hidden_accesses()
                        update_treeview(tree, saved_accesses)
                        ocultos_tree.delete(selected_item)
            if not hidden_accesses:
                        button_view_hidden.grid_remove()
            if not selected_item:
                messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para restaurar.")
                return
            item_values = ocultos_tree.item(selected_item, 'values')
            remote_id = item_values[0]
            if remote_id in hidden_accesses:
                saved_accesses[remote_id] = hidden_accesses.pop(remote_id)
                save_hidden_accesses()
                update_treeview(tree, saved_accesses)
                ocultos_tree.delete(selected_item)

        ttk.Button(ocultos_window, text="" if icon_view else "Restaurar Acesso Selecionado", image=icon_view, compound=None if icon_view else tk.LEFT, command=restaurar_selecionado).pack(pady=5)

    search_entry.bind("<KeyRelease>", on_key_release)
    tree.bind("<Double-1>", lambda event: abrir_anydesk(tree.item(tree.selection()[0], "values")[0]))

    monitor_anydesk_log(log_file_path, saved_accesses, tree, root)

    ttk.Button(frame, text="" if icon_stop else "Parar Monitoramento", image=icon_stop, compound=None if icon_stop else tk.LEFT, command=root.quit).grid(row=2, column=0, pady=5)

    iniciar_listener(lambda: update_treeview(tree, load_saved_accesses()))
    root.mainloop()

if __name__ == "__main__":
    iniciar_interface()
