from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True, autoincrement=True)
	username = Column(String, unique=True, nullable=False)
	password_hash = Column(String, nullable=False)

class Peer(Base):
	__tablename__ = 'peers'
	id = Column(Integer, primary_key=True, autoincrement=True)
	public_key = Column(String, nullable=False)
	private_key = Column(String, nullable=False)
	allowed_ips = Column(String, nullable=False)  # 服务端AllowedIPs
	client_allowed_ips = Column(String, nullable=False, default='0.0.0.0/0')  # 客户端AllowedIPs
	remark = Column(String)
	status = Column(Boolean, default=True)
	peer_ip = Column(String, nullable=False, unique=True)
	keepalive = Column(Integer, default=30)  # 默认 30 秒，最大 120 秒
	preshared_key = Column(String, nullable=True)  # 新增字段
	created_at = Column(DateTime, default=datetime.utcnow)

class ACL(Base):
	__tablename__ = 'acls'
	id = Column(Integer, primary_key=True, autoincrement=True)
	peer_id = Column(Integer, ForeignKey('peers.id'), nullable=False)  # 保持NOT NULL
	action = Column(String, nullable=False)  # allow / deny
	target = Column(String, nullable=False)  # IP 或 CIDR
	port = Column(String, nullable=False)  # 端口或端口范围
	protocol = Column(String, nullable=False)  # 协议类型
	direction = Column(String, nullable=False, default='both')  # 方向：inbound, outbound, both
	enabled = Column(Boolean, default=True, nullable=False)  # 是否启用

class ServerKey(Base):
    __tablename__ = 'server_keys'
    id = Column(Integer, primary_key=True, autoincrement=True)
    public_key = Column(String, nullable=False)
    private_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AppSecret(Base):
    __tablename__ = 'app_secrets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Activity(Base):
	__tablename__ = 'activities'
	id = Column(Integer, primary_key=True, autoincrement=True)
	type = Column(String, nullable=False)
	message = Column(String, nullable=False)
	created_at = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base):
	__tablename__ = 'system_settings'
	id = Column(Integer, primary_key=True, autoincrement=True)
	key = Column(String, unique=True, nullable=False)
	value = Column(String, nullable=False)
	description = Column(String)
	created_at = Column(DateTime, default=datetime.utcnow)
	updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
