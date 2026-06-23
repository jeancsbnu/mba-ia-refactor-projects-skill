from database import get_db


def _from_row(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar():
    rows = get_db().execute("SELECT * FROM produtos").fetchall()
    return [_from_row(r) for r in rows]


def buscar_por_id(produto_id):
    row = get_db().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _from_row(row) if row else None


def pesquisar(termo="", categoria=None, preco_min=None, preco_max=None):
    conditions, params = ["1=1"], []
    if termo:
        conditions.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        conditions.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        conditions.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        conditions.append("preco <= ?")
        params.append(preco_max)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(conditions)
    return [_from_row(r) for r in get_db().execute(sql, params).fetchall()]


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
