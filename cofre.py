from cryptography.exceptions import InvalidTag

import db
from crypto import derivar_chave, gerar_salt, cifrar, decifrar


# Texto fixo cifrado no cadastro e conferido no desbloqueio, para validar
# a senha-mestra sem nunca armazena-la.
VERIFICADOR_TEXTO = "cofre-ok"


def criar_usuario(nome_usuario, senha_mestra):
    """Cria um usuario: gera o salt, deriva a chave e guarda o verificador."""
    salt = gerar_salt()
    chave = derivar_chave(senha_mestra, salt)
    verificador = cifrar(chave, VERIFICADOR_TEXTO)
    return db.executar(
        "INSERT INTO usuario (nome_usuario, salt, verificador) VALUES (%s, %s, %s)",
        (nome_usuario, salt, verificador),
    )


def desbloquear(nome_usuario, senha_mestra):
    """Confere a senha-mestra. Se certa, devolve o id do usuario e a chave
    derivada (usada depois para cifrar/decifrar). Se errada, devolve None."""
    linhas = db.consultar(
        "SELECT id, salt, verificador FROM usuario WHERE nome_usuario = %s",
        (nome_usuario,),
    )
    if not linhas:
        return None  # usuario nao existe
    u = linhas[0]
    chave = derivar_chave(senha_mestra, bytes(u["salt"]))
    try:
        texto = decifrar(chave, bytes(u["verificador"]))
    except InvalidTag:
        return None  # senha errada: a tag nao confere
    if texto != VERIFICADOR_TEXTO:
        return None
    return {"id_usuario": u["id"], "chave": chave}


def adicionar_entrada(id_usuario, chave, titulo, senha,
                      usuario_servico=None, url=None, id_categoria=None):
    """Cifra a senha e guarda a entrada no banco."""
    senha_cifrada = cifrar(chave, senha)
    return db.executar(
        "INSERT INTO entrada (id_usuario, id_categoria, titulo, "
        "usuario_servico, url, senha_cifrada) VALUES (%s, %s, %s, %s, %s, %s)",
        (id_usuario, id_categoria, titulo, usuario_servico, url, senha_cifrada),
    )


def listar_entradas(id_usuario, chave):
    """Lista as entradas do usuario, decifrando a senha de cada uma."""
    linhas = db.consultar(
        "SELECT id, titulo, usuario_servico, url, senha_cifrada "
        "FROM entrada WHERE id_usuario = %s ORDER BY titulo",
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
