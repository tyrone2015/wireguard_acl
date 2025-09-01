#!/usr/bin/env python3
"""
数据库迁移脚本：为ACL表添加direction字段
运行此脚本前请备份数据库
"""

import sqlite3
import os
import sys

def migrate_acl_add_direction():
    """为ACL表添加direction字段"""
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

        # 检查是否已有direction字段
        direction_exists = any(col[1] == 'direction' for col in columns)
        if direction_exists:
            print("direction字段已存在，无需迁移")
            conn.close()
            return True

        print("开始迁移: 添加direction字段...")

        # 先添加direction字段（SQLite会自动为新字段设置默认值）
        print("添加direction字段...")
        cursor.execute("ALTER TABLE acls ADD COLUMN direction TEXT NOT NULL DEFAULT 'both'")

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

        # 检查direction字段的值分布
        cursor.execute("SELECT direction, COUNT(*) FROM acls GROUP BY direction")
        direction_stats = cursor.fetchall()
        print("方向字段值分布:")
        for direction, count in direction_stats:
            print(f"  {direction}: {count} 条记录")

        conn.close()
        print("迁移完成!")
        return True

    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == "__main__":
    print("WireGuard ACL 方向字段迁移工具")
    print("=" * 40)
    print("此脚本将为ACL表添加direction字段")
    print("现有记录将默认设置为'双向'(both)")
    print()

    # 确认操作
    response = input("是否继续？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("操作已取消")
        sys.exit(0)

    success = migrate_acl_add_direction()
    if success:
        print("\n✅ 迁移成功!")
        print("现在ACL表支持方向控制功能了。")
    else:
        print("\n❌ 迁移失败!")
        print("请检查错误信息并手动修复。")
        sys.exit(1)
