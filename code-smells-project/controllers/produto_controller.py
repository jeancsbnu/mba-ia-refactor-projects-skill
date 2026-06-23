import logging

import models.produto_model as produto_model
from config.settings import settings

logger = logging.getLogger(__name__)


def listar():
    return produto_model.listar()


def buscar(produto_id):
    return produto_model.buscar_por_id(produto_id)


def pesquisar(termo="", categoria=None, preco_min=None, preco_max=None):
    return produto_model.pesquisar(termo, categoria, preco_min, preco_max)


def criar(nome, descricao, preco, estoque, categoria):
    if not nome or len(nome) < 2 or len(nome) > 200:
        raise ValueError("Nome deve ter entre 2 e 200 caracteres")
    if preco is None or preco < 0:
        raise ValueError("Preço não pode ser negativo")
    if estoque is None or estoque < 0:
        raise ValueError("Estoque não pode ser negativo")
    if categoria not in settings.CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {settings.CATEGORIAS_VALIDAS}")
    novo_id = produto_model.criar(nome, descricao, preco, estoque, categoria)
    logger.info(f"Produto criado id={novo_id}")
    return novo_id


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    if not produto_model.buscar_por_id(produto_id):
        return None
    if preco is None or preco < 0:
        raise ValueError("Preço não pode ser negativo")
    if estoque is None or estoque < 0:
        raise ValueError("Estoque não pode ser negativo")
    if categoria not in settings.CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {settings.CATEGORIAS_VALIDAS}")
    produto_model.atualizar(produto_id, nome, descricao, preco, estoque, categoria)
    return True


def deletar(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        return None
    produto_model.deletar(produto_id)
    logger.info(f"Produto id={produto_id} deletado")
    return True
