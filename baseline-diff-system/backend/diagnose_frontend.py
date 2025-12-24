#!/usr/bin/env python3
"""
前端显示诊断脚本
用于排查数据库有数据但前端显示为空的问题
"""
import sys
import os
import sqlite3
import json

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database


def print_header(title):
    """打印标题"""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + f" {title}".ljust(58) + "║")
    print("╚" + "═" * 58 + "╝")


def print_section(title):
    """打印分节标题"""
    print("\n" + "─" * 60)
    print(f"  {title}")
    print("─" * 60)


def check_database_content():
    """检查数据库内容"""
    print_section("步骤 1: 检查数据库内容")

    with database.get_db() as conn:
        # Commits 统计
        cursor = conn.execute("SELECT COUNT(*) as count FROM commits")
        total_commits = cursor.fetchone()['count']
        print(f"✅ Commits 总数: {total_commits:,}")

        if total_commits == 0:
            print("❌ 数据库中没有 commits！")
            return False

        # 按 source 统计
        cursor = conn.execute(
            "SELECT source, COUNT(*) as count FROM commits GROUP BY source"
        )
        print("\n按来源分类:")
        for row in cursor.fetchall():
            source = row['source'] if row['source'] else 'NULL'
            count = row['count']
            print(f"   {source:12} : {count:,} 条")

        # 项目数量
        cursor = conn.execute("SELECT COUNT(DISTINCT project) as count FROM commits")
        project_count = cursor.fetchone()['count']
        print(f"\n✅ 项目总数: {project_count:,}")

        # Manifests 数量
        cursor = conn.execute("SELECT COUNT(*) as count FROM manifests")
        manifest_count = cursor.fetchone()['count']
        print(f"✅ Manifests 总数: {manifest_count:,}")

    return True


def check_api_data_format():
    """检查 API 数据格式"""
    print_section("步骤 2: 检查 API 返回的数据格式")

    # 模拟 API 调用
    commits = database.get_all_commits()
    print(f"✅ database.get_all_commits() 返回了 {len(commits)} 条记录")

    if len(commits) == 0:
        print("❌ get_all_commits() 返回空列表")
        return False

    # 检查第一条数据的结构
    first_commit = commits[0]
    print(f"\n数据类型: {type(first_commit)}")
    print(f"字段列表: {list(first_commit.keys())}")

    # 检查必需字段
    required_fields = ['project', 'hash', 'author', 'subject', 'source', 'categories']
    print("\n检查必需字段:")
    for field in required_fields:
        if field in first_commit:
            value = first_commit[field]
            if field == 'categories':
                print(f"   ✅ {field:12} : {type(value)} (长度: {len(value)})")
            else:
                value_str = str(value)[:50]
                print(f"   ✅ {field:12} : {value_str}")
        else:
            print(f"   ❌ {field:12} : 缺失！")

    # 检查 categories 字段格式
    if 'categories' in first_commit:
        cats = first_commit['categories']
        if isinstance(cats, list):
            print(f"\n✅ categories 是列表类型（正确）")
        else:
            print(f"\n❌ categories 不是列表！类型: {type(cats)}")

    return True


def simulate_api_response():
    """模拟 API /api/commits 的响应"""
    print_section("步骤 3: 模拟 /api/commits API 响应")

    commits = database.get_all_commits()

    response = {
        "success": True,
        "commits": commits
    }

    print(f"响应数据结构:")
    print(f"   success: {response['success']}")
    print(f"   commits: 列表，长度 {len(response['commits'])}")

    # 尝试序列化为 JSON
    try:
        json_str = json.dumps(response, ensure_ascii=False)
        print(f"\n✅ 可以序列化为 JSON")
        print(f"   JSON 字符串长度: {len(json_str):,} 字符")

        # 检查是否太大
        if len(json_str) > 10 * 1024 * 1024:  # 10MB
            print(f"   ⚠️  警告: JSON 太大 ({len(json_str)/1024/1024:.2f} MB)")

        return True
    except Exception as e:
        print(f"\n❌ 无法序列化为 JSON: {e}")
        return False


