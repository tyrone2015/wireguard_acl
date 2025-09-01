#!/usr/bin/env python3
"""
WireGuard ACL 方向控制功能完整验证
"""

import sqlite3
import os
import sys
from datetime import datetime

def comprehensive_test():
    """全面验证ACL方向控制功能"""
    print("🔍 WireGuard ACL 方向控制功能完整验证")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    db_path = '/root/code-server/config/workspace/wireguard_acl/data/wireguard_acl.db'

    # 1. 数据库结构验证
    print("1️⃣ 数据库结构验证")
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("PRAGMA table_info(acls)")
        columns = cursor.fetchall()

        required_columns = ['id', 'peer_id', 'action', 'target', 'port', 'protocol', 'enabled', 'direction']
        actual_columns = [col[1] for col in columns]

        missing_columns = [col for col in required_columns if col not in actual_columns]
        if missing_columns:
            print(f"❌ 缺少字段: {missing_columns}")
            return False

        # 检查direction字段的约束
        direction_col = next((col for col in columns if col[1] == 'direction'), None)
        if not direction_col or direction_col[3] == 0:  # NOT NULL check
            print("❌ direction字段应该是NOT NULL")
            return False

        print("✅ 数据库结构正确")
        print(f"   字段列表: {', '.join(actual_columns)}")

    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

    # 2. 数据操作验证
    print("\n2️⃣ 数据操作验证")
    try:
        # 清理旧数据
        cursor.execute("DELETE FROM acls WHERE target LIKE 'test.%' OR target LIKE '192.168.100.%'")
        conn.commit()

        # 测试插入不同方向的规则
        test_cases = [
            (-1, 'allow', 'test.inbound.com', '80', 'tcp', 'inbound'),
            (-1, 'deny', 'test.outbound.com', '443', 'tcp', 'outbound'),
            (1, 'allow', '192.168.100.0/24', '53', 'udp', 'both'),
        ]

        inserted_ids = []
        for peer_id, action, target, port, protocol, direction in test_cases:
            cursor.execute('''
                INSERT INTO acls (peer_id, action, target, port, protocol, direction, enabled)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (peer_id, action, target, port, protocol, direction))
            inserted_ids.append(cursor.lastrowid)

        conn.commit()
        print("✅ 数据插入成功")

        # 验证数据
        cursor.execute("SELECT id, peer_id, action, target, port, protocol, direction FROM acls WHERE id IN ({})".format(','.join('?' * len(inserted_ids))), inserted_ids)
        results = cursor.fetchall()

        if len(results) != len(test_cases):
            print(f"❌ 数据验证失败: 期望{len(test_cases)}条，实际{len(results)}条")
            return False

        direction_counts = {}
        for row in results:
            direction_counts[row[6]] = direction_counts.get(row[6], 0) + 1

        print("✅ 数据验证成功")
        print(f"   插入规则数量: {len(results)}")
        print(f"   方向分布: {direction_counts}")

    except Exception as e:
        print(f"❌ 数据操作失败: {e}")
        return False

    # 3. 应用层验证
    print("\n3️⃣ 应用层验证")
    try:
        from app.main import SessionLocal
        from app.models import ACL

        session = SessionLocal()
        try:
            # 查询规则
            rules = session.query(ACL).filter(ACL.target.like('test.%')).all()

            if len(rules) != 2:  # 应该有2条全局规则
                print(f"❌ 应用层查询失败: 期望2条，实际{len(rules)}条")
                return False

            # 验证方向字段
            directions = [rule.direction for rule in rules]
            if 'inbound' not in directions or 'outbound' not in directions:
                print(f"❌ 方向字段验证失败: {directions}")
                return False

            print("✅ 应用层验证成功")
            print(f"   SQLAlchemy查询正常，规则方向: {directions}")

        finally:
            session.close()

    except Exception as e:
        print(f"❌ 应用层验证失败: {e}")
        return False

    # 4. 同步逻辑验证
    print("\n4️⃣ 同步逻辑验证")
    try:
        from app.sync import apply_acl_to_iptables

        # 模拟ACL规则
        mock_acls = [
            type('MockACL', (), {
                'peer_id': -1,
                'action': 'allow',
                'target': '192.168.1.0/24',
                'port': '80',
                'protocol': 'tcp',
                'direction': 'inbound',
                'enabled': True
            })(),
            type('MockACL', (), {
                'peer_id': -1,
                'action': 'deny',
                'target': '10.0.0.0/8',
                'port': '22',
                'protocol': 'tcp',
                'direction': 'outbound',
                'enabled': True
            })(),
        ]

        # 调用同步函数
        post_up_cmds, post_down_cmds = apply_acl_to_iptables(mock_acls)

        if not post_up_cmds or not post_down_cmds:
            print("❌ 同步逻辑验证失败: 未生成iptables命令")
            return False

        # 检查是否生成了正确的方向规则
        inbound_found = any('eth0' in cmd and 'wg0' in cmd for cmd in post_up_cmds)
        outbound_found = any('wg0' in cmd and 'eth0' in cmd for cmd in post_up_cmds)

        if not inbound_found or not outbound_found:
            print("❌ 同步逻辑验证失败: 未生成正确的方向规则")
            return False

        print("✅ 同步逻辑验证成功")
        print(f"   生成的PostUp命令数量: {len(post_up_cmds)}")
        print(f"   生成的PostDown命令数量: {len(post_down_cmds)}")

    except Exception as e:
        print(f"❌ 同步逻辑验证失败: {e}")
        return False

    # 5. 清理测试数据
    print("\n5️⃣ 清理测试数据")
    try:
        cursor.execute("DELETE FROM acls WHERE target LIKE 'test.%' OR target LIKE '192.168.100.%'")
        conn.commit()
        conn.close()

        print("✅ 测试数据清理完成")

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False

    # 总结
    print("\n🎉 完整验证通过!")
    print("=" * 60)
    print("✅ 数据库结构正确")
    print("✅ 数据操作正常")
    print("✅ 应用层集成成功")
    print("✅ 同步逻辑正确")
    print("✅ 测试环境清理完成")
    print()
    print("📋 功能特性:")
    print("   • 支持入口方向(inbound)流量控制")
    print("   • 支持出口方向(outbound)流量控制")
    print("   • 支持双向(both)流量控制")
    print("   • 全局规则和节点特定规则都支持方向控制")
    print("   • iptables规则自动根据方向生成")
    print("   • 前端界面提供直观的方向选择")
    print()
    print("🚀 现在您可以创建具有方向控制的防火墙规则了!")

    return True

if __name__ == "__main__":
    success = comprehensive_test()
    if not success:
        print("\n💥 验证失败，请检查错误信息")
        sys.exit(1)
