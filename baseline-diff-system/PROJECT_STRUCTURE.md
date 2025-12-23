# 项目文件结构说明

本文档详细说明了 Baseline Diff System 的完整文件结构和各文件的功能。

## 完整文件树

```
baseline-diff-system/
├── README.md                          # 项目主文档
├── QUICKSTART.md                      # 快速启动指南
├── PROJECT_STRUCTURE.md               # 本文件
│
├── backend/                           # 后端目录
│   ├── .gitignore                     # Git 忽略文件
│   ├── requirements.txt               # Python 依赖
│   ├── init_db.sql                    # 数据库初始化 SQL
│   ├── database.py                    # 数据库操作模块
│   ├── manifest_parser.py             # Manifest.xml 解析器
│   ├── git_scanner.py                 # Git Log 扫描器
│   ├── diff_analyzer.py               # 差异分析器
│   └── main.py                        # FastAPI 主应用
│
└── frontend/                          # 前端目录
    ├── .gitignore                     # Git 忽略文件
    ├── package.json                   # npm 依赖配置
    ├── vite.config.js                 # Vite 构建配置
    ├── index.html                     # HTML 入口
    └── src/
        ├── main.jsx                   # React 入口文件
        ├── App.jsx                    # 主应用组件
        ├── api/
        │   └── client.js              # API 客户端
        └── components/
            ├── ScanForm.jsx           # 扫描表单组件
            ├── FilterPanel.jsx        # 筛选面板组件
            └── CommitTable.jsx        # Commit 表格组件
```

## 后端文件说明

### 1. backend/init_db.sql
**数据库初始化脚本**

- 创建 4 个表：commits, manifests, categories, commit_categories
- 创建必要的索引
- 插入 9 个默认分类
- 总行数：约 60 行

### 2. backend/database.py
**数据库操作模块**

核心函数：
- `init_database()` - 初始化数据库
- `insert_manifest()` - 插入 manifest 信息
- `insert_commit()` - 插入单个 commit
- `bulk_insert_commits()` - 批量插入 commits
- `get_all_commits()` - 获取所有 commits（含分类）
- `set_commit_categories()` - 设置 commit 分类
- `get_all_categories()` - 获取所有分类
- `add_category()` - 添加新分类
- `remove_category()` - 删除分类
- `clear_all_commits()` - 清空数据

总行数：约 180 行

### 3. backend/manifest_parser.py
**Manifest.xml 解析模块**

功能：
- 解析 `.repo/manifest.xml`
- 提取 `<remote>` 标签的 fetch URL
- 提取 `<project>` 标签的 name、path
- 构造完整的项目路径
- 返回项目列表

核心类：`ManifestParser`

总行数：约 90 行

### 4. backend/git_scanner.py
**Git Log 扫描模块**

功能：
- 对指定 Git 仓库执行 `git log`
- 解析 commit 信息（hash, author, date, subject, message）
- 从 message 中提取 Change-Id
- 支持批量扫描多个项目

核心类：`GitScanner`

Git 命令格式：
```bash
git -C <path> log --pretty=format:"%H||%an||%ad||%s||%b" --date=iso
```

总行数：约 120 行

### 5. backend/diff_analyzer.py
**差异分析模块**

功能：
- 从数据库加载 AOSP 和 Vendor 的 Change-Id
- 执行集合运算（交集、差集）
- 计算 common、aosp_only、vendor_only
- 更新数据库中所有 commits 的 source 字段

核心类：`DiffAnalyzer`

算法：
```
COMMON      = SA ∩ SV
AOSP_ONLY   = SA − SV
VENDOR_ONLY = SV − SA
```

总行数：约 110 行

### 6. backend/main.py
**FastAPI 主应用**

API 端点：
- `POST /scan_repos` - 扫描仓库
- `GET /commits` - 获取 commits（支持筛选）
- `POST /set_categories` - 设置 commit 分类
- `GET /categories/list` - 获取所有分类
- `POST /categories/add` - 添加分类
- `POST /categories/remove` - 删除分类
- `GET /stats` - 获取统计信息
- `GET /` - 健康检查

配置：
- CORS 支持
- 自动初始化数据库
- 错误处理

总行数：约 220 行

### 7. backend/requirements.txt
**Python 依赖**

依赖包：
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- pydantic==2.5.3
- python-multipart==0.0.6

## 前端文件说明

### 1. frontend/package.json
**npm 依赖配置**

依赖：
- react 18.2.0
- react-dom 18.2.0
- antd 5.12.0 - UI 组件库
- axios 1.6.2 - HTTP 客户端

开发依赖：
- vite 5.0.8
- @vitejs/plugin-react 4.2.1

脚本：
- `npm run dev` - 开发服务器
- `npm run build` - 构建生产版本

### 2. frontend/vite.config.js
**Vite 构建配置**

配置项：
- React 插件
- 开发服务器端口：3000
- API 代理：/api → http://localhost:8000

### 3. frontend/index.html
**HTML 入口**

简单的 HTML 模板，包含：
- `<div id="root">` - React 挂载点
- `<script src="/src/main.jsx">` - 入口脚本

### 4. frontend/src/main.jsx
**React 入口文件**

功能：
- 导入 React 和 App 组件
- 导入 Ant Design 样式
- 渲染根组件到 DOM

