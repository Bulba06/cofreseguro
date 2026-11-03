import os
import sys


def carregar_env(caminho=".env"):
    """Le o arquivo .env e devolve um dicionario com as variaveis."""
    if not os.path.exists(caminho):
        print("ERRO: arquivo .env nao encontrado. Copie o .env.example para .env.")
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
