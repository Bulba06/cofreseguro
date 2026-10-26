# Diário de decisões — CofreSeguro

Anotações feitas durante o desenvolvimento, para alimentar o documento do
protótipo e o plano de testes da Entrega 2. Atualizar a cada parte concluída.

---

## O que já funciona

- Núcleo de criptografia (arquivo `crypto.py`):
  - Derivação da chave do cofre a partir da senha-mestra (Argon2id)
  - Geração de salt aleatório por cofre
  - Cifragem e decifragem autenticada dos dados (AES-256-GCM)

## O que está pendente

- Banco de dados (tabelas + triggers)
- Operações do cofre (criar, desbloquear, adicionar, listar)
- API e interface web
- Testes automatizados (incluindo os vetores oficiais NIST / RFC 9106)

---

## Decisões de projeto

### Derivação de chave — Argon2id
- A senha-mestra digitada pelo usuário não é usada direto como chave.
  Ela passa pelo Argon2id, que gera uma chave de tamanho fixo (32 bytes).
- Argon2id foi escolhido por ser o algoritmo recomendado atualmente (RFC 9106):
  é lento e pesado de memória de propósito, o que encarece ataques de força bruta.
- Parâmetros usados: time_cost=3, memory_cost=64 MiB, parallelism=4 (RFC 9106).

### Salt
- Cada cofre tem um salt aleatório de 16 bytes.
- Serve para que a mesma senha gere chaves diferentes em cofres diferentes,
  o que derruba ataques com tabelas pré-calculadas (rainbow tables).
- O salt não é segredo; será guardado junto do cofre para rederivar a chave.

### Cifragem — AES-256-GCM
- AES-256 no modo GCM: além de cifrar, autentica o dado (gera uma "tag").
- Nonce aleatório de 12 bytes a cada cifragem (tamanho padrão do GCM),
  guardado junto do dado cifrado (não é segredo).
- Se o dado cifrado for adulterado, a decifragem falha em vez de devolver lixo.

### A senha-mestra nunca é armazenada
- Em nenhum momento a senha ou a chave derivada são salvas.
- A chave é recalculada a partir da senha + salt toda vez que o cofre é aberto.

---

## Evidências de teste (prints/resultados)

- Derivação de chave: `derivar_chave()` retorna 32 bytes (256 bits). OK
- (adicionar aqui os resultados do salt e do round-trip cifra/decifra)
