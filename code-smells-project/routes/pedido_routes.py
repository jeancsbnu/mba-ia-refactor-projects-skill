from flask import Blueprint, jsonify, request

import controllers.pedido_controller as ctrl

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.post("/pedidos")
def criar_pedido():
    dados = request.get_json() or {}
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return jsonify({"erro": "usuario_id é obrigatório", "sucesso": False}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item", "sucesso": False}), 400
    resultado = ctrl.criar(usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.get("/pedidos")
def listar_todos_pedidos():
    return jsonify({"dados": ctrl.listar_todos(), "sucesso": True}), 200


@pedido_bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": ctrl.listar_por_usuario(usuario_id), "sucesso": True}), 200


@pedido_bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status_pedido(pedido_id):
    dados = request.get_json() or {}
    ctrl.atualizar_status(pedido_id, dados.get("status", ""))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@pedido_bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": ctrl.relatorio_vendas(), "sucesso": True}), 200
