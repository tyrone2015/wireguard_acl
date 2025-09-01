#!/usr/bin/env python3
"""
数据库迁移脚本：将ACL表的peer_id字段改为可空
运行此脚本前请备份数据库
"""

import sqlite3
import os
import sys

def migrate_acl_peer_id_nullable():
    """将ACL表的peer_id字段改为可空"""
    db_path = '/root/code-server/config/workspace/wireguard_acl/data/wireguard_acl.db'

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查当前表结构
        cursor.execute("PRAGMA table_info(acls)")
        columns = cursor.fetchall()
        print("当前ACL表结构:")
        for col in columns:
            print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")

        # 查找peer_id字段
        peer_id_col = None
        for col in columns:
            if col[1] == 'peer_id':
                peer_id_col = col
                break

        if not peer_id_col:
            print("错误: 未找到peer_id字段")
            return False

        if peer_id_col[3] == 0:  # 已经是可空的
            print("peer_id字段已经是可空的，无需迁移")
            conn.close()
            return True

        print("开始迁移: 将peer_id字段改为可空...")

        # SQLite不支持直接ALTER COLUMN修改NULL约束
        # 需要重新创建表
        print("创建新表结构...")
        cursor.execute('''
            CREATE TABLE acls_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                peer_id INTEGER,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                port TEXT NOT NULL,
                protocol TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (peer_id) REFERENCES peers (id)
            )
        ''')

        # 复制数据
        print("复制现有数据...")
        cursor.execute('''
            INSERT INTO acls_new (id, peer_id, action, target, port, protocol, enabled)
            SELECT id, peer_id, action, target, port, protocol, enabled FROM acls
        ''')

        # 删除旧表
        print("删除旧表...")
        cursor.execute('DROP TABLE acls')

        # 重命名新表
        print("重命名新表...")
        cursor.execute('ALTER TABLE acls_new RENAME TO acls')

        # 提交事务
        conn.commit()

        # 验证迁移结果
        cursor.execute("PRAGMA table_info(acls)")
        new_columns = cursor.fetchall()
        print("迁移后的ACL表结构:")
        for col in new_columns:
            print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")

        # 验证数据完整性
        cursor.execute("SELECT COUNT(*) FROM acls")
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
    print("此脚本将把ACL表的peer_id字段改为可空")
    print("支持创建不绑定节点的全局规则")
    print()

    # 确认操作
    response = input("是否继续？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("操作已取消")
        sys.exit(0)

    success = migrate_acl_peer_id_nullable()
    if success:
        print("\n✅ 迁移成功!")
        print("现在您可以创建不绑定节点的全局防火墙规则了。")
    else:
        print("\n❌ 迁移失败!")
        print("请检查错误信息并手动修复。")
        sys.exit(1)
