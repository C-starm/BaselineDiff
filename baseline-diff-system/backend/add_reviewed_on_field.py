#!/usr/bin/env python3
"""
数据库迁移脚本：添加 reviewed_on 字段
用于存储 Gerrit 的 Reviewed-on URL
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def migrate():
    """执行数据库迁移"""
    print("\n" + "=" * 60)
    print("添加 reviewed_on 字段")
    print("=" * 60)

    with database.get_db() as conn:
        # 检查字段是否已存在
        cursor = conn.execute("PRAGMA table_info(commits)")
        columns = [row['name'] for row in cursor.fetchall()]

        if 'reviewed_on' in columns:
            print("\n✓ reviewed_on 字段已存在，无需迁移")
            return

        # 添加 reviewed_on 字段
        print("\n添加 reviewed_on 字段到 commits 表...")
        conn.execute("ALTER TABLE commits ADD COLUMN reviewed_on TEXT")
        conn.commit()

        print("✓ 字段添加成功")

        # 验证
        cursor = conn.execute("PRAGMA table_info(commits)")
        columns = [row['name'] for row in cursor.fetchall()]

        print("\n当前 commits 表字段:")
        for col in columns:
            print(f"  - {col}")

    print("\n" + "=" * 60)
    print("迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
