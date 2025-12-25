import React from 'react';
import { Table, Tag, Select, Typography, Space, Tooltip, Dropdown } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import { setCategories } from '../api/client';

const { Text, Link } = Typography;

const SOURCE_COLORS = {
  common: 'blue',
  aosp_only: 'green',
  vendor_only: 'orange',
};

const CommitTable = ({ commits, categories, onCategoriesChange }) => {
  const handleCategoryChange = async (commitHash, categoryIds) => {
    try {
      await setCategories(commitHash, categoryIds);
      if (onCategoriesChange) {
        onCategoriesChange();
      }
    } catch (error) {
      console.error('设置分类失败:', error);
    }
  };

  const columns = [
    {
      title: 'Project',
      dataIndex: 'project',
      key: 'project',
      width: 180,
      ellipsis: true,
    },
    {
      title: 'Hash',
      dataIndex: 'hash',
      key: 'hash',
      width: 140,
      render: (hash, record) => {
        const hasRelated = record.related_commits && record.related_commits.length > 0;

        if (hasRelated) {
          // 有相关 commits（两边都有）
          const items = [
            {
              key: 'current',
              label: (
                <div>
                  <div style={{ fontSize: '12px', color: '#999' }}>当前版本</div>
                  <div>
                    <Text strong>{record.project}</Text>
                  </div>
                  <Link href={record.url} target="_blank">
                    {hash.substring(0, 12)}
                  </Link>
                </div>
              ),
            },
            { type: 'divider' },
            ...record.related_commits.map((related, idx) => ({
              key: `related-${idx}`,
              label: (
                <div>
                  <div style={{ fontSize: '12px', color: '#999' }}>另一边版本</div>
                  <div>
                    <Text strong>{related.project}</Text>
                  </div>
                  <Link href={related.url} target="_blank">
                    {related.hash.substring(0, 12)}
                  </Link>
                </div>
              ),
            })),
          ];

          return (
            <Dropdown menu={{ items }} trigger={['click']}>
              <Space style={{ cursor: 'pointer' }}>
                <Link href={record.url} target="_blank">
                  {hash.substring(0, 8)}
                </Link>
                <Tooltip title="此 Change-Id 在两边都有，点击查看">
                  <Tag color="blue" style={{ margin: 0, fontSize: '11px' }}>
                    +{record.related_commits.length}
                  </Tag>
                </Tooltip>
              </Space>
            </Dropdown>
          );
        }

        // 只有一边
        return record.url ? (
          <Link href={record.url} target="_blank">
            {hash.substring(0, 8)}
          </Link>
        ) : (
          <Text>{hash.substring(0, 8)}</Text>
        );
      },
    },
    {
      title: 'Author',
      dataIndex: 'author',
      key: 'author',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      width: 110,
      render: (date) => date.substring(0, 10), // 只显示日期部分
    },
    {
      title: 'Commit Info',
      key: 'commit_info',
      render: (_, record) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Text strong>{record.subject}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            Change-Id: {record.change_id || '(无)'}
          </Text>
          <pre style={{
            whiteSpace: 'pre-wrap',
            margin: 0,
            fontSize: '12px',
            color: '#666',
            fontFamily: 'inherit',
            maxHeight: '120px',
            overflow: 'auto'
          }}>
            {record.message || '(无详细信息)'}
          </pre>
        </Space>
      ),
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      width: 120,
      render: (source) => (
        <Tag color={SOURCE_COLORS[source] || 'default'}>
          {source}
        </Tag>
      ),
    },
    {
      title: 'Categories',
      key: 'categories',
      width: 200,
      render: (_, record) => {
        const selectedIds = record.categories.map((c) => c.id);
        return (
          <Select
            mode="multiple"
            style={{ width: '100%' }}
            placeholder="选择分类"
            value={selectedIds}
            onChange={(value) => handleCategoryChange(record.hash, value)}
            options={categories.map((cat) => ({
              label: cat.name,
              value: cat.id,
            }))}
          />
        );
      },
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={commits}
      rowKey="hash"
      pagination={{
        pageSize: 20,
        pageSizeOptions: ['10', '20', '50', '100'],
        showSizeChanger: true,
        showTotal: (total) => `共 ${total} 条`,
      }}
      scroll={{ x: 1200 }}
    />
  );
};

export default CommitTable;
