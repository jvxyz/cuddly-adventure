import tkinter as tk
from tkinter import simpledialog, messagebox

def find_duplicate_names(accesses):
    name_to_ids = {}
    for remote_id, name in accesses.items():
        if name in name_to_ids:
            name_to_ids[name].append(remote_id)
        else:
            name_to_ids[name] = [remote_id]
    return {name: ids for name, ids in name_to_ids.items() if len(ids) > 1}

def resolve_duplicates(duplicates, accesses, save_access_callback, show_info_callback):
    for name, ids in duplicates.items():
        # Perguntar ao usuário como deseja resolver a duplicidade
        root = tk.Tk()
        root.withdraw()  # Oculta a janela principal do Tkinter
        
        # Informar o usuário sobre a duplicidade e oferecer opções
        for new_id in ids[1:]:
            current_id = ids[0]
            choice = messagebox.askquestion(
                "Resolver Duplicidade",
                f"O nome '{name}' está associado aos IDs: {current_id} e {new_id}.\n"
                "Deseja manter o ID atual ({current_id}) e alterar o nome do novo ID ({new_id})?"
            )

            if choice == 'yes':
                # Perguntar um novo nome para o novo ID
                new_name = simpledialog.askstring(
                    "Novo Nome",
                    f"Digite um novo nome para o ID '{new_id}':"
                )
                if new_name:
                    accesses[new_id] = new_name
                    save_access_callback(new_id, new_name)  # Chamar o callback correto
                    show_info_callback("Nome Atualizado", f"O ID '{new_id}' foi atualizado com o novo nome '{new_name}'.")
                else:
                    messagebox.showwarning("Ação Necessária", "Nenhum nome fornecido. O ID não foi atualizado.")
            else:
                # Manter ambos, mas com nomes diferentes
                new_name = simpledialog.askstring(
                    "Novo Nome",
                    f"O nome '{name}' está em uso.\nDigite um nome diferente para o ID '{new_id}':"
                )
                if new_name:
                    accesses[new_id] = new_name
                    save_access_callback(new_id, new_name)  # Chamar o callback correto
                    show_info_callback("Nome Atualizado", f"O ID '{new_id}' foi mantido com o novo nome '{new_name}'.")
                else:
                    messagebox.showwarning("Ação Necessária", "Nenhum nome fornecido. O ID não foi atualizado.")
