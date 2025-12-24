# Baseline Diff System（基线差异分析平台）

一个用于比较两个本地 Git 仓库（AOSP 与 Vendor）的 commit 差异分析平台，提供 WebUI 进行多标签分类和审计。

## 功能特性

- 自动解析 `.repo/manifest.xml` 获取项目信息
- 自动扫描所有项目的 git log 并提取 commit 信息
- 基于 Change-Id 进行差异分析（Common / AOSP Only / Vendor Only）
- 所有数据存储在 SQLite 数据库中
- WebUI 支持多标签分类（默认 + 自定义）
- 支持多维度筛选和关键词搜索
- 可点击 commit hash 跳转到远程仓库

## 技术栈

### 后端
- FastAPI - REST API 框架
- SQLite3 - 数据库
- Python 3.8+

### 前端
- React 18 - UI 框架
- Ant Design 5 - UI 组件库
- Vite - 构建工具
- Axios - HTTP 客户端

## 项目结构

```
baseline-diff-system/
├── backend/                     # 后端代码
│   ├── main.py                  # FastAPI 主文件
│   ├── database.py              # 数据库操作模块
│   ├── manifest_parser.py       # Manifest 解析模块
│   ├── git_scanner.py           # Git Log 扫描模块
│   ├── diff_analyzer.py         # 差异分析模块
│   ├── init_db.sql              # 数据库初始化 SQL
│   └── requirements.txt         # Python 依赖
│
├── frontend/                    # 前端代码
│   ├── src/
│   │   ├── components/          # React 组件
│   │   │   ├── ScanForm.jsx     # 扫描表单
│   │   │   ├── FilterPanel.jsx  # 筛选面板
│   │   │   └── CommitTable.jsx  # Commit 列表表格
│   │   ├── api/
│   │   │   └── client.js        # API 客户端
│   │   ├── App.jsx              # 主应用组件
│   │   └── main.jsx             # 入口文件
│   ├── package.json             # npm 依赖
│   └── vite.config.js           # Vite 配置
│
└── README.md                    # 本文档
```

## 数据库设计

### commits 表
存储所有 commit 信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| project | TEXT | 项目名称 |
| hash | TEXT | Commit Hash（唯一） |
| change_id | TEXT | Change-Id（用于差异分析） |
| author | TEXT | 作者 |
| date | TEXT | 提交日期 |
| subject | TEXT | 提交标题 |
| message | TEXT | 完整消息 |
| source | TEXT | 来源（common/aosp_only/vendor_only） |

### manifests 表
存储 manifest 项目信息

| 字段 | 类型 | 说明 |
|------|------|------|
| project | TEXT | 项目名称（主键） |
| remote_url | TEXT | 远程仓库 URL |
| path | TEXT | 项目路径 |

### categories 表
存储分类信息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| name | TEXT | 分类名称 |
| is_default | INTEGER | 是否为默认分类 |

### commit_categories 表
Commit 与分类的多对多关系

| 字段 | 类型 | 说明 |
|------|------|------|
| commit_hash | TEXT | Commit Hash（外键） |
| category_id | INTEGER | 分类 ID（外键） |

## 二进制打包部署（推荐）

如果你想在 Linux/Windows 上直接运行，无需安装 Python 和 Node.js，可以使用打包版本：

### 快速打包

```bash
# Linux
./build.sh

# Windows
build.bat
```

打包完成后，会生成单个可执行文件：
- Linux: `backend/dist/baseline-diff`
- Windows: `backend\dist\baseline-diff.exe`

### 特点

- 无需任何外部依赖（不需要 Python、Node.js）
- 单个文件包含完整的前后端
- 直接运行即可，监听 `http://0.0.0.0:8000`
- 文件大小约 80-120 MB

### 部署

```bash
# Linux 部署示例
scp backend/dist/baseline-diff user@target:/opt/
ssh user@target
cd /opt
chmod +x baseline-diff
./baseline-diff
```

详细的打包和部署说明，请参考：[BUILD_DEPLOY.md](BUILD_DEPLOY.md)

## 开发环境安装和运行

如果你需要开发或调试，按以下步骤安装：

### 1. 环境要求

- Python 3.8+
- Node.js 16+
- Git

### 2. 后端安装

```bash
cd baseline-diff-system/backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 后端运行

```bash
cd baseline-diff-system/backend

# 启动 FastAPI 服务器
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

后端将在 `http://localhost:8000` 运行

API 文档：`http://localhost:8000/docs`

### 4. 前端安装

```bash
cd baseline-diff-system/frontend

# 安装依赖
npm install
```

### 5. 前端运行

```bash
cd baseline-diff-system/frontend

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:3000` 运行

## 使用流程

### 1. 扫描仓库

在 WebUI 的"扫描仓库"表单中输入：

```json
{
  "aosp_path": "/path/to/aosp",
  "vendor_path": "/path/to/vendor"
}
```

点击"开始扫描"，系统将自动：

1. 解析两个仓库的 `.repo/manifest.xml`
2. 提取所有项目信息（name、path、remote URL）
3. 对每个项目执行 `git log`
4. 提取 Change-Id
5. 进行差异分析
6. 写入 SQLite 数据库

