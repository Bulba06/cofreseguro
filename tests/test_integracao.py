# Teste de integracao: roda o fluxo completo do cofre contra o banco de dados
# de verdade (criar -> desbloquear -> adicionar -> listar -> reordenar ->
# remover), provando que a criptografia e o banco conversam certo.
# O teste cria um usuario com nome aleatorio e apaga tudo o que criou no final.
# Precisa do MySQL rodando e do .env configurado; se o banco nao estiver
# disponivel, o teste e pulado (skip) em vez de falhar.
# Rodar com: pytest

import sys
import os
import secrets

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

import db
import cofre


def _banco_disponivel():
    try:
        conexao = db.conectar()
        conexao.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _banco_disponivel(), reason="MySQL nao disponivel")
def test_fluxo_completo_integracao():
    nome = "teste_integ_" + secrets.token_hex(4)
    senha = "SenhaMestra!" + secrets.token_hex(2)
    id_usuario = None
    try:
        # 1. criar usuario
        cofre.criar_usuario(nome, senha)
        assert cofre.usuario_existe(nome)

        # 2. desbloquear: senha errada falha, senha certa abre
        assert cofre.desbloquear(nome, "senha-errada") is None
        sessao = cofre.desbloquear(nome, senha)
        assert sessao is not None
        id_usuario, chave = sessao["id_usuario"], sessao["chave"]

        # 3. adicionar entradas
        cofre.adicionar_entrada(id_usuario, chave, "Email", "senha-email")
        cofre.adicionar_entrada(id_usuario, chave, "Banco", "senha-banco")

        # 4. listar e conferir que as senhas voltam decifradas corretamente
        entradas = cofre.listar_entradas(id_usuario, chave)
        senhas = {e["titulo"]: e["senha"] for e in entradas}
        assert senhas["Email"] == "senha-email"
        assert senhas["Banco"] == "senha-banco"

        # 5. reordenar: mover "Banco" para o topo
        ids = {e["titulo"]: e["id"] for e in entradas}
        cofre.mover_para_topo(id_usuario, ids["Banco"])
        ordem = [e["titulo"] for e in cofre.listar_entradas(id_usuario, chave)]
        assert ordem[0] == "Banco"

        # 6. remover "Email"
        cofre.remover_entrada(id_usuario, ids["Email"])
        titulos = [e["titulo"] for e in cofre.listar_entradas(id_usuario, chave)]
        assert "Email" not in titulos
    finally:
        # limpeza: apaga tudo o que o teste criou
        if id_usuario is not None:
            for e in db.consultar("SELECT id FROM entrada WHERE id_usuario = %s", (id_usuario,)):
                db.executar("DELETE FROM historico_entrada WHERE id_entrada = %s", (e["id"],))
            db.executar("DELETE FROM entrada WHERE id_usuario = %s", (id_usuario,))
            db.executar("DELETE FROM usuario WHERE id = %s", (id_usuario,))