def check_server_running():
    """检查后端服务器是否运行"""
    print_section("步骤 4: 检查后端服务器")

    try:
        import requests

        urls_to_check = [
            ("健康检查", "http://localhost:8000/api/health"),
            ("获取 commits", "http://localhost:8000/api/commits"),
            ("获取统计", "http://localhost:8000/api/stats"),
        ]

        for name, url in urls_to_check:
            try:
                print(f"\n测试 {name}:")
                print(f"   URL: {url}")
                response = requests.get(url, timeout=5)
                print(f"   ✅ 状态码: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ 返回 JSON 数据")

                        # 详细检查 commits 端点
                        if 'commits' in name.lower():
                            if 'commits' in data:
                                print(f"   ✅ 包含 'commits' 字段")
                                print(f"   ✅ commits 数量: {len(data['commits'])}")

                                if len(data['commits']) > 0:
                                    first = data['commits'][0]
                                    print(f"   ✅ 第一条数据包含字段: {list(first.keys())[:5]}...")
                                else:
                                    print(f"   ❌ commits 列表为空！")
                            else:
                                print(f"   ❌ 响应中没有 'commits' 字段")
                                print(f"   返回的字段: {list(data.keys())}")

                        # 详细检查 stats 端点
                        if 'stats' in name.lower():
                            if 'stats' in data:
                                stats = data['stats']
                                print(f"   ✅ 统计数据:")
                                for key, value in stats.items():
                                    print(f"      {key}: {value}")
                            else:
                                print(f"   ❌ 响应中没有 'stats' 字段")
                    except Exception as e:
                        print(f"   ❌ 解析 JSON 失败: {e}")
                else:
                    print(f"   ❌ 状态码异常: {response.status_code}")
                    print(f"   响应内容: {response.text[:200]}")

            except requests.exceptions.ConnectionError:
                print(f"   ❌ 无法连接到服务器")
                print(f"   请确保后端正在运行: python backend/main.py")
                return False
            except requests.exceptions.Timeout:
                print(f"   ❌ 请求超时")
                return False

        return True

    except ImportError:
        print("\n⚠️  requests 库未安装")
        print("   跳过 HTTP 测试")
        print("\n手动测试命令:")
        print("   curl http://localhost:8000/api/health")
        print("   curl http://localhost:8000/api/commits")
        print("   curl http://localhost:8000/api/stats")
        return None


def provide_frontend_checklist():
    """提供前端检查清单"""
    print_section("步骤 5: 前端问题检查清单")

    checklist = """
请在浏览器中执行以下检查：

1. 打开浏览器开发者工具（F12）

2. 切换到 Console（控制台）标签
   检查是否有红色错误信息
   特别注意：
   - CORS 错误
   - 网络错误
   - JavaScript 语法错误

3. 切换到 Network（网络）标签
   点击"刷新"按钮或重新加载页面
   查找以下请求：

   a) /api/commits 请求
      - 状态码应该是 200
      - 点击查看 Response（响应）
      - 检查是否包含 commits 数组
      - 检查 commits 数组是否为空

   b) /api/stats 请求
      - 状态码应该是 200
      - 检查统计数字是否正确

4. 检查 Console 中的日志
   看是否有类似这样的日志：
   - "加载 commits 失败"
   - "加载统计失败"

5. 尝试手动刷新
   点击 Commits 列表右上角的"刷新"按钮

6. 检查筛选条件
   确保没有设置了会过滤掉所有数据的条件
   点击"重置"按钮清除所有筛选

7. 查看 Elements（元素）标签
   检查页面 DOM 中是否有数据
   搜索第一个 commit 的 hash 值
    """
    print(checklist)


def generate_test_commands():
    """生成测试命令"""
    print_section("步骤 6: 测试命令")

    commands = """
在终端中执行以下命令进行测试：

1. 测试数据库查询:
   cd backend
   python -c "import database; commits = database.get_all_commits(); print(f'查询到 {len(commits)} 条记录')"

2. 测试 API 端点:
   curl http://localhost:8000/api/health
   curl http://localhost:8000/api/stats
   curl http://localhost:8000/api/commits | python -m json.tool | head -50

3. 检查后端日志:
   查看运行 python backend/main.py 的终端窗口
   重新加载前端页面，观察后端是否有 API 请求日志

4. 重启服务:
   # 停止后端
   pkill -f "python.*main.py"

   # 启动后端
   cd backend && python main.py

   # 重启前端（如果在开发模式）
   cd frontend && npm run dev
    """
    print(commands)


def main():
    """主函数"""
    print_header("前端显示问题诊断工具")

    print("""
本工具用于诊断"数据库有数据但前端显示为空"的问题

前提条件：
- 扫描已成功完成
- Python terminal 中能看到统计数据
- 但前端界面显示为空
    """)

    try:
        # 1. 检查数据库
        if not check_database_content():
            print("\n❌ 数据库是空的，请先完成扫描")
            return

        # 2. 检查 API 数据格式
        if not check_api_data_format():
            print("\n❌ API 数据格式有问题")
            return

        # 3. 模拟 API 响应
        if not simulate_api_response():
            print("\n❌ 无法生成有效的 API 响应")
            return

        # 4. 检查服务器
        server_ok = check_server_running()

        # 5. 前端检查清单
        provide_frontend_checklist()

        # 6. 测试命令
        generate_test_commands()

        # 总结
        print_section("诊断总结")

        if server_ok is False:
            print("❌ 后端服务器未运行或无法访问")
            print("\n解决方案:")
            print("   1. 启动后端: python backend/main.py")
            print("   2. 确保运行在 localhost:8000")
        elif server_ok is True:
            print("✅ 后端服务器正常运行且返回数据")
            print("\n问题可能在前端，请检查:")
            print("   1. 浏览器控制台的错误信息")
            print("   2. Network 标签中的 API 请求")
            print("   3. 是否有筛选条件过滤了所有数据")
        else:
            print("⚠️  无法测试后端服务器（requests 库未安装）")
            print("\n请手动测试:")
            print("   curl http://localhost:8000/api/commits")

    except Exception as e:
        print(f"\n❌ 诊断过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
