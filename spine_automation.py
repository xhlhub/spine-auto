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
        # 确保logs目录存在
        from pathlib import Path
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # 配置日志处理器
        log_file = logs_dir / "spine_automation.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_file), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"日志保存到: {log_file}")
    
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
    
    def open_logs_folder(self):
        """打开日志文件夹，查看运行日志和截图"""
        import os
        import platform
        from pathlib import Path
        
        logs_dir = Path("logs")
        
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
            self.logger.info("已创建logs目录")
        
        try:
            if platform.system() == "Windows":
                os.startfile(str(logs_dir))
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{logs_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{logs_dir}'")
            
            self.logger.info(f"已打开日志目录: {logs_dir.absolute()}")
            print(f"\n📁 日志目录已打开: {logs_dir.absolute()}")
            print("📄 这里包含：")
            print("   - spine_automation.log (运行日志)")
            print("   - screenshot_*.png (调试截图)")
            print("   - debug_*.png (验证截图)")
            
        except Exception as e:
            self.logger.error(f"无法打开日志目录: {e}")
            print(f"❌ 无法打开日志目录: {e}")
            print(f"请手动打开目录: {logs_dir.absolute()}")
    
    def show_log_summary(self):
        """显示日志摘要信息"""
        from pathlib import Path
        import os
        
        logs_dir = Path("logs")
        
        if not logs_dir.exists():
            print("❌ logs目录不存在")
            return
        
        print("\n📊 日志文件夹摘要:")
        print(f"📍 位置: {logs_dir.absolute()}")
        
        # 统计文件数量
        log_files = list(logs_dir.glob("*.log"))
        screenshot_files = list(logs_dir.glob("*.png"))
        
        print(f"📄 日志文件: {len(log_files)} 个")
        for log_file in log_files:
            size = os.path.getsize(log_file) / 1024  # KB
            print(f"   - {log_file.name} ({size:.1f} KB)")
        
        print(f"📸 截图文件: {len(screenshot_files)} 个")
        if screenshot_files:
            total_size = sum(os.path.getsize(f) for f in screenshot_files) / (1024 * 1024)  # MB
            print(f"   - 总大小: {total_size:.1f} MB")
            # 显示最新的几个截图
            screenshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            print("   - 最新截图:")
            for i, screenshot in enumerate(screenshot_files[:5]):
                print(f"     • {screenshot.name}")
        
        print(f"\n💡 使用 automation.open_logs_folder() 打开文件夹查看详细内容")
    
    def view_latest_log(self, lines: int = 50):
        """查看最新的日志内容"""
        from pathlib import Path
        
        log_file = Path("logs") / "spine_automation.log"
        
        if not log_file.exists():
            print("❌ 日志文件不存在")
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                latest_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
                print(f"\n📋 最新 {len(latest_lines)} 行日志:")
                print("=" * 60)
                for line in latest_lines:
                    print(line.rstrip())
                print("=" * 60)
                
        except Exception as e:
            print(f"❌ 读取日志文件失败: {e}")
            self.logger.error(f"读取日志文件失败: {e}")