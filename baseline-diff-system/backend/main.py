"""
FastAPI 后端主文件
提供 REST API 接口用于扫描仓库、获取 commits、分类管理等
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
import traceback
import asyncio
import json

import database
import manifest_parser
import git_scanner
import diff_analyzer
from progress_tracker import progress_tracker


app = FastAPI(title="Baseline Diff System API", version="1.0.0")

# 获取静态文件路径（支持打包后的二进制文件）
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    BASE_DIR = sys._MEIPASS
else:
    # 开发环境路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应设置具体的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    if not os.path.exists(database.DB_PATH):
        print("初始化数据库...")
        database.init_database()
    else:
        print(f"数据库已存在: {database.DB_PATH}")


# ==================== Pydantic Models ====================

class ScanRequest(BaseModel):
    aosp_path: str
    vendor_path: str


class SetCategoriesRequest(BaseModel):
    hash: str
    category_ids: List[int]


class AddCategoryRequest(BaseModel):
    name: str


class RemoveCategoryRequest(BaseModel):
    id: int


# ==================== API Endpoints ====================

@app.post("/api/scan_repos")
async def scan_repos(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    扫描 AOSP 和 Vendor 仓库
    自动执行：manifest 解析 → git log → 差异分析 → 写入数据库
    """
    try:
        aosp_path = request.aosp_path
        vendor_path = request.vendor_path

        # 验证路径
        if not os.path.exists(aosp_path):
            raise HTTPException(status_code=400, detail=f"AOSP 路径不存在: {aosp_path}")
        if not os.path.exists(vendor_path):
            raise HTTPException(status_code=400, detail=f"Vendor 路径不存在: {vendor_path}")

        # 验证 manifest.xml 是否存在
        aosp_manifest = os.path.join(aosp_path, ".repo", "manifest.xml")
        vendor_manifest = os.path.join(vendor_path, ".repo", "manifest.xml")

        if not os.path.exists(aosp_manifest):
            raise HTTPException(
                status_code=400,
                detail=f"AOSP manifest.xml 不存在: {aosp_manifest}\n请确保这是一个有效的 repo 仓库（需要先执行 repo sync）"
            )
        if not os.path.exists(vendor_manifest):
            raise HTTPException(
                status_code=400,
                detail=f"Vendor manifest.xml 不存在: {vendor_manifest}\n请确保这是一个有效的 repo 仓库（需要先执行 repo sync）"
            )

        # 初始化进度跟踪
        progress_tracker.reset()
        progress_tracker.start(total_steps=5)
        progress_tracker.update(
            stage="initializing",
            stage_name="初始化",
            current_step=0,
            message="准备开始扫描..."
        )
        await progress_tracker.notify_subscribers()

        # 清空旧数据
        print("清空旧数据...")
        database.clear_all_commits()
        progress_tracker.update(current_step=1, message="已清空旧数据")
        await progress_tracker.notify_subscribers()

        # 1. 解析 AOSP manifest
        print(f"\n=== 解析 AOSP Manifest ===")
        progress_tracker.update(
            stage="manifest_parsing",
            stage_name="解析 Manifest",
            current_step=1,
            message="正在解析 AOSP manifest..."
        )
        await progress_tracker.notify_subscribers()

        aosp_projects = manifest_parser.parse_manifest(aosp_path)
        print(f"✓ AOSP: {len(aosp_projects)} 个项目")

        # 保存 manifest 信息到数据库
        for p in aosp_projects:
            database.insert_manifest(p['name'], p['remote_url'], p['path'])

        # 2. 解析 Vendor manifest
        print(f"\n=== 解析 Vendor Manifest ===")
        progress_tracker.update(
            current_step=2,
            message=f"正在解析 Vendor manifest... (AOSP: {len(aosp_projects)} 个项目)"
        )
        await progress_tracker.notify_subscribers()

        vendor_projects = manifest_parser.parse_manifest(vendor_path)
        print(f"✓ Vendor: {len(vendor_projects)} 个项目")

        # 保存 manifest 信息到数据库
        for p in vendor_projects:
            database.insert_manifest(p['name'], p['remote_url'], p['path'])

        # 3. 扫描 AOSP git log
        print(f"\n=== 扫描 AOSP Git Log ===")
        progress_tracker.update(
            stage="git_scanning",
            stage_name="扫描 Git Log",
            current_step=3,
            message=f"正在扫描 AOSP git log... ({len(aosp_projects)} 个项目)"
        )
        await progress_tracker.notify_subscribers()

        aosp_commits = git_scanner.scan_all_projects(aosp_projects)
        print(f"✓ AOSP 扫描完成：{len(aosp_commits)} 个 commits")

        if aosp_commits:
            database.bulk_insert_commits(aosp_commits)
            print(f"✓ AOSP commits 已插入数据库")
        else:
            print(f"⚠ 警告：AOSP 没有扫描到任何 commits")

        # 4. 扫描 Vendor git log
        print(f"\n=== 扫描 Vendor Git Log ===")
        progress_tracker.update(
            current_step=4,
            message=f"正在扫描 Vendor git log... ({len(vendor_projects)} 个项目, 已扫描 {len(aosp_commits)} 个 AOSP commits)"
        )
        await progress_tracker.notify_subscribers()

        vendor_commits = git_scanner.scan_all_projects(vendor_projects)
        print(f"✓ Vendor 扫描完成：{len(vendor_commits)} 个 commits")

        if vendor_commits:
            database.bulk_insert_commits(vendor_commits)
            print(f"✓ Vendor commits 已插入数据库")
        else:
            print(f"⚠ 警告：Vendor 没有扫描到任何 commits")

        # 5. 差异分析
        print(f"\n=== 执行差异分析 ===")
        progress_tracker.update(
            stage="diff_analysis",
            stage_name="差异分析",
            current_step=5,
            message=f"正在分析差异... (共 {len(aosp_commits) + len(vendor_commits)} 个 commits)"
        )
        await progress_tracker.notify_subscribers()

        aosp_project_names = [p['name'] for p in aosp_projects]
        vendor_project_names = [p['name'] for p in vendor_projects]

        stats = diff_analyzer.analyze_diff(aosp_project_names, vendor_project_names)

        # 验证数据库中的数据
        db_commits = database.get_all_commits()
        print(f"\n✓ 数据库验证：{len(db_commits)} 个 commits")

        total_scanned = len(aosp_commits) + len(vendor_commits)
        if total_scanned == 0:
            print("\n⚠ 警告：没有扫描到任何 commits，请检查：")
            print("  1. manifest.xml 是否包含有效的项目")
            print("  2. 项目路径是否存在")
            print("  3. 项目是否为 Git 仓库")
            print("  4. Git 仓库是否包含 commits")

        # 标记为完成
        progress_tracker.complete(
            f"扫描完成！共处理 {total_scanned} 个 commits"
        )
        await progress_tracker.notify_subscribers()

        return {
            "success": True,
            "message": "扫描完成" if total_scanned > 0 else "扫描完成，但未找到任何 commits",
            "stats": {
                "aosp_projects": len(aosp_projects),
                "vendor_projects": len(vendor_projects),
                "total_commits": len(aosp_commits) + len(vendor_commits),
                "db_commits": len(db_commits),
                "diff_stats": stats
            }
        }

    except Exception as e:
        print(f"✗ 扫描失败: {e}")
        traceback.print_exc()
        # 标记为错误
        progress_tracker.error(f"扫描失败: {str(e)}")
        await progress_tracker.notify_subscribers()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits")
