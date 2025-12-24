import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Space } from 'antd';
import { scanRepos, reanalyzeDiff } from '../api/client';
import ProgressMonitor from './ProgressMonitor';

const ScanForm = ({ onScanComplete }) => {
  const [loading, setLoading] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [form] = Form.useForm();

  const handleScan = async (values) => {
    setLoading(true);
    setShowProgress(true);  // 显示进度监视器
    console.log('🚀 开始扫描仓库...', values);
    try {
      const result = await scanRepos(values.aospPath, values.vendorPath);
      message.success('扫描完成！');
      console.log('✅ 扫描结果:', result);
      if (onScanComplete) {
        onScanComplete(result);
      }
    } catch (error) {
      console.error('❌ 扫描失败:', error);
      message.error(`扫描失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
      console.log('🏁 扫描流程结束，3秒后隐藏进度监视器');
      // 延迟隐藏进度监视器，让用户看到完成状态
      setTimeout(() => {
        setShowProgress(false);
        console.log('👋 进度监视器已隐藏');
      }, 3000);
    }
  };

  const handleReanalyze = async () => {
    setReanalyzing(true);
    setShowProgress(true);  // 显示进度监视器
    console.log('🔄 开始重新分析差异...');
    try {
      const result = await reanalyzeDiff();
      message.success('差异分析完成！');
      console.log('✅ 分析结果:', result);
      if (onScanComplete) {
        onScanComplete(result);
      }
    } catch (error) {
      console.error('❌ 差异分析失败:', error);
      message.error(`差异分析失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setReanalyzing(false);
      console.log('🏁 分析流程结束，3秒后隐藏进度监视器');
      // 延迟隐藏进度监视器，让用户看到完成状态
      setTimeout(() => {
        setShowProgress(false);
        console.log('👋 进度监视器已隐藏');
      }, 3000);
    }
  };

  return (
    <>
      <ProgressMonitor visible={showProgress} />
      <Card title="扫描仓库" style={{ marginBottom: 20 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleScan}
          initialValues={{
            aospPath: '',
            vendorPath: '',
          }}
        >
          <Form.Item
            label="AOSP 仓库路径"
            name="aospPath"
            rules={[{ required: true, message: '请输入 AOSP 路径' }]}
            tooltip="包含 .repo/manifest.xml 的 AOSP 仓库根目录"
          >
            <Input placeholder="例如: /home/user/aosp" />
          </Form.Item>

          <Form.Item
            label="Vendor 仓库路径"
            name="vendorPath"
            rules={[{ required: true, message: '请输入 Vendor 路径' }]}
            tooltip="包含 .repo/manifest.xml 的 Vendor 仓库根目录"
          >
            <Input placeholder="例如: /home/user/vendor" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%' }} direction="vertical">
              <Button type="primary" htmlType="submit" loading={loading} block>
                {loading ? '扫描中...' : '开始扫描'}
              </Button>
              <Button
                type="default"
                onClick={handleReanalyze}
                loading={reanalyzing}
                block
              >
                {reanalyzing ? '分析中...' : '重新分析差异（断点续传）'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </>
  );
};

export default ScanForm;
