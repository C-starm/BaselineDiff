-- 基线差异分析平台数据库初始化脚本

-- 清理旧表
DROP TABLE IF EXISTS commit_categories;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS commits;
DROP TABLE IF EXISTS manifests;

-- manifests 表：存储 manifest.xml 中的项目信息
CREATE TABLE manifests (
    project TEXT PRIMARY KEY,
    remote_url TEXT NOT NULL,
    path TEXT NOT NULL
);

-- commits 表：存储所有 commit 信息
CREATE TABLE commits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    hash TEXT UNIQUE NOT NULL,
    change_id TEXT,
    author TEXT,
    date TEXT,
    subject TEXT,
    message TEXT,
    reviewed_on TEXT,
    source TEXT CHECK(source IS NULL OR source IN ('common','aosp_only','vendor_only')),
    FOREIGN KEY (project) REFERENCES manifests(project)
);

-- categories 表：存储所有分类（默认 + 自定义）
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0
);

-- commit_categories 表：commit 与 category 的多对多关系
CREATE TABLE commit_categories (
    commit_hash TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY(commit_hash, category_id),
    FOREIGN KEY (commit_hash) REFERENCES commits(hash) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- 创建索引以提高查询性能
CREATE INDEX idx_commits_project ON commits(project);
CREATE INDEX idx_commits_source ON commits(source);
CREATE INDEX idx_commits_change_id ON commits(change_id);
CREATE INDEX idx_commits_hash ON commits(hash);
CREATE INDEX idx_commit_categories_hash ON commit_categories(commit_hash);
CREATE INDEX idx_commit_categories_category ON commit_categories(category_id);

-- 插入默认分类
INSERT INTO categories (name, is_default) VALUES
    ('security_fix', 1),
    ('security_risk', 1),
    ('bugfix', 1),
    ('feature', 1),
    ('refactor', 1),
    ('behavior_change', 1),
    ('vendor_customization', 1),
    ('remove_upstream', 1),
    ('other', 1);
