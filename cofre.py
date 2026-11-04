from cryptography.exceptions import InvalidTag

import db
from crypto import derivar_chave, gerar_salt, cifrar, decifrar


# Texto fixo cifrado no cadastro e conferido no desbloqueio, para validar
# a senha-mestra sem nunca armazena-la.
VERIFICADOR_TEXTO = "cofre-ok"


def _normalizar(nome):
    # Nomes de usuario sao sempre tratados em minusculo, para que
    # "Guilherme", "guilherme" e "GUILHERME" sejam a mesma conta.
    return (nome or "").strip().lower()


def usuario_existe(nome_usuario):
    """Diz se ja existe um usuario com esse nome (ignorando maiusculas)."""
    return bool(db.consultar(
        "SELECT id FROM usuario WHERE nome_usuario = %s",
        (_normalizar(nome_usuario),),
    ))


def criar_usuario(nome_usuario, senha_mestra):
    """Cria um usuario: gera o salt, deriva a chave e guarda o verificador."""
    nome_usuario = _normalizar(nome_usuario)
    salt = gerar_salt()
    chave = derivar_chave(senha_mestra, salt)
    verificador = cifrar(chave, VERIFICADOR_TEXTO)
    return db.executar(
        "INSERT INTO usuario (nome_usuario, salt, verificador) VALUES (%s, %s, %s)",
        (nome_usuario, salt, verificador),
    )


def desbloquear(nome_usuario, senha_mestra):
    """Confere a senha-mestra. Se certa, devolve o id do usuario e a chave
    derivada. Se errada, devolve None."""
    linhas = db.consultar(
        "SELECT id, salt, verificador FROM usuario WHERE nome_usuario = %s",
        (_normalizar(nome_usuario),),
    )
    if not linhas:
        return None
    u = linhas[0]
    chave = derivar_chave(senha_mestra, bytes(u["salt"]))
    try:
        texto = decifrar(chave, bytes(u["verificador"]))
    except InvalidTag:
        return None
    if texto != VERIFICADOR_TEXTO:
        return None
    return {"id_usuario": u["id"], "chave": chave}


def adicionar_entrada(id_usuario, chave, titulo, senha,
                      usuario_servico=None, url=None, id_categoria=None):
    """Cifra a senha e guarda a entrada no fim da lista."""
    senha_cifrada = cifrar(chave, senha)
    # nova entrada vai para o fim da lista (maior ordem atual + 1)
    r = db.consultar(
        "SELECT COALESCE(MAX(ordem), 0) AS m FROM entrada WHERE id_usuario = %s",
        (id_usuario,),
    )
    proxima = (r[0]["m"] or 0) + 1
    return db.executar(
        "INSERT INTO entrada (id_usuario, id_categoria, titulo, usuario_servico, "
        "url, senha_cifrada, ordem) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (id_usuario, id_categoria, titulo, usuario_servico, url, senha_cifrada, proxima),
    )


def mover_para_cima(id_usuario, id_entrada):
    """Troca a entrada de lugar com a que esta logo acima dela."""
    atual = db.consultar(
        "SELECT id, ordem FROM entrada WHERE id = %s AND id_usuario = %s",
        (id_entrada, id_usuario),
    )
    if not atual:
        return
    ordem_atual = atual[0]["ordem"]
    acima = db.consultar(
        "SELECT id, ordem FROM entrada WHERE id_usuario = %s AND ordem < %s "
        "ORDER BY ordem DESC LIMIT 1",
        (id_usuario, ordem_atual),
    )
    if not acima:
        return  # ja esta no topo
    db.executar("UPDATE entrada SET ordem = %s WHERE id = %s", (acima[0]["ordem"], id_entrada))
    db.executar("UPDATE entrada SET ordem = %s WHERE id = %s", (ordem_atual, acima[0]["id"]))


def mover_para_topo(id_usuario, id_entrada):
    """Coloca a entrada no topo da lista."""
    dono = db.consultar(
        "SELECT id FROM entrada WHERE id = %s AND id_usuario = %s",
        (id_entrada, id_usuario),
    )
    if not dono:
        return
    r = db.consultar(
        "SELECT COALESCE(MIN(ordem), 0) AS m FROM entrada WHERE id_usuario = %s",
        (id_usuario,),
    )
    nova = (r[0]["m"] or 0) - 1
    db.executar("UPDATE entrada SET ordem = %s WHERE id = %s", (nova, id_entrada))


def listar_entradas(id_usuario, chave):
    """Lista as entradas na ordem definida pelo usuario, decifrando as senhas."""
    linhas = db.consultar(
        "SELECT id, titulo, usuario_servico, url, senha_cifrada FROM entrada "
        "WHERE id_usuario = %s ORDER BY ordem, id",
        (id_usuario,),
    )
    resultado = []
    for linha in linhas:
        resultado.append({
            "id": linha["id"],
            "titulo": linha["titulo"],
            "usuario_servico": linha["usuario_servico"],
            "url": linha["url"],
            "senha": decifrar(chave, bytes(linha["senha_cifrada"])),
        })
    return resultado
