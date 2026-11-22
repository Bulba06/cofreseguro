"""
Gera um certificado TLS autoassinado para rodar o CofreSeguro em HTTPS.

Uso:
    python gerar_cert.py

Cria certs/cert.pem e certs/key.pem (validos por 365 dias, CN=localhost).
O certificado e a chave NAO sobem para o GitHub (estao no .gitignore).
Por ser autoassinado, o navegador mostra um aviso na primeira vez (normal
em ambiente de desenvolvimento) - basta aceitar para continuar.
"""
import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

os.makedirs("certs", exist_ok=True)

# Chave privada RSA de 2048 bits.
chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)

nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
agora = datetime.datetime.now(datetime.timezone.utc)
cert = (
    x509.CertificateBuilder()
    .subject_name(nome)
    .issuer_name(nome)
    .public_key(chave.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(agora)
    .not_valid_after(agora + datetime.timedelta(days=365))
    .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
    .sign(chave, hashes.SHA256())
)

with open("certs/key.pem", "wb") as f:
    f.write(chave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))
with open("certs/cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Certificado gerado em certs/cert.pem e certs/key.pem (CN=localhost, 365 dias).")
