from argon2.low_level import hash_secret_raw, Type


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
