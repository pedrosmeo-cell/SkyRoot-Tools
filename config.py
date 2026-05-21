import os


class Config:
    # Chave secreta protegida por variável de ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY', 'skyroot-tools-default-key-2026')

    # PROTEÇÃO REAL: O código procura a senha no sistema.
    # NUNCA escreva a sua senha real aqui no código.
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1972')

    # Caminho base para o ficheiro de base de dados dos produtos
    DATA_FILE = os.path.join('data', 'products.json')
