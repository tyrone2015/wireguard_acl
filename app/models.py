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
	peer_id = Column(Integer, ForeignKey('peers.id'), nullable=True)  # 改为可空，支持全局规则
	rule_type = Column(String, nullable=False, default='firewall')  # firewall, route, nat
	action = Column(String, nullable=False)  # allow/deny for firewall, enable/disable for route/nat
	target = Column(String, nullable=False)  # IP/CIDR for firewall/route, source for nat
	destination = Column(String, nullable=True)  # 目标网段 for route/nat
	source_interface = Column(String, nullable=True)  # 源接口 for route/nat
	destination_interface = Column(String, nullable=True)  # 目标接口 for route/nat
	port = Column(String, nullable=False, default='')  # 端口 for firewall
	protocol = Column(String, nullable=False, default='')  # 协议 for firewall
	direction = Column(String, nullable=False, default='both')  # 方向 for firewall
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
