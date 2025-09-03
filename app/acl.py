import ipaddress
from fastapi import APIRouter, Body, Depends, HTTPException
from app.models import ACL, Peer, User
from app.auth import get_current_user
from app.activity import log_activity
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
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
			"rule_type": a.rule_type,
			"action": a.action,
			"target": a.target,
			"destination": a.destination,
			"source_interface": a.source_interface,
			"destination_interface": a.destination_interface,
			"port": a.port,
			"protocol": a.protocol,
			"direction": a.direction,
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

# ACL 创建（POST /acls，兼容前端接口，支持全局规则和方向控制）
@router.post("/acls")
def create_acl_with_port(
	rule_type: str = Body("firewall"),
	peer_id: int = Body(None),
	action: str = Body(...),
	target: str = Body(...),
	destination: str = Body(None),
	source_interface: str = Body(None),
	destination_interface: str = Body(None),
	port: str = Body(""),
	protocol: str = Body(""),
	direction: str = Body("both"),  # 添加方向参数，默认both
	current_user: User = Depends(get_current_user)
):
	if rule_type not in ["firewall", "nat"]:
		raise HTTPException(status_code=400, detail="rule_type 必须为 firewall 或 nat")
	
	if rule_type == "firewall":
		if action not in ["allow", "deny"]:
			raise HTTPException(status_code=400, detail="firewall action 必须为 allow 或 deny")
		if not validate_acl_target(target):
			raise HTTPException(status_code=400, detail="target 格式非法")
	elif rule_type == "nat":
		if action not in ["allow", "deny"]:
			raise HTTPException(status_code=400, detail="nat action 必须为 allow 或 deny")
		if not validate_acl_target(target):
			raise HTTPException(status_code=400, detail="source 格式非法")
		if not destination or not validate_acl_target(destination):
			raise HTTPException(status_code=400, detail="destination 格式非法")
	
	from app.main import SessionLocal
	session = SessionLocal()
	
	# 处理全局规则：如果peer_id为None或-1，表示全局规则
	if peer_id is None or peer_id == -1:
		peer_id = None  # 全局规则设为 None
	else:
		# 验证节点是否存在
		peer = session.query(Peer).get(peer_id)
		if not peer:
			session.close()
			raise HTTPException(status_code=400, detail="指定的节点不存在")
	
	# 检查是否已存在相同规则
	existing_acl = session.query(ACL).filter_by(
		rule_type=rule_type,
		peer_id=peer_id,
		target=target,
		destination=destination,
		source_interface=source_interface,
		destination_interface=destination_interface,
		port=port,
		protocol=protocol,
		direction=direction
	).first()
	
	if existing_acl:
		existing_acl.action = action
		msg = "ACL updated"
	else:
		acl = ACL(
			rule_type=rule_type,
			peer_id=peer_id,
			action=action,
			target=target,
			destination=destination,
			source_interface=source_interface,
			destination_interface=destination_interface,
			port=port,
			protocol=protocol,
			direction=direction
		)
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
		peer_info = "全局规则" if peer_id is None else f"peer_id={peer_id}"
		direction_info = f"方向:{direction}"
		log_activity(f"{msg}: {peer_info} target={target} {direction_info}", type='success')
	except Exception:
		pass
	return {"msg": msg, "sync_success": sync_success}

# ACL 创建（同一 Peer+target 冲突覆盖，支持全局规则）
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
	
	# 处理全局规则
	if peer_id is None or peer_id == -1:
		peer_id = -1
	else:
		# 验证节点是否存在
		peer = session.query(Peer).get(peer_id)
		if not peer:
			session.close()
			raise HTTPException(status_code=400, detail="指定的节点不存在")
	
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
		peer_info = "全局规则" if peer_id == -1 else f"peer_id={peer_id}"
		log_activity(f"{msg}: {peer_info} target={target}", type='success')
	except Exception:
		pass
	return {"msg": msg}

