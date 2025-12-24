"""
进度跟踪模块
用于跟踪和报告扫描/分析进度
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime


class ProgressTracker:
    """进度跟踪器（单例模式）"""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.current_progress: Dict = {
            "stage": "idle",  # idle, manifest_parsing, git_scanning, diff_analysis, completed, error
            "stage_name": "空闲",
            "current_step": 0,
            "total_steps": 0,
            "current_item": "",
            "message": "",
            "percentage": 0,
            "start_time": None,
            "end_time": None,
        }
        self.subscribers = []
        self._initialized = True

    def reset(self):
        """重置进度"""
        self.current_progress = {
            "stage": "idle",
            "stage_name": "空闲",
            "current_step": 0,
            "total_steps": 0,
            "current_item": "",
            "message": "",
            "percentage": 0,
            "start_time": None,
            "end_time": None,
        }

    def start(self, total_steps: int = 100):
        """开始跟踪"""
        self.current_progress = {
            "stage": "started",
            "stage_name": "开始扫描",
            "current_step": 0,
            "total_steps": total_steps,
            "current_item": "",
            "message": "正在初始化...",
            "percentage": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        }

    def update(
        self,
        stage: Optional[str] = None,
        stage_name: Optional[str] = None,
        current_step: Optional[int] = None,
        total_steps: Optional[int] = None,
        current_item: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """更新进度"""
        if stage is not None:
            self.current_progress["stage"] = stage
        if stage_name is not None:
            self.current_progress["stage_name"] = stage_name
        if current_step is not None:
            self.current_progress["current_step"] = current_step
        if total_steps is not None:
            self.current_progress["total_steps"] = total_steps
        if current_item is not None:
            self.current_progress["current_item"] = current_item
        if message is not None:
            self.current_progress["message"] = message

        # 计算百分比
        if self.current_progress["total_steps"] > 0:
            self.current_progress["percentage"] = int(
                (self.current_progress["current_step"] / self.current_progress["total_steps"]) * 100
            )
        else:
            self.current_progress["percentage"] = 0

    def complete(self, message: str = "扫描完成"):
        """标记为完成"""
        self.current_progress.update({
            "stage": "completed",
            "stage_name": "完成",
            "current_step": self.current_progress["total_steps"],
            "percentage": 100,
            "message": message,
            "end_time": datetime.now().isoformat(),
        })

    def error(self, message: str):
        """标记为错误"""
        self.current_progress.update({
            "stage": "error",
            "stage_name": "错误",
            "message": message,
            "end_time": datetime.now().isoformat(),
        })

    def get_progress(self) -> Dict:
        """获取当前进度"""
        return self.current_progress.copy()

    async def subscribe(self, queue: asyncio.Queue):
        """订阅进度更新"""
        self.subscribers.append(queue)

    async def unsubscribe(self, queue: asyncio.Queue):
        """取消订阅"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)

    async def notify_subscribers(self):
        """通知所有订阅者"""
        progress = self.get_progress()
        for queue in self.subscribers[:]:  # 复制列表以避免修改时出错
            try:
                await queue.put(progress)
            except:
                # 如果发送失败，移除订阅者
                self.subscribers.remove(queue)


# 全局实例
progress_tracker = ProgressTracker()
