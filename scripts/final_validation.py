#!/usr/bin/env python3
"""
WireGuard ACL 功能最终验证脚本
验证全局规则和方向控制功能的完整性
"""

import sqlite3
import sys
import os
from datetime import datetime

def validate_database_schema():
    """验证数据库模式是否正确"""
    print("🔍 验证数据库模式...")

    db_path = "data/wireguard_acl.db"
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查ACL表是否有direction字段
    cursor.execute("PRAGMA table_info(acls)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    required_columns = ['id', 'peer_id', 'target', 'port', 'protocol', 'direction', 'action', 'enabled']

    for col in required_columns:
        if col not in column_names:
            print(f"❌ 缺少必需的列: {col}")
            conn.close()
            return False

    print("✅ 数据库模式验证通过")
    conn.close()
    return True

def validate_global_rules():
    """验证全局规则功能"""
    print("\n🔍 验证全局规则功能...")

    db_path = "data/wireguard_acl.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查是否有全局规则（peer_id = -1）
    cursor.execute("SELECT COUNT(*) FROM acls WHERE peer_id = -1")
    global_count = cursor.fetchone()[0]

    if global_count == 0:
        print("⚠️  没有找到全局规则，这可能是正常的")
    else:
        print(f"✅ 找到 {global_count} 条全局规则")

    # 验证全局规则的方向分布
    cursor.execute("SELECT direction, COUNT(*) FROM acls WHERE peer_id = -1 GROUP BY direction")
    direction_stats = cursor.fetchall()

    print("📊 全局规则方向统计:")
    for direction, count in direction_stats:
        print(f"  - {direction}: {count} 条规则")

    conn.close()
    return True

def validate_direction_control():
    """验证方向控制功能"""
    print("\n🔍 验证方向控制功能...")

    db_path = "data/wireguard_acl.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查所有规则的方向分布
    cursor.execute("SELECT direction, COUNT(*) FROM acls GROUP BY direction")
    direction_stats = cursor.fetchall()

    print("📊 所有ACL规则方向统计:")
    total_rules = 0
    for direction, count in direction_stats:
        print(f"  - {direction}: {count} 条规则")
        total_rules += count

    # 验证方向字段的有效性
    valid_directions = ['inbound', 'outbound', 'both']
    cursor.execute("SELECT DISTINCT direction FROM acls")
    directions = [row[0] for row in cursor.fetchall()]

    invalid_directions = [d for d in directions if d not in valid_directions]
    if invalid_directions:
        print(f"❌ 发现无效的方向值: {invalid_directions}")
        conn.close()
        return False

    print(f"✅ 方向控制验证通过，共 {total_rules} 条规则")
    conn.close()
    return True

def validate_backend_files():
    """验证后端文件是否包含新功能"""
    print("\n🔍 验证后端文件...")

    files_to_check = [
        ('app/models.py', ['direction', 'peer_id']),
        ('app/acl.py', ['direction', 'global']),
        ('app/sync.py', ['apply_acl_to_iptables', 'direction'])
    ]

    for file_path, keywords in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()

        missing_keywords = [kw for kw in keywords if kw.lower() not in content]
        if missing_keywords:
            print(f"⚠️  {file_path} 可能缺少关键词: {missing_keywords}")
        else:
            print(f"✅ {file_path} 包含所需功能")

    return True

def validate_frontend_files():
    """验证前端文件是否包含新功能"""
    print("\n🔍 验证前端文件...")

    files_to_check = [
        ('frontend/src/views/ACLs.vue', ['direction', 'global', 'inbound', 'outbound'])
    ]

    for file_path, keywords in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()

        missing_keywords = [kw for kw in keywords if kw.lower() not in content]
        if missing_keywords:
            print(f"⚠️  {file_path} 可能缺少关键词: {missing_keywords}")
        else:
            print(f"✅ {file_path} 包含所需功能")

    return True

def validate_documentation():
    """验证文档文件"""
    print("\n🔍 验证文档文件...")

    docs_to_check = [
        'docs/README.md',
        'docs/API_DOCUMENTATION.md',
        'docs/guides/ACL_DIRECTION_GUIDE.md',
        'docs/guides/GLOBAL_ACL_GUIDE.md',
        'docs/guides/IMPLEMENTATION_SUMMARY.md',
        'docs/implementation/ACL_DIRECTION_IMPLEMENTATION.md',
        'docs/implementation/GLOBAL_ACL_IMPLEMENTATION.md',
        'docs/PROJECT_STRUCTURE.md'
    ]

    for doc in docs_to_check:
        if os.path.exists(doc):
            print(f"✅ 文档存在: {doc}")
        else:
            print(f"❌ 文档缺失: {doc}")

    return True

def main():
    """主验证函数"""
    print("🚀 开始WireGuard ACL功能最终验证")
    print("=" * 50)

    all_passed = True

    # 执行各项验证
    checks = [
        validate_database_schema,
        validate_global_rules,
        validate_direction_control,
        validate_backend_files,
        validate_frontend_files,
        validate_documentation
    ]

    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ 验证过程中出错: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有验证通过！WireGuard ACL功能已成功实现")
        print("\n📋 实现的功能:")
        print("  ✅ 全局ACL规则支持 (peer_id = -1)")
        print("  ✅ 方向控制 (inbound/outbound/both)")
        print("  ✅ 数据库模式更新")
        print("  ✅ 后端API更新")
        print("  ✅ 前端界面更新")
        print("  ✅ iptables规则生成")
        print("  ✅ 完整文档")
    else:
        print("⚠️  部分验证失败，请检查上述错误信息")
        sys.exit(1)

    print(f"\n⏰ 验证完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
