import json
import os
import shutil
from datetime import datetime
from config import Config

def create_backup():
    if not os.path.exists(Config.DATA_FILE):
        print("Erro: O ficheiro não existe.")
        return
    if not os.path.exists('data/backups'): os.makedirs('data/backups')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data/backups/products_backup_{timestamp}.json"
    shutil.copy2(Config.DATA_FILE, backup_path)
    print(f"✅ Backup criado: {backup_path}")

def reset_database():
    confirm = input("⚠️ Apagar TUDO? (sim/nao): ")
    if confirm.lower() == 'sim':
        with open(Config.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"products": []}, f, indent=4)
        print("✅ Base de dados limpa.")

if __name__ == "__main__":
    print("1. Backup | 2. Reset")
    op = input("Opção: ")
    if op == '1': create_backup()
    elif op == '2': reset_database()
