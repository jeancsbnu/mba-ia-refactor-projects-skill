import logging

import models.usuario_model as usuario_model

logger = logging.getLogger(__name__)


def listar():
    return usuario_model.listar()


def buscar(usuario_id):
    return usuario_model.buscar_por_id(usuario_id)


def criar(nome, email, senha):
    if not nome or not email or not senha:
        raise ValueError("Nome, email e senha são obrigatórios")
    novo_id = usuario_model.criar(nome, email, senha)
    logger.info(f"Usuário criado: {email}")
    return novo_id


def autenticar(email, senha):
    if not email or not senha:
        raise ValueError("Email e senha são obrigatórios")
    return usuario_model.autenticar(email, senha)
