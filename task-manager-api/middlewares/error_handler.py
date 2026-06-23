from flask import jsonify
import logging

logger = logging.getLogger(__name__)


class HttpError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


def register_error_handlers(app):
    @app.errorhandler(HttpError)
    def _http(e):
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(ValueError)
    def _value(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(404)
    def _not_found(e):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def _unexpected(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description}), e.code
        logger.exception("Erro inesperado")
        return jsonify({"error": "Erro interno do servidor"}), 500
