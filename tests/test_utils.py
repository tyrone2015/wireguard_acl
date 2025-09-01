import pytest
from app.settings import get_available_peer_ips
from app.acl import validate_acl_target
from app.activity import log_activity
from app.models import Activity


class TestSettings:
    """设置功能测试"""

    def test_get_available_peer_ips(self):
        """测试获取可用IP"""
        ips = get_available_peer_ips()
        assert isinstance(ips, list)
        assert len(ips) > 0

        # 验证IP格式
        import ipaddress
        for ip in ips:
            ipaddress.ip_address(ip)  # 应该不抛出异常

    def test_get_available_peer_ips_range(self):
        """测试IP范围"""
        ips = get_available_peer_ips()

        # 验证IP在10.0.0.0/24范围内
        import ipaddress
        network = ipaddress.ip_network("10.0.0.0/24")
        for ip in ips:
            assert ipaddress.ip_address(ip) in network


class TestACLValidation:
    """ACL验证测试"""

    def test_validate_acl_target_valid(self):
        """测试有效目标验证"""
        valid_targets = [
            "192.168.1.0/24",
            "10.0.0.1/32",
            "172.16.0.0/16",
            "0.0.0.0/0",
            "192.168.1.1"
        ]

        for target in valid_targets:
            assert validate_acl_target(target)

    def test_validate_acl_target_invalid(self):
        """测试无效目标验证"""
        invalid_targets = [
            "invalid_ip",
            "192.168.1.256/24",
            "192.168.1.0/33",
            "not_an_ip",
            "",
            "192.168.1.0/24/invalid"
        ]

        for target in invalid_targets:
            assert not validate_acl_target(target)


class TestActivityLogging:
    """活动日志测试"""

    def test_log_activity_success(self, db_session):
        """测试成功记录活动"""
        from app.activity import log_activity

        # 记录活动
        log_activity("测试活动", type="info")

        # 验证数据库中存在记录
        activity = db_session.query(Activity).filter_by(message="测试活动").first()
        assert activity is not None
        assert activity.type == "info"

    def test_log_activity_types(self, db_session):
        """测试不同类型的活动记录"""
        activity_types = ["info", "success", "warning", "error"]

        for activity_type in activity_types:
            log_activity(f"测试{activity_type}", type=activity_type)

            activity = db_session.query(Activity).filter_by(
                message=f"测试{activity_type}",
                type=activity_type
            ).first()
            assert activity is not None

    def test_log_activity_timestamps(self, db_session):
        """测试活动时间戳"""
        from datetime import datetime

        before = datetime.utcnow()
        log_activity("时间戳测试", type="info")
        after = datetime.utcnow()

        activity = db_session.query(Activity).filter_by(message="时间戳测试").first()
        assert activity is not None
        assert before <= activity.created_at <= after


class TestModels:
    """数据模型测试"""

    def test_user_model(self, db_session):
        """测试User模型"""
        from app.models import User
        from app.auth import hash_password

        user = User(
            username="testuser",
            password_hash=hash_password("testpass")
        )
        db_session.add(user)
        db_session.commit()

        # 验证保存成功
        saved_user = db_session.query(User).filter_by(username="testuser").first()
        assert saved_user is not None
        assert saved_user.username == "testuser"

    def test_peer_model(self, db_session):
        """测试Peer模型"""
        from app.models import Peer

        peer = Peer(
            public_key="test_public_key",
            private_key="test_private_key",
            allowed_ips="10.0.0.100/32",
            remark="测试节点",
            status=True,
            peer_ip="10.0.0.100",
            endpoint="1.2.3.4:51820",
            keepalive=30,
            preshared_key="test_psk"
        )
        db_session.add(peer)
        db_session.commit()

        saved_peer = db_session.query(Peer).filter_by(peer_ip="10.0.0.100").first()
        assert saved_peer is not None
        assert saved_peer.remark == "测试节点"
        assert saved_peer.status == True

    def test_acl_model(self, db_session):
        """测试ACL模型"""
        from app.models import ACL

        acl = ACL(
            peer_id=1,
            action="allow",
            target="192.168.1.0/24",
            port="80",
            protocol="tcp",
            enabled=True
        )
        db_session.add(acl)
        db_session.commit()

        saved_acl = db_session.query(ACL).filter_by(target="192.168.1.0/24").first()
        assert saved_acl is not None
        assert saved_acl.action == "allow"
        assert saved_acl.enabled == True

    def test_activity_model(self, db_session):
        """测试Activity模型"""
        from app.models import Activity

        activity = Activity(
            type="info",
            message="测试活动"
        )
        db_session.add(activity)
        db_session.commit()

        saved_activity = db_session.query(Activity).filter_by(message="测试活动").first()
        assert saved_activity is not None
        assert saved_activity.type == "info"


class TestIntegration:
    """集成测试"""

    def test_peer_acl_relationship(self, db_session):
        """测试Peer和ACL的关系"""
        from app.models import Peer, ACL

        # 创建Peer
        peer = Peer(
            public_key="test_public_key",
            private_key="test_private_key",
            allowed_ips="10.0.0.100/32",
            peer_ip="10.0.0.100"
        )
        db_session.add(peer)
        db_session.commit()

        # 创建关联的ACL
        acl = ACL(
            peer_id=peer.id,
            action="allow",
            target="192.168.1.0/24"
        )
        db_session.add(acl)
        db_session.commit()

        # 验证关系
        saved_acl = db_session.query(ACL).filter_by(peer_id=peer.id).first()
        assert saved_acl is not None
        assert saved_acl.target == "192.168.1.0/24"

    def test_cascade_delete(self, db_session):
        """测试级联删除"""
        from app.models import Peer, ACL

        # 创建Peer和ACL
        peer = Peer(
            public_key="test_public_key",
            private_key="test_private_key",
            peer_ip="10.0.0.101"
        )
        db_session.add(peer)
        db_session.commit()

        acl = ACL(
            peer_id=peer.id,
            action="allow",
            target="192.168.1.0/24"
        )
        db_session.add(acl)
        db_session.commit()

        # 删除Peer
        db_session.delete(peer)
        db_session.commit()

        # 验证ACL也被删除
        remaining_acl = db_session.query(ACL).filter_by(peer_id=peer.id).first()
        assert remaining_acl is None