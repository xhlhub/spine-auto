#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器模块

处理配置文件的加载、保存和默认配置创建
"""

import json
import os
import logging
from typing import Dict, Any, List, Union


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"配置文件已加载: {self.config_path}")
            else:
                self.create_default_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        self.config = {
            # 窗口标题配置 - 使用数组模式
            "window_titles": ["Spine", "Spine Trial", "Spine Pro", "Spine Esoteric Software"],
            # 应用程序名称配置 - 使用数组模式
            "app_names": ["Spine", "Spine Trial", "Spine Pro", "Spine Esoteric Software"],
            "click_delay": 5.0,  # 点击间隔(秒)
            "operation_delay": 2.0,  # 操作完成等待时间(秒)
            "confidence_threshold": 0.8,  # 图像匹配置信度
            "max_retries": 3,  # 最大重试次数
            "debug_mode": True,  # 调试模式，显示详细信息
            "matching_algorithm": "enhanced",  # 匹配算法: "basic", "multi_method", "enhanced"
            "enable_multi_scale": True,  # 启用多尺度匹配
            "enable_preprocessing": True,  # 启用图像预处理
            "scale_range": [0.8, 1.2],  # 缩放范围
            "adaptive_confidence": True,  # 自适应置信度调整
            "tree_region": {  # 树区域 (x, y, width, height)
                "x": 0,
                "y": 0, 
                "width": 300,
                "height": 800
            },
            "button_region": {  # 按钮区域
                "x": 0,
                "y": 800,
                "width": 800,
                "height": 200
            },
        }
        self.save_config()
        self.logger.info("已创建默认配置文件")
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("配置文件已保存")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """批量更新配置项"""
        self.config.update(updates)
    
    def get_window_titles(self) -> List[str]:
        """
        获取所有可能的窗口标题
        
        Returns:
            窗口标题列表
        """
        window_titles = self.config.get("window_titles", ["Spine"])
        
        # 确保返回的是列表
        if not isinstance(window_titles, list):
            window_titles = ["Spine"]
        
        # 去重并过滤空值
        return list(filter(None, list(dict.fromkeys(window_titles))))
    
    def get_app_names(self) -> List[str]:
        """
        获取所有可能的应用程序名称
        
        Returns:
            应用程序名称列表
        """
        app_names = self.config.get("app_names", ["Spine", "Spine Trial", "Spine Pro", "Spine Esoteric Software"])
        
        # 确保返回的是列表
        if not isinstance(app_names, list):
            app_names = ["Spine", "Spine Trial", "Spine Pro", "Spine Esoteric Software"]
        
        # 去重并过滤空值
        return list(filter(None, list(dict.fromkeys(app_names))))
    
    def add_window_title(self, title: str):
        """
        添加新的窗口标题
        
        Args:
            title: 新的窗口标题
        """
        if "window_titles" not in self.config:
            self.config["window_titles"] = ["Spine"]
        
        if title and title not in self.config["window_titles"]:
            self.config["window_titles"].append(title)
            self.logger.info(f"添加新的窗口标题: {title}")
    
    def add_app_name(self, name: str):
        """
        添加新的应用程序名称
        
        Args:
            name: 新的应用程序名称
        """
        if "app_names" not in self.config:
            self.config["app_names"] = ["Spine"]
        
        if name and name not in self.config["app_names"]:
            self.config["app_names"].append(name)
            self.logger.info(f"添加新的应用程序名称: {name}")
