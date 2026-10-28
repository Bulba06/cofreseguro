-- ============================================================
-- CofreSeguro - Triggers (gatilhos automaticos)
-- Rodar DEPOIS do 01_schema.sql, no mesmo banco.
--
-- Auditoria: toda alteracao na tabela 'entrada' e registrada
-- automaticamente em 'log_auditoria', sem depender da aplicacao.
-- Historico: quando a senha de uma entrada muda, a senha antiga
-- e guardada em 'historico_entrada'.
-- ============================================================

USE cofreseguro;

DELIMITER $$

-- 1. Auditoria de insercao: registra quando uma nova entrada e criada.
CREATE TRIGGER tg_entrada_insert_auditoria
AFTER INSERT ON entrada
FOR EACH ROW
BEGIN
    INSERT INTO log_auditoria (id_usuario, acao, tabela, id_registro)
    VALUES (NEW.id_usuario, 'INSERT', 'entrada', NEW.id);
END$$

-- 2. Auditoria de atualizacao: registra quando uma entrada e alterada.
CREATE TRIGGER tg_entrada_update_auditoria
AFTER UPDATE ON entrada
FOR EACH ROW
BEGIN
    INSERT INTO log_auditoria (id_usuario, acao, tabela, id_registro)
    VALUES (NEW.id_usuario, 'UPDATE', 'entrada', NEW.id);
END$$

-- 3. Auditoria de remocao: registra quando uma entrada e apagada.
--    Aqui usamos OLD, porque a linha ja nao existe mais depois do DELETE.
CREATE TRIGGER tg_entrada_delete_auditoria
AFTER DELETE ON entrada
FOR EACH ROW
BEGIN
    INSERT INTO log_auditoria (id_usuario, acao, tabela, id_registro)
    VALUES (OLD.id_usuario, 'DELETE', 'entrada', OLD.id);
END$$

-- 4. Historico da senha: so copia a senha antiga se ela realmente mudou.
CREATE TRIGGER tg_entrada_update_historico
AFTER UPDATE ON entrada
FOR EACH ROW
BEGIN
    IF OLD.senha_cifrada <> NEW.senha_cifrada THEN
        INSERT INTO historico_entrada (id_entrada, senha_cifrada)
        VALUES (OLD.id, OLD.senha_cifrada);
    END IF;
END$$

DELIMITER ;