# ACL 编辑
@router.put("/acls/{acl_id}")
def edit_acl_api(
	acl_id: int,
	rule_type: str = Body(None),
	peer_id: int = Body(None),
	action: str = Body(None),
	target: str = Body(None),
	destination: str = Body(None),
	source_interface: str = Body(None),
	destination_interface: str = Body(None),
	port: str = Body(None),
	protocol: str = Body(None),
	direction: str = Body(None),  # 添加方向参数
	current_user: User = Depends(get_current_user)
):
	from app.main import SessionLocal
	session = SessionLocal()
	acl = session.query(ACL).get(acl_id)
	if not acl:
		session.close()
		raise HTTPException(status_code=404, detail="ACL not found")
	
	# allow changing associated peer (including setting to global rule)
	if peer_id is not None:
		if peer_id == -1:
			# 设置为全局规则
			acl.peer_id = None
		else:
			# validate peer exists
			peer = session.query(Peer).get(peer_id)
			if not peer:
				session.close()
				raise HTTPException(status_code=400, detail="指定的节点不存在")
			acl.peer_id = peer_id
	
	if rule_type:
		if rule_type not in ["firewall", "nat"]:
			session.close()
			raise HTTPException(status_code=400, detail="rule_type 必须为 firewall 或 nat")
		acl.rule_type = rule_type
	
	if action:
		if acl.rule_type == "firewall" and action not in ["allow", "deny"]:
			session.close()
			raise HTTPException(status_code=400, detail="firewall action 必须为 allow 或 deny")
		elif acl.rule_type == "nat" and action not in ["allow", "deny"]:
			session.close()
			raise HTTPException(status_code=400, detail="nat action 必须为 allow 或 deny")
		acl.action = action
	
	if target:
		if not validate_acl_target(target):
			session.close()
			raise HTTPException(status_code=400, detail="target 格式非法")
		acl.target = target
	
	if destination is not None:
		if destination and not validate_acl_target(destination):
			session.close()
			raise HTTPException(status_code=400, detail="destination 格式非法")
		acl.destination = destination
	
	if source_interface is not None:
		acl.source_interface = source_interface
	
	if destination_interface is not None:
		acl.destination_interface = destination_interface
	
	if port is not None:
		acl.port = port
	
	if protocol is not None:
		# normalize "all" protocol values from frontend to empty string for storage
		if isinstance(protocol, str) and protocol.lower() in ("*", "all"):
			protocol = ""
		acl.protocol = protocol
	
	if direction:
		if acl.rule_type == "firewall" and direction not in ["inbound", "outbound", "both"]:
			session.close()
			raise HTTPException(status_code=400, detail="direction 必须为 inbound、outbound 或 both")
		acl.direction = direction
	
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

# 批量操作接口
from typing import List
from pydantic import BaseModel

class BatchACLRequest(BaseModel):
    acls: List[dict]

