import firebase_admin
from firebase_admin import credentials, firestore
from tkinter import messagebox

# Inicializar Firebase com credenciais
cred = credentials.Certificate(r"C:\Projeto Acesso AnyDesk\acesso-anydesk-firebase-adminsdk-a2j5r-617aebce54.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def load_saved_accesses():
    try:
        accesses_ref = db.collection('acessos')
        docs = accesses_ref.stream()
        return {doc.id: doc.to_dict().get('nome', '') for doc in docs}
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar acessos do Firebase: {e}")
        return {}

def save_access(remote_id, name):
    try:
        db.collection('acessos').document(remote_id).set({'nome': name})
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar acesso no Firebase: {e}")

def delete_access(remote_id):
    try:
        db.collection('acessos').document(remote_id).delete()
        messagebox.showinfo("Acesso Removido", f"O acesso com ID '{remote_id}' foi removido.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao remover acesso '{remote_id}': {e}")

def iniciar_listener(callback):
    """Inicia um listener que monitora a coleção 'acessos' e chama o callback sempre que há mudanças."""
    try:
        def on_snapshot(doc_snapshot, changes, read_time):
            for change in changes:
                if change.type.name in ['ADDED', 'MODIFIED', 'REMOVED']:
                    # Chama o callback passado como parâmetro para atualizar a interface
                    callback()

        # Configurar o listener para a coleção 'acessos'
        db.collection('acessos').on_snapshot(on_snapshot)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar o listener do Firebase: {e}")
