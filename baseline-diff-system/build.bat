@echo off
REM Baseline Diff System 自动化打包脚本 (Windows)
REM 将前后端打包成单个 Windows 可执行文件

echo =========================================
echo   Baseline Diff System 构建脚本 (Windows)
echo =========================================
echo.

REM 1. 构建前端
echo 步骤 1/4: 构建前端...
echo ----------------------------
cd frontend

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

echo 构建前端静态文件...
call npm run build

cd ..
echo ✓ 前端构建完成
echo.

REM 2. 复制前端构建产物到后端
echo 步骤 2/4: 复制前端产物到后端...
echo ----------------------------
if exist "backend\static" rmdir /s /q backend\static
mkdir backend\static
xcopy /s /e /y frontend\dist\* backend\static\
echo ✓ 前端文件已复制到 backend\static\
echo.

REM 3. 安装后端依赖
echo 步骤 3/4: 安装后端依赖...
echo ----------------------------
cd backend

if not exist "venv" (
    echo 创建 Python 虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo 安装 Python 依赖...
pip install -r requirements.txt -q
echo ✓ 后端依赖安装完成
echo.

REM 4. 使用 PyInstaller 打包
echo 步骤 4/4: 打包二进制文件...
echo ----------------------------
echo 使用 PyInstaller 打包...
pyinstaller baseline-diff.spec --clean --noconfirm

cd ..
echo ✓ 打包完成
echo.

REM 5. 输出结果
echo =========================================
echo   构建成功！
echo =========================================
echo.
echo 可执行文件位置: backend\dist\baseline-diff.exe
echo.
echo 运行方法:
echo   backend\dist\baseline-diff.exe
echo.
echo 注意事项:
echo   1. 可执行文件包含了完整的前后端代码和所有依赖
echo   2. 无需安装 Python、Node.js 或其他依赖
echo   3. 直接运行即可，默认监听 0.0.0.0:8000
echo   4. 访问 http://localhost:8000 使用 WebUI
echo   5. 数据库文件 db.sqlite3 会在运行目录下创建
echo.
pause
