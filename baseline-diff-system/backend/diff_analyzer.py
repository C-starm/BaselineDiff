"""
差异分析模块
基于 Change-Id 对 AOSP 和 Vendor 进行差异分析
"""
from typing import List, Dict, Set, Tuple
from database import get_db


class DiffAnalyzer:
    """差异分析器"""

    def __init__(self):
        self.aosp_change_ids: Set[str] = set()
        self.vendor_change_ids: Set[str] = set()
        self.common_change_ids: Set[str] = set()
        self.aosp_only_change_ids: Set[str] = set()
        self.vendor_only_change_ids: Set[str] = set()

    def load_change_ids_from_db(self, aosp_projects: List[str], vendor_projects: List[str]):
        """
        从数据库加载 Change-Id
        :param aosp_projects: AOSP 项目名称列表
        :param vendor_projects: Vendor 项目名称列表
        """
        with get_db() as conn:
            # 获取 AOSP Change-Ids
            if aosp_projects:
                placeholders = ','.join(['?'] * len(aosp_projects))
                cursor = conn.execute(
                    f"""SELECT DISTINCT change_id
                        FROM commits
                        WHERE project IN ({placeholders})
                        AND change_id IS NOT NULL AND change_id != ''""",
                    aosp_projects
                )
                self.aosp_change_ids = {row['change_id'] for row in cursor.fetchall()}
            else:
                self.aosp_change_ids = set()

            # 获取 Vendor Change-Ids
            if vendor_projects:
                placeholders = ','.join(['?'] * len(vendor_projects))
                cursor = conn.execute(
                    f"""SELECT DISTINCT change_id
                        FROM commits
                        WHERE project IN ({placeholders})
                        AND change_id IS NOT NULL AND change_id != ''""",
                    vendor_projects
                )
                self.vendor_change_ids = {row['change_id'] for row in cursor.fetchall()}
            else:
                self.vendor_change_ids = set()

    def analyze(self) -> Dict[str, int]:
        """
        执行差异分析
        返回统计信息
        """
        # 计算集合差异
        self.common_change_ids = self.aosp_change_ids & self.vendor_change_ids
        self.aosp_only_change_ids = self.aosp_change_ids - self.vendor_change_ids
        self.vendor_only_change_ids = self.vendor_change_ids - self.aosp_change_ids

        return {
            "total_aosp": len(self.aosp_change_ids),
            "total_vendor": len(self.vendor_change_ids),
            "common": len(self.common_change_ids),
            "aosp_only": len(self.aosp_only_change_ids),
            "vendor_only": len(self.vendor_only_change_ids)
        }

    def update_commit_sources_in_db(self):
        """
        根据差异分析结果更新数据库中所有 commits 的 source 字段
        """
        with get_db() as conn:
            # 更新 common
            if self.common_change_ids:
                placeholders = ','.join(['?'] * len(self.common_change_ids))
                conn.execute(
                    f"UPDATE commits SET source = 'common' WHERE change_id IN ({placeholders})",
                    list(self.common_change_ids)
                )

            # 更新 aosp_only
            if self.aosp_only_change_ids:
                placeholders = ','.join(['?'] * len(self.aosp_only_change_ids))
                conn.execute(
                    f"UPDATE commits SET source = 'aosp_only' WHERE change_id IN ({placeholders})",
                    list(self.aosp_only_change_ids)
                )

            # 更新 vendor_only
            if self.vendor_only_change_ids:
                placeholders = ','.join(['?'] * len(self.vendor_only_change_ids))
                conn.execute(
                    f"UPDATE commits SET source = 'vendor_only' WHERE change_id IN ({placeholders})",
                    list(self.vendor_only_change_ids)
                )

            # 对于没有 Change-Id 的 commits，根据它们所属的项目来标记
            # 这里需要知道哪些项目属于 AOSP，哪些属于 Vendor
            # 暂时将它们标记为 'common'（可以根据实际需求调整）
            conn.execute(
                "UPDATE commits SET source = 'common' WHERE change_id IS NULL OR change_id = ''"
            )

            conn.commit()

        print("✓ 差异分析完成，已更新 commits.source 字段")


def analyze_diff(aosp_projects: List[str], vendor_projects: List[str]) -> Dict[str, int]:
    """
    快捷方法：执行完整的差异分析
    :param aosp_projects: AOSP 项目名称列表
    :param vendor_projects: Vendor 项目名称列表
    :return: 统计信息
    """
    analyzer = DiffAnalyzer()
    analyzer.load_change_ids_from_db(aosp_projects, vendor_projects)
    stats = analyzer.analyze()
    analyzer.update_commit_sources_in_db()

    print(f"\n差异分析统计:")
    print(f"  AOSP Change-Ids:     {stats['total_aosp']}")
    print(f"  Vendor Change-Ids:   {stats['total_vendor']}")
    print(f"  Common:              {stats['common']}")
    print(f"  AOSP Only:           {stats['aosp_only']}")
    print(f"  Vendor Only:         {stats['vendor_only']}")

    return stats


def simple_diff_analysis():
    """
    简化版差异分析：自动将所有 commits 分为两类
    - 如果 commit 的 project 在两个 repo 中都存在，标记为 common
    - 否则根据来源标记为 aosp_only 或 vendor_only

    这个方法适用于无法明确区分项目来源的情况
    """
    with get_db() as conn:
        # 获取所有项目
        cursor = conn.execute("SELECT DISTINCT project FROM commits")
        all_projects = {row['project'] for row in cursor.fetchall()}

        # 简单策略：所有 commits 默认标记为 common
        # 实际使用时可以根据项目名称前缀、路径等规则来区分
        conn.execute("UPDATE commits SET source = 'common' WHERE source IS NULL OR source = ''")
        conn.commit()

    print("✓ 已将所有 commits 标记为 common（简化模式）")


if __name__ == "__main__":
    # 测试差异分析
    # 假设已经有数据在数据库中
    import database
    database.init_database()

    # 示例：假设项目名包含 'aosp' 的是 AOSP 项目，包含 'vendor' 的是 Vendor 项目
    with database.get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT project FROM commits")
        all_projects = [row['project'] for row in cursor.fetchall()]

    aosp_projects = [p for p in all_projects if 'aosp' in p.lower()]
    vendor_projects = [p for p in all_projects if 'vendor' in p.lower()]

    if aosp_projects or vendor_projects:
        analyze_diff(aosp_projects, vendor_projects)
    else:
        print("未找到 AOSP/Vendor 项目，使用简化分析模式")
        simple_diff_analysis()
