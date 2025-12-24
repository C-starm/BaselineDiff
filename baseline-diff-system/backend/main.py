"""
FastAPI 后端主文件
提供 REST API 接口用于扫描仓库、获取 commits、分类管理等
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
import traceback

import database
import manifest_parser
import git_scanner
import diff_analyzer


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

        # 清空旧数据
        print("清空旧数据...")
        database.clear_all_commits()

        # 1. 解析 AOSP manifest
        print(f"\n=== 解析 AOSP Manifest ===")
        aosp_projects = manifest_parser.parse_manifest(aosp_path)
        print(f"✓ AOSP: {len(aosp_projects)} 个项目")

        # 保存 manifest 信息到数据库
        for p in aosp_projects:
            database.insert_manifest(p['name'], p['remote_url'], p['path'])

        # 2. 解析 Vendor manifest
        print(f"\n=== 解析 Vendor Manifest ===")
        vendor_projects = manifest_parser.parse_manifest(vendor_path)
        print(f"✓ Vendor: {len(vendor_projects)} 个项目")

        # 保存 manifest 信息到数据库
        for p in vendor_projects:
            database.insert_manifest(p['name'], p['remote_url'], p['path'])

        # 3. 扫描 AOSP git log
        print(f"\n=== 扫描 AOSP Git Log ===")
        aosp_commits = git_scanner.scan_all_projects(aosp_projects)
        database.bulk_insert_commits(aosp_commits)

        # 4. 扫描 Vendor git log
        print(f"\n=== 扫描 Vendor Git Log ===")
        vendor_commits = git_scanner.scan_all_projects(vendor_projects)
        database.bulk_insert_commits(vendor_commits)

        # 5. 差异分析
        print(f"\n=== 执行差异分析 ===")
        aosp_project_names = [p['name'] for p in aosp_projects]
        vendor_project_names = [p['name'] for p in vendor_projects]

        stats = diff_analyzer.analyze_diff(aosp_project_names, vendor_project_names)

        return {
            "success": True,
            "message": "扫描完成",
            "stats": {
                "aosp_projects": len(aosp_projects),
                "vendor_projects": len(vendor_projects),
                "total_commits": len(aosp_commits) + len(vendor_commits),
                "diff_stats": stats
            }
        }

    except Exception as e:
        print(f"✗ 扫描失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits")
async def get_commits(
    source: Optional[str] = None,
    project: Optional[str] = None,
    author: Optional[str] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None
):
    """
    获取所有 commits，支持筛选
    """
    try:
        commits = database.get_all_commits()

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
            "total": len(commits),
            "commits": commits
        }

    except Exception as e:
        print(f"✗ 获取 commits 失败: {e}")
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
