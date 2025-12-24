# 打包与部署指南

本文档详细说明如何将 Baseline Diff System 打包成单个可执行文件，并在 Linux/Windows 上部署。

## 概述

打包后的特点：
- **单一可执行文件**：包含前端 + 后端 + 所有依赖
- **无需外部依赖**：不需要 Python、Node.js、npm
- **开箱即用**：直接运行即可
- **跨平台**：支持 Linux 和 Windows

## 前置要求

### 构建机器要求

在**开发机器**上进行打包，需要：

- Python 3.8+
- Node.js 16+
- npm
- Git

## 快速打包

### Linux 打包

```bash
# 克隆项目
git clone git@github.com:C-starm/BaselineDiff.git
cd BaselineDiff

# 执行自动化打包脚本
./build.sh
```

打包完成后，可执行文件位于：`backend/dist/baseline-diff`

### Windows 打包

```cmd
# 克隆项目
git clone git@github.com:C-starm/BaselineDiff.git
cd BaselineDiff

# 执行自动化打包脚本
build.bat
```

打包完成后，可执行文件位于：`backend\dist\baseline-diff.exe`

## 详细打包步骤

如果自动化脚本失败，可以手动执行以下步骤：

### 1. 构建前端

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

这会在 `frontend/dist/` 目录生成静态文件。

### 2. 复制前端产物到后端

```bash
# 返回项目根目录
cd ..

# 复制到后端 static 目录
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
```

### 3. 安装后端依赖

```bash
cd backend

# 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 使用 PyInstaller 打包

```bash
# 在 backend 目录下执行
pyinstaller baseline-diff.spec --clean --noconfirm
```

打包完成后：
- Linux: `backend/dist/baseline-diff`
- Windows: `backend\dist\baseline-diff.exe`

## 部署到目标机器

### Linux 部署

```bash
# 1. 复制到目标机器
scp backend/dist/baseline-diff user@target-host:/opt/baseline-diff/

# 2. SSH 到目标机器
ssh user@target-host

# 3. 添加执行权限
chmod +x /opt/baseline-diff/baseline-diff

# 4. 运行
cd /opt/baseline-diff
./baseline-diff
```

服务会在 `http://0.0.0.0:8000` 启动。

### Windows 部署

1. 复制 `baseline-diff.exe` 到目标机器
2. 双击运行，或在命令行中执行：
   ```cmd
   baseline-diff.exe
   ```

## 配置和使用

### 默认配置

- 监听地址：`0.0.0.0`
- 监听端口：`8000`
- 数据库文件：`db.sqlite3`（在运行目录下自动创建）

### 访问 WebUI

打开浏览器访问：
- 本地：http://localhost:8000
- 远程：http://目标机器IP:8000

### 修改监听端口

如果需要修改端口，编辑 `backend/main.py` 最后一行：

```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # 改成你想要的端口
```

然后重新打包。

### 后台运行（Linux）

#### 方法 1：使用 nohup

```bash
nohup ./baseline-diff > baseline-diff.log 2>&1 &
```

#### 方法 2：使用 systemd

创建 `/etc/systemd/system/baseline-diff.service`：

```ini
[Unit]
Description=Baseline Diff System
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/opt/baseline-diff
ExecStart=/opt/baseline-diff/baseline-diff
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable baseline-diff
sudo systemctl start baseline-diff
sudo systemctl status baseline-diff
```

#### 方法 3：使用 screen 或 tmux

```bash
screen -S baseline-diff
./baseline-diff
# 按 Ctrl+A 然后 D 分离会话

# 重新连接
screen -r baseline-diff
```

### 后台运行（Windows）

#### 方法 1：使用 NSSM（推荐）

1. 下载 NSSM: https://nssm.cc/download
2. 安装服务：
   ```cmd
   nssm install BaselineDiff C:\path\to\baseline-diff.exe
   nssm start BaselineDiff
   ```

#### 方法 2：使用任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：系统启动时
4. 操作：启动程序 `baseline-diff.exe`

## 数据备份

重要：定期备份数据库文件！

```bash
# 备份
cp db.sqlite3 backup/db_$(date +%Y%m%d_%H%M%S).sqlite3

# 恢复
cp backup/db_20241224_120000.sqlite3 db.sqlite3
```

## 性能优化

### 1. 限制并发扫描

修改 `backend/git_scanner.py`，添加并发限制：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_all_projects(projects, max_count=None, max_workers=4):
    all_commits = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scan_project, p['path'], p['name'], max_count): p
            for p in projects
        }
        for future in as_completed(futures):
            commits = future.result()
            all_commits.extend(commits)
    return all_commits
```

### 2. 数据库优化

在 `backend/init_db.sql` 中已创建必要的索引。如果数据量很大，可以考虑：

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;  -- 64MB
```

### 3. 使用 Nginx 反向代理（生产环境）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置（扫描可能很慢）
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

## 故障排查

### 问题 1：二进制文件无法运行

**错误**：`./baseline-diff: Permission denied`

**解决**：
```bash
chmod +x baseline-diff
```

### 问题 2：端口被占用

**错误**：`Address already in use`

**解决**：
1. 查找占用端口的进程：
   ```bash
   # Linux
   lsof -i :8000
   netstat -tulpn | grep 8000

   # Windows
   netstat -ano | findstr :8000
   ```

2. 修改端口或停止占用进程

### 问题 3：静态文件 404

**原因**：前端文件未正确打包

**解决**：
1. 确认 `backend/static/` 目录存在且包含文件
2. 重新执行打包脚本

### 问题 4：数据库锁定

**错误**：`database is locked`

**解决**：
1. 检查是否有多个实例同时运行
2. 使用 WAL 模式（见性能优化）

### 问题 5：扫描超时

**错误**：扫描大型仓库时超时

**解决**：
1. 修改 `frontend/src/api/client.js` 的 timeout 值
2. 分批扫描小项目

## 安全建议

### 生产环境

1. **不要以 root 用户运行**
   ```bash
   # 创建专用用户
   sudo useradd -r -s /bin/false baseline-diff
   sudo -u baseline-diff ./baseline-diff
   ```

2. **限制访问 IP**
   - 使用防火墙规则
   - 使用 Nginx 反向代理

3. **使用 HTTPS**
   - 配置 SSL 证书
   - 使用 Let's Encrypt

4. **定期更新**
   - 关注安全更新
   - 定期重新打包

## 文件大小

打包后的文件大小：
- Linux: 约 80-120 MB
- Windows: 约 90-130 MB

大小包含：
- Python 解释器
- 所有 Python 库
- 前端静态文件
- 数据库初始化脚本

## 更新和维护

### 更新代码后重新打包

```bash
# 拉取最新代码
git pull origin main

# 重新打包
./build.sh  # Linux
# 或 build.bat  # Windows

# 替换旧的可执行文件
scp backend/dist/baseline-diff user@target:/opt/baseline-diff/
```

### 数据迁移

旧版本的数据库可能与新版本不兼容，迁移步骤：

1. 导出数据（CSV 或 JSON）
2. 更新程序
3. 重新导入数据

## 高级：Docker 部署（可选）

如果目标环境支持 Docker，也可以使用 Docker 部署：

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY --from=frontend-build /app/dist ./static

CMD ["python", "main.py"]
```

构建和运行：

```bash
docker build -t baseline-diff .
docker run -d -p 8000:8000 -v $(pwd)/data:/app baseline-diff
```

## 许可证

MIT License

## 技术支持

遇到问题请提交 Issue：
https://github.com/C-starm/BaselineDiff/issues

---

**祝部署顺利！**
