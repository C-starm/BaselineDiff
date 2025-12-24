# 故障排查指南

## 错误：lib64/ld-linux-x86_64.so.2: no such file

### 问题诊断

如果你在运行可执行文件时遇到 `lib64/ld-linux-x86_64.so.2: no such file` 错误，请按以下步骤诊断：

#### 1. 检查你的 Linux 发行版

```bash
cat /etc/os-release
```

#### 2. 检查动态链接器是否存在

```bash
ls -la /lib64/ld-linux-x86_64.so.2
# 或
ls -la /lib/x86_64-linux-gnu/ld-linux-x86_64.so.2
```

#### 3. 检查可执行文件的依赖

```bash
ldd baseline-diff-linux-x86_64
```

### 解决方案

#### 方案 1: 安装 glibc（推荐）

**对于 Debian/Ubuntu 系统：**
```bash
sudo apt-get update
sudo apt-get install libc6
```

**对于 CentOS/RHEL/Rocky Linux：**
```bash
sudo yum install glibc
```

**对于 Fedora：**
```bash
sudo dnf install glibc
```

**对于 Alpine Linux：**
Alpine Linux 默认使用 musl libc 而不是 glibc，需要安装 glibc 兼容层：
```bash
apk add gcompat
```

#### 方案 2: 使用 Docker 运行（推荐）

如果你的系统环境比较特殊，最简单的方法是使用 Docker：

```bash
# 使用 Docker 运行 x86_64 版本
docker run --rm -p 8000:8000 \
  -v $(pwd)/baseline-diff-linux-x86_64:/app/baseline-diff \
  -v $(pwd)/data:/app/data \
  python:3.11-slim \
  /app/baseline-diff
```

或者使用 ARM64 版本：
```bash
# 使用 Docker 运行 ARM64 版本
docker run --rm -p 8000:8000 \
  -v $(pwd)/baseline-diff-linux-arm64:/app/baseline-diff \
  -v $(pwd)/data:/app/data \
  python:3.11-slim \
  /app/baseline-diff
```

#### 方案 3: 在 Alpine Linux 上运行

如果你使用的是 Alpine Linux，需要安装兼容层：

```bash
# 安装 glibc 兼容层
apk add --no-cache gcompat

# 运行可执行文件
./baseline-diff-linux-x86_64
```

#### 方案 4: 检查文件权限

确保文件有执行权限：

```bash
chmod +x baseline-diff-linux-x86_64
./baseline-diff-linux-x86_64
```

### 常见问题

#### Q: 我的系统是 Alpine Linux，应该用哪个版本？

A: Alpine Linux 使用 musl libc，与我们构建的 glibc 版本不兼容。推荐：
1. 使用 Docker 运行（最简单）
2. 安装 `gcompat` 包提供 glibc 兼容层
3. 联系我们提供专门的 Alpine Linux 静态链接版本

#### Q: 如何确认我的系统架构？

```bash
uname -m
```
- `x86_64` 或 `amd64` - 使用 baseline-diff-linux-x86_64
- `aarch64` 或 `arm64` - 使用 baseline-diff-linux-arm64

#### Q: 错误信息显示 "cannot execute binary file"？

这通常意味着你在错误的架构上运行了可执行文件。检查系统架构并下载对应的版本。

#### Q: 如何在容器中持久化数据？

使用 volume 挂载数据目录：

```bash
mkdir -p data
docker run --rm -p 8000:8000 \
  -v $(pwd)/baseline-diff-linux-x86_64:/app/baseline-diff \
  -v $(pwd)/data:/app/data \
  -w /app/data \
  python:3.11-slim \
  /app/baseline-diff
```

这样 `db.sqlite3` 会保存在 `./data` 目录中。

### 获取帮助

如果以上方法都无法解决问题，请在 GitHub Issues 中报告：
https://github.com/C-starm/BaselineDiff/issues

请提供以下信息：
1. `cat /etc/os-release` 的输出
2. `uname -a` 的输出
3. `ldd baseline-diff-linux-x86_64` 的输出（如果可以运行）
4. 完整的错误信息
