#!/usr/bin/env python3
"""
数据库迁移脚本 - 修复 source 字段的 CHECK 约束
"""
import sqlite3
import os
import sys

DB_PATH = "db.sqlite3"


def migrate_database():
    """迁移数据库，修复 CHECK 约束"""

    if not os.path.exists(DB_PATH):
        print(f"✗ 数据库文件不存在: {DB_PATH}")
        print("请先运行程序创建数据库")
        return False

    print("="*60)
    print("数据库迁移 - 修复 source 字段约束")
    print("="*60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. 检查当前数据
        cursor.execute("SELECT COUNT(*) FROM commits")
        old_count = cursor.fetchone()[0]
        print(f"\n当前 commits 数量: {old_count}")

        # 2. 创建新表（带修复的约束）
        print("\n创建新表结构...")
        cursor.execute("""
            CREATE TABLE commits_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                hash TEXT UNIQUE NOT NULL,
                change_id TEXT,
                author TEXT,
                date TEXT,
                subject TEXT,
                message TEXT,
                source TEXT CHECK(source IS NULL OR source IN ('common','aosp_only','vendor_only')),
                FOREIGN KEY (project) REFERENCES manifests(project)
            )
        """)

        # 3. 复制数据（将空字符串转为 NULL）
        print("迁移数据...")
        cursor.execute("""
            INSERT INTO commits_new (id, project, hash, change_id, author, date, subject, message, source)
            SELECT id, project, hash, change_id, author, date, subject, message,
                   CASE WHEN source = '' THEN NULL ELSE source END
            FROM commits
        """)

        # 4. 删除旧表
        print("删除旧表...")
        cursor.execute("DROP TABLE commits")

        # 5. 重命名新表
        print("重命名新表...")
        cursor.execute("ALTER TABLE commits_new RENAME TO commits")

        # 6. 重建索引
        print("重建索引...")
        cursor.execute("CREATE INDEX idx_commits_project ON commits(project)")
        cursor.execute("CREATE INDEX idx_commits_source ON commits(source)")
        cursor.execute("CREATE INDEX idx_commits_change_id ON commits(change_id)")
        cursor.execute("CREATE INDEX idx_commits_hash ON commits(hash)")

        # 7. 验证
        cursor.execute("SELECT COUNT(*) FROM commits")
        new_count = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        print(f"\n✓ 迁移成功")
        print(f"  - 旧表记录数: {old_count}")
        print(f"  - 新表记录数: {new_count}")

        if old_count == new_count:
            print("  - 数据完整性: ✓")
        else:
            print(f"  - 警告: 数据数量不一致")

        return True

    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def recreate_database():
    """重新创建数据库（删除旧数据）"""

    print("="*60)
    print("重新创建数据库（会删除所有数据）")
    print("="*60)

    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.backup"
        print(f"\n备份旧数据库到: {backup_path}")
        import shutil
        shutil.copy(DB_PATH, backup_path)

    print("\n删除旧数据库...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    print("执行初始化脚本...")
    import database
    database.init_database()

    print("\n✓ 数据库重新创建完成")
    print("你现在可以重新扫描仓库")


def main():
    """主函数"""

    if len(sys.argv) > 1 and sys.argv[1] == "--recreate":
        recreate_database()
        return

    print("\n选择操作:")
    print("  1. 迁移数据库（保留现有数据）")
    print("  2. 重新创建数据库（删除所有数据）")
    print("  3. 退出")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        success = migrate_database()
        if success:
            print("\n建议: 重新运行扫描以确保所有数据正确")
    elif choice == "2":
        confirm = input("\n⚠ 警告: 这将删除所有数据！确认继续? (yes/no): ").strip().lower()
        if confirm == "yes":
            recreate_database()
        else:
            print("已取消")
    elif choice == "3":
        print("已退出")
    else:
        print("无效选择")


if __name__ == "__main__":
    # 切换到脚本所在目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
