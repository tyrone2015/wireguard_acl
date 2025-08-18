from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, AppSecret
from app.peer import router as peer_router
from app.acl import router as acl_router
from app.auth import router as auth_router
import os
from cryptography.fernet import Fernet

from app.sync import sync_acl_and_wireguard
from app.system_status import router as system_status_router
from app.activity import router as activity_router
app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# SQLite 数据库路径 - 移动到 data 文件夹
DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DB_DIR, exist_ok=True)  # 确保 data 目录存在
DB_PATH = os.path.join(DB_DIR, 'wireguard_acl.db')
DB_URL = f'sqlite:///{DB_PATH}'
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 从数据库获取或生成 FERNET_KEY
def get_fernet_key_from_db():
    session = SessionLocal()
    secret = session.query(AppSecret).filter_by(name='FERNET_KEY').first()
    if not secret:
        key = Fernet.generate_key().decode()
        secret = AppSecret(name='FERNET_KEY', value=key)
        session.add(secret)
        session.commit()
    session.close()

# 启动时自动建表
def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info(f"数据库初始化完成，路径: {DB_PATH}")
    # 自动生成并持久化FERNET_KEY
    get_fernet_key_from_db()


init_db()

# 启动时自动插入 admin 用户（如不存在）
def init_admin():
    from app.auth import hash_password
    session = SessionLocal()
    admin = session.query(User).filter_by(username='admin').first()
    if not admin:
        pwd = os.environ.get('WG_ADMIN_INIT_PWD', 'admin123')
        pwd_hash = hash_password(pwd)
        session.add(User(username='admin', password_hash=pwd_hash))
        session.commit()
        logger.info(f"已初始化 admin 用户，初始密码: {pwd}")
    session.close()

init_admin()

# FastAPI 启动事件钩子：启动时自动同步 WireGuard 配置
@app.on_event("startup")
def sync_wg_on_startup():
    logger.info("启动时自动同步 WireGuard 配置...")
    sync_acl_and_wireguard()

@app.get("/health")
def health_check():
    """健康检查接口"""
    return JSONResponse(content={"status": "ok"})

# 注册各功能模块路由
app.include_router(peer_router, prefix="")
app.include_router(acl_router, prefix="")
app.include_router(auth_router, prefix="")
app.include_router(system_status_router, prefix="")
app.include_router(activity_router, prefix="")
