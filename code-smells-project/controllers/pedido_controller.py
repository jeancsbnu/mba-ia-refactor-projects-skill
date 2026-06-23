import logging

import models.pedido_model as pedido_model
import models.produto_model as produto_model
from config.settings import settings
from database import get_db

logger = logging.getLogger(__name__)


def listar_todos():
    return pedido_model.listar_todos()


def listar_por_usuario(usuario_id):
    return pedido_model.listar_por_usuario(usuario_id)


def criar(usuario_id, itens):
    if not itens:
        raise ValueError("Pedido deve ter pelo menos 1 item")

    total = 0
    validados = []
    for item in itens:
        produto = produto_model.buscar_por_id(item["produto_id"])
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
        validados.append((item, produto))

    db = get_db()
    try:
        pedido_id = pedido_model.criar(usuario_id, total)
        for item, produto in validados:
            pedido_model.inserir_item(
                pedido_id, item["produto_id"], item["quantidade"], produto["preco"]
            )
            pedido_model.decrementar_estoque(item["produto_id"], item["quantidade"])
        db.commit()
    except Exception:
        db.rollback()
        raise

    logger.info(f"Pedido id={pedido_id} criado para usuario_id={usuario_id} total={total}")
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    if novo_status not in settings.STATUS_PEDIDO_VALIDOS:
        raise ValueError(f"Status inválido. Válidos: {settings.STATUS_PEDIDO_VALIDOS}")
    pedido_model.atualizar_status(pedido_id, novo_status)
    logger.info(f"Pedido id={pedido_id} → {novo_status}")


def relatorio_vendas():
    dados = pedido_model.resumo_vendas()
    faturamento = dados["faturamento"]
    desconto = 0
    for limite, taxa in settings.REGRAS_DESCONTO:
        if faturamento > limite:
            desconto = faturamento * taxa
            break
    por_status = dados["por_status"]
    total = dados["total_pedidos"]
    return {
        "total_pedidos": total,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get("pendente", 0),
        "pedidos_aprovados": por_status.get("aprovado", 0),
        "pedidos_cancelados": por_status.get("cancelado", 0),
        "ticket_medio": round(faturamento / total, 2) if total > 0 else 0,
    }
