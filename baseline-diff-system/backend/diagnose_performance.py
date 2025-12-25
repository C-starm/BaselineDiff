#!/usr/bin/env python3
"""
性能诊断工具
诊断数据库查询性能问题
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def check_database_size():
    """检查数据库大小和记录数"""
    print("\n" + "=" * 60)
    print("数据库基本信息")
    print("=" * 60)

    db_path = database.DB_PATH
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / 1024 / 1024
        size_gb = size_mb / 1024

        if size_gb >= 1:
            print(f"数据库文件大小: {size_gb:.2f} GB")
        else:
            print(f"数据库文件大小: {size_mb:.2f} MB")

    with database.get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits")
        count = cursor.fetchone()['count']
        print(f"Commits 总数: {count:,}")

        if count == 0:
            print("\n⚠️  数据库是空的！请先导入数据或复制已有数据库文件。")
            return False

    return True


def check_indexes():
    """检查索引情况"""
    print("\n" + "=" * 60)
    print("索引检查")
    print("=" * 60)

    with database.get_db() as conn:
        cursor = conn.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type='index' AND tbl_name='commits'
            ORDER BY name
        """)

        indexes = cursor.fetchall()

        required_indexes = {
            'idx_commits_date': False,
            'idx_commits_author': False,
            'idx_commits_source': False,
            'idx_commits_project': False,
        }

        print("\n已创建的索引:")
        for idx in indexes:
            idx_name = idx['name']
            print(f"  ✓ {idx_name}")
            if idx_name in required_indexes:
                required_indexes[idx_name] = True

        print("\n缺失的关键索引:")
        missing = [name for name, exists in required_indexes.items() if not exists]
        if missing:
            for name in missing:
                print(f"  ✗ {name}")
            return False
        else:
            print("  (无)")
            return True


def test_query_performance():
    """测试查询性能"""
    print("\n" + "=" * 60)
    print("查询性能测试")
    print("=" * 60)

    tests = []

    # 测试 1: 简单查询前 1000 条
    print("\n[1/6] 测试无筛选查询（LIMIT 1000）...")
    start = time.time()
    commits = database.get_all_commits(limit=1000, offset=0)
    elapsed = time.time() - start
    tests.append(("无筛选查询 1000 条", len(commits), elapsed))
    print(f"  结果: {len(commits)} 条")
    print(f"  耗时: {elapsed:.3f} 秒")

    # 测试 2: 统计总数
    print("\n[2/6] 测试统计查询（COUNT）...")
    start = time.time()
    count = database.get_commits_count()
    elapsed = time.time() - start
    tests.append(("统计总数", count, elapsed))
    print(f"  结果: {count:,} 条")
    print(f"  耗时: {elapsed:.3f} 秒")

    # 测试 3: 按 source 筛选
    print("\n[3/6] 测试按 source 筛选...")
    start = time.time()
    commits = database.get_all_commits(limit=1000, source='common')
    elapsed = time.time() - start
    tests.append(("source=common 筛选", len(commits), elapsed))
    print(f"  结果: {len(commits)} 条")
    print(f"  耗时: {elapsed:.3f} 秒")

    # 测试 4: 按 project 筛选
    print("\n[4/6] 测试按 project 筛选...")
    projects = database.get_unique_projects()
    if projects:
        project = projects[0]
        start = time.time()
        commits = database.get_all_commits(limit=100, project=project)
        elapsed = time.time() - start
        tests.append(("project 筛选", len(commits), elapsed))
        print(f"  项目: {project}")
        print(f"  结果: {len(commits)} 条")
        print(f"  耗时: {elapsed:.3f} 秒")

    # 测试 5: 日期范围筛选
    print("\n[5/6] 测试日期范围筛选...")
    start = time.time()
    commits = database.get_all_commits(
        limit=1000,
        date_from='2024-01-01',
        date_to='2024-12-31'
    )
    elapsed = time.time() - start
    tests.append(("日期范围筛选", len(commits), elapsed))
    print(f"  日期: 2024-01-01 ~ 2024-12-31")
    print(f"  结果: {len(commits)} 条")
    print(f"  耗时: {elapsed:.3f} 秒")

    # 测试 6: 组合筛选
    print("\n[6/6] 测试组合筛选（source + date）...")
    start = time.time()
    commits = database.get_all_commits(
        limit=1000,
        source='common',
        date_from='2024-01-01',
        date_to='2024-12-31'
    )
    elapsed = time.time() - start
    tests.append(("组合筛选", len(commits), elapsed))
    print(f"  结果: {len(commits)} 条")
    print(f"  耗时: {elapsed:.3f} 秒")

    return tests


