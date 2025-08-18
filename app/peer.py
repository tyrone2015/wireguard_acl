import subprocess
import ipaddress
from app.sync import generate_preshared_key
from fastapi import APIRouter, Body, Depends, HTTPException
from app.models import  Peer, User, ServerKey
from app.activity import log_activity
from app.settings import get_available_peer_ips
from app.auth import get_current_user
router = APIRouter()

# 获取一个可用 peer_ip（GET /peers/available-ip）
@router.get("/peers/available-ip")
def get_available_peer_ip(current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	used_ips = set()
	for p in session.query(Peer).all():
		for ip in p.peer_ip.split(','):
			used_ips.add(ip.strip())
	available_ips = [ip for ip in get_available_peer_ips() if ip not in used_ips]
	session.close()
	if not available_ips:
		raise HTTPException(status_code=400, detail="可分配的 Peer IP 已用尽")
	return {"peer_ip": available_ips[0]}

# Peer 新建时自动分配唯一 IP，allowed_ips 自动生成且不可更改
@router.post("/peers")
def create_peer_api(
	remark: str = Body(''),
	status: bool = Body(True),
	endpoint: str = Body(''),
	allowed_ips: str = Body(""),
	peer_ip: str = Body(''),
	keepalive: int = Body(30),
	current_user: User = Depends(get_current_user)
):
	public_key, private_key = generate_wg_keypair()
	enc_private_key = encrypt_private_key(private_key)
	preshared_key = generate_preshared_key()
	from app.main import SessionLocal
	session = SessionLocal()
	# 获取已分配的 IP
	used_ips = set()
	for p in session.query(Peer).all():
		used_ips.add(p.peer_ip.strip())
	# 获取可用 IP
	available_ips = [ip for ip in get_available_peer_ips() if ip not in used_ips]
	if not available_ips:
		session.close()
		raise HTTPException(status_code=400, detail="可分配的 Peer IP 已用尽")
	assigned_peer_ip = available_ips[0]
	peer = Peer(
		public_key=public_key,
		private_key=enc_private_key,
		allowed_ips=allowed_ips,
		remark=remark,
		status=status,
		peer_ip=assigned_peer_ip,
		endpoint=endpoint,
		keepalive=min(max(keepalive, 30), 120),
		preshared_key=preshared_key
	)
	session.add(peer)
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	msg = "Peer created"
	# 记录活动
	try:
		log_activity(f"创建 节点: {peer.remark or peer.peer_ip}", type='success')
	except Exception:
		pass
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	return {"msg": msg, "public_key": public_key, "peer_ip": assigned_peer_ip, "sync_success": sync_success}


# WireGuard 在线节点统计接口（10分钟内有握手的节点数）
import subprocess
import time
@router.get("/wg/online-nodes-count")
def get_wg_online_nodes_count():
	try:
		result = subprocess.check_output(["wg", "show", "wg0", "latest-handshakes"]).decode().strip()
		now = int(time.time())
		threshold = 600  # 10分钟
		count = 0
		for line in result.splitlines():
			parts = line.strip().split()
			if len(parts) == 2:
				handshake = int(parts[1])
				if handshake > 0 and now - handshake <= threshold:
					count += 1
	except Exception as e:
		count = 0
	return {"wg_online_nodes_count": count}

# Peer 密钥生成接口
@router.post("/peers/generate-key")
def generate_key_api(current_user: User = Depends(get_current_user)):
	public_key, private_key = generate_wg_keypair()
	enc_private_key = encrypt_private_key(private_key)
	return {
		"public_key": public_key,
		"private_key": private_key,
		"encrypted_private_key": enc_private_key
	}

# Peer 列表接口
@router.get("/peers")
def get_peers(current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	peers = session.query(Peer).all()
	session.close()
	return [
		{
			"id": p.id,
			"public_key": p.public_key,
			"allowed_ips": p.allowed_ips,
			"remark": p.remark,
			"status": p.status,
			"peer_ip": p.peer_ip,
			"created_at": p.created_at,
			"endpoint": p.endpoint,
			"keepalive": p.keepalive
		} for p in peers
	]

# WireGuard 密钥生成
def generate_wg_keypair():
	private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
	public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).decode().strip()
	return public_key, private_key

# 加密密钥（环境变量或默认）
def get_fernet_key_from_db():
	from app.models import AppSecret
	from app.main import SessionLocal
	
	session = SessionLocal()
	secret = session.query(AppSecret).filter_by(name='FERNET_KEY').first()
	secret=secret.value
	session.close()
	return secret

# 删除环境变量相关的密钥逻辑，只保留数据库密钥获取
from cryptography.fernet import Fernet
def encrypt_private_key(private_key: str) -> str:
    key = get_fernet_key_from_db()
    fernet = Fernet(key.encode())
    return fernet.encrypt(private_key.encode()).decode()

def decrypt_private_key(enc: str) -> str:
    key = get_fernet_key_from_db()
    fernet = Fernet(key.encode())
    return fernet.decrypt(enc.encode()).decode()

# AllowedIPs 校验工具
def validate_allowed_ips(allowed_ips: str) -> bool:
	try:
		for ip in allowed_ips.split(','):
			ipaddress.ip_network(ip.strip())
		return True
	except Exception:
		return False



# Peer 编辑（AllowedIPs、备注、状态）
@router.put("/peers/{peer_id}")
def edit_peer_api(
	peer_id: int,
	allowed_ips: str = Body(None),
	remark: str = Body(None),
	status: bool = Body(None),
	endpoint: str = Body(None),
	keepalive: int = Body(None),
	current_user: User = Depends(get_current_user)
):
	from app.main import SessionLocal
	session = SessionLocal()
	peer = session.query(Peer).get(peer_id)
	if not peer:
		session.close()
		raise HTTPException(status_code=404, detail="Peer not found")
	if allowed_ips is not None:
		if not validate_allowed_ips(allowed_ips):
			session.close()
			raise HTTPException(status_code=400, detail="AllowedIPs 格式非法")
		peer.allowed_ips = allowed_ips
	if remark is not None:
		peer.remark = remark
	if status is not None:
		peer.status = status
	if endpoint is not None:
		peer.endpoint = endpoint
	if keepalive is not None:
		peer.keepalive = min(max(keepalive, 30), 120)
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	msg = "Peer updated"
	# 记录活动
	try:
		log_activity(f"更新 节点: {peer.remark or peer.peer_ip}", type='info')
	except Exception:
		pass
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	return {"msg": msg, "sync_success": sync_success}

# Peer 启用/禁用接口
@router.post("/peers/{peer_id}/toggle")
def toggle_peer_status(peer_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	peer = session.query(Peer).get(peer_id)
	if not peer:
		session.close()
		raise HTTPException(status_code=404, detail="Peer not found")
	peer.status = not peer.status
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	msg = "Peer status toggled"
	# 记录活动
	try:
		log_activity(f"切换 节点 状态: {peer.remark or peer.peer_ip} -> {'启用' if peer.status else '禁用'}", type='info')
	except Exception:
		pass
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	return {"msg": msg, "status": peer.status, "sync_success": sync_success}

# 生成客户端配置内容
def generate_client_config(peer, server_public_key=None):
	from app.peer import decrypt_private_key
	private_key = decrypt_private_key(peer.private_key)
	config = f"""[Interface]\nPrivateKey = {private_key}\nListenPort = 51820\nAddress = {peer.peer_ip}/32\nDNS = 10.0.0.1\n\n[Peer]\nPublicKey = {server_public_key or 'SERVER_PUBLIC_KEY'}\nPresharedKey = {peer.preshared_key}\nAllowedIPs = 0.0.0.0/0\nEndpoint = {peer.endpoint or ''}\nPersistentKeepalive = {peer.keepalive}\n"""
	return config

# 下载客户端配置文件接口
from fastapi import Response
@router.get("/peers/{peer_id}/config")
def download_peer_config(peer_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	peer = session.query(Peer).get(peer_id)
	server_key = session.query(ServerKey).first()
	session.close()
	if not peer:
		raise HTTPException(status_code=404, detail="Peer not found")
	if not server_key:
		raise HTTPException(status_code=500, detail="Server key not found")
	server_public_key = server_key.public_key
	config = generate_client_config(peer, server_public_key)
	return Response(content=config, media_type="text/plain", headers={
		"Content-Disposition": f"attachment; filename=peer_{peer_id}_config.conf"
	})

# 显示客户端配置文件二维码接口
from fastapi.responses import StreamingResponse
import qrcode
from io import BytesIO
@router.get("/peers/{peer_id}/config/qrcode")
def get_peer_config_qrcode(peer_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	peer = session.query(Peer).get(peer_id)
	server_key = session.query(ServerKey).first()
	session.close()
	if not peer:
		raise HTTPException(status_code=404, detail="Peer not found")
	if not server_key:
		raise HTTPException(status_code=500, detail="Server key not found")
	server_public_key = server_key.public_key
	config = generate_client_config(peer, server_public_key)
	img = qrcode.make(config)
	buf = BytesIO()
	img.save(buf, format="PNG")
	buf.seek(0)
	return StreamingResponse(buf, media_type="image/png")
