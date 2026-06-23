from database import get_db

_JOIN_SQL = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, pr.nome AS produto_nome,
           ip.quantidade, ip.preco_unitario
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
    {where}
    ORDER BY p.id
"""


def _agrupar(rows):
    pedidos: dict = {}
    for r in rows:
        pid = r["id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": r["id"],
                "usuario_id": r["usuario_id"],
                "status": r["status"],
                "total": r["total"],
                "criado_em": r["criado_em"],
                "itens": [],
            }
        if r["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": r["produto_id"],
                "produto_nome": r["produto_nome"] or "Desconhecido",
                "quantidade": r["quantidade"],
                "preco_unitario": r["preco_unitario"],
            })
    return list(pedidos.values())


def listar_todos():
    rows = get_db().execute(_JOIN_SQL.format(where="")).fetchall()
    return _agrupar(rows)


def listar_por_usuario(usuario_id):
    sql = _JOIN_SQL.format(where="WHERE p.usuario_id = ?")
    rows = get_db().execute(sql, (usuario_id,)).fetchall()
    return _agrupar(rows)


def criar(usuario_id, total):
    cursor = get_db().execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    return cursor.lastrowid


def inserir_item(pedido_id, produto_id, quantidade, preco_unitario):
    get_db().execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def decrementar_estoque(produto_id, quantidade):
    get_db().execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        (quantidade, produto_id),
    )


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def resumo_vendas():
    db = get_db()
    total_pedidos, faturamento = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos"
    ).fetchone()
    por_status = {
        row[0]: row[1]
        for row in db.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall()
    }
    return {"total_pedidos": total_pedidos, "faturamento": faturamento, "por_status": por_status}
