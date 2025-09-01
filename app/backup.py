from fastapi import APIRouter, Response, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from app.models import Peer, ACL, ServerKey, AppSecret, Activity, User
from app.auth import get_current_user
from app.activity import log_activity
import json
import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/backup/export")
def export_configuration(current_user: User = Depends(get_current_user)):
    """导出系统配置"""
    try:
        logger.info(f"用户 {current_user.username} 导出系统配置")

        from app.main import SessionLocal
        session = SessionLocal()

        # 导出Peers
        peers = session.query(Peer).all()
        peers_data = []
        for peer in peers:
            peers_data.append({
                "id": peer.id,
                "public_key": peer.public_key,
                "allowed_ips": peer.allowed_ips,
                "remark": peer.remark,
                "status": peer.status,
                "peer_ip": peer.peer_ip,
                "endpoint": peer.endpoint,
                "keepalive": peer.keepalive,
                "created_at": peer.created_at.isoformat() if peer.created_at else None
            })

        # 导出ACLs
        acls = session.query(ACL).all()
        acls_data = []
        for acl in acls:
            acls_data.append({
                "id": acl.id,
                "peer_id": acl.peer_id,
                "action": acl.action,
                "target": acl.target,
                "port": acl.port,
                "protocol": acl.protocol,
                "enabled": acl.enabled
            })

        # 导出服务器密钥
        server_key = session.query(ServerKey).first()
        server_key_data = None
        if server_key:
            server_key_data = {
                "public_key": server_key.public_key,
                "created_at": server_key.created_at.isoformat() if server_key.created_at else None
            }

        session.close()

        # 构建导出数据
        export_data = {
            "version": "1.0",
            "export_time": datetime.datetime.utcnow().isoformat(),
            "peers": peers_data,
            "acls": acls_data,
            "server_key": server_key_data
        }

        # 记录活动
        try:
            log_activity(f"导出系统配置: {len(peers_data)}个节点, {len(acls_data)}个规则", type='info')
        except Exception:
            pass

        logger.info(f"配置导出成功: {len(peers_data)}个节点, {len(acls_data)}个规则")

        return JSONResponse(content=export_data)

    except Exception as e:
        logger.error(f"导出配置时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="导出配置失败")


@router.post("/backup/import")
def import_configuration(data: dict = Body(...), current_user: User = Depends(get_current_user)):
    """导入系统配置"""
    try:
        logger.info(f"用户 {current_user.username} 导入系统配置")

        if not data or "peers" not in data:
            raise HTTPException(status_code=400, detail="无效的配置文件")

        from app.main import SessionLocal
        session = SessionLocal()

        imported_peers = 0
        imported_acls = 0
        errors = []

        try:
            # 导入Peers
            if "peers" in data:
                for peer_data in data["peers"]:
                    try:
                        # 检查IP是否已被使用
                        existing_peer = session.query(Peer).filter_by(peer_ip=peer_data["peer_ip"]).first()
                        if existing_peer:
                            errors.append(f"Peer IP {peer_data['peer_ip']} 已存在，跳过")
                            continue

                        peer = Peer(
                            public_key=peer_data["public_key"],
                            private_key="",  # 私钥不会在备份中导出
                            allowed_ips=peer_data.get("allowed_ips", ""),
                            remark=peer_data.get("remark", ""),
                            status=peer_data.get("status", True),
                            peer_ip=peer_data["peer_ip"],
                            endpoint=peer_data.get("endpoint", ""),
                            keepalive=peer_data.get("keepalive", 30)
                        )
                        session.add(peer)
                        imported_peers += 1

                    except Exception as e:
                        errors.append(f"导入Peer失败: {str(e)}")

            # 导入ACLs
            if "acls" in data:
                for acl_data in data["acls"]:
                    try:
                        # 验证Peer是否存在
                        peer = session.query(Peer).filter_by(peer_ip=acl_data.get("peer_ip")).first()
                        if not peer:
                            errors.append(f"ACL对应的Peer不存在: {acl_data.get('peer_ip')}")
                            continue

                        acl = ACL(
                            peer_id=peer.id,
                            action=acl_data["action"],
                            target=acl_data["target"],
                            port=acl_data.get("port", ""),
                            protocol=acl_data.get("protocol", ""),
                            enabled=acl_data.get("enabled", True)
                        )
                        session.add(acl)
                        imported_acls += 1

                    except Exception as e:
                        errors.append(f"导入ACL失败: {str(e)}")

            session.commit()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        # 同步WireGuard
        from app.sync import sync_acl_and_wireguard
        sync_success = sync_acl_and_wireguard()

        result_msg = f"导入完成: {imported_peers}个节点, {imported_acls}个规则"
        if errors:
            result_msg += f", {len(errors)}个错误"

        # 记录活动
        try:
            log_activity(f"导入系统配置: {imported_peers}个节点, {imported_acls}个规则", type='success')
        except Exception:
            pass

        logger.info(f"配置导入完成: {imported_peers}个节点, {imported_acls}个规则")

        return {
            "msg": result_msg,
            "imported_peers": imported_peers,
            "imported_acls": imported_acls,
            "errors": errors,
            "sync_success": sync_success
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入配置时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="导入配置失败")


@router.get("/backup/status")
def get_backup_status(current_user: User = Depends(get_current_user)):
    """获取备份状态信息"""
    try:
        from app.main import SessionLocal
        session = SessionLocal()

        peer_count = session.query(Peer).count()
        acl_count = session.query(ACL).count()
        activity_count = session.query(Activity).count()

        # 获取最后备份时间（通过活动日志判断）
        last_backup_activity = session.query(Activity).filter(
            Activity.message.like("%导出系统配置%")
        ).order_by(Activity.created_at.desc()).first()

        last_backup_time = None
        if last_backup_activity:
            last_backup_time = last_backup_activity.created_at.isoformat()

        session.close()

        return {
            "peer_count": peer_count,
            "acl_count": acl_count,
            "activity_count": activity_count,
            "last_backup_time": last_backup_time
        }

    except Exception as e:
        logger.error(f"获取备份状态时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="获取备份状态失败")