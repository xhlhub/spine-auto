#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spine UI自动化脚本 - 主类文件
自动点击骨骼树节点并点击网格按钮

作者: Assistant
功能: 循环点击Spine右侧树节点 → 点击网格按钮 → 重复操作
"""

import pyautogui
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

# 导入各个模块
from config_manager import ConfigManager
from template_manager import TemplateManager
from window_manager import WindowManager
from click_manager import ClickManager
from automation import AutomationRunner

# 配置pyautogui
pyautogui.FAILSAFE = True  # 鼠标移到左上角停止
pyautogui.PAUSE = 0.2  # 操作间隔


@dataclass
class ClickTarget:
    """点击目标配置"""
    name: str
    template_path: str
    confidence: float = 0.8
    region: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)


class SpineAutomation:
    """Spine自动化操作类"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化自动化脚本
        
        Args:
            config_path: 配置文件路径
        """
        # 设置日志
        self.setup_logging()
        
        # 初始化各个管理器
        self.config_manager = ConfigManager(config_path)
        self.template_manager = TemplateManager(self.config_manager)
        self.window_manager = WindowManager(self.config_manager)
        self.click_manager = ClickManager(self.config_manager)
        self.automation_runner = AutomationRunner(
            self.config_manager, 
            self.template_manager, 
            self.window_manager, 
            self.click_manager
        )
        
        # 初始化点击目标
        self.click_targets: List[ClickTarget] = []
        self.grid_button: Optional[ClickTarget] = None
        
        self.logger.info("Spine自动化脚本初始化完成")
    
    def setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spine_automation.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_automation(self):
        """运行自动化流程"""
        self.automation_runner.run_automation()
    
    def setup_templates(self):
        """设置模板图片（需要用户手动截图）"""
        self.automation_runner.setup_templates()
    
    def test_click_functionality(self):
        """测试点击功能"""
        self.click_manager.test_click_functionality()
    
    
    def save_template_from_selection(self, name: str, region: Tuple[int, int, int, int]):
        """
        保存选定区域作为模板
        
        Args:
            name: 模板名称
            region: 选择区域 (x, y, width, height)
        """
        return self.template_manager.save_template_from_selection(name, region)