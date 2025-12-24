#!/bin/bash
# Baseline Diff System 自动化打包脚本
# 将前后端打包成单个 Linux 可执行文件

set -e  # 遇到错误立即退出

echo "========================================="
echo "  Baseline Diff System 构建脚本"
echo "========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. 构建前端
echo "步骤 1/4: 构建前端..."
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
echo "步骤 2/4: 复制前端产物到后端..."
echo "----------------------------"
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
echo "✓ 前端文件已复制到 backend/static/"
echo ""

# 3. 安装后端依赖
echo "步骤 3/4: 安装后端依赖..."
echo "----------------------------"
cd backend

if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "安装 Python 依赖..."
pip install -r requirements.txt -q
echo "✓ 后端依赖安装完成"
echo ""

# 4. 使用 PyInstaller 打包
echo "步骤 4/4: 打包二进制文件..."
echo "----------------------------"
echo "使用 PyInstaller 打包..."
pyinstaller baseline-diff.spec --clean --noconfirm

cd ..
echo "✓ 打包完成"
echo ""

# 5. 输出结果
echo "========================================="
echo "  构建成功！"
echo "========================================="
echo ""
echo "二进制文件位置: backend/dist/baseline-diff"
echo ""
echo "运行方法:"
echo "  ./backend/dist/baseline-diff"
echo ""
echo "或复制到其他 Linux 机器上运行:"
echo "  scp backend/dist/baseline-diff user@remote:/path/to/dest"
echo "  ssh user@remote '/path/to/dest/baseline-diff'"
echo ""
echo "注意事项:"
echo "  1. 二进制文件包含了完整的前后端代码和所有依赖"
echo "  2. 无需安装 Python、Node.js 或其他依赖"
echo "  3. 直接运行即可，默认监听 0.0.0.0:8000"
echo "  4. 访问 http://localhost:8000 使用 WebUI"
echo "  5. 数据库文件 db.sqlite3 会在运行目录下创建"
echo ""
