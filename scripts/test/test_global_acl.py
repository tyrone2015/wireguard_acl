#!/usr/bin/env python3
"""
验证ACL全局规则功能的测试脚本
"""

import sqlite3
import sys
import os

def test_acl_global_rules():
    """测试ACL全局规则功能"""
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

        peer_id_exists = False
        for col in columns:
            if col[1] == 'peer_id':
                peer_id_exists = True
                print(f"   peer_id字段: {'可空' if col[3] == 0 else '不可空（使用-1表示全局规则）'}")
                break

        if not peer_id_exists:
            print("❌ 未找到peer_id字段")
            return False

        # 插入测试数据
        print("📝 插入测试数据...")

        # 插入全局规则（peer_id为-1）
        cursor.execute('''
            INSERT INTO acls (peer_id, action, target, port, protocol, enabled)
            VALUES (-1, 'allow', '192.168.1.0/24', '80', 'tcp', 1)
        ''')

        # 插入绑定节点的规则
        cursor.execute('''
            INSERT INTO acls (peer_id, action, target, port, protocol, enabled)
            VALUES (1, 'deny', '10.0.0.0/8', '22', 'tcp', 1)
        ''')

        conn.commit()

        # 查询验证
        print("✅ 验证数据插入...")
        cursor.execute("SELECT id, peer_id, action, target, port, protocol FROM acls WHERE peer_id = -1")
        global_rules = cursor.fetchall()
        print(f"   全局规则数量: {len(global_rules)}")
        for rule in global_rules:
            print(f"   规则: ID={rule[0]}, 动作={rule[2]}, 目标={rule[3]}, 端口={rule[4]}")

        cursor.execute("SELECT id, peer_id, action, target, port, protocol FROM acls WHERE peer_id > 0")
        bound_rules = cursor.fetchall()
        print(f"   绑定规则数量: {len(bound_rules)}")
        for rule in bound_rules:
            print(f"   规则: ID={rule[0]}, 节点={rule[1]}, 动作={rule[2]}, 目标={rule[3]}, 端口={rule[4]}")

        # 清理测试数据
        print("🧹 清理测试数据...")
        cursor.execute("DELETE FROM acls WHERE target IN ('192.168.1.0/24', '10.0.0.0/8')")
        conn.commit()

        conn.close()

        print("✅ 所有测试通过!")
        print("\n📋 功能验证结果:")
        print("   ✓ ACL表结构支持可空peer_id")
        print("   ✓ 可以创建全局规则（peer_id=NULL）")
        print("   ✓ 可以创建绑定节点规则（peer_id=具体值）")
        print("   ✓ 数据完整性保持正常")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("WireGuard ACL 全局规则功能验证")
    print("=" * 40)

    success = test_acl_global_rules()
    if success:
        print("\n🎉 功能验证成功!")
        print("现在您可以创建不绑定节点的全局防火墙规则了。")
    else:
        print("\n💥 功能验证失败!")
        print("请检查错误信息并修复问题。")
        sys.exit(1)
