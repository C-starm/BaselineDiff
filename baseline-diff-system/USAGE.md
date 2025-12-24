# Baseline Diff System - 使用指南

## 系统要求

这个系统专门用于比较 **repo 管理的多项目仓库**（如 AOSP）。

### 必需的目录结构

你的 AOSP 和 Vendor 目录必须包含：

```
your-aosp/
├── .repo/
│   └── manifest.xml    ← 必需
├── project1/
│   └── .git/
├── project2/
│   └── .git/
└── ...
```

### 不支持的情况

如果你只有单个 Git 仓库（没有 `.repo` 文件夹），这个系统**无法工作**。

## 快速开始

### 1. 启动服务

```bash
# 使用可执行文件
./baseline-diff-linux-x86_64

# 或使用 Docker
docker run --rm -p 8000:8000 \
  -v $(pwd)/baseline-diff-linux-x86_64:/app/baseline-diff \
  python:3.11-slim \
  /app/baseline-diff
```

### 2. 访问 WebUI

打开浏览器访问：http://localhost:8000

### 3. 配置路径

在 WebUI 中输入：
- **AOSP Path**: `/path/to/your-aosp` (包含 `.repo` 文件夹的目录)
- **Vendor Path**: `/path/to/your-vendor` (包含 `.repo` 文件夹的目录)

### 4. 开始扫描

点击"开始扫描"按钮，系统将：
1. 解析 `manifest.xml`
2. 扫描所有项目的 Git log
3. 分析差异
4. 显示结果

## 故障排查

### 问题：commits 表为空

如果扫描后 commits 表为空，请使用诊断脚本：

```bash
cd backend
python diagnose.py /path/to/your-aosp
```

诊断脚本会检查：
1. 数据库状态
2. manifest.xml 是否存在
3. 项目列表是否正确
4. Git 仓库是否有效
5. Git log 是否能正常扫描

### 常见错误

#### 错误 1: manifest.xml 不存在

```
✗ manifest.xml 不存在: /path/to/repo/.repo/manifest.xml
```

**解决方案**：
- 确认路径正确
- 确认是 repo 管理的仓库
- 确认有 `.repo/manifest.xml` 文件

#### 错误 2: 项目路径不存在

```
⚠ 项目路径不存在: /path/to/project
```

**解决方案**：
- 检查 manifest.xml 中的项目路径是否正确
- 确认项目已经 repo sync 下载

#### 错误 3: 不是 Git 仓库

```
⚠ 不是 Git 仓库: /path/to/project
```

**解决方案**：
- 确认项目目录下有 `.git` 文件夹
- 尝试重新 `repo sync`

#### 错误 4: Git 仓库为空

```
✓ 找到 0 个 commits
```

**解决方案**：
- 检查 Git 仓库是否真的有 commits
- 运行 `git log` 手动验证

## 高级用法

### 查看后端日志

后端运行时会在控制台输出详细日志：

```
=== 解析 AOSP Manifest ===
✓ AOSP: 150 个项目

=== 扫描 AOSP Git Log ===
[1/150] 扫描项目: platform/frameworks/base
  ✓ 找到 1234 个 commits
[2/150] 扫描项目: platform/system/core
  ✓ 找到 567 个 commits
...

✓ 扫描完成，共 50000 个 commits
✓ AOSP commits 已插入数据库
```

如果看到：
```
⚠ 警告：AOSP 没有扫描到任何 commits
```

说明扫描出现问题，请使用诊断脚本排查。

### 手动测试 manifest 解析

```bash
cd backend
python manifest_parser.py /path/to/your-aosp
```

输出示例：
```
✓ 解析成功，共找到 150 个项目
  - platform/frameworks/base: /path/to/aosp/frameworks/base
  - platform/system/core: /path/to/aosp/system/core
  ... 还有 148 个项目
```

### 手动测试 Git 扫描

```bash
cd backend
python git_scanner.py /path/to/aosp/frameworks/base
```

输出示例：
```
✓ 找到 10 个 commits

  Hash: a1b2c3d4
  Author: Developer Name
  Date: 2024-01-01 12:00:00 +0800
  Subject: Add new feature
  Change-Id: I1234567890abcdef
```

### 直接检查数据库

```bash
cd backend
sqlite3 db.sqlite3

sqlite> SELECT COUNT(*) FROM commits;
sqlite> SELECT COUNT(*) FROM manifests;
sqlite> SELECT * FROM commits LIMIT 5;
```

## 性能优化

### 限制扫描数量

如果仓库很大，可以修改 `git_scanner.py` 中的 `max_count` 参数：

```python
# 在 scan_all_projects 函数中
commits = scan_project(project['path'], project['name'], max_count=100)
```

这样每个项目最多只扫描 100 个 commits。

### 并行扫描

默认是串行扫描，可以修改为并行扫描以提高速度（需要修改代码）。

## 数据管理

### 清空数据

在 WebUI 中点击"清空所有数据"，或手动：

```bash
cd backend
sqlite3 db.sqlite3 "DELETE FROM commits;"
sqlite3 db.sqlite3 "DELETE FROM manifests;"
```

### 备份数据

```bash
cd backend
cp db.sqlite3 db.sqlite3.backup
```

### 恢复数据

```bash
cd backend
cp db.sqlite3.backup db.sqlite3
```

## 获取帮助

如果以上方法都无法解决问题：

1. 运行诊断脚本并保存输出：
   ```bash
   python backend/diagnose.py /path/to/aosp > diagnose.log 2>&1
   ```

2. 在 GitHub 提交 Issue：
   https://github.com/C-starm/BaselineDiff/issues

3. 附上以下信息：
   - `diagnose.log` 内容
   - 操作系统和版本
   - manifest.xml 示例（前10行）
   - 完整的错误信息