async def get_commits(
    source: Optional[str] = None,
    project: Optional[str] = None,
    author: Optional[str] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: Optional[int] = 1000,
    offset: Optional[int] = 0
):
    """
    获取 commits，支持筛选和分页
    :param limit: 返回的最大记录数，默认 1000（防止数据量过大）
    :param offset: 偏移量，用于分页
    """
    try:
        # 获取总数
        total_count = database.get_commits_count()

        # 获取分页数据
        commits = database.get_all_commits(limit=limit, offset=offset)

        # 应用筛选
        if source:
            commits = [c for c in commits if c['source'] == source]

        if project:
            commits = [c for c in commits if c['project'] == project]

        if author:
            commits = [c for c in commits if author.lower() in c['author'].lower()]

        if category_id:
            commits = [
                c for c in commits
                if any(cat['id'] == category_id for cat in c['categories'])
            ]

        if search:
            search_lower = search.lower()
            commits = [
                c for c in commits
                if search_lower in c['subject'].lower() or search_lower in c['message'].lower()
            ]

        return {
            "success": True,
            "total": total_count,  # 总记录数
            "count": len(commits),  # 当前返回的记录数
            "limit": limit,
            "offset": offset,
            "commits": commits
        }

    except Exception as e:
        print(f"✗ 获取 commits 失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metadata")
