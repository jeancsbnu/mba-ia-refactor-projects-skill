from flask import Blueprint, jsonify, request

import controllers.produto_controller as ctrl

produto_bp = Blueprint("produtos", __name__)


@produto_bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": ctrl.listar(), "sucesso": True}), 200


@produto_bp.get("/produtos/busca")
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria") or None
    preco_min = float(request.args.get("preco_min")) if request.args.get("preco_min") else None
    preco_max = float(request.args.get("preco_max")) if request.args.get("preco_max") else None
    resultados = ctrl.pesquisar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.get("/produtos/<int:produto_id>")
def get_produto(produto_id):
    produto = ctrl.buscar(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


@produto_bp.post("/produtos")
def criar_produto():
    dados = request.get_json() or {}
    nome = dados.get("nome", "")
    descricao = dados.get("descricao", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")
    categoria = dados.get("categoria", "geral")
    if not nome or preco is None or estoque is None:
        return jsonify({"erro": "nome, preco e estoque são obrigatórios", "sucesso": False}), 400
    novo_id = ctrl.criar(nome, descricao, preco, estoque, categoria)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.put("/produtos/<int:produto_id>")
def atualizar_produto(produto_id):
    dados = request.get_json() or {}
    nome = dados.get("nome", "")
    descricao = dados.get("descricao", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")
    categoria = dados.get("categoria", "geral")
    if not nome or preco is None or estoque is None:
        return jsonify({"erro": "nome, preco e estoque são obrigatórios", "sucesso": False}), 400
    resultado = ctrl.atualizar(produto_id, nome, descricao, preco, estoque, categoria)
    if resultado is None:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.delete("/produtos/<int:produto_id>")
def deletar_produto(produto_id):
    resultado = ctrl.deletar(produto_id)
    if resultado is None:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
