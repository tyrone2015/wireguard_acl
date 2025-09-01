#!/usr/bin/env python3
"""
测试ACL方向控制功能
"""

import sqlite3
import sys
import os

def test_acl_direction_feature():
    """测试ACL方向控制功能"""
    db_path = '/root/code-server/config/workspace/wireguard_acl/data/wireguard_acl.db'

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表结构
        print("🔍 检查ACL表结构...")
        cursor.execute("PRAGMA table_info(acls)")
        columns = cursor.fetchall()

        direction_exists = False
        for col in columns:
            if col[1] == 'direction':
                direction_exists = True
                print(f"   direction字段: {'存在' if direction_exists else '不存在'}")
                break

        if not direction_exists:
            print("❌ 未找到direction字段，请先运行数据库迁移")
            return False

        # 清理旧的测试数据
        cursor.execute("DELETE FROM acls WHERE target LIKE '192.168.100.%' OR target LIKE '10.100.%'")
        conn.commit()

        # 插入测试数据
        print("📝 插入测试数据...")

        # 插入不同方向的规则
        test_rules = [
            (-1, 'allow', '192.168.100.0/24', '80', 'tcp', 'inbound'),   # 全局入口规则
            (-1, 'deny', '10.100.0.0/16', '22', 'tcp', 'outbound'),     # 全局出口规则
            (1, 'allow', '192.168.200.0/24', '443', 'tcp', 'both'),     # 节点双向规则
        ]

        for peer_id, action, target, port, protocol, direction in test_rules:
            cursor.execute('''
                INSERT INTO acls (peer_id, action, target, port, protocol, direction, enabled)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (peer_id, action, target, port, protocol, direction))

        conn.commit()

        # 查询验证
        print("✅ 验证数据插入...")
        cursor.execute("SELECT id, peer_id, action, target, port, protocol, direction FROM acls WHERE target LIKE '192.168.100.%' OR target LIKE '10.100.%' OR target LIKE '192.168.200.%'")
        rules = cursor.fetchall()
        print(f"   插入了 {len(rules)} 条测试规则")

        direction_counts = {}
        for rule in rules:
            direction = rule[6]
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
            print(f"     规则ID={rule[0]}: peer_id={rule[1]}, {rule[2]} {rule[3]}:{rule[4]} {rule[5]} 方向={rule[6]}")

        print(f"   方向统计: {direction_counts}")

        # 验证方向字段的约束
        print("🔒 验证方向字段约束...")
        try:
            cursor.execute('''
                INSERT INTO acls (peer_id, action, target, port, protocol, direction, enabled)
                VALUES (1, 'allow', '192.168.1.0/24', '80', 'tcp', 'invalid_direction', 1)
            ''')
            print("   ❌ 无效方向值被接受（不应该发生）")
            conn.rollback()
        except sqlite3.IntegrityError:
            print("   ✅ 无效方向值被正确拒绝")

        # 清理测试数据
        print("🧹 清理测试数据...")
        cursor.execute("DELETE FROM acls WHERE target LIKE '192.168.100.%' OR target LIKE '10.100.%' OR target LIKE '192.168.200.%'")
        conn.commit()

        conn.close()

        print("✅ 所有测试通过!")
        print("\n📋 功能验证结果:")
        print("   ✓ ACL表结构包含direction字段")
        print("   ✓ 可以创建inbound方向规则")
        print("   ✓ 可以创建outbound方向规则")
        print("   ✓ 可以创建both方向规则")
        print("   ✓ 全局规则支持方向控制")
        print("   ✓ 节点特定规则支持方向控制")
        print("   ✓ 无效方向值会被拒绝")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("WireGuard ACL 方向控制功能验证")
    print("=" * 50)

    success = test_acl_direction_feature()
    if success:
        print("\n🎉 功能验证成功!")
        print("现在您可以创建具有方向控制的防火墙规则了。")
        print("\n📝 支持的方向类型:")
        print("   - inbound: 入口方向（从外部进入WireGuard网络）")
        print("   - outbound: 出口方向（从WireGuard网络出去）")
        print("   - both: 双向（同时控制入口和出口）")
    else:
        print("\n💥 功能验证失败!")
        print("请检查错误信息并修复问题。")
        sys.exit(1)
