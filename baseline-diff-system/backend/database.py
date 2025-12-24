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
                  author: str, date: str, subject: str, message: str, source: str):
    """插入 commit 记录"""
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO commits
               (project, hash, change_id, author, date, subject, message, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project, hash, change_id, author, date, subject, message, source)
        )
        conn.commit()


def update_commit_source(hash: str, source: str):
    """更新 commit 的 source 字段"""
    with get_db() as conn:
        conn.execute("UPDATE commits SET source = ? WHERE hash = ?", (source, hash))
        conn.commit()


def get_all_commits(limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict]:
    """
    获取所有 commit 及其分类
    :param limit: 限制返回的记录数（用于分页）
    :param offset: 偏移量（用于分页）
    """
    with get_db() as conn:
        # 构建 SQL 查询
        sql = """
            SELECT
                c.id, c.project, c.hash, c.change_id, c.author, c.date,
                c.subject, c.message, c.source,
                m.remote_url,
                GROUP_CONCAT(cat.id) as category_ids,
                GROUP_CONCAT(cat.name) as category_names
            FROM commits c
            LEFT JOIN manifests m ON c.project = m.project
            LEFT JOIN commit_categories cc ON c.hash = cc.commit_hash
            LEFT JOIN categories cat ON cc.category_id = cat.id
            GROUP BY c.hash
            ORDER BY c.date DESC
        """

        # 添加分页参数
        if limit is not None:
            sql += f" LIMIT {limit}"
        if offset is not None:
            sql += f" OFFSET {offset}"

        cursor = conn.execute(sql)

        commits = []
        for row in cursor.fetchall():
            commit = dict(row)
            # 构造 commit URL
            if commit['remote_url']:
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

            commits.append(commit)

        return commits


def get_commits_count() -> int:
    """获取 commits 总数"""
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits")
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
               (project, hash, change_id, author, date, subject, message, source)
               VALUES (:project, :hash, :change_id, :author, :date, :subject, :message, :source)""",
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
