-- ============================================================
-- CofreSeguro - Esquema do banco de dados (6 tabelas)
-- Rodar no MySQL Workbench ou no cliente mysql.
-- Os triggers ficam no arquivo 02_triggers.sql (proxima etapa).
-- ============================================================

CREATE DATABASE IF NOT EXISTS cofreseguro
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cofreseguro;

-- 1. usuario: a conta e os dados necessarios para abrir o cofre.
--    'salt' alimenta o Argon2; 'verificador' e um valor conhecido cifrado,
--    usado para checar a senha-mestra sem nunca armazena-la.
CREATE TABLE usuario (
    id INT NOT NULL AUTO_INCREMENT,
    nome_usuario VARCHAR(50) NOT NULL UNIQUE,
    salt VARBINARY(16) NOT NULL,
    verificador VARBINARY(60) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- 2. categoria: grupos para organizar as entradas (ex: Trabalho, Pessoal).
CREATE TABLE categoria (
    id INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    nome VARCHAR(50) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id)
) ENGINE=InnoDB;

-- 3. entrada: cada credencial guardada. A senha fica SEMPRE cifrada em
--    'senha_cifrada' (nonce + texto cifrado + tag, tudo junto em bytes).
CREATE TABLE entrada (
    id INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_categoria INT NULL,
    titulo VARCHAR(100) NOT NULL,
    usuario_servico VARCHAR(150) NULL,
    url VARCHAR(255) NULL,
    senha_cifrada VARBINARY(255) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id),
    FOREIGN KEY (id_categoria) REFERENCES categoria(id)
) ENGINE=InnoDB;

-- 4. historico_entrada: guarda versoes antigas da senha cifrada. Vai ser
--    preenchida automaticamente por um trigger quando a senha mudar.
CREATE TABLE historico_entrada (
    id INT NOT NULL AUTO_INCREMENT,
    id_entrada INT NOT NULL,
    senha_cifrada VARBINARY(255) NOT NULL,
    trocada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (id_entrada) REFERENCES entrada(id)
) ENGINE=InnoDB;

-- 5. log_auditoria: registro de acoes (quem mexeu em que). Tambem vai ser
--    preenchida por triggers, nao pela aplicacao.
CREATE TABLE log_auditoria (
    id INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NULL,
    acao VARCHAR(20) NOT NULL,
    tabela VARCHAR(50) NOT NULL,
    id_registro INT NULL,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- 6. configuracao: preferencias por usuario (ex: tempo de bloqueio do cofre).
--    A dupla (id_usuario, chave) e unica: cada usuario tem uma config por chave.
CREATE TABLE configuracao (
    id INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    chave VARCHAR(50) NOT NULL,
    valor VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id),
    UNIQUE (id_usuario, chave)
) ENGINE=InnoDB;
