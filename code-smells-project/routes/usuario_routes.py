from flask import Blueprint, jsonify, request

import controllers.usuario_controller as ctrl

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.get("/usuarios")
def listar_usuarios():
    return jsonify({"dados": ctrl.listar(), "sucesso": True}), 200


@usuario_bp.get("/usuarios/<int:usuario_id>")
def get_usuario(usuario_id):
    usuario = ctrl.buscar(usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado", "sucesso": False}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


@usuario_bp.post("/usuarios")
def criar_usuario():
    dados = request.get_json() or {}
    novo_id = ctrl.criar(
        dados.get("nome", ""),
        dados.get("email", ""),
        dados.get("senha", ""),
    )
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


@usuario_bp.post("/login")
def login():
    dados = request.get_json() or {}
    usuario = ctrl.autenticar(dados.get("email", ""), dados.get("senha", ""))
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
