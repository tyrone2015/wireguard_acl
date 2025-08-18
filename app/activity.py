from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models import Activity

router = APIRouter()


def log_activity(message: str, type: str = 'info'):
    """记录一条活动到数据库（函数内导入 SessionLocal，避免循环导入）"""
    from app.main import SessionLocal
    session = SessionLocal()
    act = Activity(type=type, message=message)
    session.add(act)
    session.commit()
    session.close()


@router.get('/activities')
def get_activities(limit: int = 20):
    """返回最近的活动，按时间倒序（函数内导入 SessionLocal，避免循环导入）"""
    from app.main import SessionLocal
    session = SessionLocal()
    acts = session.query(Activity).order_by(Activity.created_at.desc()).limit(limit).all()
    session.close()
    return [
        {
            'id': a.id,
            'type': a.type,
            'message': a.message,
            'timestamp': a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for a in acts
    ]
