import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { scanRepos } from '../api/client';

const ScanForm = ({ onScanComplete }) => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleScan = async (values) => {
    setLoading(true);
    try {
      const result = await scanRepos(values.aospPath, values.vendorPath);
      message.success('扫描完成！');
      console.log('扫描结果:', result);
      if (onScanComplete) {
        onScanComplete(result);
      }
    } catch (error) {
      console.error('扫描失败:', error);
      message.error(`扫描失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="扫描仓库" style={{ marginBottom: 20 }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleScan}
        initialValues={{
          aospPath: '/path/to/aosp',
          vendorPath: '/path/to/vendor',
        }}
      >
        <Form.Item
          label="AOSP 仓库路径"
          name="aospPath"
          rules={[{ required: true, message: '请输入 AOSP 路径' }]}
        >
          <Input placeholder="/path/to/aosp" />
        </Form.Item>

        <Form.Item
          label="Vendor 仓库路径"
          name="vendorPath"
          rules={[{ required: true, message: '请输入 Vendor 路径' }]}
        >
          <Input placeholder="/path/to/vendor" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            {loading ? '扫描中...' : '开始扫描'}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ScanForm;
