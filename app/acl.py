import ipaddress
from fastapi import APIRouter, Body, Depends, HTTPException
from app.models import ACL, Peer, User
from app.auth import get_current_user
from app.activity import log_activity
router = APIRouter()


# ACL 启用
@router.put("/acls/{acl_id}/enable")
def enable_acl_api(acl_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	acl = session.query(ACL).get(acl_id)
	if not acl:
		session.close()
		raise HTTPException(status_code=404, detail="ACL not found")
	acl.enabled = True
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	msg = "ACL enabled"
	# 记录活动
	try:
		log_activity(f"启用 防火墙 规则: {acl_id}", type='info')
	except Exception:
		pass
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	return {"msg": msg, "sync_success": sync_success}

# ACL 禁用
@router.put("/acls/{acl_id}/disable")
def disable_acl_api(acl_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	acl = session.query(ACL).get(acl_id)
	if not acl:
		session.close()
		raise HTTPException(status_code=404, detail="ACL not found")
	acl.enabled = False
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	msg = "ACL disabled"
	# 记录活动
	try:
		log_activity(f"禁用 防火墙 规则: {acl_id}", type='info')
	except Exception:
		pass
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	return {"msg": msg, "sync_success": sync_success}

# ACL 列表接口
@router.get("/acls")
def get_acls(current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	acls = session.query(ACL).all()
	session.close()
	return [
		{
			"id": a.id,
			"peer_id": a.peer_id,
			"action": a.action,
			"target": a.target,
			"port": a.port,
			# normalize empty protocol (means all protocols) to '*' for frontend display
			"protocol": a.protocol or "*",
			"enabled": a.enabled
		} for a in acls
	]

# 防火墙 规则合法性校验
def validate_acl_target(target: str) -> bool:
	try:
		ipaddress.ip_network(target.strip())
		return True
	except Exception:
		return False

# ACL 创建（POST /acls，兼容前端接口）
@router.post("/acls")
def create_acl_with_port(
	peer_id: int = Body(...),
	action: str = Body(...),
	target: str = Body(...),
	port: str = Body(...),
	protocol: str = Body(...),
	current_user: User = Depends(get_current_user)
):
	if action not in ["allow", "deny"]:
		raise HTTPException(status_code=400, detail="action 必须为 allow 或 deny")
	if not validate_acl_target(target):
		raise HTTPException(status_code=400, detail="target 格式非法")
	from app.main import SessionLocal
	session = SessionLocal()
	# normalize "all" protocol values from frontend to empty string for storage
	if isinstance(protocol, str) and protocol.lower() in ("*", "all"):
		protocol = ""

	acl = session.query(ACL).filter_by(peer_id=peer_id, target=target, port=port, protocol=protocol).first()
	if acl:
		acl.action = action
		msg = "ACL updated"
	else:
		acl = ACL(peer_id=peer_id, action=action, target=target, port=port, protocol=protocol)
		session.add(acl)
		msg = "ACL created"
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	# 记录活动
	try:
		log_activity(f"{msg}: peer_id={peer_id} target={target} port={port}", type='success')
	except Exception:
		pass
	return {"msg": msg, "sync_success": sync_success}

# ACL 创建（同一 Peer+target 冲突覆盖）
@router.post("/acls/create")
def create_acl_minimal(
	peer_id: int = Body(...),
	action: str = Body(...),
	target: str = Body(...),
	current_user: User = Depends(get_current_user)
):
	if action not in ["allow", "deny"]:
		raise HTTPException(status_code=400, detail="action 必须为 allow 或 deny")
	if not validate_acl_target(target):
		raise HTTPException(status_code=400, detail="target 格式非法")
	from app.main import SessionLocal
	session = SessionLocal()
	acl = session.query(ACL).filter_by(peer_id=peer_id, target=target).first()
	if acl:
		acl.action = action
		msg = "ACL updated"
	else:
		acl = ACL(peer_id=peer_id, action=action, target=target)
		session.add(acl)
		msg = "ACL created"
	session.commit()
	session.close()
	# 记录活动
	try:
		log_activity(f"{msg}: peer_id={peer_id} target={target}", type='success')
	except Exception:
		pass
	return {"msg": msg}

# ACL 编辑
@router.put("/acls/{acl_id}")
def edit_acl_api(
	acl_id: int,
	peer_id: int = Body(None),
	action: str = Body(None),
	target: str = Body(None),
	port: str = Body(None),
	protocol: str = Body(None),
	current_user: User = Depends(get_current_user)
):
	from app.main import SessionLocal
	session = SessionLocal()
	acl = session.query(ACL).get(acl_id)
	if not acl:
		session.close()
		raise HTTPException(status_code=404, detail="ACL not found")
	# allow changing associated peer
	if peer_id is not None:
		# validate peer exists
		peer = session.query(Peer).get(peer_id)
		if not peer:
			session.close()
			raise HTTPException(status_code=400, detail="peer_id 指定的节点不存在")
		acl.peer_id = peer_id
	if action:
		if action not in ["allow", "deny"]:
			session.close()
			raise HTTPException(status_code=400, detail="action 必须为 allow 或 deny")
		acl.action = action
	if target:
		if not validate_acl_target(target):
			session.close()
			raise HTTPException(status_code=400, detail="target 格式非法")
		acl.target = target
	if port:
		acl.port = port
	if protocol:
		# normalize "all" protocol values from frontend to empty string for storage
		if isinstance(protocol, str) and protocol.lower() in ("*", "all"):
			protocol = ""
		acl.protocol = protocol
	session.commit()
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	msg = "ACL updated"
	# 记录活动
	try:
		log_activity(f"更新 防火墙 规则: {acl_id}", type='info')
	except Exception:
		pass
	if not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	return {"msg": msg, "sync_success": sync_success}

# ACL 删除
@router.delete("/acls/{acl_id}")
def delete_acl_api(acl_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	acl = session.query(ACL).get(acl_id)
	if acl:
		session.delete(acl)
		session.commit()
		msg = "ACL deleted"
	else:
		msg = "ACL not found"
	session.close()
	from app.sync import sync_acl_and_wireguard
	sync_success = sync_acl_and_wireguard()
	if msg == "ACL deleted" and not sync_success:
		msg += " (警告: WireGuard 同步失败)"
	# 记录活动
	try:
		if msg == "ACL deleted":
			log_activity(f"删除 防火墙 规则: {acl_id}", type='warning')
		else:
			log_activity(f"尝试 删除 防火墙 规则: {acl_id} 但未找到", type='warning')
	except Exception:
		pass
	return {"msg": msg, "sync_success": sync_success}

# Peer 删除时级联删除 ACL
@router.delete("/peers/{peer_id}")
def delete_peer_cascade(peer_id: int, current_user: User = Depends(get_current_user)):
	from app.main import SessionLocal
	session = SessionLocal()
	peer = session.query(Peer).get(peer_id)
	if peer:
		session.query(ACL).filter_by(peer_id=peer_id).delete()
		session.delete(peer)
		session.commit()
		msg = "Peer and related ACLs deleted"
		# 记录活动
		try:
			log_activity(f"删除 节点: {peer_id} 及其相关规则", type='warning')
		except Exception:
			pass
	else:
		msg = "Peer not found"
	session.close()
	return {"msg": msg}

# NOTE: ACL -> iptables 的实现已统一放在 app.sync.apply_acl_to_iptables
# 以避免重复和冲突，这里不再保留旧实现。
