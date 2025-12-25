#!/usr/bin/env python3
"""
分析 common commits 的两边信息
验证同一个 Change-Id 在两边的不同表现
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def analyze_common_commits():
    """分析 common commits"""
    print("\n" + "=" * 70)
    print("Common Commits 分析")
    print("=" * 70)

    with database.get_db() as conn:
        # 查询有多个 hash 的 Change-Id (说明两边都有)
        cursor = conn.execute("""
            SELECT change_id, COUNT(*) as count
            FROM commits
            WHERE change_id IS NOT NULL
              AND change_id != ''
              AND source = 'common'
            GROUP BY change_id
            HAVING count > 1
            LIMIT 10
        """)

        multi_hash_change_ids = cursor.fetchall()

        if not multi_hash_change_ids:
            print("\n⚠️  未找到同一 Change-Id 对应多个 hash 的 common commits")
            print("可能原因:")
            print("  1. 数据库中还没有 common commits")
            print("  2. 每个 Change-Id 只有一个 commit")
            return

        print(f"\n找到 {len(multi_hash_change_ids)} 个 Change-Id 在两边都有不同的 commits")

        # 显示详细信息
        for row in multi_hash_change_ids[:5]:
            change_id = row['change_id']
            count = row['count']

            print(f"\n{'='*70}")
            print(f"Change-Id: {change_id} (共 {count} 个 commits)")
            print("-" * 70)

            # 查询该 Change-Id 的所有 commits
            cursor = conn.execute("""
                SELECT c.hash, c.project, c.subject, c.reviewed_on, m.remote_url
                FROM commits c
                LEFT JOIN manifests m ON c.project = m.project
                WHERE c.change_id = ?
                ORDER BY c.project
            """, (change_id,))

            commits = cursor.fetchall()

            for idx, commit in enumerate(commits, 1):
                commit_dict = dict(commit)
                print(f"\nCommit {idx}:")
                print(f"  Project:     {commit_dict['project']}")
                print(f"  Hash:        {commit_dict['hash'][:16]}...")
                print(f"  Subject:     {commit_dict['subject'][:60]}...")

                # 构建 URL
                if commit_dict['reviewed_on']:
                    url = commit_dict['reviewed_on']
                elif commit_dict['remote_url']:
                    url = f"{commit_dict['remote_url']}/{commit_dict['project']}/commit/{commit_dict['hash']}"
                else:
                    url = None

                print(f"  URL:         {url}")


def show_current_structure():
    """显示当前数据结构"""
    print("\n" + "=" * 70)
    print("当前数据结构分析")
    print("=" * 70)

    with database.get_db() as conn:
        # 统计
        cursor = conn.execute("""
            SELECT
                source,
                COUNT(*) as total_commits,
                COUNT(DISTINCT change_id) as unique_change_ids
            FROM commits
            WHERE change_id IS NOT NULL AND change_id != ''
            GROUP BY source
        """)

        print("\n按 source 统计:")
        for row in cursor.fetchall():
            print(f"  {row['source']:12}: {row['total_commits']:,} commits, "
                  f"{row['unique_change_ids']:,} unique Change-Ids")

        # 检查是否有重复的 Change-Id
        cursor = conn.execute("""
            SELECT
                COUNT(DISTINCT change_id) as unique_change_ids,
                COUNT(*) as total_commits
            FROM commits
            WHERE change_id IS NOT NULL AND change_id != ''
        """)
        stats = cursor.fetchone()

        if stats:
            unique = stats['unique_change_ids']
            total = stats['total_commits']
            duplicates = total - unique

            print(f"\n总体统计:")
            print(f"  唯一 Change-Ids: {unique:,}")
            print(f"  总 commits:      {total:,}")
            print(f"  重复数量:        {duplicates:,}")

            if duplicates > 0:
                print(f"\n  → 有 {duplicates:,} 个 commits 对应相同的 Change-Id")
                print(f"    （说明同一个改动在不同地方被 cherry-pick）")


def suggest_solution():
    """建议解决方案"""
    print("\n" + "=" * 70)
    print("显示方案建议")
    print("=" * 70)

    print("""
方案 1: 后端分组（推荐）
-------
在后端查询时，对于 common commits：
- 按 Change-Id 分组
- 收集每个 Change-Id 对应的所有 commits
- 返回结构：
  {
    "change_id": "I12345",
    "subject": "Fix bug",
    "commits": [
      {"hash": "abc", "project": "aosp/project1", "url": "..."},
      {"hash": "def", "project": "vendor/project2", "url": "..."}
    ]
  }

优点：
✓ 数据结构清晰
✓ 前端容易展示
✓ 可以显示两边的差异（hash、project 不同）

方案 2: 前端合并
-------
后端返回原始数据，前端检测相同 Change-Id 并合并显示

优点：
✓ 后端改动小
✓ 灵活性高

缺点：
✗ 前端逻辑复杂
✗ 分页时可能遗漏

推荐：方案 1
""")


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "Common Commits 分析" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")

    # 显示当前结构
    show_current_structure()

    # 分析 common commits
    analyze_common_commits()

    # 建议方案
    suggest_solution()

    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
