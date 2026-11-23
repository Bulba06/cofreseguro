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


import time


def _login(cliente):
    """Injeta uma sessao valida (sem tocar no banco), simulando o cofre aberto."""
    token = "token-de-teste"
    app_module._sessoes[token] = {
        "id_usuario": 1,
        "chave": b"0" * 32,
        "ultima_atividade": time.time(),
    }
    with cliente.session_transaction() as sess:
        sess["token"] = token
    return token


def test_criar_usuario_campos_vazios(cliente):
    r = cliente.post("/criar_usuario", json={})
    assert r.status_code == 400


def test_criar_usuario_duplicado(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "usuario_existe", lambda n: True)
    r = cliente.post("/criar_usuario", json={"nome_usuario": "ana", "senha_mestra": "123"})
    assert r.status_code == 400


def test_criar_usuario_ok(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "usuario_existe", lambda n: False)
    monkeypatch.setattr(app_module.cofre, "criar_usuario", lambda n, s: 1)
    r = cliente.post("/criar_usuario", json={"nome_usuario": "ana", "senha_mestra": "123"})
    assert r.status_code == 200


def test_desbloquear_senha_errada(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "desbloquear", lambda n, s: None)
    r = cliente.post("/desbloquear", json={"nome_usuario": "ana", "senha_mestra": "x"})
    assert r.status_code == 401


def test_desbloquear_ok(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "desbloquear",
                        lambda n, s: {"id_usuario": 1, "chave": b"0" * 32})
    r = cliente.post("/desbloquear", json={"nome_usuario": "ana", "senha_mestra": "123"})
    assert r.status_code == 200


def test_adicionar_autenticado(cliente, monkeypatch):
    chamou = {}
    monkeypatch.setattr(app_module.cofre, "adicionar_entrada",
                        lambda *a, **k: chamou.setdefault("ok", True))
    _login(cliente)
    r = cliente.post("/adicionar", json={"titulo": "Gmail", "senha": "123"})
    assert r.status_code == 200 and chamou.get("ok")


def test_adicionar_sem_titulo(cliente):
    _login(cliente)
    r = cliente.post("/adicionar", json={"senha": "123"})
    assert r.status_code == 400


def test_listar_autenticado(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "listar_entradas",
                        lambda i, c: [{"id": 1, "titulo": "Gmail", "senha": "x",
                                       "usuario_servico": None, "url": None}])
    _login(cliente)
    r = cliente.get("/listar")
    assert r.status_code == 200
    assert r.get_json()["entradas"][0]["titulo"] == "Gmail"


def test_editar_autenticado(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "editar_entrada", lambda *a, **k: None)
    _login(cliente)
    r = cliente.post("/editar", json={"id": 1, "titulo": "Novo"})
    assert r.status_code == 200


def test_editar_sem_titulo(cliente):
    _login(cliente)
    r = cliente.post("/editar", json={"id": 1})
    assert r.status_code == 400


def test_buscar_autenticado(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "buscar_entradas",
                        lambda i, c, t: [{"id": 1, "titulo": "Gmail", "senha": "x",
                                          "usuario_servico": None, "url": None}])
    _login(cliente)
    r = cliente.post("/buscar", json={"termo": "gm"})
    assert r.status_code == 200
    assert len(r.get_json()["entradas"]) == 1


def test_remover_autenticado(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "remover_entrada", lambda *a, **k: None)
    _login(cliente)
    r = cliente.post("/remover", json={"id": 1})
    assert r.status_code == 200


def test_mover_autenticado(cliente, monkeypatch):
    monkeypatch.setattr(app_module.cofre, "mover_para_topo", lambda *a, **k: None)
    monkeypatch.setattr(app_module.cofre, "mover_para_cima", lambda *a, **k: None)
    _login(cliente)
    r = cliente.post("/mover", json={"id": 1, "direcao": "topo"})
    assert r.status_code == 200


def test_bloquear_limpa_sessao(cliente):
    token = _login(cliente)
    r = cliente.post("/bloquear")
    assert r.status_code == 200
    assert token not in app_module._sessoes


def test_timeout_expira_sessao(cliente):
    token = _login(cliente)
    # Força a ultima atividade para antes do limite -> a sessao deve expirar.
    app_module._sessoes[token]["ultima_atividade"] = time.time() - (app_module._TIMEOUT_SEG + 10)
    r = cliente.get("/listar")
    assert r.status_code == 401
