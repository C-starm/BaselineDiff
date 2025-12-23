import React from 'react';
import { Table, Tag, Select, Typography, Space } from 'antd';
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
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Hash',
      dataIndex: 'hash',
      key: 'hash',
      width: 120,
      render: (hash, record) => (
        record.url ? (
          <Link href={record.url} target="_blank">
            {hash.substring(0, 8)}
          </Link>
        ) : (
          <Text>{hash.substring(0, 8)}</Text>
        )
      ),
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
      width: 180,
    },
    {
      title: 'Subject',
      dataIndex: 'subject',
      key: 'subject',
      ellipsis: true,
      width: 300,
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
      width: 250,
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
        pageSize: 50,
        showSizeChanger: true,
        showTotal: (total) => `共 ${total} 条`,
      }}
      expandable={{
        expandedRowRender: (record) => (
          <div style={{ padding: 16, background: '#f5f5f5' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Change-Id:</Text> {record.change_id || '(无)'}
              </div>
              <div>
                <Text strong>Message:</Text>
                <pre style={{ whiteSpace: 'pre-wrap', marginTop: 8 }}>
                  {record.message || '(无)'}
                </pre>
              </div>
            </Space>
          </div>
        ),
      }}
      scroll={{ x: 1500 }}
    />
  );
};

export default CommitTable;
