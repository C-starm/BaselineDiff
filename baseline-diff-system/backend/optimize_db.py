#!/usr/bin/env python3
"""
数据库优化脚本
为大数据量场景添加索引，提升查询性能
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def print_header(title):
    """打印标题"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + f" {title}".ljust(58) + "║")
    print("╚" + "═" * 58 + "╝")


def check_existing_indexes():
    """检查现有索引"""
    print("\n检查现有索引...")

    with database.get_db() as conn:
        cursor = conn.execute("""
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type='index'
            AND tbl_name='commits'
            ORDER BY name
        """)

        indexes = cursor.fetchall()
        if indexes:
            print(f"✅ 找到 {len(indexes)} 个索引:")
            for idx in indexes:
                print(f"   - {idx['name']}")
        else:
            print("⚠️  没有找到索引")

        return [idx['name'] for idx in indexes]


def create_indexes():
    """创建索引"""
    print("\n" + "=" * 60)
    print("创建性能优化索引")
    print("=" * 60)

    indexes_to_create = [
        ("idx_commits_source", "CREATE INDEX IF NOT EXISTS idx_commits_source ON commits(source)"),
        ("idx_commits_project", "CREATE INDEX IF NOT EXISTS idx_commits_project ON commits(project)"),
        ("idx_commits_author", "CREATE INDEX IF NOT EXISTS idx_commits_author ON commits(author)"),
        ("idx_commits_date", "CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(date DESC)"),
        ("idx_commits_change_id", "CREATE INDEX IF NOT EXISTS idx_commits_change_id ON commits(change_id)"),
    ]

    with database.get_db() as conn:
        for idx_name, sql in indexes_to_create:
            print(f"\n创建索引: {idx_name}")
            start_time = time.time()

            try:
                conn.execute(sql)
                conn.commit()

                elapsed = time.time() - start_time
                print(f"   ✅ 完成 ({elapsed:.2f} 秒)")

            except Exception as e:
                print(f"   ❌ 失败: {e}")


def analyze_database():
    """分析数据库，优化查询计划"""
    print("\n" + "=" * 60)
    print("分析数据库")
    print("=" * 60)

    print("\n运行 ANALYZE 命令...")
    start_time = time.time()

    try:
        with database.get_db() as conn:
            conn.execute("ANALYZE")
            conn.commit()

        elapsed = time.time() - start_time
        print(f"✅ 完成 ({elapsed:.2f} 秒)")

    except Exception as e:
        print(f"❌ 失败: {e}")


def vacuum_database():
    """清理数据库，回收空间"""
    print("\n" + "=" * 60)
    print("清理数据库（可选，可能需要较长时间）")
    print("=" * 60)

    response = input("\n是否执行 VACUUM？这会清理数据库并回收空间。(y/N): ")

    if response.lower() != 'y':
        print("跳过 VACUUM")
        return

    print("\n运行 VACUUM 命令...")
    print("⚠️  警告：大数据库可能需要数分钟...")
    start_time = time.time()

    try:
        with database.get_db() as conn:
            conn.execute("VACUUM")

        elapsed = time.time() - start_time
        print(f"✅ 完成 ({elapsed:.2f} 秒)")

    except Exception as e:
        print(f"❌ 失败: {e}")


def test_query_performance():
    """测试查询性能"""
    print("\n" + "=" * 60)
    print("测试查询性能")
    print("=" * 60)

    queries = [
        ("统计总数", "SELECT COUNT(*) FROM commits"),
        ("按来源统计", "SELECT source, COUNT(*) FROM commits GROUP BY source"),
        ("获取唯一项目", "SELECT DISTINCT project FROM commits"),
        ("获取唯一作者", "SELECT DISTINCT author FROM commits"),
        ("获取最新1000条", "SELECT * FROM commits ORDER BY date DESC LIMIT 1000"),
    ]

    with database.get_db() as conn:
        for name, sql in queries:
            print(f"\n测试: {name}")
            start_time = time.time()

            try:
                cursor = conn.execute(sql)
                result = cursor.fetchall()

                elapsed = time.time() - start_time
                print(f"   ✅ 完成 ({elapsed:.2f} 秒) - 返回 {len(result)} 行")

            except Exception as e:
                print(f"   ❌ 失败: {e}")


def get_database_size():
    """获取数据库大小"""
    db_path = database.DB_PATH
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / 1024 / 1024
        size_gb = size_mb / 1024

        if size_gb >= 1:
            return f"{size_gb:.2f} GB"
        else:
            return f"{size_mb:.2f} MB"
    return "未知"


def main():
    """主函数"""
    print_header("数据库性能优化工具")

    print(f"\n数据库文件: {database.DB_PATH}")
    print(f"数据库大小: {get_database_size()}")

    # 1. 检查现有索引
    existing_indexes = check_existing_indexes()

    # 2. 创建索引
    print("\n" + "=" * 60)
    if existing_indexes:
        response = input("发现已有索引，是否重新创建？(y/N): ")
        if response.lower() != 'y':
            print("跳过创建索引")
        else:
            create_indexes()
    else:
        create_indexes()

    # 3. 分析数据库
    analyze_database()

    # 4. 可选：清理数据库
    vacuum_database()

    # 5. 测试性能
    test_query_performance()

    # 总结
    print("\n" + "=" * 60)
    print("优化完成")
    print("=" * 60)
    print("\n优化效果:")
    print("  • 查询速度应该明显提升")
    print("  • 特别是按项目、作者、来源筛选时")
    print("  • 统计信息加载应该更快")
    print("\n建议:")
    print("  • 重启后端服务使优化生效")
    print("  • 刷新浏览器页面")
    print("  • 观察加载速度是否改善")


if __name__ == "__main__":
    main()
