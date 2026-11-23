# Testes das rotas Flask. Nao precisam de banco de dados: verificam o controle
# de acesso (rotas protegidas exigem sessao) e os cabecalhos de seguranca.
# Rodar com: pytest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import app as app_module


@pytest.fixture
def cliente():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_pagina_inicial_responde(cliente):
    # A pagina de login deve carregar sem precisar de sessao.
    r = cliente.get("/")
    assert r.status_code == 200


def test_headers_de_seguranca(cliente):
    # Toda resposta deve trazer os cabecalhos de seguranca.
    r = cliente.get("/")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Cache-Control") == "no-store"
    assert "Content-Security-Policy" in r.headers
    assert "Strict-Transport-Security" in r.headers


@pytest.mark.parametrize("rota,metodo", [
    ("/listar", "get"),
    ("/adicionar", "post"),
    ("/editar", "post"),
    ("/buscar", "post"),
    ("/remover", "post"),
    ("/mover", "post"),
])
def test_rotas_protegidas_exigem_sessao(cliente, rota, metodo):
    # Sem desbloquear o cofre, as rotas sensiveis devem responder 401.
    resp = getattr(cliente, metodo)(rota, json={})
    assert resp.status_code == 401
