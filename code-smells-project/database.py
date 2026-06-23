import logging
import sqlite3

import bcrypt
from flask import current_app, g

logger = logging.getLogger(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        _migrate_if_needed()
        _create_tables()
        _seed_if_empty()


def _migrate_if_needed():
    db = get_db()
    cursor = db.execute("PRAGMA table_info(usuarios)")
    cols = {row[1] for row in cursor.fetchall()}
    if "senha" in cols:
        for tbl in ["itens_pedido", "pedidos", "usuarios", "produtos"]:
            db.execute(f"DROP TABLE IF EXISTS {tbl}")
        db.commit()
        logger.info("Schema antigo detectado; tabelas recriadas com nova estrutura.")


def _create_tables():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL,
            estoque INTEGER,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            total REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)
    db.commit()


def _seed_if_empty():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return

    produtos = [
        ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
        ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
        ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
        ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
        ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
        ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
        ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
        ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
        ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
        ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
    ]
    db.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        produtos,
    )

    for nome, email, senha, tipo in [
        ("Admin", "admin@loja.com", "admin123", "admin"),
        ("João Silva", "joao@email.com", "123456", "cliente"),
        ("Maria Santos", "maria@email.com", "senha123", "cliente"),
    ]:
        pw_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode("utf-8")
        db.execute(
            "INSERT INTO usuarios (nome, email, password_hash, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, pw_hash, tipo),
        )

    db.commit()
    logger.info("Banco inicializado com dados de seed.")
