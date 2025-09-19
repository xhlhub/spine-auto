#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口管理器模块

处理窗口查找、激活和权限检查
"""

import subprocess
import time
import logging
import platform
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
        查找Spine窗口（跨平台，支持多个标题匹配）
        
        Returns:
            窗口位置和大小 (x, y, width, height) 或 None
        """
        try:
            import pygetwindow as gw
            
            # 获取所有窗口标题
            all_titles = gw.getAllTitles()
            self.logger.debug(f"所有窗口: {all_titles}")
            
            # 获取配置的窗口标题列表
            window_titles = self.config_manager.get_window_titles()
            self.logger.info(f"查找窗口标题: {window_titles}")
            
            # 尝试匹配每个可能的标题
            matched_window = None
            matched_title = None
            
            for window_title in window_titles:
                spine_windows = [title for title in all_titles if window_title.lower() in title.lower()]
                if spine_windows:
                    matched_window = spine_windows[0]
                    matched_title = window_title
                    self.logger.info(f"找到Spine窗口: '{matched_window}' (匹配标题: '{matched_title}')")
                    break
            
            if matched_window:
                # 自动检测和保存应用程序名称
                detected_app_name = self.detect_app_name_from_title(matched_window)
                if detected_app_name:
                    # 添加到配置中
                    self.config_manager.add_app_name(detected_app_name)
                    self.config_manager.add_window_title(matched_title)
                    self.config_manager.save_config()
                    self.logger.info(f"自动检测并保存应用程序名称: {detected_app_name}")
                
                # Windows上可以获取窗口几何信息
                if platform.system() == "Windows":
                    try:
                        window = gw.getWindowsWithTitle(matched_window)[0]
                        return (window.left, window.top, window.width, window.height)
                    except Exception as e:
                        self.logger.warning(f"获取Windows窗口几何信息失败: {e}")
                        return None
                else:
                    # macOS上pygetwindow功能有限，使用全屏模式
                    return None
            else:
                self.logger.warning(f"未找到匹配以下标题的窗口: {window_titles}")
                return None
                
        except ImportError:
            self.logger.warning("pygetwindow未安装，使用全屏截图")
            return None
        except Exception as e:
            self.logger.error(f"查找窗口失败: {e}")
            return None
    
    def detect_app_name_from_title(self, window_title: str) -> Optional[str]:
        """
        从窗口标题检测应用程序名称（跨平台）
        
        Args:
            window_title: 窗口标题
            
        Returns:
            应用程序名称或None
        """
        try:
            # 获取配置的应用名称列表
            possible_names = self.config_manager.get_app_names()
            
            # 从窗口标题中提取额外的可能名称
            title_parts = window_title.split()
            for part in title_parts:
                if "Spine" in part and part not in possible_names:
                    possible_names.append(part)
            
            # 根据平台选择检测方法
            if platform.system() == "Darwin":
                return self._detect_app_name_macos(possible_names)
            elif platform.system() == "Windows":
                return self._detect_app_name_windows(possible_names, window_title)
            else:
                return self._detect_app_name_linux(possible_names, window_title)
            
        except Exception as e:
            self.logger.error(f"检测应用程序名称失败: {e}")
            return None
    
    def _detect_app_name_macos(self, possible_names: list) -> Optional[str]:
        """在macOS上检测应用程序名称"""
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
                    self.logger.info(f"检测到有效的macOS应用程序名称: {app_name}")
                    return app_name
                    
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        return None
    
    def _detect_app_name_windows(self, possible_names: list, window_title: str) -> Optional[str]:
        """在Windows上检测应用程序名称"""
        try:
            import pygetwindow as gw
            
            # 直接从窗口标题推断应用名称
            for app_name in possible_names:
                if app_name.lower() in window_title.lower():
                    self.logger.info(f"检测到Windows应用程序名称: {app_name}")
                    return app_name
            
            # 如果没有直接匹配，返回第一个可能的名称
            if possible_names:
                return possible_names[0]
                
        except Exception as e:
            self.logger.debug(f"Windows应用名称检测失败: {e}")
        
        return None
    
    def _detect_app_name_linux(self, possible_names: list, window_title: str) -> Optional[str]:
        """在Linux上检测应用程序名称"""
        # Linux上的检测逻辑与Windows类似
        for app_name in possible_names:
            if app_name.lower() in window_title.lower():
                self.logger.info(f"检测到Linux应用程序名称: {app_name}")
                return app_name
        
        if possible_names:
            return possible_names[0]
        
        return None
    
    def check_accessibility_permissions(self):
        """检查辅助功能权限（跨平台）"""
        try:
            if platform.system() == "Darwin":
                # macOS权限检查
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
            
            elif platform.system() == "Windows":
                # Windows权限检查
                try:
                    import win32api
                    import win32con
                    import win32gui
                    
                    # 检查是否以管理员权限运行
                    import ctypes
                    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                    
                    if not is_admin:
                        self.logger.warning("建议以管理员权限运行以获得最佳兼容性")
                    
                    # 基本的Windows API测试
                    win32gui.GetForegroundWindow()
                    self.logger.info("✅ Windows API权限检查通过")
                    return True
                    
                except ImportError:
                    self.logger.warning("pywin32未安装，跳过Windows权限检查")
                    return True
                except Exception as e:
                    self.logger.error(f"Windows权限检查失败: {e}")
                    return False
            
            else:
                # 其他系统（Linux等）
                self.logger.info("跳过权限检查（非macOS/Windows系统）")
                return True
            
        except Exception as e:
            self.logger.error(f"检查辅助功能权限失败: {e}")
            return False
    
    def activate_spine_window(self):
        """跨平台的激活Spine窗口方法"""
        try:
            app_name = self.config_manager.get("app_name", "Spine")
            self.logger.info(f"尝试激活{app_name}窗口...")
            
            if platform.system() == "Darwin":
                return self._activate_window_macos(app_name)
            elif platform.system() == "Windows":
                return self._activate_window_windows(app_name)
            else:
                return self._activate_window_linux(app_name)
                
        except Exception as e:
            self.logger.warning(f"激活{app_name}窗口失败: {e}")
            return False
    
    def _activate_window_macos(self, app_name: str) -> bool:
        """macOS窗口激活（支持多个应用名称）"""
        app_names = [app_name] if isinstance(app_name, str) else self.config_manager.get_app_names()
        
        for name in app_names:
            try:
                # 尝试使用AppleScript激活
                activate_script = f'''
                try
                    tell application "{name}"
                        activate
                        delay 0.5
                    end tell
                    
                    tell application "System Events"
                        tell process "{name}"
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
                    self.logger.info(f"{name}窗口已激活")
                    time.sleep(0.8)  # 等待窗口完全激活
                    return True
                else:
                    self.logger.debug(f"AppleScript激活{name}失败: {result.stderr if result.stderr else result.stdout}")
                    
            except subprocess.TimeoutExpired:
                self.logger.debug(f"激活{name}超时")
                continue
            except Exception as e:
                self.logger.debug(f"激活{name}失败: {e}")
                continue
        
        # 如果所有名称都失败，尝试系统命令
        for name in app_names:
            try:
                subprocess.run(['open', '-a', name], check=False, timeout=3)
                time.sleep(1.0)
                self.logger.info(f"使用系统命令激活{name}")
                return True
            except subprocess.TimeoutExpired:
                self.logger.debug(f"系统命令激活{name}超时")
                continue
            except Exception as e:
                self.logger.debug(f"系统命令激活{name}失败: {e}")
                continue
        
        return False
    
    def _activate_window_windows(self, app_name: str) -> bool:
        """Windows窗口激活（支持多个标题匹配）"""
        try:
            import pygetwindow as gw
            
            # 获取所有可能的窗口标题
            window_titles = self.config_manager.get_window_titles()
            
            # 方法1: 使用pygetwindow查找并激活窗口
            for window_title in window_titles:
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    window = windows[0]
                    try:
                        # 激活窗口
                        if window.isMinimized:
                            window.restore()
                        window.activate()
                        self.logger.info(f"通过pygetwindow激活窗口成功: {window_title}")
                        time.sleep(0.5)
                        return True
                    except Exception as e:
                        self.logger.debug(f"pygetwindow激活{window_title}失败: {e}")
                        continue
            
            # 方法2: 使用Windows API
            try:
                import win32gui
                import win32con
                
                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        for title in window_titles:
                            if title.lower() in window_text.lower():
                                windows.append((hwnd, window_text, title))
                                return True
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)
                
                if windows:
                    hwnd, window_text, matched_title = windows[0]
                    # 激活窗口
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    self.logger.info(f"通过Windows API激活窗口成功: {window_text} (匹配: {matched_title})")
                    time.sleep(0.5)
                    return True
                    
            except ImportError:
                self.logger.warning("pywin32未安装，无法使用Windows API")
            except Exception as e:
                self.logger.warning(f"Windows API激活失败: {e}")
            
            # 方法3: 使用系统命令启动应用
            app_names = self.config_manager.get_app_names()
            for name in app_names:
                try:
                    import os
                    # 尝试启动应用程序
                    os.system(f'start "" "{name}"')
                    time.sleep(2.0)
                    self.logger.info(f"使用系统命令启动{name}")
                    return True
                except Exception as e:
                    self.logger.debug(f"系统命令启动{name}失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Windows窗口激活失败: {e}")
            return False
    
    def _activate_window_linux(self, app_name: str) -> bool:
        """Linux窗口激活（支持多个标题匹配）"""
        try:
            import pygetwindow as gw
            
            window_titles = self.config_manager.get_window_titles()
            
            # 尝试pygetwindow
            for window_title in window_titles:
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    window = windows[0]
                    try:
                        window.activate()
                        self.logger.info(f"Linux窗口激活成功: {window_title}")
                        time.sleep(0.5)
                        return True
                    except Exception as e:
                        self.logger.debug(f"Linux窗口激活{window_title}失败: {e}")
                        continue
            
            # 尝试使用xdotool（如果可用）
            for window_title in window_titles:
                try:
                    subprocess.run(['xdotool', 'search', '--name', window_title, 'windowactivate'], 
                                  check=True, timeout=3)
                    self.logger.info(f"使用xdotool激活窗口成功: {window_title}")
                    time.sleep(0.5)
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.logger.debug(f"xdotool激活{window_title}失败")
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Linux窗口激活失败: {e}")
            return False