### 2. 查看 Commit 列表

扫描完成后，Commit 列表会自动显示：

- Project：项目名称
- Hash：Commit Hash（可点击跳转）
- Author：作者
- Date：提交日期
- Subject：提交标题
- Source：来源标签（Common / AOSP Only / Vendor Only）
- Categories：分类多选框

### 3. 筛选和搜索

左侧筛选面板支持：

- 按 Source 筛选
- 按 Project 筛选
- 按 Author 筛选
- 按 Category 筛选（多选）
- 关键词搜索（subject/message）

### 4. 分类管理

#### 默认分类

系统自带 9 个默认分类：

- security_fix
- security_risk
- bugfix
- feature
- refactor
- behavior_change
- vendor_customization
- remove_upstream
- other

#### 添加自定义分类

在右上角的"自定义分类"输入框中输入分类名称，点击"添加"。

#### 设置 Commit 分类

在 Commit 列表的 Categories 列中，使用多选下拉框选择分类，修改会自动保存。

### 5. 展开查看详情

点击表格行左侧的展开按钮，可以查看：

- Change-Id
- 完整的 commit message

## API 接口

### POST /scan_repos

扫描仓库

**请求体：**
```json
{
  "aosp_path": "/path/to/aosp",
  "vendor_path": "/path/to/vendor"
}
```

**响应：**
```json
{
  "success": true,
  "message": "扫描完成",
  "stats": {
    "aosp_projects": 100,
    "vendor_projects": 120,
    "total_commits": 5000,
    "diff_stats": {
      "total_aosp": 2000,
      "total_vendor": 2500,
      "common": 1500,
      "aosp_only": 500,
      "vendor_only": 1000
    }
  }
}
```

### GET /commits

获取所有 commits

**查询参数：**
- `source`（可选）：common / aosp_only / vendor_only
- `project`（可选）：项目名称
- `author`（可选）：作者名称
- `category_id`（可选）：分类 ID
- `search`（可选）：搜索关键词

**响应：**
```json
{
  "success": true,
  "total": 100,
  "commits": [...]
}
```

### POST /set_categories

设置 commit 分类

**请求体：**
```json
{
  "hash": "abc123...",
  "category_ids": [1, 2, 3]
}
```

### GET /categories/list

获取所有分类

**响应：**
```json
{
  "success": true,
  "categories": [
    {"id": 1, "name": "security_fix", "is_default": 1},
    {"id": 2, "name": "bugfix", "is_default": 1}
  ]
}
```

### POST /categories/add

添加自定义分类

**请求体：**
```json
{
  "name": "custom_category"
}
```

### POST /categories/remove

删除分类

**请求体：**
```json
{
  "id": 10
}
```

### GET /stats

获取统计信息

**响应：**
```json
{
  "success": true,
  "stats": {
    "total_commits": 5000,
    "common": 1500,
    "aosp_only": 500,
    "vendor_only": 1000
  }
}
```

## 差异分析规则

系统基于 Change-Id 进行差异分析：

1. 提取所有 AOSP commits 的 Change-Id → 集合 SA
2. 提取所有 Vendor commits 的 Change-Id → 集合 SV
3. 计算：
   - **COMMON** = SA ∩ SV（两边都有）
   - **AOSP_ONLY** = SA − SV（仅 AOSP 有）
   - **VENDOR_ONLY** = SV − SA（仅 Vendor 有）

4. 更新数据库中所有 commits 的 `source` 字段

## Commit URL 构造

系统会自动从 `manifest.xml` 中提取 `remote.fetch` URL，并构造 commit 链接：

```
remote_url + "/" + project + "/commit/" + hash
```

例如：
```
https://android.googlesource.com/platform/frameworks/base/commit/abc123def456
```

## 注意事项

1. 扫描大型仓库可能需要较长时间，请耐心等待
2. 确保 `.repo/manifest.xml` 文件存在且格式正确
3. 数据库文件 `db.sqlite3` 会在后端目录自动创建
4. 建议在扫描前备份数据库（如需保留旧数据）
5. 如果遇到权限问题，确保对仓库目录有读取权限

## 故障排查

### 后端无法启动

- 检查 Python 版本：`python --version`
- 检查依赖是否安装：`pip list`
- 查看错误日志

### 前端无法启动

- 检查 Node.js 版本：`node --version`
- 删除 `node_modules` 重新安装：`rm -rf node_modules && npm install`
- 检查端口 3000 是否被占用

### 扫描失败

- 检查路径是否正确
- 确保 `.repo/manifest.xml` 存在
- 检查 Git 是否安装：`git --version`
- 查看后端控制台日志

### API 请求失败

- 检查后端是否运行（访问 `http://localhost:8000`）
- 检查浏览器控制台的网络请求
- 确认 CORS 配置正确

## 开发和贡献

### 后端开发

修改代码后，uvicorn 会自动重载（使用 `--reload` 参数）

### 前端开发

修改代码后，Vite 会自动热更新

### 数据库重置

如需重置数据库：

```bash
cd baseline-diff-system/backend
rm db.sqlite3
python main.py  # 会自动重新初始化
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
