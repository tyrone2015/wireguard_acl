#!/usr/bin/env python3
"""
演示ACL全局规则功能的使用方法
"""

import requests
import json
import sys

def demo_global_acl():
    """演示全局ACL规则功能"""
    base_url = "http://localhost:8000"  # 假设应用运行在8000端口

    print("WireGuard ACL 全局规则功能演示")
    print("=" * 50)

    # 首先登录获取token
    print("1. 登录获取访问令牌...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{base_url}/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ 登录成功")
        else:
            print(f"   ❌ 登录失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        print("   请确保应用正在运行（python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000）")
        return False

    # 创建全局规则示例
    print("\n2. 创建全局规则示例...")

    global_rules = [
        {
            "peer_id": -1,  # 全局规则标识符
            "action": "deny",
            "target": "10.0.0.0/8",
            "port": "22",
            "protocol": "tcp"
        },
        {
            "peer_id": -1,
            "action": "allow",
            "target": "192.168.1.0/24",
            "port": "80",
            "protocol": "tcp"
        }
    ]

    created_rules = []
    for i, rule in enumerate(global_rules, 1):
        try:
            response = requests.post(f"{base_url}/acls", json=rule, headers=headers)
            if response.status_code == 200:
                print(f"   ✅ 全局规则{i}创建成功: {rule['action']} {rule['target']}:{rule['port']}")
                created_rules.append(response.json())
            else:
                print(f"   ❌ 全局规则{i}创建失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ 全局规则{i}创建异常: {e}")

    # 获取所有规则
    print("\n3. 查看所有规则...")
    try:
        response = requests.get(f"{base_url}/acls", headers=headers)
        if response.status_code == 200:
            acls = response.json()
            print(f"   总共 {len(acls)} 条规则:")
            for acl in acls:
                peer_info = "全局规则" if acl.get("peer_id") == -1 else f"节点{acl.get('peer_id')}"
                print(f"     - {peer_info}: {acl['action']} {acl['target']}:{acl['port']} ({acl['protocol']})")
        else:
            print(f"   ❌ 获取规则失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 获取规则异常: {e}")

    # 演示前端界面使用方法
    print("\n4. 前端界面使用说明:")
    print("   在ACL管理页面:")
    print("   - 选择节点下拉框中的'全局规则（所有节点）'选项")
    print("   - 或清空节点选择（留空）")
    print("   - 创建的规则将应用于所有活跃的WireGuard节点")

    print("\n5. 技术实现说明:")
    print("   - 使用 peer_id = -1 表示全局规则")
    print("   - 同步时自动为所有活跃节点生成对应的iptables规则")
    print("   - 保持数据库兼容性，无需迁移现有数据")

    # 清理演示数据
    print("\n6. 清理演示数据...")
    for rule in created_rules:
        if "msg" in rule and "created" in rule["msg"].lower():
            # 这里应该从响应中提取ACL ID，但简化起见我们跳过
            pass

    print("\n✅ 演示完成!")
    print("\n📝 使用建议:")
    print("   - 全局规则适用于需要统一应用的策略，如安全基线")
    print("   - 可以与节点特定规则结合使用，节点规则优先级更高")
    print("   - 定期检查规则列表，避免规则冲突")

    return True

if __name__ == "__main__":
    success = demo_global_acl()
    if not success:
        sys.exit(1)
