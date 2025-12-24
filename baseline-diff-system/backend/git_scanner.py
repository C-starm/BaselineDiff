"""
Git Log 扫描模块
对指定 Git 仓库执行 git log 并提取 commit 信息
"""
import os
import re
import subprocess
from typing import List, Dict, Optional


class GitScanner:
    """Git 日志扫描器"""

    def __init__(self, project_path: str, project_name: str):
        """
        初始化扫描器
        :param project_path: Git 仓库路径
        :param project_name: 项目名称
        """
        self.project_path = project_path
        self.project_name = project_name

    def extract_change_id(self, message: str) -> Optional[str]:
        """
        从 commit message 中提取 Change-Id
        格式通常为: Change-Id: I1234567890abcdef...
        """
        match = re.search(r'Change-Id:\s*([A-Za-z0-9]+)', message, re.IGNORECASE)
        return match.group(1) if match else None

    def scan_commits(self, max_count: Optional[int] = None) -> List[Dict]:
        """
        扫描 git log 并返回 commit 列表
        :param max_count: 最大扫描数量（None = 全部）
        :return: commit 列表
        """
        if not os.path.exists(self.project_path):
            print(f"⚠ 项目路径不存在: {self.project_path}")
            return []

        if not os.path.exists(os.path.join(self.project_path, ".git")):
            print(f"⚠ 不是 Git 仓库: {self.project_path}")
            return []

        # 构造 git log 命令
        # 格式: hash||author||date||subject||body
        cmd = [
            "git",
            "-C", self.project_path,
            "log",
            "--pretty=format:%H||%an||%ad||%s||%b",
            "--date=iso"
        ]

        if max_count:
            cmd.extend(["-n", str(max_count)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                check=True
            )

            commits = []
            lines = result.stdout.strip().split('\n')

            for line in lines:
                if not line.strip():
                    continue

                parts = line.split('||', 4)
                if len(parts) < 4:
                    continue

                hash_val = parts[0].strip()
                author = parts[1].strip()
                date = parts[2].strip()
                subject = parts[3].strip()
                message = parts[4].strip() if len(parts) > 4 else ""

                # 提取 Change-Id
                change_id = self.extract_change_id(message)

                commits.append({
                    "project": self.project_name,
                    "hash": hash_val,
                    "change_id": change_id,
                    "author": author,
                    "date": date,
                    "subject": subject,
                    "message": message,
                    "source": None  # 初始化为 NULL，后续差异分析时填充
                })

            return commits

        except subprocess.TimeoutExpired:
            print(f"✗ Git log 超时: {self.project_name}")
            return []
        except subprocess.CalledProcessError as e:
            print(f"✗ Git log 失败: {self.project_name} - {e}")
            return []
        except Exception as e:
            print(f"✗ 未知错误: {self.project_name} - {e}")
            return []


def scan_project(project_path: str, project_name: str, max_count: Optional[int] = None) -> List[Dict]:
    """
    快捷方法：扫描单个项目的 git log
    :param project_path: 项目路径
    :param project_name: 项目名称
    :param max_count: 最大扫描数量
    :return: commit 列表
    """
    scanner = GitScanner(project_path, project_name)
    return scanner.scan_commits(max_count)


def scan_all_projects(projects: List[Dict], max_count: Optional[int] = None) -> List[Dict]:
    """
    扫描所有项目的 git log
    :param projects: 项目列表（来自 manifest_parser）
    :param max_count: 每个项目的最大扫描数量
    :return: 所有 commit 的列表
    """
    all_commits = []
    total = len(projects)

    for idx, project in enumerate(projects, 1):
        print(f"[{idx}/{total}] 扫描项目: {project['name']}")
        commits = scan_project(project['path'], project['name'], max_count)
        all_commits.extend(commits)
        print(f"  ✓ 找到 {len(commits)} 个 commits")

    print(f"\n✓ 扫描完成，共 {len(all_commits)} 个 commits")
    return all_commits


def test_scanner():
    """测试扫描器"""
    import sys
    if len(sys.argv) < 2:
        print("用法: python git_scanner.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    project_name = os.path.basename(project_path)

    commits = scan_project(project_path, project_name, max_count=10)
    print(f"\n✓ 找到 {len(commits)} 个 commits")

    for c in commits[:3]:
        print(f"\n  Hash: {c['hash']}")
        print(f"  Author: {c['author']}")
        print(f"  Date: {c['date']}")
        print(f"  Subject: {c['subject']}")
        print(f"  Change-Id: {c['change_id'] or '(无)'}")


if __name__ == "__main__":
    test_scanner()
