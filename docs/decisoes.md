# Diário de decisões — CofreSeguro

Anotações feitas durante o desenvolvimento, para alimentar o documento do
protótipo e o plano de testes da Entrega 2. Atualizar a cada parte concluída.

---

## O que já funciona

- Núcleo de criptografia (arquivo `crypto.py`):
  - Derivação da chave do cofre a partir da senha-mestra (Argon2id)
  - Geração de salt aleatório por cofre
  - Cifragem e decifragem autenticada dos dados (AES-256-GCM)
- Banco de dados (MySQL):
  - 6 tabelas com chaves estrangeiras (usuario, categoria, entrada,
    historico_entrada, log_auditoria, configuracao)
  - 4 triggers (auditoria de insert/update/delete e histórico de senha)
  - Script `setup_db.py` que cria o banco e aplica schema e triggers
  - Usuário de aplicação dedicado (cofre_app), sem usar o root
- Camada de acesso ao banco (`db.py` + `config.py`) com consultas parametrizadas

## O que está pendente

- Operações do cofre (criar, desbloquear, adicionar, listar)
- API e interface web
- Testes automatizados (incluindo os vetores oficiais NIST / RFC 9106)
- Usuário de aplicação com privilégio mínimo real (só leitura/escrita)

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

### Banco de dados — modelo relacional
- 6 tabelas ligadas por chaves estrangeiras, tudo girando em torno do usuario.
- A senha de cada entrada fica em VARBINARY (bytes cifrados), nunca em texto.
- Rótulos (título, categoria) usam charset utf8mb4 para aceitar acentos.

### Banco de dados — triggers
- Auditoria e histórico ficam no banco via triggers, não na aplicação, para
  garantir que toda alteração seja registrada mesmo que a aplicação falhe ou
  seja burlada.
- O carimbo de data (atualizado_em) usa ON UPDATE CURRENT_TIMESTAMP, sem
  precisar de trigger.

### Banco de dados — usuário dedicado (menor privilégio)
- A aplicação não usa o root. Foi criado um usuário cofre_app com acesso
  apenas ao banco cofreseguro.
- Isso limita o estrago caso a aplicação seja comprometida.
- Como o cofre_app não é super-admin, a criação de triggers exigiu habilitar
  log_bin_trust_function_creators no servidor (prova de que o usuário é mesmo
  restrito).

### Acesso ao banco — consultas parametrizadas (contra SQL injection)
- Todas as consultas separam o comando SQL dos valores (ex: WHERE nome = %s,
  com o valor passado numa lista à parte).
- O driver trata o valor sempre como dado, nunca como comando, então é
  impossível injetar lógica SQL (defesa contra SQL injection, OWASP Top 10).

---

## Evidências de teste (prints/resultados)

- Derivação de chave: `derivar_chave()` retorna 32 bytes (256 bits). OK
- Suíte de 8 testes de criptografia passando (01-testes-crypto.png)
- 6 tabelas criadas no Workbench (02-banco-tabelas.png)
- 4 triggers criados e funcionando (03-triggers-criados.png, 04-trigger-funcionando.png)
- Banco criado automaticamente pelo setup_db.py (05-setup-db.png)