async def get_metadata():
    """
    获取元数据（项目列表、作者列表等）
    用于填充筛选器下拉列表
    """
    try:
        projects = database.get_unique_projects()
        authors = database.get_unique_authors()

        return {
            "success": True,
            "projects": projects,
            "authors": authors
        }

    except Exception as e:
        print(f"✗ 获取元数据失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/set_categories")
async def set_categories(request: SetCategoriesRequest):
    """
    设置 commit 的分类
    """
    try:
        database.set_commit_categories(request.hash, request.category_ids)
        return {"success": True, "message": "分类已更新"}

    except Exception as e:
        print(f"✗ 设置分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories/list")
async def get_categories():
    """
    获取所有分类
    """
    try:
        categories = database.get_all_categories()
        return {
            "success": True,
            "categories": categories
        }

    except Exception as e:
        print(f"✗ 获取分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/categories/add")
async def add_category(request: AddCategoryRequest):
    """
    添加自定义分类
    """
    try:
        category_id = database.add_category(request.name, is_default=0)
        return {
            "success": True,
            "message": "分类已添加",
            "category_id": category_id
        }

    except Exception as e:
        print(f"✗ 添加分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/categories/remove")
async def remove_category(request: RemoveCategoryRequest):
    """
    删除分类
    """
    try:
        database.remove_category(request.id)
        return {"success": True, "message": "分类已删除"}

    except Exception as e:
        print(f"✗ 删除分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reanalyze_diff")
