"""Popula o banco SQLite usado pela API com os dados iniciais.

O sqlite_database.py já chama este script depois de criar as tabelas. Para
popular de novo um banco que já existe (apaga os dados e insere tudo outra vez):

    python sqlite_populate.py
"""

import sqlite3
from pathlib import Path

from security.password import gerar_hash_de_senha

CAMINHO_DO_BANCO = Path(__file__).resolve().parent / "database.db"


USUARIOS = [
    ("admin", "admin123"),
    ("analista", "analista123"),
]

# Predições divididas entre os dois usuários. A 1 e a 2 são do admin, a 3 é do
# analista - é essa separação que os testes de BOLA usam.
PREDICOES = [
    (
        "Meu produto parou de funcionar depois da última atualização.",
        "Technical issue",
        "admin",
    ),
    (
        "Fui cobrado duas vezes na fatura deste mês e queria entender o motivo.",
        "Billing inquiry",
        "admin",
    ),
    (
        "Gostaria de cancelar minha assinatura a partir do próximo ciclo.",
        "Cancellation request",
        "analista",
    ),
]


def popular_banco(conexao: sqlite3.Connection) -> None:
    """Insere os usuários e as predições de exemplo."""

    cursor = conexao.cursor()

    ids_por_usuario: dict[str, int] = {}
    for username, senha in USUARIOS:
        cursor.execute(
            "INSERT INTO user (username, hashed_password) VALUES (?, ?)",
            (username, gerar_hash_de_senha(senha)),
        )
        ids_por_usuario[username] = cursor.lastrowid
        print(f"Usuário criado: {username} (id={cursor.lastrowid})")

    for texto, intencao, dono in PREDICOES:
        cursor.execute(
            """
            INSERT INTO prediction (texto, intencao, criado_em, owner_id)
            VALUES (?, ?, datetime('now'), ?)
            """,
            (texto, intencao, ids_por_usuario[dono]),
        )
        print(f"Predição {cursor.lastrowid} criada para '{dono}'")


def repopular_banco() -> None:
    """Apaga os dados de um banco já criado e insere tudo de novo."""

    if not CAMINHO_DO_BANCO.exists():
        raise SystemExit(
            "database.db não encontrado. Rode antes: python sqlite_database.py"
        )

    conexao = sqlite3.connect(CAMINHO_DO_BANCO)

    try:
        conexao.execute("PRAGMA foreign_keys = ON")

        # Apaga primeiro as predições, por causa da chave estrangeira, e zera
        # os contadores de id para os registros voltarem a ter id 1, 2 e 3.
        conexao.execute("DELETE FROM prediction")
        conexao.execute("DELETE FROM user")
        conexao.execute("DELETE FROM sqlite_sequence")

        popular_banco(conexao)
        conexao.commit()

    finally:
        conexao.close()

    print(f"\nBanco populado em: {CAMINHO_DO_BANCO}")


if __name__ == "__main__":
    repopular_banco()
