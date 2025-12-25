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
        分批处理以避免 SQLite 的 999 变量限制
        :param aosp_projects: AOSP 项目名称列表
        :param vendor_projects: Vendor 项目名称列表
        """
        BATCH_SIZE = 500  # 每批最多 500 个变量，安全余量

        def load_change_ids_in_batches(conn, projects: List[str]) -> Set[str]:
            """分批加载，避免超过 SQLite 变量限制"""
            all_change_ids = set()
            total = len(projects)

            for i in range(0, total, BATCH_SIZE):
                batch = projects[i:i + BATCH_SIZE]
                placeholders = ','.join(['?'] * len(batch))
                cursor = conn.execute(
                    f"""SELECT DISTINCT change_id
                        FROM commits
                        WHERE project IN ({placeholders})
                        AND change_id IS NOT NULL AND change_id != ''""",
                    batch
                )
                all_change_ids.update(row['change_id'] for row in cursor.fetchall())

            return all_change_ids

        with get_db() as conn:
            # 获取 AOSP Change-Ids
            if aosp_projects:
                self.aosp_change_ids = load_change_ids_in_batches(conn, aosp_projects)
            else:
                self.aosp_change_ids = set()

            # 获取 Vendor Change-Ids
            if vendor_projects:
                self.vendor_change_ids = load_change_ids_in_batches(conn, vendor_projects)
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

    def update_commit_sources_in_db(self, aosp_projects: List[str], vendor_projects: List[str]):
        """
        根据差异分析结果更新数据库中所有 commits 的 source 字段
        分批处理以避免 SQLite 的 999 变量限制

        :param aosp_projects: AOSP 项目名称列表
        :param vendor_projects: Vendor 项目名称列表
        """
        BATCH_SIZE = 500  # 每批最多 500 个变量，安全余量

        def update_in_batches(conn, change_ids: Set[str], source_value: str):
            """分批更新，避免超过 SQLite 变量限制"""
            change_id_list = list(change_ids)
            total = len(change_id_list)

            for i in range(0, total, BATCH_SIZE):
                batch = change_id_list[i:i + BATCH_SIZE]
                placeholders = ','.join(['?'] * len(batch))
                conn.execute(
                    f"UPDATE commits SET source = ? WHERE change_id IN ({placeholders})",
                    [source_value] + batch
                )

            if total > 0:
                print(f"  ✓ 已更新 {total} 个 Change-Id 为 {source_value}")

        def update_by_projects_in_batches(conn, projects: List[str], source_value: str):
            """根据项目列表分批更新"""
            total = len(projects)
            updated = 0

            for i in range(0, total, BATCH_SIZE):
                batch = projects[i:i + BATCH_SIZE]
                placeholders = ','.join(['?'] * len(batch))
                cursor = conn.execute(
                    f"""UPDATE commits SET source = ?
                        WHERE project IN ({placeholders})
                        AND (change_id IS NULL OR change_id = '')""",
                    [source_value] + batch
                )
                updated += cursor.rowcount

            if updated > 0:
                print(f"  ✓ 已更新 {updated} 个无 Change-Id 的 commits 为 {source_value}")
            return updated

        with get_db() as conn:
            # 1. 基于 Change-Id 更新（有 Change-Id 的 commits）
            print("\n基于 Change-Id 更新 source:")

            if self.common_change_ids:
                update_in_batches(conn, self.common_change_ids, 'common')

            if self.aosp_only_change_ids:
                update_in_batches(conn, self.aosp_only_change_ids, 'aosp_only')

            if self.vendor_only_change_ids:
                update_in_batches(conn, self.vendor_only_change_ids, 'vendor_only')

            # 2. 基于项目归属更新（没有 Change-Id 的 commits）
            print("\n基于项目归属更新无 Change-Id 的 commits:")

            # 区分项目归属
            aosp_projects_set = set(aosp_projects)
            vendor_projects_set = set(vendor_projects)
            common_projects = aosp_projects_set & vendor_projects_set
            aosp_only_projects = list(aosp_projects_set - vendor_projects_set)
            vendor_only_projects = list(vendor_projects_set - aosp_projects_set)

            # 更新只在 AOSP 的项目
            if aosp_only_projects:
                update_by_projects_in_batches(conn, aosp_only_projects, 'aosp_only')

            # 更新只在 Vendor 的项目
            if vendor_only_projects:
                update_by_projects_in_batches(conn, vendor_only_projects, 'vendor_only')

            # 对于两边都有的项目，无 Change-Id 的 commits 根据 hash 判断
            if common_projects:
                common_projects_list = list(common_projects)
                updated = 0

                for i in range(0, len(common_projects_list), BATCH_SIZE):
                    batch = common_projects_list[i:i + BATCH_SIZE]
                    placeholders = ','.join(['?'] * len(batch))

                    # 对于两边都有的项目，如果 hash 相同则标记为 common
                    # 否则按项目来源标记（这里简化处理，统一标记为 common）
                    cursor = conn.execute(
                        f"""UPDATE commits SET source = 'common'
                            WHERE project IN ({placeholders})
                            AND (change_id IS NULL OR change_id = '')
                            AND source IS NULL""",
                        batch
                    )
                    updated += cursor.rowcount

                if updated > 0:
                    print(f"  ✓ 已更新 {updated} 个两边共有项目的无 Change-Id commits 为 common")

            conn.commit()

        print("\n✓ 差异分析完成，已更新 commits.source 字段")


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
    analyzer.update_commit_sources_in_db(aosp_projects, vendor_projects)

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
