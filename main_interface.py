import time
import os
import sys
import subprocess
import win32com.client
from tkinter import messagebox, simpledialog, ttk
import tkinter as tk
from PIL import Image, ImageTk

# Adicionar o diretório raiz ao sys.path para permitir importação do firebase_service
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Adicionar o diretório 'interface' ao sys.path
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
            start = line.find('"') + 1
            end = line.find('"', start)
            remote_id = line[start:end]

            if remote_id in saved_accesses:
                continue

            name = ask_for_access_name(remote_id)
            if not name:
                continue

            duplicate_name_ids = [rid for rid, n in saved_accesses.items() if n == name]
            if duplicate_name_ids:
                duplicates = {name: duplicate_name_ids + [remote_id]}
                for rid in duplicates[name]:
                    if messagebox.askyesno("Duplicidade Encontrada", f"O nome '{name}' já está associado ao ID '{rid}'. Deseja substituir pelo novo ID '{remote_id}'?"):
                        delete_access(rid)
                        save_access(remote_id, name)
                        saved_accesses[remote_id] = name
                        break
                    else:
                        new_name = simpledialog.askstring("Novo Nome", f"Digite um novo nome para o ID '{remote_id}':", parent=root)
                        if new_name:
                            save_access(remote_id, new_name)
                            saved_accesses[remote_id] = new_name
                        else:
                            messagebox.showwarning("Ação Necessária", "Nenhum nome fornecido. O ID não foi atualizado.")
            else:
                save_access(remote_id, name)
                saved_accesses[remote_id] = name

last_position = 0  # Declaração da variável global

def monitor_anydesk_log(log_path, saved_accesses, tree, root):
    global last_position  # Torna a variável acessível dentro da função
    log_lines, last_position = tail_log_file(log_path, last_position)
    
    if log_lines:
        process_logs(log_lines, saved_accesses, root)
        # Atualiza a interface
        update_treeview(tree, saved_accesses)
    
    # Agendar a próxima execução após 10 segundos (10000 milissegundos)
    tree.after(10000, monitor_anydesk_log, log_path, saved_accesses, tree, root)

def update_treeview(tree, saved_accesses):
    # Limpa todos os itens existentes na Treeview
    for item in tree.get_children():
        tree.delete(item)
    
    # Adiciona novamente os acessos atualizados
    for remote_id, name in saved_accesses.items():
        tree.insert("", "end", values=(remote_id, name))

def iniciar_interface():
    root = tk.Tk()
    root.title("Monitoramento de Acessos AnyDesk")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    tree = ttk.Treeview(frame, columns=("ID", "Nome"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Nome", text="Nome")
    tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    saved_accesses = load_saved_accesses()
    update_treeview(tree, saved_accesses)  # Atualiza a Treeview inicialmente

    def on_tree_double_click(event):
        item = tree.selection()
        if item:
            remote_id = tree.item(item[0], "values")[0]
            abrir_anydesk(remote_id)

    tree.bind("<Double-1>", on_tree_double_click)

    start_button = ttk.Button(frame, text="Iniciar Monitoramento", command=lambda: monitor_anydesk_log(log_file_path, saved_accesses, tree, root))
    start_button.grid(row=1, column=0, pady=5)

    stop_button = ttk.Button(frame, text="Parar Monitoramento", command=root.quit)
    stop_button.grid(row=2, column=0, pady=5)

    # Botão para abrir AnyDesk (com ícone de trovão)
    def on_click_anydesk_button():
        item = tree.selection()
        if item:
            remote_id = tree.item(item[0], "values")[0]
            abrir_anydesk(remote_id)
        else:
            messagebox.showwarning("Seleção necessária", "Por favor, selecione um ID para acessar.")

    thunder_icon_path = "thunder_icon.png"  # Substituir pelo caminho do ícone desejado
    if os.path.exists(thunder_icon_path):
        thunder_image = Image.open(thunder_icon_path)
        thunder_image = thunder_image.resize((24, 24), Image.ANTIALIAS)
        thunder_icon = ImageTk.PhotoImage(thunder_image)

        thunder_button = ttk.Button(frame, image=thunder_icon, command=on_click_anydesk_button)
        thunder_button.grid(row=0, column=1, padx=5, sticky=(tk.N, tk.S))
    else:
        thunder_button = ttk.Button(frame, text="Abrir AnyDesk", command=on_click_anydesk_button)
        thunder_button.grid(row=0, column=1, padx=5, sticky=(tk.N, tk.S))

    # Iniciar o listener do Firebase e passar o callback para atualizar a Treeview
    iniciar_listener(lambda: update_treeview(tree, load_saved_accesses()))

    root.mainloop()

if __name__ == "__main__":
    iniciar_interface()
