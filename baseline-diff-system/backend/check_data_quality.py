#!/usr/bin/env python3
"""
数据质量检查工具
检查数据库中已有 commits 的解析质量，判断是否需要重新扫描
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def check_data_quality():
    """检查数据质量"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "数据质量检查" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")

    with database.get_db() as conn:
        # 1. 基本统计
        print("\n" + "=" * 60)
        print("基本统计")
        print("=" * 60)

        cursor = conn.execute("SELECT COUNT(*) as count FROM commits")
        total = cursor.fetchone()['count']
        print(f"总记录数: {total:,}")

        if total == 0:
            print("\n⚠️  数据库是空的，需要扫描数据")
            return False

        # 2. 检查空字段
        print("\n" + "=" * 60)
        print("检查必填字段")
        print("=" * 60)

        issues = []

        # 检查空 hash
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits WHERE hash IS NULL OR hash = ''")
        empty_hash = cursor.fetchone()['count']
        if empty_hash > 0:
            print(f"❌ 空 hash: {empty_hash:,} 条 ({empty_hash/total*100:.2f}%)")
            issues.append(("空 hash", empty_hash))
        else:
            print(f"✓ Hash: 全部正常")

        # 检查空 author
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits WHERE author IS NULL OR author = ''")
        empty_author = cursor.fetchone()['count']
        if empty_author > 0:
            print(f"❌ 空 author: {empty_author:,} 条 ({empty_author/total*100:.2f}%)")
            issues.append(("空 author", empty_author))
        else:
            print(f"✓ Author: 全部正常")

        # 检查空 date
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits WHERE date IS NULL OR date = ''")
        empty_date = cursor.fetchone()['count']
        if empty_date > 0:
            print(f"❌ 空 date: {empty_date:,} 条 ({empty_date/total*100:.2f}%)")
            issues.append(("空 date", empty_date))
        else:
            print(f"✓ Date: 全部正常")

        # 检查空 subject
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits WHERE subject IS NULL OR subject = ''")
        empty_subject = cursor.fetchone()['count']
        if empty_subject > 0:
            print(f"❌ 空 subject: {empty_subject:,} 条 ({empty_subject/total*100:.2f}%)")
            issues.append(("空 subject", empty_subject))
        else:
            print(f"✓ Subject: 全部正常")

        # 3. 检查 Change-Id
        print("\n" + "=" * 60)
        print("检查 Change-Id")
        print("=" * 60)

        cursor = conn.execute("SELECT COUNT(*) as count FROM commits WHERE change_id IS NOT NULL AND change_id != ''")
        with_change_id = cursor.fetchone()['count']
        print(f"包含 Change-Id: {with_change_id:,} / {total:,} ({with_change_id/total*100:.2f}%)")

        if with_change_id / total < 0.1:  # 少于 10% 有 Change-Id
            print("⚠️  Change-Id 比例很低，可能解析有问题")
            issues.append(("Change-Id 比例低", total - with_change_id))

        # 4. 检查异常数据
        print("\n" + "=" * 60)
        print("检查异常数据")
        print("=" * 60)

        # 检查 hash 长度（Git hash 应该是 40 个字符）
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM commits
            WHERE LENGTH(hash) != 40
        """)
        invalid_hash = cursor.fetchone()['count']
        if invalid_hash > 0:
            print(f"❌ Hash 长度异常: {invalid_hash:,} 条")
            issues.append(("Hash 长度异常", invalid_hash))
        else:
            print(f"✓ Hash 长度: 全部正常")

        # 检查 subject 中是否包含分隔符（说明解析可能有问题）
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM commits
            WHERE subject LIKE '%||%'
        """)
        separator_in_subject = cursor.fetchone()['count']
        if separator_in_subject > 0:
            print(f"⚠️  Subject 包含 '||': {separator_in_subject:,} 条（可能解析有误）")
            issues.append(("Subject 包含分隔符", separator_in_subject))
        else:
            print(f"✓ Subject 格式: 全部正常")

        # 5. 抽样检查
        print("\n" + "=" * 60)
        print("数据抽样检查（前 3 条）")
        print("=" * 60)

        cursor = conn.execute("SELECT * FROM commits LIMIT 3")
        samples = cursor.fetchall()

        for idx, row in enumerate(samples, 1):
            commit = dict(row)
            print(f"\n[样本 {idx}]")
            print(f"  Hash:      {commit['hash'][:16]}...")
            print(f"  Author:    {commit['author'][:40]}...")
            print(f"  Date:      {commit['date']}")
            print(f"  Subject:   {commit['subject'][:60]}...")
            print(f"  Change-Id: {commit['change_id'] or '(无)'}")
            print(f"  Message:   {(commit['message'] or '')[:80]}...")

        # 6. 总结
        print("\n" + "=" * 60)
        print("质量评估")
        print("=" * 60)

        if not issues:
            print("\n✅ 数据质量良好，无需重新扫描")
            print("\n建议操作:")
            print("  1. 确保已添加性能优化索引: python3 optimize_db.py")
            print("  2. 直接使用现有数据即可")
            return True
        else:
            print(f"\n⚠️  发现 {len(issues)} 个问题:")
            total_affected = 0
            for issue_name, count in issues:
                print(f"  • {issue_name}: {count:,} 条")
                total_affected += count

            affected_percent = total_affected / total * 100 if total > 0 else 0

            print(f"\n受影响记录: {total_affected:,} / {total:,} ({affected_percent:.2f}%)")

            if affected_percent > 5:  # 超过 5% 有问题
                print("\n❌ 建议重新扫描")
                print("  问题较多，建议重新扫描以获得完整准确的数据")
                return False
            else:
                print("\n✓ 可以继续使用")
                print("  问题较少，可以继续使用现有数据")
                print("  如果需要完美数据，可以选择重新扫描")
                return True


def main():
    """主函数"""
    try:
        quality_ok = check_data_quality()

        print("\n" + "=" * 60)
        print("最终建议")
        print("=" * 60)

        if quality_ok:
            print("\n✅ 数据质量良好")
            print("\n后续操作:")
            print("  1. 运行: python3 optimize_db.py（添加索引优化性能）")
            print("  2. 启动服务测试筛选速度")
            print("  3. 如果速度满意，无需重新扫描")
        else:
            print("\n⚠️  建议重新扫描")
            print("\n重新扫描步骤:")
            print("  1. 备份现有数据库: cp db.sqlite3 db.sqlite3.backup")
            print("  2. 清空数据: python3 -c 'import database; database.clear_all_commits()'")
            print("  3. 启动后端服务")
            print("  4. 在前端重新执行扫描")
            print("\n注意: 重新扫描需要较长时间（取决于项目数量和 commits 数量）")

        return 0 if quality_ok else 1

    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
