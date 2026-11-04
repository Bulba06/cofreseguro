import secrets
from flask import Flask, request, jsonify, session, render_template

import cofre
from config import carregar_env

app = Flask(__name__)
# Chave de assinatura dos cookies de sessao (do .env, ou aleatoria se nao houver).
app.secret_key = carregar_env().get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Sessoes abertas: token -> {id_usuario, chave}. A chave derivada fica SO na
# memoria do servidor, nunca no cookie do navegador.
_sessoes = {}


def _sessao_atual():
    token = session.get("token")
    return _sessoes.get(token) if token else None


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


@app.route("/listar")
def listar():
    s = _sessao_atual()
    if not s:
        return jsonify({"erro": "Cofre bloqueado."}), 401
    return jsonify({"entradas": cofre.listar_entradas(s["id_usuario"], s["chave"])})


@app.route("/bloquear", methods=["POST"])
def bloquear():
    token = session.pop("token", None)
    if token:
        _sessoes.pop(token, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
