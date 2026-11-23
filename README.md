# 🔐 CofreSeguro

Gerenciador de senhas desenvolvido para o **Projeto Integrador 4 — Cibersegurança em Programação Segura** (PUC-Campinas).

As credenciais são guardadas **cifradas**, protegidas por uma **senha-mestra que nunca é armazenada** em lugar nenhum. Sem ela, o conteúdo do cofre é apenas um conjunto de bytes ilegíveis.

---

## 👥 Integrantes

- Dimas Marcondes Moreira da Silva — 24024188
- Eduardo da Silva Carneiro Malta — 24025488
- Gabriel James Fuzinatto — 25009884
- Guilherme Orlando Lucredi Menezes Leal — 25014634
- Murilo Dias Bartkevicius — 24004162

---

## 🧩 Tecnologias

- **Python 3.10+** com **Flask** (API e interface web)
- **MySQL 8.4 LTS** (banco de dados)
- **cryptography** (AES-256-GCM) e **argon2-cffi** (Argon2id)

---

## ✨ Funcionalidades

- Criar cofre protegido por senha-mestra
- Desbloquear / bloquear o cofre
- Adicionar, listar, **editar**, **buscar**, reordenar e remover senhas
- Revelar e copiar senhas
- Gerador de senhas fortes
- Bloqueio automático por inatividade (timeout de sessão)

---

## 🔒 Segurança aplicada

- **Senha-mestra nunca armazenada** — vira a chave via Argon2id e só existe na memória durante a sessão
- **Argon2id** (RFC 9106) para derivar a chave (lento e pesado de memória, contra força bruta)
- **Salt** único por cofre (derruba rainbow tables)
- **AES-256-GCM** para cifrar e autenticar os dados (nonce + tag)
- **Verificador** valida o login sem guardar a senha
- **TLS/HTTPS** (certificado autoassinado para desenvolvimento)
- **Cabeçalhos de segurança** (CSP estrito, X-Frame-Options, HSTS, etc.)
- **Timeout de sessão** por inatividade
- **Consultas parametrizadas** (contra SQL injection)
- **Usuário de banco de privilégio mínimo** (`cofre_app`, não o root)
- **Triggers** de auditoria e histórico no próprio banco

---

## 🛠️ Roteiro de instalação (reproduzir em outra máquina)

