import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.main import SessionLocal


@pytest.fixture(scope="session")
def test_db():
    """创建测试数据库"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    # 创建测试数据库引擎
    test_engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
    
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    
    # 创建测试会话工厂
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    yield TestSessionLocal
    
    # 清理
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """提供数据库会话"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI测试客户端"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    # 临时修改数据库配置为内存数据库
    original_db_url = app.state.db_url if hasattr(app.state, 'db_url') else None
    
    # 使用内存数据库进行测试
    from app.main import engine
    original_engine = engine
    
    # 创建内存数据库
    from sqlalchemy import create_engine
    test_engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    
    # 替换全局引擎
    import app.main
    app.main.engine = test_engine
    app.main.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    with TestClient(app) as client:
        yield client
    
    # 恢复原始配置
    app.main.engine = original_engine
    app.main.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=original_engine)


@pytest.fixture
def auth_headers(client):
    """获取认证头"""
    # 登录获取token
    response = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_test_data(db_session):
    """设置测试数据"""
    from app.models import User
    from app.auth import hash_password
    
    # 检查用户是否已存在，只在不存在时创建
    existing_user = db_session.query(User).filter_by(username="admin").first()
    if not existing_user:
        admin_user = User(username="admin", password_hash=hash_password("admin123"))
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)