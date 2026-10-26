import secrets
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Gera a chave de 32 bytes do cofre a partir da senha-mestra e de um salt,
# usando Argon2id (parametros do RFC 9106). A senha nunca e armazenada.
def derivar_chave(senha: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=senha.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID,
    )


# Gera um salt aleatorio de 16 bytes, um para cada cofre.
def gerar_salt() -> bytes:
    return secrets.token_bytes(16)


# Cifra um texto com AES-256-GCM. Devolve o nonce + o texto cifrado (que ja
# carrega a tag de autenticacao). O nonce e aleatorio e unico a cada chamada.
def cifrar(chave: bytes, texto: str) -> bytes:
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(chave)
    cifrado = aesgcm.encrypt(nonce, texto.encode(), None)
    return nonce + cifrado


# Decifra um dado gerado por cifrar(). Separa o nonce (12 bytes) do resto e usa
# a tag para garantir que o dado nao foi adulterado; se foi, levanta erro.
def decifrar(chave: bytes, dado: bytes) -> str:
    nonce = dado[:12]
    cifrado = dado[12:]
    aesgcm = AESGCM(chave)
    texto = aesgcm.decrypt(nonce, cifrado, None)
    return texto.decode()
