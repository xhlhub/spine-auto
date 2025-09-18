#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口管理器模块

处理窗口查找、激活和权限检查
"""

import subprocess
import time
import logging
from typing import Optional, Tuple


class WindowManager:
    """窗口管理器类"""
    
    def __init__(self, config_manager):
        """
        初始化窗口管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def find_spine_window(self) -> Optional[Tuple[int, int, int, int]]:
        """
        查找Spine窗口
        
        Returns:
            窗口位置和大小 (x, y, width, height) 或 None
        """
        try:
            import pygetwindow as gw
            
            # 获取所有窗口标题
            all_titles = gw.getAllTitles()
            print(all_titles)
            window_title = self.config_manager.get("window_title", "Spine")
            spine_windows = [title for title in all_titles if window_title in title]
            
            if spine_windows:
                self.logger.info(f"找到Spine窗口: {spine_windows[0]}")
                
                # 自动检测应用程序名称
                if self.config_manager.get("app_name") is None:
                    detected_app_name = self.detect_app_name_from_title(spine_windows[0])
                    if detected_app_name:
                        self.config_manager.set("app_name", detected_app_name)
                        self.config_manager.save_config()  # 保存检测到的应用程序名称
                        self.logger.info(f"自动检测到应用程序名称: {detected_app_name}")
                
                # 注意：在macOS上，pygetwindow的功能有限
                # 我们暂时返回None，让脚本使用全屏模式
                # 这是因为macOS版本的pygetwindow无法获取窗口几何信息
                return None
            else:
                self.logger.warning(f"未找到包含'{window_title}'的窗口")
                return None
                
        except ImportError:
            self.logger.warning("pygetwindow未安装，使用全屏截图")
            return None
        except Exception as e:
            self.logger.error(f"查找窗口失败: {e}")
            return None
    
    def detect_app_name_from_title(self, window_title: str) -> Optional[str]:
        """
        从窗口标题检测应用程序名称
        
        Args:
            window_title: 窗口标题
            
        Returns:
            应用程序名称或None
        """
        try:
            # 尝试常见的应用程序名称模式
            possible_names = []
            
            # 从窗口标题中提取可能的应用程序名称
            title_parts = window_title.split()
            for part in title_parts:
                if "Spine" in part and part != "Spine":
                    possible_names.append(part)
            
            # 添加常见的Spine应用程序名称
            possible_names.extend([
                "Spine Trial",
                "Spine",
                "Spine Esoteric Software", 
                "Spine Pro"
            ])
            
            # 测试每个可能的名称
            for app_name in possible_names:
                try:
                    # 测试应用程序是否存在
                    test_script = f'''
                    tell application "{app_name}"
                        return name
                    end tell
                    '''
                    result = subprocess.run(['osascript', '-e', test_script], 
                                          capture_output=True, text=True, timeout=2)
                    
                    if result.returncode == 0:
                        self.logger.info(f"检测到有效的应用程序名称: {app_name}")
                        return app_name
                        
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue
            
            self.logger.warning("无法自动检测应用程序名称")
            return None
            
        except Exception as e:
            self.logger.error(f"检测应用程序名称失败: {e}")
            return None
    
    def check_accessibility_permissions(self):
        """检查辅助功能权限"""
        try:
            # 检查当前进程是否有辅助功能权限
            script = '''
            tell application "System Events"
                return enabled of UI elements
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error("缺少辅助功能权限！")
                self.logger.error("请在 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 中添加Python或终端应用程序")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查辅助功能权限失败: {e}")
            return False
    
    def activate_spine_window(self):
        """改进的激活Spine窗口方法"""
        try:
            # 获取应用程序名称
            app_name = self.config_manager.get("app_name", "Spine")
            self.logger.info(f"尝试激活{app_name}窗口...")
            
            # 首先尝试使用AppleScript激活
            activate_script = f'''
            try
                tell application "{app_name}"
                    activate
                    delay 0.5
                end tell
                
                tell application "System Events"
                    tell process "{app_name}"
                        set frontmost to true
                        delay 0.2
                    end tell
                end tell
                return "success"
            on error errMsg
                return "error: " & errMsg
            end try
            '''
            
            result = subprocess.run(['osascript', '-e', activate_script], 
                                   capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "success" in result.stdout:
                self.logger.info(f"{app_name}窗口已激活")
                time.sleep(0.8)  # 等待窗口完全激活
                return True
            else:
                self.logger.warning(f"AppleScript激活失败: {result.stderr if result.stderr else result.stdout}")
                
            # 方法2: 使用系统命令激活
            try:
                subprocess.run(['open', '-a', app_name], check=False, timeout=3)
                time.sleep(1.0)
                self.logger.info(f"使用系统命令激活{app_name}")
                return True
            except subprocess.TimeoutExpired:
                self.logger.warning("系统命令激活超时")
            
            return False
            
        except subprocess.TimeoutExpired:
            self.logger.error("激活窗口超时")
            return False
        except Exception as e:
            app_name = self.config_manager.get("app_name", "Spine")
            self.logger.warning(f"激活{app_name}窗口失败: {e}")
            return False
