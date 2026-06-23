import bcrypt

from database import get_db


def _from_row(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_from_row(r) for r in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _from_row(row) if row else None


def criar(nome, email, senha, tipo="cliente"):
    pw_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode("utf-8")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, password_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, pw_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email, senha):
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    if row and bcrypt.checkpw(senha.encode(), row["password_hash"].encode("utf-8")):
        return _from_row(row)
    return None
