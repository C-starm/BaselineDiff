#!/usr/bin/env python3
"""
诊断脚本 - 检查为什么 commits 表为空
"""
import sys
import os
import sqlite3

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

import manifest_parser
import git_scanner
import database


def check_database():
    """检查数据库状态"""
    print("\n" + "="*60)
    print("1. 检查数据库")
    print("="*60)

    if not os.path.exists("db.sqlite3"):
        print("✗ 数据库文件不存在")
        return False

    print("✓ 数据库文件存在")

    # 检查表结构
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # 检查 manifests 表
    cursor.execute("SELECT COUNT(*) FROM manifests")
    manifest_count = cursor.fetchone()[0]
    print(f"  - manifests 表: {manifest_count} 条记录")

    # 检查 commits 表
    cursor.execute("SELECT COUNT(*) FROM commits")
    commit_count = cursor.fetchone()[0]
    print(f"  - commits 表: {commit_count} 条记录")

    if manifest_count > 0:
        cursor.execute("SELECT project, remote_url, path FROM manifests LIMIT 3")
        print("\n  前3个 manifest 项目:")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[2]}")

    conn.close()

    if commit_count == 0:
        print("\n⚠ commits 表为空，继续诊断...")
        return False
    else:
        print("\n✓ commits 表有数据，诊断完成")
        return True


def check_manifest(repo_path: str):
    """检查 manifest 解析"""
    print("\n" + "="*60)
    print(f"2. 检查 manifest 解析: {repo_path}")
    print("="*60)

    manifest_xml = os.path.join(repo_path, ".repo", "manifest.xml")

    if not os.path.exists(repo_path):
        print(f"✗ 路径不存在: {repo_path}")
        return None

    if not os.path.exists(manifest_xml):
        print(f"✗ manifest.xml 不存在: {manifest_xml}")
        return None

    print(f"✓ manifest.xml 存在: {manifest_xml}")

    try:
        projects = manifest_parser.parse_manifest(repo_path)
        print(f"✓ 解析成功，找到 {len(projects)} 个项目")

        if len(projects) == 0:
            print("⚠ 警告: 项目列表为空")
            return []

        # 显示前5个项目
        print("\n  前5个项目:")
        for p in projects[:5]:
            print(f"    - {p['name']}")
            print(f"      路径: {p['path']}")
            print(f"      存在: {'✓' if os.path.exists(p['path']) else '✗'}")
            print(f"      是Git仓库: {'✓' if os.path.exists(os.path.join(p['path'], '.git')) else '✗'}")

        return projects

    except Exception as e:
        print(f"✗ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_git_scan(projects: list, max_count: int = 5):
    """检查 git 扫描"""
    print("\n" + "="*60)
    print(f"3. 检查 Git 扫描 (前{max_count}个项目)")
    print("="*60)

    if not projects:
        print("✗ 没有项目可扫描")
        return []

    test_projects = projects[:max_count]
    all_commits = []

    for idx, project in enumerate(test_projects, 1):
        print(f"\n[{idx}/{len(test_projects)}] 扫描: {project['name']}")
        print(f"  路径: {project['path']}")

        if not os.path.exists(project['path']):
            print(f"  ✗ 路径不存在")
            continue

        if not os.path.exists(os.path.join(project['path'], '.git')):
            print(f"  ✗ 不是 Git 仓库")
            continue

        try:
            scanner = git_scanner.GitScanner(project['path'], project['name'])
            commits = scanner.scan_commits(max_count=10)
            print(f"  ✓ 找到 {len(commits)} 个 commits")

            if commits:
                # 显示第一个 commit
                c = commits[0]
                print(f"    示例 commit:")
                print(f"      Hash: {c['hash'][:8]}...")
                print(f"      Author: {c['author']}")
                print(f"      Subject: {c['subject'][:50]}...")
                all_commits.extend(commits)
            else:
                print(f"  ⚠ 该项目没有 commits")

        except Exception as e:
            print(f"  ✗ 扫描失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n总计扫描到 {len(all_commits)} 个 commits")
    return all_commits


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Baseline Diff System - 诊断工具")
    print("="*60)

    # 1. 检查数据库
    db_ok = check_database()

    if db_ok:
        print("\n✓ 诊断完成：数据库正常")
        return

    # 2. 获取用户输入的路径
    if len(sys.argv) < 2:
        print("\n请提供 AOSP 或 Vendor 路径进行诊断:")
        print(f"  用法: python {sys.argv[0]} <repo_path>")
        print(f"  示例: python {sys.argv[0]} /path/to/aosp")
        sys.exit(1)

    repo_path = sys.argv[1]

    # 3. 检查 manifest
    projects = check_manifest(repo_path)

    if not projects:
        print("\n✗ 诊断失败：无法解析 manifest 或项目列表为空")
        print("\n可能的原因:")
        print("  1. manifest.xml 不存在")
        print("  2. manifest.xml 格式不正确")
        print("  3. manifest.xml 中没有 <project> 标签")
        sys.exit(1)

    # 4. 检查 git 扫描
    commits = check_git_scan(projects, max_count=3)

    if not commits:
        print("\n✗ 诊断失败：无法扫描到任何 commits")
        print("\n可能的原因:")
        print("  1. 项目路径不存在")
        print("  2. 项目路径不是 Git 仓库")
        print("  3. Git 仓库为空（没有 commits）")
        print("  4. Git 命令执行失败")
        sys.exit(1)

    # 5. 测试数据库插入
    print("\n" + "="*60)
    print("4. 测试数据库插入")
    print("="*60)

    try:
        print(f"尝试插入 {len(commits)} 个 commits...")
        database.bulk_insert_commits(commits)
        print("✓ 插入成功")

        # 验证
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM commits")
        count = cursor.fetchone()[0]
        conn.close()

        print(f"✓ 数据库中现在有 {count} 个 commits")

    except Exception as e:
        print(f"✗ 插入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*60)
    print("✓ 诊断完成：所有检查通过")
    print("="*60)
    print("\n建议:")
    print("  1. 检查 WebUI 中使用的路径是否正确")
    print("  2. 确认 manifest.xml 包含有效的项目")
    print("  3. 确认项目路径下的 Git 仓库不为空")


if __name__ == "__main__":
    main()
