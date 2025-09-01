#!/usr/bin/env python3
"""
演示ACL方向控制功能的使用方法
"""

import requests
import json
import sys

def demo_acl_direction():
    """演示ACL方向控制功能"""
    base_url = "http://localhost:8000"  # 假设应用运行在8000端口

    print("WireGuard ACL 方向控制功能演示")
    print("=" * 60)

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

    # 创建不同方向的规则示例
    print("\n2. 创建不同方向的规则示例...")

    direction_examples = [
        {
            "name": "入口方向规则",
            "description": "允许外部网络访问WireGuard节点的Web服务",
            "rule": {
                "peer_id": -1,  # 全局规则
                "action": "allow",
                "target": "0.0.0.0/0",
                "port": "80",
                "protocol": "tcp",
                "direction": "inbound"
            }
        },
        {
            "name": "出口方向规则",
            "description": "允许WireGuard节点访问外部DNS服务",
            "rule": {
                "peer_id": -1,  # 全局规则
                "action": "allow",
                "target": "8.8.8.8/32",
                "port": "53",
                "protocol": "udp",
                "direction": "outbound"
            }
        },
        {
            "name": "双向规则",
            "description": "禁止与危险网段的双向通信",
            "rule": {
                "peer_id": -1,  # 全局规则
                "action": "deny",
                "target": "10.0.0.0/8",
                "port": "*",
                "protocol": "*",
                "direction": "both"
            }
        }
    ]

    created_rules = []
    for i, example in enumerate(direction_examples, 1):
        try:
            response = requests.post(f"{base_url}/acls", json=example["rule"], headers=headers)
            if response.status_code == 200:
                print(f"   ✅ {example['name']}创建成功")
                print(f"      描述: {example['description']}")
                created_rules.append(response.json())
            else:
                print(f"   ❌ {example['name']}创建失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ {example['name']}创建异常: {e}")

    # 获取所有规则并显示方向信息
    print("\n3. 查看所有规则的方向信息...")
    try:
        response = requests.get(f"{base_url}/acls", headers=headers)
        if response.status_code == 200:
            acls = response.json()
            print(f"   总共 {len(acls)} 条规则:")

            # 按方向分组统计
            direction_stats = {}
            for acl in acls:
                direction = acl.get("direction", "both")
                if direction not in direction_stats:
                    direction_stats[direction] = []
                direction_stats[direction].append(acl)

            for direction, rules in direction_stats.items():
                direction_name = {
                    "inbound": "入口方向",
                    "outbound": "出口方向",
                    "both": "双向"
                }.get(direction, direction)

                print(f"\n   {direction_name}规则 ({len(rules)} 条):")
                for acl in rules:
                    peer_info = "全局规则" if acl.get("peer_id") == -1 else f"节点{acl.get('peer_id')}"
                    action_text = "允许" if acl["action"] == "allow" else "拒绝"
                    protocol_text = acl["protocol"] if acl["protocol"] != "*" else "所有协议"
                    print(f"     - {peer_info}: {action_text} {acl['target']}:{acl['port']} ({protocol_text})")

        else:
            print(f"   ❌ 获取规则失败: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 获取规则异常: {e}")

    # 演示前端界面使用方法
    print("\n4. 前端界面使用说明:")
    print("   在ACL管理页面创建规则时:")
    print("   - 入口方向：控制外部网络访问WireGuard网络的流量")
    print("   - 出口方向：控制WireGuard网络访问外部网络的流量")
    print("   - 双向：同时控制进出两个方向的流量")
    print()
    print("   📝 实际应用示例:")
    print("   • 允许外部访问公司Web服务器：入口方向规则")
    print("   • 允许内部访问外部API：出口方向规则")
    print("   • 禁止访问危险网站：双向规则")

    # 技术实现说明
    print("\n5. 技术实现说明:")
    print("   • 数据库字段：direction TEXT NOT NULL DEFAULT 'both'")
    print("   • iptables规则：根据方向生成不同的链路规则")
    print("   • 应用验证：确保direction值为有效选项")
    print("   • 兼容性：现有规则自动设为双向")

    print("\n✅ 演示完成!")
    print("\n🎯 方向控制的优势:")
    print("   • 更精细的流量控制")
    print("   • 提高网络安全等级")
    print("   • 支持复杂的访问策略")
    print("   • 保持配置的清晰性")

    return True

if __name__ == "__main__":
    success = demo_acl_direction()
    if not success:
        sys.exit(1)
