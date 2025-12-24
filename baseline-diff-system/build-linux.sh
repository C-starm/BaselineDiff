#!/bin/bash
# Baseline Diff System - Linux 可执行文件构建脚本
# 在 macOS/Windows 上使用 Docker 构建 Linux 可执行文件

set -e  # 遇到错误立即退出

echo "========================================="
echo "  Baseline Diff System - Linux 构建"
echo "========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到 Docker，请先安装 Docker"
    echo "下载地址: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. 构建前端
echo "步骤 1/5: 构建前端..."
echo "----------------------------"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "构建前端静态文件..."
npm run build

cd ..
echo "✓ 前端构建完成"
echo ""

# 2. 复制前端构建产物到后端
echo "步骤 2/5: 复制前端产物到后端..."
echo "----------------------------"
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
echo "✓ 前端文件已复制到 backend/static/"
echo ""

# 3. 构建 Docker 镜像
echo "步骤 3/5: 构建 Docker 镜像..."
echo "----------------------------"
docker build -f Dockerfile.build -t baseline-diff-builder .
echo "✓ Docker 镜像构建完成"
echo ""

# 4. 在 Docker 容器中运行 PyInstaller
echo "步骤 4/5: 在 Docker 容器中打包..."
echo "----------------------------"
# 创建临时容器并运行打包
CONTAINER_ID=$(docker create baseline-diff-builder)
echo "容器 ID: $CONTAINER_ID"

# 运行打包命令
docker start -a $CONTAINER_ID

echo "✓ 打包完成"
echo ""

# 5. 从容器中复制可执行文件
echo "步骤 5/5: 提取可执行文件..."
echo "----------------------------"
# 清理旧的 dist 目录
rm -rf backend/dist
mkdir -p backend/dist

# 从容器中复制可执行文件
docker cp $CONTAINER_ID:/build/backend/dist/baseline-diff backend/dist/
docker rm $CONTAINER_ID

echo "✓ 可执行文件已提取"
echo ""

# 输出结果
echo "========================================="
echo "  构建成功！"
echo "========================================="
echo ""
echo "Linux 二进制文件位置: backend/dist/baseline-diff"
echo ""
echo "文件信息:"
file backend/dist/baseline-diff || echo "  (file 命令未安装，跳过文件类型检测)"
ls -lh backend/dist/baseline-diff
echo ""
echo "运行方法:"
echo "  1. 复制到 Linux 机器:"
echo "     scp backend/dist/baseline-diff user@linux-server:/path/to/dest"
echo ""
echo "  2. 在 Linux 上运行:"
echo "     chmod +x /path/to/dest/baseline-diff"
echo "     /path/to/dest/baseline-diff"
echo ""
echo "  3. 或使用 Docker 测试运行:"
echo "     docker run --rm -p 8000:8000 -v \$(pwd)/backend/dist:/app python:3.11-slim /app/baseline-diff"
echo ""
echo "注意事项:"
echo "  1. 生成的是 Linux x86_64 可执行文件"
echo "  2. 无需在 Linux 上安装 Python、Node.js 或其他依赖"
echo "  3. 直接运行即可，默认监听 0.0.0.0:8000"
echo "  4. 访问 http://localhost:8000 使用 WebUI"
echo "  5. 数据库文件 db.sqlite3 会在运行目录下创建"
echo ""
