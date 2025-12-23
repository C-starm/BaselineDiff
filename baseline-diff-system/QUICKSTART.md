# 快速启动指南

## 一、环境准备

确保已安装：
- Python 3.8+
- Node.js 16+
- Git

## 二、后端启动

```bash
# 1. 进入后端目录
cd baseline-diff-system/backend

# 2. 创建虚拟环境（可选但推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动后端服务器
python main.py
```

后端运行在：**http://localhost:8000**

API 文档：**http://localhost:8000/docs**

## 三、前端启动

**打开新的终端窗口**

```bash
# 1. 进入前端目录
cd baseline-diff-system/frontend

# 2. 安装依赖
npm install

# 3. 启动前端服务器
npm run dev
```

前端运行在：**http://localhost:3000**

## 四、使用系统

1. 打开浏览器访问：**http://localhost:3000**

2. 在"扫描仓库"表单中输入路径：
   - AOSP 仓库路径：`/path/to/your/aosp`
   - Vendor 仓库路径：`/path/to/your/vendor`

3. 点击"开始扫描"

4. 等待扫描完成（大型仓库可能需要数分钟）

5. 查看 Commit 列表并进行分类

## 五、示例数据流

### 1. 扫描仓库

POST http://localhost:8000/scan_repos
```json
{
  "aosp_path": "/home/user/aosp",
  "vendor_path": "/home/user/vendor"
}
```

### 2. 获取 Commits

GET http://localhost:8000/commits

### 3. 设置分类

POST http://localhost:8000/set_categories
```json
{
  "hash": "abc123def456",
  "category_ids": [1, 2, 3]
}
```

### 4. 添加自定义分类

POST http://localhost:8000/categories/add
```json
{
  "name": "my_custom_category"
}
```

## 六、常见问题

### Q1: 扫描速度慢？
A: 这是正常的。系统需要遍历所有项目的 git log。可以在后端控制台查看进度。

### Q2: 数据库在哪里？
A: SQLite 数据库文件 `db.sqlite3` 位于 `backend/` 目录下。

### Q3: 如何重置数据？
A: 删除 `backend/db.sqlite3` 文件，重启后端即可自动重建。

```bash
cd baseline-diff-system/backend
rm db.sqlite3
python main.py
```

### Q4: 前端看不到数据？
A: 确保：
1. 后端正在运行（访问 http://localhost:8000 检查）
2. 已经执行过扫描操作
3. 浏览器控制台没有错误

### Q5: 端口冲突？
A: 修改配置：
- 后端：`main.py` 最后一行改 `port=8001`
- 前端：`vite.config.js` 改 `port: 3001`

## 七、停止服务

在各自的终端窗口中按 `Ctrl+C` 停止服务。

## 八、生产部署建议

### 后端
```bash
# 使用 gunicorn 或 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 前端
```bash
# 构建生产版本
npm run build

# 使用 nginx 或其他 Web 服务器托管 dist/ 目录
```

## 九、数据库备份

定期备份数据库文件：

```bash
cp backend/db.sqlite3 backup/db_$(date +%Y%m%d).sqlite3
```

## 十、性能优化提示

1. **限制扫描范围**：如果只需要最近的 commits，可以修改 `git_scanner.py` 的 `max_count` 参数

2. **并行扫描**：修改 `git_scanner.py` 使用多进程扫描多个项目

3. **数据库索引**：已在 `init_db.sql` 中创建了必要的索引

4. **分页加载**：前端已配置分页（每页 50 条）

祝使用愉快！
