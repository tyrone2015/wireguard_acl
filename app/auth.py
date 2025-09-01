from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.models import User
from datetime import datetime, timedelta
import os
import re
from app.activity import log_activity

router = APIRouter()

SECRET_KEY = os.environ.get("WG_SECRET_KEY", "wireguardaclsecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    密码强度验证
    返回: (是否有效, 错误信息)
    """
    if len(password) < 8:
        return False, "密码长度至少8位"

    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"

    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"

    if not re.search(r'\d', password):
        return False, "密码必须包含至少一个数字"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含至少一个特殊字符"

    # 检查常见弱密码
    weak_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password123', 'admin123', 'letmein', 'welcome', 'monkey'
    ]

    if password.lower() in weak_passwords:
        return False, "密码过于简单，请使用更复杂的密码"

    return True, ""

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    # 暂时使用简单验证，避免循环导入
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效认证")
    except JWTError:
        raise HTTPException(status_code=401, detail="认证失败")

    # 动态导入SessionLocal避免循环导入
    import importlib
    main_module = importlib.import_module('app.main')
    SessionLocal = main_module.SessionLocal

    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    session.close()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

# 登录接口
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    from app.main import SessionLocal
    session = SessionLocal()
    user = session.query(User).filter_by(username=form_data.username).first()
    session.close()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    access_token = create_access_token(data={"sub": user.username})
    # 记录登录活动
    try:
        log_activity(f"用户 登录: {user.username}", type='info')
    except Exception:
        pass
    return {"access_token": access_token, "token_type": "bearer"}

# 修改密码接口（仅 admin）
from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user)):
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="仅 admin 可修改密码")

    # 验证当前密码
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")

    # 验证新密码强度
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    from app.main import SessionLocal
    session = SessionLocal()
    user = session.query(User).filter_by(username="admin").first()
    if user:
        user.password_hash = hash_password(request.new_password)
        session.commit()
        # 记录活动
        try:
            log_activity(f"修改 管理员 密码", type='info')
        except Exception:
            pass
        session.close()
        return {"msg": "密码修改成功"}
    else:
        session.close()
        raise HTTPException(status_code=404, detail="admin 用户不存在")
# 用户列表接口
@router.get("/users")
def get_users(current_user: User = Depends(get_current_user)):
    from app.main import SessionLocal
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return [{"id": u.id, "username": u.username} for u in users]
