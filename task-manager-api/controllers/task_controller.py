from database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.error_handler import HttpError
from datetime import datetime
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


def _task_to_dict(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks():
    tasks = Task.query.options(
        db.joinedload(Task.user),
        db.joinedload(Task.category),
    ).all()
    return [_task_to_dict(t) for t in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise HttpError(404, 'Task não encontrada')
    return _task_to_dict(task)


def create_task(data):
    if not data:
        raise HttpError(400, 'Dados inválidos')
    title = data.get('title', '').strip()
    if not title:
        raise HttpError(400, 'Título é obrigatório')
    if len(title) < 3 or len(title) > 200:
        raise HttpError(400, 'Título deve ter entre 3 e 200 caracteres')

    status = data.get('status', 'pending')
    if status not in ['pending', 'in_progress', 'done', 'cancelled']:
        raise HttpError(400, 'Status inválido')

    priority = data.get('priority', 3)
    if not isinstance(priority, int) or priority < 1 or priority > 5:
        raise HttpError(400, 'Prioridade deve ser entre 1 e 5')

    user_id = data.get('user_id')
    if user_id and not db.session.get(User, user_id):
        raise HttpError(404, 'Usuário não encontrado')

    category_id = data.get('category_id')
    if category_id and not db.session.get(Category, category_id):
        raise HttpError(404, 'Categoria não encontrada')

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
    )

    due_date = data.get('due_date')
    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            raise HttpError(400, 'Formato de data inválido. Use YYYY-MM-DD')

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: id=%s title=%s", task.id, task.title)
    return task.to_dict()


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise HttpError(404, 'Task não encontrada')
    if not data:
        raise HttpError(400, 'Dados inválidos')

    if 'title' in data:
        title = data['title'].strip()
        if len(title) < 3 or len(title) > 200:
            raise HttpError(400, 'Título deve ter entre 3 e 200 caracteres')
        task.title = title

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in ['pending', 'in_progress', 'done', 'cancelled']:
            raise HttpError(400, 'Status inválido')
        task.status = data['status']

    if 'priority' in data:
        p = data['priority']
        if not isinstance(p, int) or p < 1 or p > 5:
            raise HttpError(400, 'Prioridade deve ser entre 1 e 5')
        task.priority = p

    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            raise HttpError(404, 'Usuário não encontrado')
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            raise HttpError(404, 'Categoria não encontrada')
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                raise HttpError(400, 'Formato de data inválido. Use YYYY-MM-DD')
        else:
            task.due_date = None

    if 'tags' in data:
        tags = data['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    task.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info("Task atualizada: id=%s", task.id)
    return task.to_dict()


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise HttpError(404, 'Task não encontrada')
    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: id=%s", task_id)


def search_tasks(args):
    query = Task.query
    if args.get('q'):
        q = args['q']
        query = query.filter(
            db.or_(Task.title.like(f'%{q}%'), Task.description.like(f'%{q}%'))
        )
    if args.get('status'):
        query = query.filter(Task.status == args['status'])
    if args.get('priority'):
        query = query.filter(Task.priority == int(args['priority']))
    if args.get('user_id'):
        query = query.filter(Task.user_id == int(args['user_id']))
    return [t.to_dict() for t in query.all()]


def task_stats():
    total = Task.query.count()
    status_counts = dict(
        db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    )
    overdue_count = sum(
        1 for t in Task.query.filter(
            Task.due_date.isnot(None),
            Task.status.notin_(['done', 'cancelled']),
        ).all()
        if t.is_overdue()
    )
    done = status_counts.get('done', 0)
    return {
        'total': total,
        'pending': status_counts.get('pending', 0),
        'in_progress': status_counts.get('in_progress', 0),
        'done': done,
        'cancelled': status_counts.get('cancelled', 0),
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
