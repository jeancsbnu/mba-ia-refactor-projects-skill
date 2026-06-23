from database import db
from models.task import Task
from models.user import User
from models.category import Category
from middlewares.error_handler import HttpError
from datetime import datetime, timedelta
from sqlalchemy import func


def summary_report():
    now = datetime.utcnow()
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = dict(
        db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    )
    priority_counts = dict(
        db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    )

    overdue_candidates = Task.query.filter(
        Task.due_date.isnot(None),
        Task.status.notin_(['done', 'cancelled']),
    ).all()
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (now - t.due_date).days,
        }
        for t in overdue_candidates if t.due_date < now
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done', Task.updated_at >= seven_days_ago
    ).count()

    # N+1 fix: eager-load all user tasks in 2 queries
    users = User.query.options(db.joinedload(User.tasks)).all()
    user_stats = []
    for u in users:
        total = len(u.tasks)
        done = sum(1 for t in u.tasks if t.status == 'done')
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'done': status_counts.get('done', 0),
            'cancelled': status_counts.get('cancelled', 0),
        },
        'tasks_by_priority': {
            'critical': priority_counts.get(1, 0),
            'high': priority_counts.get(2, 0),
            'medium': priority_counts.get(3, 0),
            'low': priority_counts.get(4, 0),
            'minimal': priority_counts.get(5, 0),
        },
        'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise HttpError(404, 'Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    status_counts = {}
    overdue = 0
    high_priority = 0
    for t in tasks:
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
        if t.priority <= 2:
            high_priority += 1
        if t.is_overdue():
            overdue += 1

    done = status_counts.get('done', 0)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'cancelled': status_counts.get('cancelled', 0),
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        },
    }
