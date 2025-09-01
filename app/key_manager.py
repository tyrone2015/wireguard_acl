# 密钥管理配置
import os
import secrets
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from app.models import AppSecret


class KeyManager:
    """JWT密钥管理器"""

    def __init__(self):
        self.key_rotation_days = int(os.environ.get('JWT_KEY_ROTATION_DAYS', '30'))
        self.current_key_name = 'JWT_SECRET_KEY'
        self.previous_key_name = 'JWT_PREVIOUS_KEY'
        self.key_timestamp_name = 'JWT_KEY_TIMESTAMP'

    def get_current_key(self) -> str:
        """获取当前有效的JWT密钥"""
        from app.main import SessionLocal
        session = SessionLocal()

        try:
            # 获取当前密钥
            current_key_record = session.query(AppSecret).filter_by(
                name=self.current_key_name
            ).first()

            if not current_key_record:
                # 如果没有密钥，生成新密钥
                return self._generate_new_key(session)

            # 检查是否需要轮换
            timestamp_record = session.query(AppSecret).filter_by(
                name=self.key_timestamp_name
            ).first()

            if timestamp_record:
                key_age = datetime.utcnow() - datetime.fromisoformat(timestamp_record.value)
                if key_age.days >= self.key_rotation_days:
                    return self._rotate_key(session, current_key_record.value)

            return current_key_record.value

        finally:
            session.close()

    def _generate_new_key(self, session) -> str:
        """生成新密钥"""
        new_key = secrets.token_urlsafe(32)

        # 保存新密钥
        current_key_record = AppSecret(
            name=self.current_key_name,
            value=new_key
        )
        session.add(current_key_record)

        # 保存时间戳
        timestamp_record = AppSecret(
            name=self.key_timestamp_name,
            value=datetime.utcnow().isoformat()
        )
        session.add(timestamp_record)

        session.commit()
        return new_key

    def _rotate_key(self, session, old_key: str) -> str:
        """轮换密钥"""
        new_key = secrets.token_urlsafe(32)

        # 将当前密钥移到previous
        previous_record = session.query(AppSecret).filter_by(
            name=self.previous_key_name
        ).first()

        if previous_record:
            previous_record.value = old_key
        else:
            previous_record = AppSecret(
                name=self.previous_key_name,
                value=old_key
            )
            session.add(previous_record)

        # 更新当前密钥
        current_record = session.query(AppSecret).filter_by(
            name=self.current_key_name
        ).first()
        current_record.value = new_key

        # 更新时间戳
        timestamp_record = session.query(AppSecret).filter_by(
            name=self.key_timestamp_name
        ).first()
        timestamp_record.value = datetime.utcnow().isoformat()

        session.commit()
        return new_key

    def validate_token_with_previous(self, token: str) -> tuple[bool, str]:
        """使用当前和前一个密钥验证token"""
        from jose import jwt, JWTError

        current_key = self.get_current_key()

        # 先尝试当前密钥
        try:
            payload = jwt.decode(token, current_key, algorithms=["HS256"])
            return True, payload.get("sub")
        except JWTError:
            pass

        # 尝试前一个密钥（用于过渡期）
        from app.main import SessionLocal
        session = SessionLocal()

        try:
            previous_record = session.query(AppSecret).filter_by(
                name=self.previous_key_name
            ).first()

            if previous_record:
                try:
                    payload = jwt.decode(token, previous_record.value, algorithms=["HS256"])
                    return True, payload.get("sub")
                except JWTError:
                    pass
        finally:
            session.close()

        return False, None


# 全局密钥管理器实例
key_manager = KeyManager()