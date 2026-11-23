import os
import secrets
import time
from flask import Flask, request, jsonify, session, render_template

import cofre
from config import carregar_env

app = Flask(__name__)
_env_inicial = carregar_env()
# Chave de assinatura dos cookies de sessao (do .env, ou aleatoria se nao houver).
app.secret_key = _env_inicial.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Tempo maximo de inatividade antes de bloquear o cofre (minutos, do .env).
_TIMEOUT_SEG = int(_env_inicial.get("SESSION_TIMEOUT_MIN", "15")) * 60

# Sessoes abertas: token -> {id_usuario, chave, ultima_atividade}. A chave
# derivada fica SO na memoria do servidor, nunca no cookie do navegador.
_sessoes = {}


def _sessao_atual():
    token = session.get("token")
    if not token:
        return None
    s = _sessoes.get(token)
    if not s:
        return None
    # Expira a sessao se passou do tempo de inatividade (bloqueia o cofre).
    if time.time() - s.get("ultima_atividade", 0) > _TIMEOUT_SEG:
        _sessoes.pop(token, None)
        session.pop("token", None)
        return None
    # Atividade valida: renova a janela de inatividade.
    s["ultima_atividade"] = time.time()
    return s


@app.after_request
def aplicar_headers_seguranca(resposta):
    # Cabecalhos de seguranca aplicados a TODAS as respostas.
    resposta.headers["X-Content-Type-Options"] = "nosniff"   # impede MIME sniffing
    resposta.headers["X-Frame-Options"] = "DENY"             # impede clickjacking
    resposta.headers["Referrer-Policy"] = "no-referrer"
    resposta.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # CSP: so carrega recursos da propria origem (inline liberado por ora,
    # pois o prototipo usa JS embutido no index.html).
    resposta.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'"
    )
    # HSTS: instrui o navegador a so usar HTTPS (efetivo quando servido por TLS).
    resposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Nao guardar respostas do cofre em cache (contem senhas decifradas).
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/criar_usuario", methods=["POST"])
def criar_usuario():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome_usuario") or "").strip()
    senha = dados.get("senha_mestra") or ""
    if not nome or not senha:
        return jsonify({"erro": "Preencha usuário e senha-mestra."}), 400
    if cofre.usuario_existe(nome):
        return jsonify({"erro": "Já existe um usuário com esse nome. Tente outro."}), 400
    try:
        cofre.criar_usuario(nome, senha)
    except Exception:
        return jsonify({"erro": "Não foi possível criar o cofre. Tente novamente."}), 400
    return jsonify({"ok": True})


@app.route("/desbloquear", methods=["POST"])
def desbloquear():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome_usuario") or "").strip()
    senha = dados.get("senha_mestra") or ""
    sessao = cofre.desbloquear(nome, senha)
    if not sessao:
        return jsonify({"erro": "Usuário ou senha-mestra inválidos."}), 401
    sessao["ultima_atividade"] = time.time()
    token = secrets.token_hex(16)
    _sessoes[token] = sessao
    session["token"] = token
    return jsonify({"ok": True})


@app.route("/adicionar", methods=["POST"])
def adicionar():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    dados = request.get_json(silent=True) or {}
    titulo = (dados.get("titulo") or "").strip()
    senha = dados.get("senha") or ""
    if not titulo or not senha:
        return jsonify({"erro": "Preencha título e senha."}), 400
    cofre.adicionar_entrada(
        s["id_usuario"], s["chave"], titulo, senha,
        usuario_servico=(dados.get("usuario_servico") or "").strip() or None,
        url=(dados.get("url") or "").strip() or None,
    )
    return jsonify({"ok": True})


@app.route("/editar", methods=["POST"])
def editar():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    dados = request.get_json(silent=True) or {}
    id_entrada = dados.get("id")
    titulo = (dados.get("titulo") or "").strip()
    if not id_entrada or not titulo:
        return jsonify({"erro": "Preencha o titulo."}), 400
    cofre.editar_entrada(
        s["id_usuario"], id_entrada, titulo,
        usuario_servico=(dados.get("usuario_servico") or "").strip() or None,
        url=(dados.get("url") or "").strip() or None,
        chave=s["chave"],
        nova_senha=(dados.get("senha") or "") or None,
    )
    return jsonify({"ok": True})


@app.route("/listar")
def listar():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    return jsonify({"entradas": cofre.listar_entradas(s["id_usuario"], s["chave"])})


@app.route("/buscar", methods=["POST"])
def buscar():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    dados = request.get_json(silent=True) or {}
    termo = (dados.get("termo") or "").strip()
    entradas = cofre.buscar_entradas(s["id_usuario"], s["chave"], termo)
    return jsonify({"entradas": entradas})


@app.route("/mover", methods=["POST"])
def mover():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    dados = request.get_json(silent=True) or {}
    id_entrada = dados.get("id")
    direcao = dados.get("direcao")
    if not id_entrada:
        return jsonify({"erro": "Entrada inválida."}), 400
    if direcao == "topo":
        cofre.mover_para_topo(s["id_usuario"], id_entrada)
    else:
        cofre.mover_para_cima(s["id_usuario"], id_entrada)
    return jsonify({"ok": True})


@app.route("/remover", methods=["POST"])
def remover():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    dados = request.get_json(silent=True) or {}
    id_entrada = dados.get("id")
    if not id_entrada:
        return jsonify({"erro": "Entrada inválida."}), 400
    cofre.remover_entrada(s["id_usuario"], id_entrada)
    return jsonify({"ok": True})


@app.route("/bloquear", methods=["POST"])
def bloquear():
    token = session.pop("token", None)
    if token:
        _sessoes.pop(token, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    # debug controlado pelo .env; padrao False. Rodar com debug=True expoe o
    # console do Werkzeug, que permite execucao de codigo arbitrario (CWE-94).
    env = carregar_env()
    debug = env.get("FLASK_DEBUG", "false").strip().lower() == "true"

    # TLS/HTTPS: se houver certificado, sobe em HTTPS; senao, cai para HTTP
    # (apenas desenvolvimento). Gere o certificado com: python gerar_cert.py
    cert = env.get("TLS_CERT", "certs/cert.pem")
    chave_tls = env.get("TLS_KEY", "certs/key.pem")
    if os.path.exists(cert) and os.path.exists(chave_tls):
        print("Rodando em HTTPS: https://localhost:5000")
        app.run(debug=debug, port=5000, ssl_context=(cert, chave_tls))
    else:
        print("AVISO: certificado nao encontrado, rodando em HTTP (dev).")
        print("Para HTTPS, rode antes: python gerar_cert.py")
        app.run(debug=debug, port=5000)
