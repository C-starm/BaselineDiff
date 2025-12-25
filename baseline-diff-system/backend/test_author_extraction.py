#!/usr/bin/env python3
"""
测试 Author 字段提取准确性
验证 Git log 中 Author 信息的提取
"""
import subprocess
import tempfile
import os


def create_test_commits():
    """创建包含不同 author 格式的测试 commits"""
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)

    # 初始化 Git 仓库
    subprocess.run(["git", "init"], check=True, capture_output=True)

    # 创建不同 author 格式的 commits
    test_authors = [
        ("Simple Name", "simple@example.com"),
        ("Android Build Coastguard Worker", "android-build-coastguard-worker@google.com"),
        ("Matt Pietal", "mpietal@google.com"),
        ("Wu Ahan", "ahanwu@google.com"),
        ("Name With Spaces", "user@domain.com"),
        ("中文名字", "chinese@example.com"),
    ]

    for idx, (name, email) in enumerate(test_authors):
        # 配置 author
        subprocess.run(["git", "config", "user.name", name], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", email], check=True, capture_output=True)

        # 创建文件并提交
        with open(f"file{idx}.txt", "w") as f:
            f.write(f"Content {idx}")
        subprocess.run(["git", "add", f"file{idx}.txt"], check=True, capture_output=True)
        subprocess.run([
            "git", "commit", "-m",
            f"Test commit {idx}\n\nChange-Id: I{idx}{'0' * 39}"
        ], check=True, capture_output=True)

    return temp_dir


def test_git_formats():
    """测试不同的 Git format 选项"""
    print("\n" + "=" * 70)
    print("Git Format 选项对比")
    print("=" * 70)

    # 测试不同的 format
    formats = {
        "%an": "Author Name (只有名字)",
        "%ae": "Author Email (只有邮箱)",
        "%an <%ae>": "Author Name <Email> (完整格式)",
        "%aN": "Author Name (respecting .mailmap)",
        "%aE": "Author Email (respecting .mailmap)",
    }

    for fmt, description in formats.items():
        print(f"\n格式: {fmt}")
        print(f"说明: {description}")
        print("-" * 70)

        result = subprocess.run(
            ["git", "log", f"--pretty=format:{fmt}", "-3"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.strip().split('\n')
        for idx, line in enumerate(lines[:3], 1):
            print(f"  [{idx}] {line}")


def test_current_implementation():
    """测试当前实现的提取逻辑"""
    print("\n" + "=" * 70)
    print("当前实现测试 (使用 %an)")
    print("=" * 70)

    separator = "<<GIT_COMMIT_SEP>>"
    field_sep = "<<FIELD_SEP>>"

    result = subprocess.run(
        ["git", "log", f"--pretty=format:{separator}%H{field_sep}%an{field_sep}%ae{field_sep}%ad{field_sep}%s", "--date=iso"],
        capture_output=True,
        text=True
    )

    commit_texts = result.stdout.split(separator)

    print("\n提取结果:")
    for idx, commit_text in enumerate(commit_texts, 1):
        commit_text = commit_text.strip()
        if not commit_text:
            continue

        parts = commit_text.split(field_sep, 4)
        if len(parts) < 4:
            continue

        hash_val = parts[0].strip()[:12]
        author_name = parts[1].strip()
        author_email = parts[2].strip()
        date = parts[3].strip()

        print(f"\n[Commit {idx}]")
        print(f"  Hash:   {hash_val}")
        print(f"  Name:   {author_name}")
        print(f"  Email:  {author_email}")
        print(f"  Date:   {date}")


def analyze_recommendations():
    """分析并给出建议"""
    print("\n" + "=" * 70)
    print("分析与建议")
    print("=" * 70)

    print("""
当前实现: 使用 %an (author name)
- ✓ 优点: 简洁，便于显示
- ✗ 缺点: 缺少邮箱信息，可能有重名

建议选项:

1. 【推荐】保持 %an，但在数据库中额外存储邮箱
   - 表格显示: 名字
   - 详细视图: 名字 + 邮箱
   - 修改: 添加 author_email 字段

2. 改用 "%an <%ae>" 存储完整信息
   - 存储: "Matt Pietal <mpietal@google.com>"
   - 显示时可以格式化
   - 修改: 只改 %an 为 "%an <%ae>"

3. 分别存储 name 和 email（最佳方案）
   - 数据库: 两个字段 (author_name, author_email)
   - 灵活显示
   - 修改: 数据库 schema + 解析逻辑

当前行为验证:
""")

    # 验证当前行为
    result = subprocess.run(
        ["git", "log", "--pretty=format:%an", "-1"],
        capture_output=True,
        text=True
    )
    print(f"✓ 当前 %an 提取: '{result.stdout.strip()}'")

    result = subprocess.run(
        ["git", "log", "--pretty=format:%an <%ae>", "-1"],
        capture_output=True,
        text=True
    )
    print(f"✓ 完整格式示例: '{result.stdout.strip()}'")


def main():
    """主函数"""
    print("\n" + "╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "Author 提取测试" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")

    # 创建测试仓库
    print("\n创建测试仓库...")
    repo_path = create_test_commits()
    print(f"✓ 测试仓库: {repo_path}")

    try:
        # 测试不同格式
        test_git_formats()

        # 测试当前实现
        test_current_implementation()

        # 分析建议
        analyze_recommendations()

        print("\n" + "=" * 70)
        print("测试完成")
        print("=" * 70)

    finally:
        # 清理
        import shutil
        print(f"\n清理测试仓库: {repo_path}")
        shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    main()
