import React, { useState, useEffect, useRef } from 'react';
import { Card, Progress, Steps, Alert, Typography } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

const ProgressMonitor = ({ visible = false }) => {
  const [progress, setProgress] = useState(null);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!visible) {
      // 如果不可见，关闭连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    // 创建 SSE 连接
    const eventSource = new EventSource('/api/progress/stream');
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress(data);
      } catch (error) {
        console.error('Failed to parse progress data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
    };

    // 清理函数
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [visible]);

  if (!visible || !progress) {
    return null;
  }

  // 根据 stage 确定步骤状态
  const getStepStatus = (stageName) => {
    if (!progress) return 'wait';

    const stageOrder = {
      'idle': 0,
      'initializing': 0,
      'manifest_parsing': 1,
      'git_scanning': 2,
      'diff_analysis': 3,
      'completed': 4,
      'error': 4,
    };

    const currentStageIndex = stageOrder[progress.stage] || 0;
    const targetStageIndex = stageOrder[stageName] || 0;

    if (currentStageIndex > targetStageIndex) return 'finish';
    if (currentStageIndex === targetStageIndex) {
      if (progress.stage === 'error') return 'error';
      if (progress.stage === 'completed') return 'finish';
      return 'process';
    }
    return 'wait';
  };

  const steps = [
    {
      title: '初始化',
      stage: 'initializing',
    },
    {
      title: '解析 Manifest',
      stage: 'manifest_parsing',
    },
    {
      title: '扫描 Git Log',
      stage: 'git_scanning',
    },
    {
      title: '差异分析',
      stage: 'diff_analysis',
    },
  ];

  const getCurrentStep = () => {
    const stageMap = {
      'idle': 0,
      'initializing': 0,
      'manifest_parsing': 1,
      'git_scanning': 2,
      'diff_analysis': 3,
      'completed': 4,
      'error': 3,
    };
    return stageMap[progress.stage] || 0;
  };

  const getStatusColor = () => {
    if (progress.stage === 'error') return 'exception';
    if (progress.stage === 'completed') return 'success';
    return 'active';
  };

  return (
    <Card
      title="扫描进度"
      style={{ marginBottom: 20 }}
      extra={
        progress.stage === 'completed' ? (
          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
        ) : progress.stage === 'error' ? (
          <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
        ) : (
          <LoadingOutlined style={{ fontSize: 20 }} />
        )
      }
    >
      {/* 进度条 */}
      <Progress
        percent={progress.percentage}
        status={getStatusColor()}
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#87d068',
        }}
      />

      {/* 步骤显示 */}
      <Steps
        current={getCurrentStep()}
        status={progress.stage === 'error' ? 'error' : undefined}
        style={{ marginTop: 20, marginBottom: 20 }}
        items={steps.map(step => ({
          title: step.title,
          status: getStepStatus(step.stage),
        }))}
      />

      {/* 当前消息 */}
      {progress.message && (
        <Alert
          message={progress.stage_name || '处理中'}
          description={
            <div>
              <Text>{progress.message}</Text>
              {progress.current_item && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">当前项: {progress.current_item}</Text>
                </div>
              )}
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">
                  步骤: {progress.current_step} / {progress.total_steps}
                </Text>
              </div>
            </div>
          }
          type={
            progress.stage === 'error'
              ? 'error'
              : progress.stage === 'completed'
              ? 'success'
              : 'info'
          }
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  );
};

export default ProgressMonitor;
