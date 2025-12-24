#!/usr/bin/env python3
"""
快速测试 API 端点
用于验证后端 API 是否正常工作
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def test_stats():
    """测试统计信息查询"""
    print("\n" + "=" * 60)
    print("测试 /api/stats 查询")
    print("=" * 60)

    try:
        with database.get_db() as conn:
            # 总数
            cursor = conn.execute("SELECT COUNT(*) as count FROM commits")
            total = cursor.fetchone()['count']
            print(f"✅ 总 commits: {total:,}")

            # 按 source 分组
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM commits
                GROUP BY source
            """)
            print("\n按来源统计:")
            for row in cursor.fetchall():
                source = row['source'] if row['source'] else 'NULL'
                count = row['count']
                print(f"   {source:12} : {count:,}")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata():
    """测试元数据查询"""
    print("\n" + "=" * 60)
    print("测试 /api/metadata 查询")
    print("=" * 60)

    try:
        # 项目列表
        projects = database.get_unique_projects()
        print(f"✅ 项目总数: {len(projects):,}")
        if len(projects) > 0:
            print(f"\n前 10 个项目:")
            for p in projects[:10]:
                print(f"   - {p}")

        # 作者列表
        authors = database.get_unique_authors()
        print(f"\n✅ 作者总数: {len(authors):,}")
        if len(authors) > 0:
            print(f"\n前 10 个作者:")
            for a in authors[:10]:
                print(f"   - {a}")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_commits():
    """测试 commits 分页查询"""
    print("\n" + "=" * 60)
    print("测试 /api/commits 查询")
    print("=" * 60)

    try:
        # 获取前 10 条
        commits = database.get_all_commits(limit=10)
        print(f"✅ 成功获取 {len(commits)} 条 commits")

        if len(commits) > 0:
            print(f"\n第一条 commit:")
            c = commits[0]
            print(f"   项目: {c['project']}")
            print(f"   Hash: {c['hash'][:12]}...")
            print(f"   作者: {c['author']}")
            print(f"   标题: {c['subject'][:60]}...")
            print(f"   来源: {c['source']}")

        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "API 测试工具" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 1. 测试统计信息
    results.append(("统计信息", test_stats()))

    # 2. 测试元数据
    results.append(("元数据", test_metadata()))

    # 3. 测试 commits
    results.append(("Commits", test_commits()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"   {name:12} : {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ 所有测试通过！后端 API 工作正常。")
        print("\n如果前端仍然显示为空，请检查:")
        print("   1. 浏览器控制台（F12）是否有错误")
        print("   2. Network 标签中的 API 请求是否成功")
        print("   3. 前端是否正确调用了这些 API")
    else:
        print("\n❌ 部分测试失败，请检查数据库或代码。")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
