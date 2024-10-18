import os
from tkinter import messagebox

def tail_log_file(filepath, last_position=0):
    try:
        with open(filepath, 'r') as f:
            f.seek(last_position)
            new_lines = f.readlines()
            last_position = f.tell()
            return new_lines, last_position
    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo de log não encontrado.")
        return [], last_position
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao ler o arquivo: {e}")
        return [], last_position
