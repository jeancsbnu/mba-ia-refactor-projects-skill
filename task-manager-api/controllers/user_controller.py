from database import db
from models.user import User
from models.task import Task
from middlewares.error_handler import HttpError
import re
import secrets
import logging

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def list_users():
    users = User.query.all()
    return [{**u.to_dict(), 'task_count': len(u.tasks)} for u in users]


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise HttpError(404, 'Usuário não encontrado')
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    if not data:
        raise HttpError(400, 'Dados inválidos')
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')

    if not name:
        raise HttpError(400, 'Nome é obrigatório')
    if not email:
        raise HttpError(400, 'Email é obrigatório')
    if not password:
        raise HttpError(400, 'Senha é obrigatória')
    if not _EMAIL_RE.match(email):
        raise HttpError(400, 'Email inválido')
    if len(password) < 4:
        raise HttpError(400, 'Senha deve ter no mínimo 4 caracteres')
    if role not in ['user', 'admin', 'manager']:
        raise HttpError(400, 'Role inválido')
    if User.query.filter_by(email=email).first():
        raise HttpError(409, 'Email já cadastrado')

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: id=%s email=%s", user.id, user.email)
    return user.to_dict()


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise HttpError(404, 'Usuário não encontrado')
    if not data:
        raise HttpError(400, 'Dados inválidos')

    if 'name' in data:
        user.name = data['name'].strip()

    if 'email' in data:
        if not _EMAIL_RE.match(data['email']):
            raise HttpError(400, 'Email inválido')
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            raise HttpError(409, 'Email já cadastrado')
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < 4:
            raise HttpError(400, 'Senha deve ter no mínimo 4 caracteres')
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in ['user', 'admin', 'manager']:
            raise HttpError(400, 'Role inválido')
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise HttpError(404, 'Usuário não encontrado')
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: id=%s", user_id)


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise HttpError(404, 'Usuário não encontrado')
    tasks = Task.query.filter_by(user_id=user_id).all()
    return [{**t.to_dict(), 'overdue': t.is_overdue()} for t in tasks]


def login(data):
    if not data:
        raise HttpError(400, 'Dados inválidos')
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not email or not password:
        raise HttpError(400, 'Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise HttpError(401, 'Credenciais inválidas')
    if not user.active:
        raise HttpError(403, 'Usuário inativo')

    token = secrets.token_hex(32)
    return {'message': 'Login realizado com sucesso', 'user': user.to_dict(), 'token': token}
