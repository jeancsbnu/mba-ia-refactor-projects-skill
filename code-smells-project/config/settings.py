import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

    CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
    STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
    # (limite_faturamento, taxa_desconto)
    REGRAS_DESCONTO = [(10_000, 0.10), (5_000, 0.05), (1_000, 0.02)]


settings = Settings()
