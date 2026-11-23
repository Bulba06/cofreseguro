"""
DAST - analise dinamica leve do CofreSeguro.
Testa o servidor RODANDO (precisa do app no ar). Verifica:
  1. HTTPS e os cabecalhos de seguranca nas respostas;
  2. Protecao das rotas sensiveis (401 sem sessao);
  3. Resistencia a um payload de SQL injection no login.

Uso (em dois terminais, com o venv ativo e o MySQL ligado):
    python app.py          # terminal 1
    python dast_scan.py    # terminal 2
"""
import json
import ssl
import urllib.request
import urllib.error

BASE = "https://localhost:5000"

# Certificado autoassinado (dev): nao validamos a cadeia, so testamos o app.
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

_ok = 0
_falhas = 0


def _req(caminho, metodo="GET", corpo=None):
    data = json.dumps(corpo).encode() if corpo is not None else None
    r = urllib.request.Request(BASE + caminho, data=data, method=metodo)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(r, context=_ctx, timeout=10)
        return resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)


def _check(desc, cond):
    global _ok, _falhas
    print(("  [OK]    " if cond else "  [FALHA] ") + desc)
    if cond:
        _ok += 1
    else:
        _falhas += 1


print("== DAST - CofreSeguro ==\n")

# 1) HTTPS + cabecalhos de seguranca
status, headers = _req("/")
print("1) Servidor e cabecalhos de seguranca (GET /)")
_check("Responde em HTTPS (status %s)" % status, status == 200)
for h, esperado in [
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Content-Security-Policy", None),
    ("Strict-Transport-Security", None),
    ("Cache-Control", "no-store"),
]:
    val = headers.get(h)
    cond = (val is not None) if esperado is None else (val == esperado)
    _check("Header %s%s" % (h, "" if esperado is None else " = " + esperado), cond)

# 2) Rotas protegidas exigem sessao
print("\n2) Rotas protegidas sem sessao (esperado 401)")
for rota, metodo in [("/listar", "GET"), ("/adicionar", "POST"), ("/editar", "POST"),
                     ("/buscar", "POST"), ("/remover", "POST"), ("/mover", "POST")]:
    status, _ = _req(rota, metodo, {} if metodo == "POST" else None)
    _check("%s %s -> %s" % (metodo, rota, status), status == 401)

# 3) Tentativa de SQL injection no login (parametrizadas devem rejeitar)
print("\n3) SQL injection no login (esperado 401, sem erro 500)")
payload = {"nome_usuario": "admin' OR '1'='1", "senha_mestra": "x' OR '1'='1"}
status, _ = _req("/desbloquear", "POST", payload)
_check("Payload de injection rejeitado (status %s)" % status, status == 401)

print("\n== Resultado: %d OK, %d falha(s) ==" % (_ok, _falhas))
