from fastapi import APIRouter, Depends, HTTPException
from app.models import SystemSetting
from app.auth import get_current_user, User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 获取系统设置
@router.get("/system/settings")
def get_system_settings(current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	try:
		settings = session.query(SystemSetting).all()
		result = {setting.key: setting.value for setting in settings}
		return result
	except Exception as e:
		logger.error(f"获取系统设置失败: {str(e)}")
		raise HTTPException(status_code=500, detail="获取系统设置失败")
	finally:
		session.close()

# 更新系统设置
@router.put("/system/settings")
def update_system_settings(settings: dict, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	try:
		for key, value in settings.items():
			setting = session.query(SystemSetting).filter_by(key=key).first()
			if setting:
				setting.value = value
			else:
				setting = SystemSetting(key=key, value=value)
				session.add(setting)
		session.commit()
		return {"msg": "系统设置更新成功"}
	except Exception as e:
		session.rollback()
		logger.error(f"更新系统设置失败: {str(e)}")
		raise HTTPException(status_code=500, detail="更新系统设置失败")
	finally:
		session.close()

# 获取单个系统设置
@router.get("/system/settings/{key}")
def get_system_setting(key: str, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	try:
		setting = session.query(SystemSetting).filter_by(key=key).first()
		if not setting:
			return {"value": ""}
		return {"value": setting.value}
	except Exception as e:
		logger.error(f"获取系统设置失败: {str(e)}")
		raise HTTPException(status_code=500, detail="获取系统设置失败")
	finally:
		session.close()

# 更新单个系统设置
@router.put("/system/settings/{key}")
def update_system_setting(key: str, value: str = "", current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	try:
		setting = session.query(SystemSetting).filter_by(key=key).first()
		if setting:
			setting.value = value
		else:
			setting = SystemSetting(key=key, value=value)
			session.add(setting)
		session.commit()
		return {"msg": f"系统设置 {key} 更新成功"}
	except Exception as e:
		session.rollback()
		logger.error(f"更新系统设置失败: {str(e)}")
		raise HTTPException(status_code=500, detail="更新系统设置失败")
	finally:
		session.close()
