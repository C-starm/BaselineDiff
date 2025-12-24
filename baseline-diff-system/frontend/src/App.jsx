import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Statistic, Input, Button, Space, message } from 'antd';
import ScanForm from './components/ScanForm';
import FilterPanel from './components/FilterPanel';
import CommitTable from './components/CommitTable';
import { getCommits, getCategories, addCategory, getStats, getMetadata } from './api/client';

const { Header, Content } = Layout;

function App() {
  const [commits, setCommits] = useState([]);
  const [filteredCommits, setFilteredCommits] = useState([]);
  const [categories, setCategories] = useState([]);
  const [stats, setStats] = useState({});
  const [totalCommits, setTotalCommits] = useState(0);  // 总记录数
  const [displayedCount, setDisplayedCount] = useState(0);  // 显示的记录数
  const [projects, setProjects] = useState([]);  // 所有项目列表
  const [authors, setAuthors] = useState([]);  // 所有作者列表
  const [filters, setFilters] = useState({
    source: undefined,
    project: undefined,
    author: undefined,
    categoryIds: [],
    search: '',
  });
  const [customCategoryName, setCustomCategoryName] = useState('');

  // 加载 commits
  const loadCommits = async () => {
    try {
      const result = await getCommits();
      setCommits(result.commits);
      setFilteredCommits(result.commits);
      setTotalCommits(result.total || 0);
      setDisplayedCount(result.count || result.commits.length);

      // 如果数据量很大，显示警告
      if (result.total > 10000) {
        message.warning(
          `数据量较大（共 ${result.total.toLocaleString()} 条），当前仅显示前 ${result.count.toLocaleString()} 条记录。建议使用筛选功能。`,
          10
        );
      }
    } catch (error) {
      console.error('加载 commits 失败:', error);
      message.error('加载 commits 失败');
    }
  };

  // 加载 categories
  const loadCategories = async () => {
    try {
      const result = await getCategories();
      setCategories(result.categories);
    } catch (error) {
      console.error('加载 categories 失败:', error);
    }
  };

  // 加载统计信息
  const loadStats = async () => {
    try {
      const result = await getStats();
      setStats(result.stats);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  // 加载元数据（项目列表、作者列表）
  const loadMetadata = async () => {
    try {
      const result = await getMetadata();
      setProjects(result.projects || []);
      setAuthors(result.authors || []);
    } catch (error) {
      console.error('加载元数据失败:', error);
    }
  };

  // 初始加载
  useEffect(() => {
    loadCategories();
    loadCommits();
    loadStats();
    loadMetadata();
  }, []);

  // 应用筛选
  useEffect(() => {
    let filtered = [...commits];

    if (filters.source) {
      filtered = filtered.filter((c) => c.source === filters.source);
    }

    if (filters.project) {
      filtered = filtered.filter((c) => c.project === filters.project);
    }

    if (filters.author) {
      filtered = filtered.filter((c) => c.author.includes(filters.author));
    }

    if (filters.categoryIds && filters.categoryIds.length > 0) {
      filtered = filtered.filter((c) =>
        filters.categoryIds.some((catId) =>
          c.categories.some((cc) => cc.id === catId)
        )
      );
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(
        (c) =>
          c.subject.toLowerCase().includes(searchLower) ||
          c.message.toLowerCase().includes(searchLower)
      );
    }

    setFilteredCommits(filtered);
  }, [filters, commits]);

  // 扫描完成回调
  const handleScanComplete = () => {
    loadCommits();
    loadStats();
    loadMetadata();
  };

  // 重置筛选
  const handleResetFilters = () => {
    setFilters({
      source: undefined,
      project: undefined,
      author: undefined,
      categoryIds: [],
      search: '',
    });
  };

  // 添加自定义分类
  const handleAddCategory = async () => {
    if (!customCategoryName.trim()) {
      message.warning('请输入分类名称');
      return;
    }

    try {
      await addCategory(customCategoryName);
      message.success('分类已添加');
      setCustomCategoryName('');
      loadCategories();
    } catch (error) {
      console.error('添加分类失败:', error);
      message.error('添加分类失败');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', color: 'white', fontSize: 24, fontWeight: 'bold' }}>
        Baseline Diff System
      </Header>

      <Content style={{ padding: '20px' }}>
        <Row gutter={20}>
          {/* 左侧：扫描表单 + 筛选器 */}
          <Col xs={24} lg={6}>
            <ScanForm onScanComplete={handleScanComplete} />

            <Card title="统计信息" style={{ marginBottom: 20 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic title="总 Commits" value={stats.total_commits || 0} />
                <Statistic title="Common" value={stats.common || 0} />
                <Statistic title="AOSP Only" value={stats.aosp_only || 0} />
                <Statistic title="Vendor Only" value={stats.vendor_only || 0} />
              </Space>
            </Card>

            <FilterPanel
              filters={filters}
              onFilterChange={setFilters}
              categories={categories}
              projects={projects}
              authors={authors}
              onReset={handleResetFilters}
            />

            <Card title="自定义分类" style={{ marginTop: 20 }}>
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  placeholder="分类名称"
                  value={customCategoryName}
                  onChange={(e) => setCustomCategoryName(e.target.value)}
                  onPressEnter={handleAddCategory}
                />
                <Button type="primary" onClick={handleAddCategory}>
                  添加
                </Button>
              </Space.Compact>
            </Card>
          </Col>

          {/* 右侧：Commit 列表 */}
          <Col xs={24} lg={18}>
            <Card
              title={
                totalCommits > displayedCount
                  ? `Commits 列表 (显示 ${filteredCommits.length.toLocaleString()} / 已加载 ${commits.length.toLocaleString()} / 总共 ${totalCommits.toLocaleString()})`
                  : `Commits 列表 (${filteredCommits.length.toLocaleString()} / ${commits.length.toLocaleString()})`
              }
              extra={
                <Button onClick={loadCommits}>
                  刷新
                </Button>
              }
            >
              <CommitTable
                commits={filteredCommits}
                categories={categories}
                onCategoriesChange={loadCommits}
              />
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
}

export default App;
