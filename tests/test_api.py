import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """认证API测试"""

    def test_login_success(self, client):
        """测试成功登录"""
        response = client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """测试密码错误登录"""
        response = client.post("/login", data={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 400
        assert "错误" in response.json()["detail"]

    def test_login_wrong_username(self, client):
        """测试用户名错误登录"""
        response = client.post("/login", data={
            "username": "nonexistent",
            "password": "admin123"
        })
        assert response.status_code == 400

    def test_change_password(self, client, auth_headers):
        """测试修改密码"""
        response = client.post("/change-password",
            json={"new_password": "newpassword123"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "成功" in response.json()["msg"]

    def test_get_users(self, client, auth_headers):
        """测试获取用户列表"""
        response = client.get("/users", headers=auth_headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1
        assert users[0]["username"] == "admin"


class TestPeerAPI:
    """Peer API测试"""

    def test_get_peers_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get("/peers")
        assert response.status_code == 401

    def test_get_peers_authorized(self, client, auth_headers):
        """测试授权访问Peer列表"""
        response = client.get("/peers", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_peer(self, client, auth_headers):
        """测试创建Peer"""
        peer_data = {
            "remark": "测试节点",
            "status": True,
            "endpoint": "1.2.3.4:51820",
            "allowed_ips": "10.0.0.100/32",
            "peer_ip": "10.0.0.100",
            "keepalive": 30
        }
        response = client.post("/peers", json=peer_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "msg" in data
        assert "public_key" in data
        assert "peer_ip" in data

    def test_get_available_peer_ip(self, client, auth_headers):
        """测试获取可用IP"""
        response = client.get("/peers/available-ip", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "peer_ip" in data

    def test_generate_key(self, client, auth_headers):
        """测试生成密钥"""
        response = client.post("/peers/generate-key", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert "private_key" in data
        assert "encrypted_private_key" in data


class TestACLAPI:
    """ACL API测试"""

    def test_get_acls(self, client, auth_headers):
        """测试获取ACL列表"""
        response = client.get("/acls", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_acl(self, client, auth_headers):
        """测试创建ACL规则"""
        # 先创建Peer
        peer_response = client.post("/peers", json={
            "remark": "测试Peer",
            "peer_ip": "10.0.0.101"
        }, headers=auth_headers)
        assert peer_response.status_code == 200
        peer_data = peer_response.json()

        # 创建绑定节点的ACL
        acl_data = {
            "peer_id": 1,  # 假设是第一个Peer
            "action": "allow",
            "target": "192.168.1.0/24",
            "port": "80",
            "protocol": "tcp",
            "direction": "inbound"  # 添加方向字段
        }
        response = client.post("/acls", json=acl_data, headers=auth_headers)
        assert response.status_code == 200
        assert "msg" in response.json()

    def test_create_global_acl(self, client, auth_headers):
        """测试创建全局ACL规则（不绑定节点）"""
        # 创建全局ACL（不绑定特定节点）
        acl_data = {
            "peer_id": None,  # 全局规则
            "action": "deny",
            "target": "10.0.0.0/8",
            "port": "22",
            "protocol": "tcp",
            "direction": "both"  # 添加方向字段
        }
        response = client.post("/acls", json=acl_data, headers=auth_headers)
        assert response.status_code == 200
        assert "msg" in response.json()

    def test_create_acl_invalid_target(self, client, auth_headers):
        """测试创建无效目标的ACL"""
        acl_data = {
            "peer_id": 1,
            "action": "allow",
            "target": "invalid_ip",
            "port": "80",
            "protocol": "tcp",
            "direction": "inbound"
        }
        response = client.post("/acls", json=acl_data, headers=auth_headers)
        assert response.status_code == 400
        assert "格式非法" in response.json()["detail"]

    def test_create_acl_invalid_action(self, client, auth_headers):
        """测试创建无效action的ACL"""
        acl_data = {
            "peer_id": 1,
            "action": "invalid_action",
            "target": "192.168.1.0/24",
            "port": "80",
            "protocol": "tcp",
            "direction": "both"
        }
        response = client.post("/acls", json=acl_data, headers=auth_headers)
        assert response.status_code == 400

    def test_create_acl_invalid_direction(self, client, auth_headers):
        """测试创建无效direction的ACL"""
        acl_data = {
            "peer_id": 1,
            "action": "allow",
            "target": "192.168.1.0/24",
            "port": "80",
            "protocol": "tcp",
            "direction": "invalid_direction"
        }
        response = client.post("/acls", json=acl_data, headers=auth_headers)
        assert response.status_code == 400


class TestSystemAPI:
    """系统API测试"""

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_system_stats(self, client, auth_headers):
        """测试系统统计"""
        response = client.get("/system/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data

    def test_get_activities(self, client, auth_headers):
        """测试获取活动日志"""
        response = client.get("/activities", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestWireGuardAPI:
    """WireGuard相关API测试"""

    def test_online_nodes_count(self, client, auth_headers):
        """测试在线节点统计"""
        response = client.get("/wg/online-nodes-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "wg_online_nodes_count" in data
        assert isinstance(data["wg_online_nodes_count"], int)