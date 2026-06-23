import logging

from flask import Flask, jsonify

from config.settings import settings
from database import get_db, init_db
from flask_cors import CORS
from middlewares.error_handler import register_error_handlers
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DATABASE"] = settings.DB_PATH
    app.config["DEBUG"] = settings.DEBUG

    CORS(app, origins=settings.CORS_ORIGINS)
    register_error_handlers(app)

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)

    init_db(app)

    @app.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    @app.get("/health")
    def health_check():
        db = get_db()
        produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        return jsonify({
            "status": "ok",
            "database": "connected",
            "versao": "1.0.0",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
        })

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
