
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.models import User
from datetime import datetime, timedelta
import os
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

def create_access_token(data: dict, expires_delta: timedelta = None):
	to_encode = data.copy()
	expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
	to_encode.update({"exp": expire})
	return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if username is None:
			raise HTTPException(status_code=401, detail="无效认证")
	except JWTError:
		raise HTTPException(status_code=401, detail="认证失败")
	from app.main import SessionLocal
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
	new_password: str

@router.post("/change-password")
def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user)):
	if current_user.username != "admin":
		raise HTTPException(status_code=403, detail="仅 admin 可修改密码")
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
