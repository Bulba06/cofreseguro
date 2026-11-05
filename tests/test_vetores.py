# Testes de validacao contra vetores conhecidos/oficiais.
#   - AES-256-GCM: vetores oficiais do NIST (usados na validacao CAVP do GCM).
#   - Argon2id: teste de resposta conhecida com os parametros do RFC 9106.
# Rodar com: pytest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from crypto import derivar_chave


def _h(s):
    return bytes.fromhex(s.replace(" ", ""))


# Vetores oficiais do GCM para AES-256.
# Formato: (chave, nonce/IV, texto_claro, AAD, texto_cifrado_esperado, tag_esperada)
VETORES_GCM = [
    ("00" * 32, "00" * 12, "", "",
     "", "530f8afbc74536b9a963b4f1c4cb738b"),
    ("00" * 32, "00" * 12, "00" * 16, "",
     "cea7403d4d606b6e074ec5d3baf39d18", "d0d1c8a799996bf0265b98b5d48ab919"),
    ("feffe9928665731c6d6a8f9467308308feffe9928665731c6d6a8f9467308308",
     "cafebabefacedbaddecaf888",
     "d9313225f88406e5a55909c5aff5269a86a7a9531534f7da2e4c303d8a318a72"
     "1c3c0c95956809532fcf0e2449a6b525b16aedf5aa0de657ba637b39",
     "feedfacedeadbeeffeedfacedeadbeefabaddad2",
     "522dc1f099567d07f47f37a32a84427d643a8cdcbfe5c0c97598a2bd2555d1aa"
     "8cb08e48590dbb3da7b08b1056828838c5f61e6393ba7a0abcc9f662",
     "76fc6ece0f4e1768cddf8853bb2d551b"),
]


def test_aes_gcm_vetores_oficiais_nist():
    # Para cada vetor do NIST, cifrar com a chave/nonce/AAD dados deve produzir
    # exatamente o texto cifrado e a tag esperados. Prova que o AES-256-GCM
    # esta correto segundo o padrao.
    for chave, iv, pt, aad, ct_esp, tag_esp in VETORES_GCM:
        chave, iv, pt, aad = _h(chave), _h(iv), _h(pt), _h(aad)
        saida = AESGCM(chave).encrypt(iv, pt, aad if aad else None)
        texto_cifrado, tag = saida[:-16], saida[-16:]
        assert texto_cifrado.hex() == ct_esp.replace(" ", "")
        assert tag.hex() == tag_esp.replace(" ", "")


def test_argon2id_resposta_conhecida_rfc9106():
    # Com a mesma entrada e os mesmos parametros (RFC 9106), o Argon2id sempre
    # gera a mesma chave. Garante que o algoritmo e os parametros nao mudaram.
    salt = bytes.fromhex("02" * 16)
    chave = derivar_chave("senha-de-teste", salt)
    esperado = "9fa8538d6b27c18b651259ada23f7a28630007f3b6f6dbac92c36be23d28ec53"
    assert chave.hex() == esperado