@router.post("/acls/batch")
def batch_create_acls(request: BatchACLRequest, current_user: User = Depends(get_current_user)):
    """批量创建ACL规则"""
    try:
        logger.info(f"用户 {current_user.username} 尝试批量创建 {len(request.acls)} 个ACL")

        results = []
        success_count = 0
        fail_count = 0

        from app.main import SessionLocal
        session = SessionLocal()

        for i, acl_data in enumerate(request.acls):
            try:
                # 验证必需字段
                required_fields = ['action', 'target']  # 移除peer_id的必需验证
                for field in required_fields:
                    if field not in acl_data:
                        raise ValueError(f"缺少必需字段: {field}")

                # 验证action
                if acl_data['action'] not in ["allow", "deny"]:
                    raise ValueError("action必须为allow或deny")

                # 验证target
                if not validate_acl_target(acl_data['target']):
                    raise ValueError("target格式非法")

                # 验证peer_id（如果提供的话）
                peer_id = acl_data.get('peer_id')
                if peer_id is not None:
                    peer = session.query(Peer).get(peer_id)
                    if not peer:
                        raise ValueError("指定的节点不存在")

                # 检查是否已存在相同规则
                existing_acl = session.query(ACL).filter_by(
                    rule_type=acl_data.get('rule_type', 'firewall'),
                    peer_id=acl_data.get('peer_id'),
                    target=acl_data['target'],
                    destination=acl_data.get('destination'),
                    source_interface=acl_data.get('source_interface'),
                    destination_interface=acl_data.get('destination_interface'),
                    port=acl_data.get('port', ''),
                    protocol=acl_data.get('protocol', ''),
                    direction=acl_data.get('direction', 'both')  # 添加direction到唯一性检查
                ).first()

                if existing_acl:
                    existing_acl.action = acl_data['action']
                    msg = "ACL updated"
                else:
                    # 标准化协议
                    protocol = acl_data.get('protocol', '')
                    if isinstance(protocol, str) and protocol.lower() in ("*", "all"):
                        protocol = ""

                    acl = ACL(
                        rule_type=acl_data.get('rule_type', 'firewall'),
                        peer_id=acl_data.get('peer_id'),
                        action=acl_data['action'],
                        target=acl_data['target'],
                        destination=acl_data.get('destination'),
                        source_interface=acl_data.get('source_interface'),
                        destination_interface=acl_data.get('destination_interface'),
                        port=acl_data.get('port', ''),
                        protocol=protocol,
                        direction=acl_data.get('direction', 'both')
                    )
                    session.add(acl)
                    msg = "ACL created"

                results.append({
                    "index": i,
                    "success": True,
                    "message": msg
                })
                success_count += 1

            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1

        session.commit()
        session.close()

        # 同步WireGuard
        from app.sync import sync_acl_and_wireguard
        sync_success = sync_acl_and_wireguard()

        logger.info(f"批量创建ACL完成: 成功{success_count}, 失败{fail_count}")

        # 记录活动
        try:
            log_activity(f"批量创建防火墙规则: 成功{success_count}, 失败{fail_count}", type='success')
        except Exception:
            pass

        return {
            "msg": f"批量创建完成: 成功{success_count}, 失败{fail_count}",
            "results": results,
            "sync_success": sync_success
        }

    except Exception as e:
        logger.error(f"批量创建ACL时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="批量创建失败")


@router.post("/acls/batch-toggle")
def batch_toggle_acls(acl_ids: List[int] = Body(...), current_user: User = Depends(get_current_user)):
    """批量启用/禁用ACL规则"""
    try:
        logger.info(f"用户 {current_user.username} 尝试批量操作 {len(acl_ids)} 个ACL")

        from app.main import SessionLocal
        session = SessionLocal()

        updated_count = 0
        for acl_id in acl_ids:
            acl = session.query(ACL).get(acl_id)
            if acl:
                acl.enabled = not acl.enabled
                updated_count += 1

        session.commit()
        session.close()

        # 同步WireGuard
        from app.sync import sync_acl_and_wireguard
        sync_success = sync_acl_and_wireguard()

        logger.info(f"批量切换ACL状态完成: 更新{updated_count}个规则")

        # 记录活动
        try:
            log_activity(f"批量切换防火墙规则状态: 更新{updated_count}个", type='info')
        except Exception:
            pass

        return {
            "msg": f"批量操作完成: 更新{updated_count}个规则",
            "updated_count": updated_count,
            "sync_success": sync_success
        }

    except Exception as e:
        logger.error(f"批量切换ACL状态时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="批量操作失败")


@router.delete("/acls/batch")
def batch_delete_acls(acl_ids: List[int] = Body(...), current_user: User = Depends(get_current_user)):
    """批量删除ACL规则"""
    try:
        logger.info(f"用户 {current_user.username} 尝试批量删除 {len(acl_ids)} 个ACL")

        from app.main import SessionLocal
        session = SessionLocal()

        deleted_count = 0
        for acl_id in acl_ids:
            acl = session.query(ACL).get(acl_id)
            if acl:
                session.delete(acl)
                deleted_count += 1

        session.commit()
        session.close()

        # 同步WireGuard
        from app.sync import sync_acl_and_wireguard
        sync_success = sync_acl_and_wireguard()

        logger.info(f"批量删除ACL完成: 删除{deleted_count}个规则")

        # 记录活动
        try:
            log_activity(f"批量删除防火墙规则: 删除{deleted_count}个", type='warning')
        except Exception:
            pass

        return {
            "msg": f"批量删除完成: 删除{deleted_count}个规则",
            "deleted_count": deleted_count,
            "sync_success": sync_success
        }

    except Exception as e:
        logger.error(f"批量删除ACL时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="批量删除失败")

# NOTE: ACL -> iptables 的实现已统一放在 app.sync.apply_acl_to_iptables
# 以避免重复和冲突，这里不再保留旧实现。
