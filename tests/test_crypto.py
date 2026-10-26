# Testes deterministicos do nucleo de criptografia (crypto.py).
# Rodar com: pytest  (ou: pytest -v  para ver cada teste)

import sys
import os

# permite importar o crypto.py que esta na raiz do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from cryptography.exceptions import InvalidTag
from crypto import derivar_chave, gerar_salt, cifrar, decifrar


# Entrada fixa -> saida conhecida. Com o mesmo salt e a mesma senha, o Argon2id
# sempre gera a mesma chave. Garante que a derivacao nao mudou sem querer.
def test_derivar_chave_valor_conhecido():
    salt = bytes(16)  # 16 bytes zero, valor fixo so para teste
    chave = derivar_chave("senha123", salt)
    esperado = "691767e4b1e7ec83670966450b0b0cb8d1ea0791ec6ec82f52993b175efa8da8"
    assert chave.hex() == esperado


# A chave precisa ter 32 bytes (256 bits) para o AES-256.
def test_derivar_chave_tamanho():
    chave = derivar_chave("qualquer", gerar_salt())
    assert len(chave) == 32


# O salt precisa ter 16 bytes.
def test_gerar_salt_tamanho():
    assert len(gerar_salt()) == 16


# Dois salts gerados em sequencia nao podem ser iguais (precisa ser aleatorio).
def test_gerar_salt_unico():
    assert gerar_salt() != gerar_salt()


# Round-trip: decifrar o que foi cifrado devolve o texto original.
def test_cifrar_decifrar_roundtrip():
    chave = derivar_chave("senha123", gerar_salt())
    original = "minha senha secreta"
    dado = cifrar(chave, original)
    assert decifrar(chave, dado) == original


# Cifrar o mesmo texto duas vezes deve gerar resultados diferentes,
# porque o nonce e aleatorio a cada chamada.
def test_cifrar_nonce_diferente():
    chave = derivar_chave("senha123", gerar_salt())
    d1 = cifrar(chave, "mesmo texto")
    d2 = cifrar(chave, "mesmo texto")
    assert d1 != d2


# Se o dado cifrado for adulterado, a decifragem deve falhar (nao devolver lixo).
def test_decifrar_dado_adulterado():
    chave = derivar_chave("senha123", gerar_salt())
    dado = bytearray(cifrar(chave, "dado importante"))
    dado[-1] ^= 0x01  # troca um bit do ultimo byte
    with pytest.raises(InvalidTag):
        decifrar(chave, bytes(dado))


# Decifrar com a chave errada (senha errada) deve falhar.
def test_decifrar_chave_errada():
    dado = cifrar(derivar_chave("senha_certa", gerar_salt()), "segredo")
    chave_errada = derivar_chave("senha_errada", gerar_salt())
    with pytest.raises(InvalidTag):
        decifrar(chave_errada, dado)
