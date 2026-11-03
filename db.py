import mysql.connector
from config import carregar_env


def conectar():
    """Abre uma conexao com o banco cofreseguro usando as credenciais do .env."""
    env = carregar_env()
    return mysql.connector.connect(
        host=env.get("DB_HOST", "localhost"),
        port=int(env.get("DB_PORT", 3306)),
        user=env.get("DB_USER", "cofre_app"),
        password=env.get("DB_PASSWORD", ""),
        database=env.get("DB_NAME", "cofreseguro"),
    )


def executar(sql, params=()):
    """Executa um comando que altera dados (INSERT/UPDATE/DELETE).
    Usa consulta parametrizada (os valores vao separados do SQL, o que
    evita SQL injection). Devolve o id gerado, quando houver."""
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(sql, params)
    conexao.commit()
    id_gerado = cursor.lastrowid
    cursor.close()
    conexao.close()
    return id_gerado


def consultar(sql, params=()):
    """Executa uma consulta (SELECT) e devolve as linhas como dicionarios.
    Tambem usa consulta parametrizada."""
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(sql, params)
    linhas = cursor.fetchall()
    cursor.close()
    conexao.close()
    return linhas
