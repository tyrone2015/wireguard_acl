#!/usr/bin/env python3
"""
数据库迁移脚本：从peers表中移除endpoint字段
运行此脚本前请备份数据库
"""

import sqlite3
import os
import sys

def migrate_peers_remove_endpoint():
    """从peers表中移除endpoint字段"""
    db_path = '/root/code-server/config/workspace/wireguard_acl/data/wireguard_acl.db'

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查当前peers表结构
        cursor.execute("PRAGMA table_info(peers)")
        columns = cursor.fetchall()
        print("当前peers表结构:")
        for col in columns:
            print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")

        # 检查是否存在endpoint字段
        has_endpoint = any(col[1] == 'endpoint' for col in columns)

        if not has_endpoint:
            print("endpoint字段不存在，无需迁移")
            conn.close()
            return True

        print("开始迁移: 移除endpoint字段...")

        # SQLite不支持直接ALTER TABLE DROP COLUMN
        # 需要重新创建表
        print("创建新表结构...")
        cursor.execute('''
            CREATE TABLE peers_new (
                id INTEGER NULL,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                allowed_ips TEXT NOT NULL,
                client_allowed_ips TEXT NOT NULL,
                remark TEXT NULL,
                status BOOLEAN NULL,
                peer_ip TEXT NOT NULL,
                keepalive INTEGER NULL,
                preshared_key TEXT NULL,
                created_at DATETIME NULL
            )
        ''')

        # 复制数据，排除endpoint字段
        print("复制现有数据...")
        cursor.execute('''
            INSERT INTO peers_new (id, public_key, private_key, allowed_ips, client_allowed_ips, remark, status, peer_ip, keepalive, preshared_key, created_at)
            SELECT id, public_key, private_key, allowed_ips, client_allowed_ips, remark, status, peer_ip, keepalive, preshared_key, created_at FROM peers
        ''')

        # 删除旧表
        print("删除旧表...")
        cursor.execute('DROP TABLE peers')

        # 重命名新表
        print("重命名新表...")
        cursor.execute('ALTER TABLE peers_new RENAME TO peers')

        # 提交事务
        conn.commit()

        # 验证迁移结果
        cursor.execute("PRAGMA table_info(peers)")
        new_columns = cursor.fetchall()
        print("迁移后的peers表结构:")
        for col in new_columns:
            print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")

        # 验证数据完整性
        cursor.execute("SELECT COUNT(*) FROM peers")
        count = cursor.fetchone()[0]
        print(f"迁移后记录数: {count}")

        conn.close()
        print("迁移完成!")
        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == "__main__":
    print("WireGuard ACL 数据库迁移工具")
    print("=" * 40)
    print("此脚本将从peers表中移除endpoint字段")
    print("端点配置将移至系统设置中统一管理")
    print()

    # 确认操作
    response = input("是否继续？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("操作已取消")
        sys.exit(0)

    success = migrate_peers_remove_endpoint()
    if success:
        print("\n✅ 迁移成功!")
        print("现在端点配置将在系统设置中统一管理。")
    else:
        print("\n❌ 迁移失败!")
        print("请检查错误信息并手动修复。")
        sys.exit(1)