总行数：约 10 行

### 5. frontend/src/App.jsx
**主应用组件**

功能：
- 管理全局状态（commits, categories, filters, stats）
- 加载数据（commits, categories, stats）
- 应用筛选逻辑
- 处理用户交互（扫描、分类、搜索）
- 布局：左侧筛选面板 + 右侧表格

总行数：约 180 行

### 6. frontend/src/api/client.js
**API 客户端**

功能：
- 封装所有 API 调用
- 配置 axios 实例
- 设置超时时间（10 分钟）

导出函数：
- `scanRepos()`
- `getCommits()`
- `setCategories()`
- `getCategories()`
- `addCategory()`
- `removeCategory()`
- `getStats()`

总行数：约 50 行

### 7. frontend/src/components/ScanForm.jsx
**扫描表单组件**

功能：
- 输入 AOSP 和 Vendor 路径
- 提交扫描请求
- 显示加载状态
- 扫描完成后触发回调

使用的 Ant Design 组件：
- Form, Input, Button, Card

总行数：约 60 行

### 8. frontend/src/components/FilterPanel.jsx
**筛选面板组件**

功能：
- Source 筛选（单选）
- Project 筛选（单选，可搜索）
- Author 筛选（单选，可搜索）
- Category 筛选（多选）
- 关键词搜索
- 重置按钮

使用的 Ant Design 组件：
- Card, Select, Input, Button, Space

总行数：约 90 行

### 9. frontend/src/components/CommitTable.jsx
**Commit 表格组件**

功能：
- 显示 commit 列表
- 支持分页
- 可展开查看详细信息
- 在线修改分类（多选下拉框）
- Hash 可点击跳转

列：
- Project
- Hash（可点击）
- Author
- Date
- Subject
- Source（标签）
- Categories（多选）

使用的 Ant Design 组件：
- Table, Tag, Select, Typography

总行数：约 100 行

## 数据库设计

### commits 表
```sql
CREATE TABLE commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT,
    hash TEXT UNIQUE,
    change_id TEXT,
    author TEXT,
    date TEXT,
    subject TEXT,
    message TEXT,
    source TEXT CHECK(source IN ('common','aosp_only','vendor_only'))
)
```

### manifests 表
```sql
CREATE TABLE manifests (
    project TEXT PRIMARY KEY,
    remote_url TEXT,
    path TEXT
)
```

### categories 表
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    is_default INTEGER DEFAULT 0
)
```

### commit_categories 表
```sql
CREATE TABLE commit_categories (
    commit_hash TEXT,
    category_id INTEGER,
    PRIMARY KEY(commit_hash, category_id)
)
```

## 代码统计

### 后端
- init_db.sql: ~60 行
- database.py: ~180 行
- manifest_parser.py: ~90 行
- git_scanner.py: ~120 行
- diff_analyzer.py: ~110 行
- main.py: ~220 行
- **后端总计：~780 行**

### 前端
- main.jsx: ~10 行
- App.jsx: ~180 行
- client.js: ~50 行
- ScanForm.jsx: ~60 行
- FilterPanel.jsx: ~90 行
- CommitTable.jsx: ~100 行
- **前端总计：~490 行**

### 配置文件
- package.json, vite.config.js, index.html: ~50 行
- requirements.txt: ~5 行
- .gitignore: ~30 行

**项目总代码量：约 1355 行**

## 技术亮点

1. **模块化设计**：后端每个功能独立成模块，便于维护和扩展

2. **自动化流程**：一键扫描 → 解析 → 分析 → 存储

3. **高效数据库设计**：
   - 多对多关系表
   - 完善的索引
   - 事务支持

4. **用户友好的 UI**：
   - 实时筛选
   - 多选分类
   - 展开详情
   - 一键跳转

5. **可扩展性**：
   - 支持自定义分类
   - 易于添加新的筛选条件
   - API 设计清晰

## 运行流程图

```
用户输入路径
    ↓
POST /scan_repos
    ↓
解析 AOSP manifest.xml ──→ 保存到 manifests 表
    ↓
解析 Vendor manifest.xml ──→ 保存到 manifests 表
    ↓
扫描 AOSP git log ──→ 批量插入 commits 表
    ↓
扫描 Vendor git log ──→ 批量插入 commits 表
    ↓
执行差异分析 ──→ 更新 commits.source 字段
    ↓
返回统计信息
    ↓
前端刷新数据
    ↓
显示 Commit 列表
    ↓
用户筛选/分类/搜索
```

## 维护建议

1. **定期备份数据库**
   ```bash
   cp backend/db.sqlite3 backup/db_$(date +%Y%m%d).sqlite3
   ```

2. **监控性能**
   - 扫描大型仓库时观察 CPU/内存
   - 数据库查询优化（已有索引）

3. **日志记录**
   - 后端已有 print 输出
   - 建议添加文件日志（logging 模块）

4. **安全性**
   - 生产环境修改 CORS 配置
   - 添加用户认证（如需要）
   - 限制 API 请求频率

5. **扩展功能**
   - 添加导出功能（CSV/Excel）
   - 添加更多统计图表
   - 支持 diff 对比
   - 添加评论功能

祝使用愉快！
