import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Statistic, Input, Button, Space, message, Spin, Empty } from 'antd';
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
    dateRange: null,
  });
  const [customCategoryName, setCustomCategoryName] = useState('');
  const [loading, setLoading] = useState(false);  // 加载状态

  // 加载 commits（支持筛选）
  const loadCommits = async (filterParams = {}) => {
    setLoading(true);
    try {
      // 构建 API 参数
      const params = {
        limit: 1000,
        offset: 0,
        ...filterParams
      };

      // 如果有日期范围，添加 date_from 和 date_to
      if (filterParams.dateRange && filterParams.dateRange.length === 2) {
        params.date_from = filterParams.dateRange[0];
        params.date_to = filterParams.dateRange[1];
        delete params.dateRange;
      }

      const result = await getCommits(params);
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
    } finally {
      setLoading(false);
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

  // 应用筛选（使用后端 API）
  useEffect(() => {
    // 提取后端支持的筛选参数
    const backendFilters = {
      source: filters.source,
      project: filters.project,
      author: filters.author,
      search: filters.search,
      dateRange: filters.dateRange,
    };

    // 调用后端 API 获取筛选后的数据
    loadCommits(backendFilters);
  }, [
    filters.source,
    filters.project,
    filters.author,
    filters.search,
    filters.dateRange,
  ]);

  // 对 categoryIds 进行客户端筛选（后端暂不支持）
  useEffect(() => {
    if (filters.categoryIds && filters.categoryIds.length > 0) {
      const filtered = commits.filter((c) =>
        filters.categoryIds.some((catId) =>
          c.categories.some((cc) => cc.id === catId)
        )
      );
      setFilteredCommits(filtered);
    } else {
      setFilteredCommits(commits);
    }
  }, [filters.categoryIds, commits]);

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
      dateRange: null,
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
                <Button onClick={() => loadCommits()} loading={loading}>
                  刷新
                </Button>
              }
            >
              {loading ? (
                <div style={{ textAlign: 'center', padding: '50px 0' }}>
                  <Spin size="large" tip="加载中，请稍候..." />
                </div>
              ) : filteredCommits.length === 0 ? (
                <Empty
                  description={
                    <span>
                      {totalCommits === 0
                        ? '暂无数据，请先扫描仓库'
                        : '没有符合筛选条件的 commits'}
                    </span>
                  }
                  style={{ padding: '50px 0' }}
                />
              ) : (
                <CommitTable
                  commits={filteredCommits}
                  categories={categories}
                  onCategoriesChange={loadCommits}
                />
              )}
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
}

export default App;
