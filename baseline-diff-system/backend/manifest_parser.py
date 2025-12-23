"""
Manifest 解析模块
解析 .repo/manifest.xml 并提取项目信息
"""
import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional


class ManifestParser:
    """Manifest.xml 解析器"""

    def __init__(self, repo_path: str):
        """
        初始化解析器
        :param repo_path: repo 根目录路径（包含 .repo 文件夹）
        """
        self.repo_path = repo_path
        self.manifest_path = os.path.join(repo_path, ".repo", "manifest.xml")
        self.remotes = {}  # remote name -> fetch URL
        self.default_remote = None
        self.projects = []

    def parse(self) -> List[Dict]:
        """
        解析 manifest.xml
        返回项目列表，每个项目包含：{name, path, remote_url}
        """
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"manifest.xml 不存在: {self.manifest_path}")

        tree = ET.parse(self.manifest_path)
        root = tree.getroot()

        # 1. 解析 <remote> 标签
        for remote in root.findall("remote"):
            name = remote.get("name")
            fetch = remote.get("fetch")
            if name and fetch:
                # 清理 fetch URL（移除末尾的 /）
                fetch = fetch.rstrip('/')
                self.remotes[name] = fetch

        # 2. 解析 <default> 标签
        default_elem = root.find("default")
        if default_elem is not None:
            self.default_remote = default_elem.get("remote")

        # 3. 解析 <project> 标签
        for project in root.findall("project"):
            name = project.get("name")
            path = project.get("path", name)  # 如果没有 path，默认使用 name
            remote = project.get("remote", self.default_remote)

            if not name:
                continue

            # 获取 remote URL
            remote_url = self.remotes.get(remote, "")

            # 完整的项目路径
            full_path = os.path.join(self.repo_path, path)

            self.projects.append({
                "name": name,
                "path": full_path,
                "remote_url": remote_url,
                "relative_path": path
            })

        return self.projects

    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """根据项目名获取项目信息"""
        for project in self.projects:
            if project['name'] == name:
                return project
        return None

    def get_all_project_paths(self) -> List[str]:
        """获取所有项目的完整路径"""
        return [p['path'] for p in self.projects]


def parse_manifest(repo_path: str) -> List[Dict]:
    """
    快捷方法：解析 manifest.xml 并返回项目列表
    :param repo_path: repo 根目录
    :return: 项目列表
    """
    parser = ManifestParser(repo_path)
    return parser.parse()


def test_parser():
    """测试解析器"""
    import sys
    if len(sys.argv) < 2:
        print("用法: python manifest_parser.py <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    try:
        projects = parse_manifest(repo_path)
        print(f"✓ 解析成功，共找到 {len(projects)} 个项目")
        for p in projects[:5]:  # 只显示前 5 个
            print(f"  - {p['name']}: {p['path']}")
        if len(projects) > 5:
            print(f"  ... 还有 {len(projects) - 5} 个项目")
    except Exception as e:
        print(f"✗ 解析失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_parser()