def analyze_slow_queries(tests):
    """分析慢查询"""
    print("\n" + "=" * 60)
    print("性能分析")
    print("=" * 60)

    slow_threshold = 1.0  # 1秒阈值

    slow_queries = [(name, count, elapsed) for name, count, elapsed in tests if elapsed > slow_threshold]

    if slow_queries:
        print(f"\n⚠️  发现慢查询（> {slow_threshold}秒）:")
        for name, count, elapsed in slow_queries:
            print(f"  • {name}: {elapsed:.3f} 秒")

        print("\n可能的原因:")
        print("  1. 缺少索引或索引未生效")
        print("  2. 数据库文件过大需要 VACUUM")
        print("  3. SQLite 配置未优化")
        print("  4. 查询计划未使用索引")

        return False
    else:
        print(f"\n✓ 所有查询性能良好（< {slow_threshold}秒）")
        for name, count, elapsed in tests:
            print(f"  • {name}: {elapsed:.3f} 秒")
        return True


def check_query_plan():
    """检查查询执行计划"""
    print("\n" + "=" * 60)
    print("查询执行计划分析")
    print("=" * 60)

    with database.get_db() as conn:
        # 检查简单查询的执行计划
        print("\n查询计划（无筛选 LIMIT 1000）:")
        cursor = conn.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM commits
            ORDER BY date DESC
            LIMIT 1000
        """)
        for row in cursor.fetchall():
            print(f"  {dict(row)}")

        # 检查筛选查询的执行计划
        print("\n查询计划（source 筛选）:")
        cursor = conn.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM commits
            WHERE source = 'common'
            ORDER BY date DESC
            LIMIT 1000
        """)
        for row in cursor.fetchall():
            plan = dict(row)
            print(f"  {plan}")

            # 检查是否使用了索引
            detail = str(plan.get('detail', ''))
            if 'INDEX' in detail.upper():
                print(f"    ✓ 使用索引")
            elif 'SCAN' in detail.upper():
                print(f"    ⚠️  全表扫描（性能差）")


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "性能诊断工具" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")

    # 1. 检查数据库
    if not check_database_size():
        return 1

    # 2. 检查索引
    indexes_ok = check_indexes()

    # 3. 检查查询执行计划
    check_query_plan()

    # 4. 测试查询性能
    tests = test_query_performance()

    # 5. 分析结果
    performance_ok = analyze_slow_queries(tests)

    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    if indexes_ok and performance_ok:
        print("\n✓ 数据库性能正常")
        print("\n如果前端仍然很慢，可能的原因:")
        print("  1. 网络延迟（检查浏览器 Network 标签）")
        print("  2. 前端渲染慢（数据量大时）")
        print("  3. 后端服务器性能限制")
    else:
        print("\n⚠️  发现性能问题")
        if not indexes_ok:
            print("\n建议操作:")
            print("  运行: python3 optimize_db.py")
            print("  这将创建缺失的索引并优化数据库")
        if not performance_ok:
            print("\n进一步调查:")
            print("  1. 检查查询执行计划是否使用索引")
            print("  2. 运行 VACUUM 清理数据库")
            print("  3. 考虑增加 SQLite 内存缓存")

    return 0 if (indexes_ok and performance_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
