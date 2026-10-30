"""
Script de setup do banco do CofreSeguro.
Cria o banco e aplica o schema (tabelas) e os triggers automaticamente.

Uso:
    python setup_db.py

As credenciais do MySQL vem do arquivo .env (ver .env.example).
ATENCAO: este script recria o banco do zero (apaga o que existir).
"""

import os
import sys
import mysql.connector


def carregar_env(caminho=".env"):
    """Le o arquivo .env e devolve um dicionario com as variaveis."""
    if not os.path.exists(caminho):
        print("ERRO: arquivo .env nao encontrado.")
        print("Copie o .env.example para .env e preencha a senha do MySQL.")
        sys.exit(1)
    config = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            config[chave.strip()] = valor.strip()
    return config


def executar_script(cursor, caminho):
    """Executa um arquivo .sql respeitando mudancas de DELIMITER."""
    delimitador = ";"
    buffer = ""
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            stripped = linha.strip()
            if not stripped or stripped.startswith("--"):
                continue
            if stripped.upper().startswith("DELIMITER"):
                delimitador = stripped.split()[1]
                continue
            buffer += linha
            while delimitador in buffer:
                comando, buffer = buffer.split(delimitador, 1)
                if comando.strip():
                    cursor.execute(comando)
    if buffer.strip():
        cursor.execute(buffer)


def main():
    env = carregar_env()
    nome_banco = env.get("DB_NAME", "cofreseguro")

    # conecta no servidor (ainda sem escolher um banco)
    conexao = mysql.connector.connect(
        host=env.get("DB_HOST", "localhost"),
        port=int(env.get("DB_PORT", 3306)),
        user=env.get("DB_USER", "root"),
        password=env.get("DB_PASSWORD", ""),
    )
    cursor = conexao.cursor()

    print(f"Recriando o banco '{nome_banco}' do zero...")
    cursor.execute(f"DROP DATABASE IF EXISTS {nome_banco}")

    print("Aplicando o schema (tabelas)...")
    executar_script(cursor, "db/01_schema.sql")

    print("Aplicando os triggers...")
    executar_script(cursor, "db/02_triggers.sql")

    conexao.commit()
    cursor.close()
    conexao.close()
    print("Banco criado com sucesso! As 6 tabelas e os 4 triggers estao prontos.")


if __name__ == "__main__":
    main()
