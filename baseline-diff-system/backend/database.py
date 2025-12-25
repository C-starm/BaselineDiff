"""
数据库操作模块
处理所有 SQLite 数据库的 CRUD 操作
"""
import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager


DB_PATH = "db.sqlite3"


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """初始化数据库（执行 init_db.sql）"""
    sql_file = os.path.join(os.path.dirname(__file__), "init_db.sql")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    with get_db() as conn:
        conn.executescript(sql_script)
        conn.commit()
    print("✓ 数据库初始化完成")


def insert_manifest(project: str, remote_url: str, path: str):
    """插入 manifest 项目信息"""
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO manifests (project, remote_url, path) VALUES (?, ?, ?)",
            (project, remote_url, path)
        )
        conn.commit()


def insert_commit(project: str, hash: str, change_id: Optional[str],
                  author: str, date: str, subject: str, message: str, source: str,
                  reviewed_on: Optional[str] = None):
    """插入 commit 记录"""
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO commits
               (project, hash, change_id, author, date, subject, message, source, reviewed_on)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project, hash, change_id, author, date, subject, message, source, reviewed_on)
        )
        conn.commit()


def update_commit_source(hash: str, source: str):
    """更新 commit 的 source 字段"""
    with get_db() as conn:
        conn.execute("UPDATE commits SET source = ? WHERE hash = ?", (source, hash))
        conn.commit()


def get_all_commits(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    source: Optional[str] = None,
    project: Optional[str] = None,
    author: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict]:
    """
    获取 commits，支持筛选和分页
    :param limit: 限制返回的记录数
    :param offset: 偏移量
    :param source: 按来源筛选
    :param project: 按项目筛选
    :param author: 按作者筛选（模糊匹配）
    :param search: 搜索标题或消息（模糊匹配）
    :param date_from: 起始日期（格式：YYYY-MM-DD）
    :param date_to: 结束日期（格式：YYYY-MM-DD）
    """
    with get_db() as conn:
        # 构建 WHERE 条件
        where_conditions = []
        params = []

        if source:
            where_conditions.append("source = ?")
            params.append(source)

        if project:
            where_conditions.append("project = ?")
            params.append(project)

        if author:
            where_conditions.append("author LIKE ?")
            params.append(f"%{author}%")

        if search:
            where_conditions.append("(subject LIKE ? OR message LIKE ?)")
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        if date_from:
            where_conditions.append("date >= ?")
            params.append(date_from)

        if date_to:
            # 包含结束日期当天，所以加一天
            where_conditions.append("date < date(?, '+1 day')")
            params.append(date_to)

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 优化的 SQL 查询：先筛选分页，再 JOIN
        # 使用子查询避免在全表上做 GROUP BY
        sql = f"""
            WITH filtered_commits AS (
                SELECT
                    id, project, hash, change_id, author, date,
                    subject, message, source, reviewed_on
                FROM commits
                {where_clause}
                ORDER BY date DESC
                {"LIMIT " + str(limit) if limit is not None else ""}
                {"OFFSET " + str(offset) if offset is not None else ""}
            )
            SELECT
                fc.id, fc.project, fc.hash, fc.change_id, fc.author, fc.date,
                fc.subject, fc.message, fc.source, fc.reviewed_on,
                m.remote_url,
                GROUP_CONCAT(cat.id) as category_ids,
                GROUP_CONCAT(cat.name) as category_names
            FROM filtered_commits fc
            LEFT JOIN manifests m ON fc.project = m.project
            LEFT JOIN commit_categories cc ON fc.hash = cc.commit_hash
            LEFT JOIN categories cat ON cc.category_id = cat.id
            GROUP BY fc.hash
            ORDER BY fc.date DESC
        """

        cursor = conn.execute(sql, params)

        commits = []
        for row in cursor.fetchall():
            commit = dict(row)
            # 构造 commit URL - 优先使用 Reviewed-on URL
            if commit.get('reviewed_on'):
                # 如果有 Reviewed-on URL，直接使用
                commit['url'] = commit['reviewed_on']
            elif commit['remote_url']:
                # 否则使用基于 hash 的 URL
                commit['url'] = f"{commit['remote_url']}/{commit['project']}/commit/{commit['hash']}"
            else:
                commit['url'] = None

            # 解析分类
            if commit['category_ids']:
                commit['categories'] = [
                    {'id': int(cid), 'name': name}
                    for cid, name in zip(
                        commit['category_ids'].split(','),
                        commit['category_names'].split(',')
                    )
                ]
            else:
                commit['categories'] = []

            # 对于 common commits，查找相同 Change-Id 的其他 commits（两边的版本）
            if commit.get('source') == 'common' and commit.get('change_id'):
                related_cursor = conn.execute("""
                    SELECT c.hash, c.project, c.reviewed_on, m.remote_url
                    FROM commits c
                    LEFT JOIN manifests m ON c.project = m.project
                    WHERE c.change_id = ? AND c.hash != ?
                    LIMIT 5
                """, (commit['change_id'], commit['hash']))

                related_commits = []
                for related_row in related_cursor.fetchall():
                    related = dict(related_row)
                    # 构造 URL
                    if related.get('reviewed_on'):
                        related['url'] = related['reviewed_on']
                    elif related.get('remote_url'):
                        related['url'] = f"{related['remote_url']}/{related['project']}/commit/{related['hash']}"
                    else:
                        related['url'] = None
                    related_commits.append(related)

                commit['related_commits'] = related_commits
            else:
                commit['related_commits'] = []

            commits.append(commit)

        return commits


