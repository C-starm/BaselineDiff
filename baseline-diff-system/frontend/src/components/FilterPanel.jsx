import React from 'react';
import { Card, Select, Input, Button, Space } from 'antd';

const { Option } = Select;

const FilterPanel = ({
  filters,
  onFilterChange,
  categories,
  projects,
  authors,
  onReset
}) => {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <Card title="筛选条件" style={{ marginBottom: 20 }}>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <div style={{ marginBottom: 8, fontWeight: 'bold' }}>来源 (Source)</div>
          <Select
            style={{ width: '100%' }}
            placeholder="选择来源"
            allowClear
            value={filters.source}
            onChange={(value) => handleChange('source', value)}
          >
            <Option value="common">Common (两者都有)</Option>
            <Option value="aosp_only">AOSP Only</Option>
            <Option value="vendor_only">Vendor Only</Option>
          </Select>
        </div>

        <div>
          <div style={{ marginBottom: 8, fontWeight: 'bold' }}>项目 (Project)</div>
          <Select
            style={{ width: '100%' }}
            placeholder="选择项目"
            allowClear
            showSearch
            value={filters.project}
            onChange={(value) => handleChange('project', value)}
          >
            {projects.map((p) => (
              <Option key={p} value={p}>
                {p}
              </Option>
            ))}
          </Select>
        </div>

        <div>
          <div style={{ marginBottom: 8, fontWeight: 'bold' }}>作者 (Author)</div>
          <Select
            style={{ width: '100%' }}
            placeholder="选择作者"
            allowClear
            showSearch
            value={filters.author}
            onChange={(value) => handleChange('author', value)}
          >
            {authors.map((a) => (
              <Option key={a} value={a}>
                {a}
              </Option>
            ))}
          </Select>
        </div>

        <div>
          <div style={{ marginBottom: 8, fontWeight: 'bold' }}>分类 (Category)</div>
          <Select
            style={{ width: '100%' }}
            placeholder="选择分类"
            allowClear
            mode="multiple"
            value={filters.categoryIds}
            onChange={(value) => handleChange('categoryIds', value)}
          >
            {categories.map((cat) => (
              <Option key={cat.id} value={cat.id}>
                {cat.name}
              </Option>
            ))}
          </Select>
        </div>

        <div>
          <div style={{ marginBottom: 8, fontWeight: 'bold' }}>关键词搜索</div>
          <Input
            placeholder="搜索 subject/message"
            allowClear
            value={filters.search}
            onChange={(e) => handleChange('search', e.target.value)}
          />
        </div>

        <Button onClick={onReset} block>
          重置筛选
        </Button>
      </Space>
    </Card>
  );
};

export default FilterPanel;
