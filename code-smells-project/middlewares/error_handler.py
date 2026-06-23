import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class HttpError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def register_error_handlers(app):
    # HTTP exceptions from werkzeug (404, 405, etc.) must be registered first
    # so they take priority over the generic Exception handler in Flask 3.x
    @app.errorhandler(HTTPException)
    def _werkzeug(e):
        return jsonify({"erro": e.description, "sucesso": False}), e.code

    @app.errorhandler(HttpError)
    def _http(e):
        return jsonify({"erro": str(e), "sucesso": False}), e.status

    @app.errorhandler(ValueError)
    def _value(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(Exception)
    def _unexpected(e):
        if isinstance(e, HTTPException):
            return jsonify({"erro": e.description, "sucesso": False}), e.code
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
