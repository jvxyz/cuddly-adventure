import time
import os
import sys
import subprocess
import win32com.client
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk
from tkinter import Frame, Button
from ttkthemes import ThemedTk
from PIL import Image, ImageTk

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

interface_path = os.path.join(project_root, 'interface')
sys.path.append(interface_path)

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

def abrir_anydesk(remote_id):
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        comando = f'"{shortcut_path}" {remote_id}'
        subprocess.Popen(comando, shell=True)
    except Exception as e:
        messagebox.showerror("Erro ao abrir AnyDesk", str(e))

def process_logs(log_lines, saved_accesses, root):
    for line in log_lines:
        if 'app.session' in line and 'Connecting to "' in line:
            remote_id = line.split('"')[1]
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
hidden_accesses = {}

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
    root = ThemedTk(theme="arc")
    root.title("Monitoramento de Acessos AnyDesk")
    root.geometry("800x400")

    search_frame = ttk.Frame(root)
    search_frame.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
    ttk.Label(search_frame, text="Buscar ID ou Nome:").pack(side=tk.LEFT, padx=5)
    search_entry = ttk.Entry(search_frame, width=30)
    search_entry.pack(side=tk.LEFT, padx=5)
    ttk.Button(search_frame, text="Abrir AnyDesk", command=lambda: abrir_anydesk(search_entry.get())).pack(side=tk.LEFT, padx=5)

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
    frame.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    tree = ttk.Treeview(frame, columns=("ID", "Nome"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Nome", text="Nome")
    tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    hidden_button = ttk.Button(root, text="Ver Acessos Ocultos", command=lambda: mostrar_acessos_ocultos())
    hidden_button.grid(row=0, column=1, padx=5, sticky=(tk.E))

    hide_button = ttk.Button(root, text="Ocultar Acesso Selecionado", command=lambda: ocultar_selecionado(tree))
    hide_button.grid(row=1, column=1, padx=5, sticky=(tk.E))

    saved_accesses = load_saved_accesses()
    update_treeview(tree, saved_accesses)

    def on_key_release(event):
        query = search_entry.get().strip().lower()
        resultados = [(id, name) for id, name in saved_accesses.items() if query in id.lower() or query in name.lower()]
        tree.delete(*tree.get_children())
        for remote_id, name in resultados:
            if remote_id not in hidden_accesses:
                tree.insert("", "end", values=(remote_id, name))

    def hide_access(remote_id):
        if remote_id in saved_accesses:
            hidden_accesses[remote_id] = saved_accesses.pop(remote_id)
            update_treeview(tree, saved_accesses)

    def ocultar_selecionado(tree):
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("Nenhuma seleção", "Por favor, selecione um item para ocultar.")
            return
        item_values = tree.item(selected_item, 'values')
        hide_access(item_values[0])

    def mostrar_acessos_ocultos():
        ocultos_window = tk.Toplevel(root)
        ocultos_window.title("Acessos Ocultos")
        ocultos_tree = ttk.Treeview(ocultos_window, columns=("ID", "Nome"), show="headings")
        ocultos_tree.heading("ID", text="ID")
        ocultos_tree.heading("Nome", text="Nome")
        ocultos_tree.pack(fill=tk.BOTH, expand=True)

        for remote_id, name in hidden_accesses.items():
            ocultos_tree.insert("", "end", values=(remote_id, name))

    search_entry.bind("<KeyRelease>", on_key_release)
    tree.bind("<Double-1>", lambda event: abrir_anydesk(tree.item(tree.selection()[0], "values")[0]))

    ttk.Button(frame, text="Iniciar Monitoramento", command=lambda: monitor_anydesk_log(log_file_path, saved_accesses, tree, root)).grid(row=1, column=0, pady=5)
    ttk.Button(frame, text="Parar Monitoramento", command=root.quit).grid(row=2, column=0, pady=5)

    iniciar_listener(lambda: update_treeview(tree, load_saved_accesses()))
    root.mainloop()

if __name__ == "__main__":
    iniciar_interface()