def get_commits_count(
    source: Optional[str] = None,
    project: Optional[str] = None,
    author: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> int:
    """
    获取 commits 总数（支持筛选）
    :param source: 按来源筛选
    :param project: 按项目筛选
    :param author: 按作者筛选
    :param search: 搜索关键字
    :param date_from: 起始日期（格式：YYYY-MM-DD）
    :param date_to: 结束日期（格式：YYYY-MM-DD）
    """
    with get_db() as conn:
        # 构建 WHERE 条件
        where_conditions = []
        params = []

        if source:
            where_conditions.append("source = ?")
            params.append(source)

        if project:
            where_conditions.append("project = ?")
            params.append(project)

        if author:
            where_conditions.append("author LIKE ?")
            params.append(f"%{author}%")

        if search:
            where_conditions.append("(subject LIKE ? OR message LIKE ?)")
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        if date_from:
            where_conditions.append("date >= ?")
            params.append(date_from)

        if date_to:
            where_conditions.append("date < date(?, '+1 day')")
            params.append(date_to)

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        sql = f"SELECT COUNT(*) as count FROM commits {where_clause}"
        cursor = conn.execute(sql, params)
        return cursor.fetchone()['count']


def get_unique_projects() -> List[str]:
    """获取所有唯一的项目名称"""
    with get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT project FROM commits ORDER BY project")
        return [row['project'] for row in cursor.fetchall()]


def get_unique_authors() -> List[str]:
    """获取所有唯一的作者"""
    with get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT author FROM commits ORDER BY author")
        return [row['author'] for row in cursor.fetchall()]


def get_commits_by_change_id(change_id: str) -> List[str]:
    """根据 Change-Id 获取所有 commit hash"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT hash FROM commits WHERE change_id = ?", (change_id,)
        )
        return [row['hash'] for row in cursor.fetchall()]


def get_all_change_ids_by_repo(aosp_path: str, vendor_path: str) -> Tuple[set, set]:
    """
    获取 AOSP 和 Vendor 的所有 Change-Id
    返回: (aosp_change_ids, vendor_change_ids)
    """
    # 这里需要根据实际 manifest 中的项目来区分 AOSP/Vendor
    # 简化实现：假设所有 commits 都已标记 source
    with get_db() as conn:
        # 获取 AOSP change_ids
        cursor = conn.execute("""
            SELECT DISTINCT change_id
            FROM commits
            WHERE change_id IS NOT NULL AND change_id != ''
        """)
        all_change_ids = {row['change_id'] for row in cursor.fetchall()}

        return all_change_ids, set()


def set_commit_categories(commit_hash: str, category_ids: List[int]):
    """设置 commit 的分类（会先删除旧分类）"""
    with get_db() as conn:
        # 删除旧分类
        conn.execute("DELETE FROM commit_categories WHERE commit_hash = ?", (commit_hash,))

        # 插入新分类
        for category_id in category_ids:
            conn.execute(
                "INSERT INTO commit_categories (commit_hash, category_id) VALUES (?, ?)",
                (commit_hash, category_id)
            )

        conn.commit()


def get_all_categories() -> List[Dict]:
    """获取所有分类"""
    with get_db() as conn:
        cursor = conn.execute("SELECT id, name, is_default FROM categories ORDER BY is_default DESC, name")
        return [dict(row) for row in cursor.fetchall()]


def add_category(name: str, is_default: int = 0) -> int:
    """添加新分类，返回分类 ID"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO categories (name, is_default) VALUES (?, ?)",
            (name, is_default)
        )
        conn.commit()
        return cursor.lastrowid


def remove_category(category_id: int):
    """删除分类（会自动删除关联的 commit_categories）"""
    with get_db() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()


def clear_all_commits():
    """清空所有 commit 和 manifest 数据"""
    with get_db() as conn:
        conn.execute("DELETE FROM commit_categories")
        conn.execute("DELETE FROM commits")
        conn.execute("DELETE FROM manifests")
        conn.commit()


def bulk_insert_commits(commits: List[Dict]):
    """批量插入 commits"""
    with get_db() as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO commits
               (project, hash, change_id, author, date, subject, message, source, reviewed_on)
               VALUES (:project, :hash, :change_id, :author, :date, :subject, :message, :source, :reviewed_on)""",
            commits
        )
        conn.commit()


def get_manifest_info(project: str) -> Optional[Dict]:
    """获取项目的 manifest 信息"""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT project, remote_url, path FROM manifests WHERE project = ?",
            (project,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
