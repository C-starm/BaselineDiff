#!/usr/bin/env python3
"""
测试 Git Log 解析器
验证解析逻辑能否正确处理各种格式的 commit
"""
import sys
import os
import tempfile
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from git_scanner import GitScanner


def create_test_repo():
    """创建测试 Git 仓库"""
    temp_dir = tempfile.mkdtemp()
    print(f"创建测试仓库: {temp_dir}")

    os.chdir(temp_dir)

    # 初始化 Git 仓库
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)

    # 创建第一个 commit（简单 commit）
    with open("file1.txt", "w") as f:
        f.write("test content")
    subprocess.run(["git", "add", "file1.txt"], check=True, capture_output=True)
    subprocess.run([
        "git", "commit", "-m",
        "Simple commit\n\nThis is a simple commit message.\n\nChange-Id: I1234567890abcdef"
    ], check=True, capture_output=True)

    # 创建第二个 commit（多行 message）
    with open("file2.txt", "w") as f:
        f.write("test content 2")
    subprocess.run(["git", "add", "file2.txt"], check=True, capture_output=True)
    subprocess.run([
        "git", "commit", "-m",
        """DO NOT MERGE: Fix security issue

The size of the input may be very big that system server
got OOM while handling it, so we decode it first.

Bug: 204087139
Test: Manually set wallpaper, no PDoS observed.
Change-Id: I014cf461954992782b3dfa0dde67c98a572cc770
Merged-In:I014cf461954992782b3dfa0dde67c98a572cc770"""
    ], check=True, capture_output=True)

    # 创建分支用于 merge commit
    subprocess.run(["git", "checkout", "-b", "feature"], check=True, capture_output=True)
    with open("file3.txt", "w") as f:
        f.write("feature content")
    subprocess.run(["git", "add", "file3.txt"], check=True, capture_output=True)
    subprocess.run([
        "git", "commit", "-m",
        "Feature commit\n\nChange-Id: Iabc123"
    ], check=True, capture_output=True)

    # 回到主分支并 merge
    subprocess.run(["git", "checkout", "master"], check=True, capture_output=True)
    subprocess.run([
        "git", "merge", "feature", "--no-ff", "-m",
        "Merge feature branch\n\nMerge cherrypicks into release.\n\nChange-Id: Id0407409af0f9d4144f2ef6252d896f5c6345f51"
    ], check=True, capture_output=True)

    return temp_dir


def test_parser(repo_path):
    """测试解析器"""
    print("\n" + "=" * 60)
    print("测试 Git Log 解析器")
    print("=" * 60)

    scanner = GitScanner(repo_path, "test-project")
    commits = scanner.scan_commits()

    print(f"\n✓ 成功解析 {len(commits)} 个 commits\n")

    for idx, commit in enumerate(commits, 1):
        print(f"[Commit {idx}]")
        print(f"  Hash:      {commit['hash']}")
        print(f"  Author:    {commit['author']}")
        print(f"  Date:      {commit['date']}")
        print(f"  Subject:   {commit['subject']}")
        print(f"  Change-Id: {commit['change_id'] or '(无)'}")
        print(f"  Message Preview: {commit['message'][:100]}..." if len(commit['message']) > 100 else f"  Message: {commit['message']}")
        print()

    # 验证关键字段
    print("=" * 60)
    print("验证解析结果")
    print("=" * 60)

    errors = []

    for idx, commit in enumerate(commits, 1):
        if not commit['hash']:
            errors.append(f"Commit {idx}: hash 为空")
        if not commit['author']:
            errors.append(f"Commit {idx}: author 为空")
        if not commit['date']:
            errors.append(f"Commit {idx}: date 为空")
        if not commit['subject']:
            errors.append(f"Commit {idx}: subject 为空")

    if errors:
        print("\n❌ 发现错误:")
        for err in errors:
            print(f"  • {err}")
        return False
    else:
        print("\n✓ 所有 commits 解析正确")
        print(f"  • Hash: ✓")
        print(f"  • Author: ✓")
        print(f"  • Date: ✓")
        print(f"  • Subject: ✓")
        print(f"  • Change-Id: {sum(1 for c in commits if c['change_id'])} / {len(commits)}")
        return True


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 16 + "Git Parser 测试工具" + " " * 24 + "║")
    print("╚" + "═" * 58 + "╝")

    # 创建测试仓库
    repo_path = create_test_repo()

    try:
        # 测试解析器
        success = test_parser(repo_path)
        return 0 if success else 1
    finally:
        # 清理测试仓库
        import shutil
        print(f"\n清理测试仓库: {repo_path}")
        shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
