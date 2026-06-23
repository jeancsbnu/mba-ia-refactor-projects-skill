from database import db
from models.category import Category
from models.task import Task
from middlewares.error_handler import HttpError
import logging

logger = logging.getLogger(__name__)


def list_categories():
    categories = Category.query.all()
    return [
        {**c.to_dict(), 'task_count': Task.query.filter_by(category_id=c.id).count()}
        for c in categories
    ]


def create_category(data):
    if not data:
        raise HttpError(400, 'Dados inválidos')
    name = data.get('name', '').strip()
    if not name:
        raise HttpError(400, 'Nome é obrigatório')
    category = Category(
        name=name,
        description=data.get('description', ''),
        color=data.get('color', '#000000'),
    )
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, data):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise HttpError(404, 'Categoria não encontrada')
    if not data:
        raise HttpError(400, 'Dados inválidos')
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise HttpError(404, 'Categoria não encontrada')
    db.session.delete(cat)
    db.session.commit()
    logger.info("Categoria deletada: id=%s", cat_id)