async def reanalyze_diff():
    """
    重新执行差异分析（断点续传功能）
    使用数据库中已有的 commits 和 manifests 数据
    适用于之前扫描在差异分析阶段失败的情况
    """
    try:
        # 初始化进度跟踪
        progress_tracker.reset()
        progress_tracker.start(total_steps=3)
        progress_tracker.update(
            stage="initializing",
            stage_name="初始化",
            current_step=0,
            message="准备重新分析差异..."
        )
        await progress_tracker.notify_subscribers()

        # 检查数据库中是否有数据
        commits = database.get_all_commits()
        if not commits:
            progress_tracker.error("数据库中没有 commits 数据")
            await progress_tracker.notify_subscribers()
            raise HTTPException(
                status_code=400,
                detail="数据库中没有 commits 数据，请先执行完整扫描"
            )

        # 从数据库获取所有项目
        progress_tracker.update(
            stage="manifest_parsing",
            stage_name="加载数据",
            current_step=1,
            message=f"正在加载数据库中的 {len(commits)} 个 commits..."
        )
        await progress_tracker.notify_subscribers()

        with database.get_db() as conn:
            cursor = conn.execute("SELECT DISTINCT project FROM manifests")
            all_projects = [row['project'] for row in cursor.fetchall()]

        if not all_projects:
            progress_tracker.error("数据库中没有 manifest 数据")
            await progress_tracker.notify_subscribers()
            raise HTTPException(
                status_code=400,
                detail="数据库中没有 manifest 数据，请先执行完整扫描"
            )

        print(f"\n=== 重新执行差异分析 ===")
        print(f"数据库中有 {len(commits)} 个 commits")
        print(f"数据库中有 {len(all_projects)} 个项目")

        # 简单策略：根据项目名称区分 AOSP 和 Vendor
        # 这里假设项目名包含特定关键字来区分
        # 用户可以根据实际情况调整这个逻辑
        progress_tracker.update(
            stage="diff_analysis",
            stage_name="差异分析",
            current_step=2,
            message=f"正在分析 {len(all_projects)} 个项目的差异..."
        )
        await progress_tracker.notify_subscribers()

        aosp_projects = [p for p in all_projects if 'aosp' in p.lower()]
        vendor_projects = [p for p in all_projects if 'vendor' in p.lower()]

        # 如果无法区分，则获取用户输入或使用全部项目
        if not aosp_projects and not vendor_projects:
            print("⚠ 无法自动区分 AOSP 和 Vendor 项目，将所有 commits 标记为 common")
            diff_analyzer.simple_diff_analysis()
            stats = {
                "total_aosp": 0,
                "total_vendor": 0,
                "common": len(commits),
                "aosp_only": 0,
                "vendor_only": 0
            }
        else:
            print(f"识别到 {len(aosp_projects)} 个 AOSP 项目，{len(vendor_projects)} 个 Vendor 项目")
            stats = diff_analyzer.analyze_diff(aosp_projects, vendor_projects)

        # 重新获取统计信息
        progress_tracker.update(
            current_step=3,
            message="正在统计分析结果..."
        )
        await progress_tracker.notify_subscribers()

        commits = database.get_all_commits()
        updated_stats = {
            "total_commits": len(commits),
            "common": len([c for c in commits if c['source'] == 'common']),
            "aosp_only": len([c for c in commits if c['source'] == 'aosp_only']),
            "vendor_only": len([c for c in commits if c['source'] == 'vendor_only']),
        }

        # 标记为完成
        progress_tracker.complete(
            f"差异分析完成！共分析 {len(commits)} 个 commits"
        )
        await progress_tracker.notify_subscribers()

        return {
            "success": True,
            "message": "差异分析完成",
            "stats": {
                "diff_stats": stats,
                "updated_stats": updated_stats
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ 差异分析失败: {e}")
        traceback.print_exc()
        # 标记为错误
        progress_tracker.error(f"差异分析失败: {str(e)}")
        await progress_tracker.notify_subscribers()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """
    获取统计信息
    """
    try:
        commits = database.get_all_commits()

        stats = {
            "total_commits": len(commits),
            "common": len([c for c in commits if c['source'] == 'common']),
            "aosp_only": len([c for c in commits if c['source'] == 'aosp_only']),
            "vendor_only": len([c for c in commits if c['source'] == 'vendor_only']),
        }

        return {"success": True, "stats": stats}

    except Exception as e:
        print(f"✗ 获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/progress")
async def get_progress():
    """获取当前进度（轮询模式）"""
    return progress_tracker.get_progress()


@app.get("/api/progress/stream")
async def progress_stream():
    """
    SSE 端点：实时推送进度更新
    """
    async def event_generator():
        queue = asyncio.Queue()
        await progress_tracker.subscribe(queue)

        try:
            # 首先发送当前进度
            current_progress = progress_tracker.get_progress()
            yield f"data: {json.dumps(current_progress)}\n\n"

            # 持续发送更新
            while True:
                try:
                    # 等待进度更新，超时60秒
                    progress = await asyncio.wait_for(queue.get(), timeout=60.0)
                    yield f"data: {json.dumps(progress)}\n\n"

                    # 如果任务完成或出错，关闭连接
                    if progress.get("stage") in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    # 发送心跳包
                    yield f": heartbeat\n\n"
                    continue

        finally:
            await progress_tracker.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        }
    )


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "service": "Baseline Diff System API",
        "status": "running",
        "version": "1.0.0"
    }


# 挂载静态文件（前端构建产物）
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        """提供前端首页"""
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            return {"message": "Frontend not built. Please run 'npm run build' in frontend directory."}

    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """提供前端路由（SPA 支持）"""
        # 如果是 API 请求，跳过
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # 检查是否是静态文件
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # 否则返回 index.html（SPA 路由）
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        """开发模式健康检查"""
        return {
            "service": "Baseline Diff System API",
            "status": "running",
            "version": "1.0.0",
            "message": "Static files not found. Run in development mode or build frontend first."
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
