"""Cria o banco SQLite usado pela API e chama a população inicial.

    python sqlite_database.py

As tabelas são criadas aqui. Os dados de exemplo ficam no sqlite_populate.py.
"""

import sqlite3
from pathlib import Path

from sqlite_populate import popular_banco

CAMINHO_DO_BANCO = Path(__file__).resolve().parent / "database.db"


CRIAR_TABELA_USER = """
CREATE TABLE user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL
)
"""

CRIAR_TABELA_PREDICTION = """
CREATE TABLE prediction (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    texto      VARCHAR(5000) NOT NULL,
    intencao   VARCHAR(50)   NOT NULL,
    criado_em  TIMESTAMP     NOT NULL,
    owner_id   INTEGER       NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id)
)
"""

CRIAR_INDICE_USERNAME = "CREATE UNIQUE INDEX ix_user_username ON user (username)"
CRIAR_INDICE_OWNER = "CREATE INDEX ix_prediction_owner_id ON prediction (owner_id)"


def criar_banco() -> None:
    """Apaga o banco anterior, recria o schema e insere os dados iniciais."""

    if CAMINHO_DO_BANCO.exists():
        CAMINHO_DO_BANCO.unlink()
        print(f"Banco anterior removido: {CAMINHO_DO_BANCO.name}")

    conexao = sqlite3.connect(CAMINHO_DO_BANCO)
    cursor = conexao.cursor()

    try:
        # O SQLite não valida chave estrangeira por padrão; precisa ligar.
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute(CRIAR_TABELA_USER)
        cursor.execute(CRIAR_TABELA_PREDICTION)
        cursor.execute(CRIAR_INDICE_USERNAME)
        cursor.execute(CRIAR_INDICE_OWNER)
        print("Tabelas 'user' e 'prediction' criadas.")

        popular_banco(conexao)

        conexao.commit()

    finally:
        conexao.close()

    print(f"\nBanco pronto em: {CAMINHO_DO_BANCO}")


if __name__ == "__main__":
    criar_banco()