### Pré-requisitos
- [Python 3.10+](https://www.python.org/downloads/)
- [MySQL 8.4 LTS](https://dev.mysql.com/downloads/) (com MySQL Workbench, opcional)
- [Git](https://git-scm.com/)

### 1. Clonar o repositório
```bash
git clone https://github.com/Bulba06/cofreseguro.git
cd cofreseguro
```

### 2. Criar e ativar o ambiente virtual
```bash
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Preparar o banco de dados (MySQL)
No MySQL Workbench (ou cliente `mysql`), crie o usuário da aplicação e libere a criação de triggers:
```sql
CREATE USER 'cofre_app'@'localhost' IDENTIFIED BY 'sua_senha_aqui';
GRANT ALL PRIVILEGES ON cofreseguro.* TO 'cofre_app'@'localhost';
FLUSH PRIVILEGES;
SET GLOBAL log_bin_trust_function_creators = 1;
```

### 5. Configurar o arquivo `.env`
Copie o modelo e preencha com os seus dados:
```bash
# Windows:
copy .env.example .env
# Linux/Mac:
cp .env.example .env
```
Edite o `.env`:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cofreseguro
DB_USER=cofre_app
DB_PASSWORD=sua_senha_aqui
FLASK_DEBUG=false
SESSION_TIMEOUT_MIN=15
```
> O `.env` tem dados sensíveis e **não sobe para o GitHub** (está no `.gitignore`).

### 6. Criar as tabelas e triggers
```bash
python setup_db.py
```
Isso cria o banco `cofreseguro` com as **6 tabelas** e os **4 triggers** automaticamente.

### 7. Gerar o certificado TLS (HTTPS)
```bash
python gerar_cert.py
```

### 8. Rodar a aplicação
```bash
python app.py
```
Acesse **https://localhost:5000** no navegador.
> Por ser um certificado autoassinado, o navegador mostra um aviso na primeira vez — clique em "Avançado → Continuar". A conexão está criptografada; o aviso é só porque o certificado não vem de uma autoridade certificadora.

---

## 📖 Roteiro de uso

1. **Criar um cofre:** na tela inicial, digite um nome de usuário e uma senha-mestra forte e clique em **Criar cofre**.
   > ⚠️ **Guarde bem a senha-mestra.** Ela não é armazenada e **não há como recuperá-la** — se esquecer, perde o acesso ao cofre (isso é proposital, por segurança).
2. **Desbloquear:** digite usuário e senha-mestra e clique em **Desbloquear**.
3. **Adicionar uma senha:** preencha o título (ex: "Gmail"), o usuário do serviço (opcional) e a senha — ou use **Gerar** para criar uma senha forte. Clique em **Adicionar senha**.
4. **Ver / copiar:** em cada item, use **Mostrar** para revelar e **Copiar** para copiar a senha.
5. **Editar:** clique em **Editar**; os dados carregam no formulário. Deixe o campo senha vazio para manter a senha atual, ou digite uma nova para trocá-la.
6. **Buscar:** use o campo **Buscar** para filtrar por título, usuário ou site.
7. **Reordenar:** use **↑** e **Topo** para organizar a lista.
8. **Remover:** clique em **Remover** (pede confirmação).
9. **Bloquear:** clique em **Bloquear** para fechar o cofre. Ele também se bloqueia sozinho após 15 min de inatividade.

### Dúvidas comuns
- **Esqueci a senha-mestra, e agora?** Não há recuperação, por design. O cofre fica inacessível.
- **O navegador diz "Não seguro".** É por causa do certificado autoassinado (desenvolvimento). A conexão está cifrada.
- **Deu erro de módulo (flask/cryptography).** O ambiente virtual não está ativo — rode o passo 2.
- **Deu "Access denied" no banco.** Verifique usuário/senha no `.env` e se o usuário `cofre_app` foi criado.

---

## 🧪 Testes e análises

```bash
# Testes automatizados (precisa do MySQL ligado para os de integração)
pytest

# Cobertura de testes
pytest --cov=crypto --cov=config --cov=db --cov=cofre --cov=app --cov-report=term-missing

# Análise estática (SAST)
bandit -r . -x ./venv,./tests
pip-audit -r requirements.txt

# Análise dinâmica (DAST) - com o app rodando em outro terminal
python dast_scan.py
```

---

## 📂 Estrutura do projeto

```
cofreseguro/
├── app.py                # API web (Flask) e rotas
├── cofre.py              # Lógica do cofre (criar, desbloquear, CRUD)
├── crypto.py             # Núcleo de criptografia (Argon2id, AES-256-GCM)
├── db.py                 # Acesso ao banco (consultas parametrizadas)
├── config.py             # Leitura do .env
├── setup_db.py           # Cria o banco, tabelas e triggers
├── gerar_cert.py         # Gera o certificado TLS autoassinado
├── dast_scan.py          # Script de análise dinâmica (DAST)
├── requirements.txt      # Dependências
├── db/
│   ├── 01_schema.sql     # 6 tabelas
│   └── 02_triggers.sql   # 4 triggers
├── templates/
│   └── index.html        # Interface web
├── static/
│   ├── style.css         # Estilos
│   └── app.js            # JavaScript da interface
└── tests/                # Testes automatizados
    ├── test_crypto.py
    ├── test_vetores.py
    ├── test_app.py
    └── test_integracao.py
```

---

## 📄 Licença

MIT — veja o arquivo [LICENSE](LICENSE).
