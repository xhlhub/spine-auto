#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
点击管理器模块

处理点击操作、坐标转换和DPR检测
"""

import pyautogui
import time
import logging
import subprocess
import platform
import json
from typing import Tuple, Optional, List


class ClickManager:
    """点击管理器类"""
    
    def __init__(self, config_manager):
        """
        初始化点击管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # 检测和设置DPR
        if "manual_dpr" in self.config_manager.config and self.config_manager.config["manual_dpr"]:
            self.dpr = self.config_manager.config["manual_dpr"]
            self.logger.info(f"使用手动设置的DPR: {self.dpr}")
        else:
            self.dpr = self.detect_display_scaling()
            self.logger.info(f"自动检测到显示器缩放比例: {self.dpr}")
    
    def detect_display_scaling(self) -> float:
        """
        检测显示器的缩放比例（DPR）- 跨平台支持
        
        Returns:
            显示器缩放比例
        """
        try:
            system = platform.system()
            
            if system == "Darwin":
                return self._detect_macos_dpr()
            elif system == "Windows":
                return self._detect_windows_dpr()
            else:
                self.logger.info(f"系统 {system} 使用默认缩放比例1.0")
                return 1.0
                
        except Exception as e:
            self.logger.error(f"检测显示器缩放比例失败: {e}")
            return 1.0
    
    def _detect_macos_dpr(self) -> float:
        """
        检测macOS显示器的缩放比例
        
        Returns:
            显示器缩放比例
        """
        try:
            self.logger.info("开始检测macOS显示器DPR...")
            
            # 方法1: 使用Cocoa框架直接获取backingScaleFactor (最准确的方法)
            try:
                self.logger.debug("尝试方法1: Cocoa NSScreen.backingScaleFactor")
                cocoa_script = '''
import Cocoa
try:
    screen = Cocoa.NSScreen.mainScreen()
    if screen:
        scale_factor = screen.backingScaleFactor()
        print(f"SCALE_FACTOR:{scale_factor}")
    else:
        print("SCALE_FACTOR:1.0")
except Exception as e:
    print(f"ERROR:{e}")
'''
                
                result = subprocess.run(['python3', '-c', cocoa_script], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.startswith('SCALE_FACTOR:'):
                            scale_factor = float(line.split(':')[1])
                            self.logger.info(f"方法1: 通过Cocoa NSScreen检测到DPR: {scale_factor}")
                            return scale_factor
                            
            except Exception as e:
                self.logger.debug(f"方法1失败: {e}")
            
            # 方法2: 使用system_profiler获取显示器信息
            try:
                self.logger.debug("尝试方法2: system_profiler")
                result = subprocess.run([
                    'system_profiler', 'SPDisplaysDataType', '-json'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    display_data = json.loads(result.stdout)
                    
                    # 查找主显示器的分辨率信息
                    displays = display_data.get('SPDisplaysDataType', [])
                    for display_group in displays:
                        displays_list = display_group.get('spdisplays_ndrvs', [])
                        for display in displays_list:
                            # 检查是否为主显示器
                            if display.get('spdisplays_main', 'spdisplays_no') == 'spdisplays_yes':
                                resolution = display.get('spdisplays_resolution', '')
                                self.logger.debug(f"主显示器分辨率字符串: {resolution}")
                                
                                if 'Retina' in resolution or '@ 2x' in resolution:
                                    self.logger.info("方法2: 检测到Retina显示器，设置DPR为2.0")
                                    return 2.0
                                elif '@ 3x' in resolution:
                                    self.logger.info("方法2: 检测到3x显示器，设置DPR为3.0")
                                    return 3.0
                                
            except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as e:
                self.logger.debug(f"方法2失败: {e}")
            
            # 方法3: 使用pyautogui和tkinter比较屏幕尺寸
            try:
                self.logger.debug("尝试方法3: pyautogui + tkinter尺寸比较")
                import tkinter as tk
                
                # 获取pyautogui的屏幕尺寸 (通常是物理像素)
                screen_width, screen_height = pyautogui.size()
                self.logger.debug(f"pyautogui屏幕尺寸: {screen_width}x{screen_height}")
                
                # 创建临时窗口获取逻辑尺寸
                root = tk.Tk()
                root.withdraw()  # 隐藏窗口
                
                # 获取tkinter的屏幕尺寸 (逻辑像素)
                tk_width = root.winfo_screenwidth()
                tk_height = root.winfo_screenheight()
                
                # 获取DPI信息
                dpi = root.winfo_fpixels('1i')  # 每英寸像素数
                
                root.destroy()
                
                self.logger.debug(f"tkinter屏幕尺寸: {tk_width}x{tk_height}")
                self.logger.debug(f"DPI: {dpi}")
                
                # 比较pyautogui和tkinter的屏幕尺寸差异来确定缩放比例
                if tk_width > 0 and tk_height > 0:
                    width_ratio = screen_width / tk_width
                    height_ratio = screen_height / tk_height
                    avg_ratio = (width_ratio + height_ratio) / 2
                    
                    self.logger.debug(f"尺寸比例 - 宽度: {width_ratio:.2f}, 高度: {height_ratio:.2f}, 平均: {avg_ratio:.2f}")
                    
                    if avg_ratio >= 2.75:
                        dpr = 3.0
                    elif avg_ratio >= 1.75:
                        dpr = 2.0
                    elif avg_ratio >= 1.25:
                        dpr = 1.5
                    else:
                        dpr = 1.0
                    
                    self.logger.info(f"方法3: 通过尺寸比较检测到DPR: {dpr}")
                    return dpr
                
            except Exception as e:
                self.logger.debug(f"方法3失败: {e}")
            
            # 默认返回1.0
            self.logger.warning("所有macOS DPR检测方法都失败，使用默认值1.0")
            self.logger.warning("如果你的显示器是Retina屏幕，请在config.json中手动设置 'manual_dpr': 2.0")
            return 1.0
            
        except Exception as e:
            self.logger.error(f"检测macOS显示器缩放比例失败: {e}")
            return 1.0
    
    def _detect_windows_dpr(self) -> float:
        """
        检测Windows显示器的缩放比例
        
        在Windows系统中，DPR固定返回1.0，因为Windows的屏幕缩放值
        与实际需要的DPR计算不匹配，直接使用1.0可以得到正确的坐标计算结果
        
        Returns:
            显示器缩放比例 (固定返回1.0)
        """
        try:
            self.logger.info("Windows系统DPR设置为固定值1.0")
            
            # 记录检测到的系统缩放信息（仅用于日志，不影响返回值）
            try:
                import ctypes
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                
                hdc = user32.GetDC(0)
                dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
                user32.ReleaseDC(0, hdc)
                
                scale_x = dpi_x / 96.0
                scale_y = dpi_y / 96.0
                detected_scale = max(scale_x, scale_y)
                
                self.logger.info(f"系统检测到的DPI缩放: {detected_scale} (DPI: {dpi_x}x{dpi_y})")
                self.logger.info("但Windows系统DPR固定使用1.0以确保坐标计算正确")
                
            except Exception as e:
                self.logger.debug(f"获取系统DPI信息失败: {e}")
            
            # Windows系统固定返回1.0
            return 1.0
            
        except Exception as e:
            self.logger.error(f"Windows DPR设置失败: {e}")
            return 1.0
    
    def click_at_position(self, x: int, y: int, window_region: Optional[Tuple[int, int, int, int]] = None):
        """
        在指定位置点击，自动处理DPR缩放
        
        Args:
            x: 相对于截图区域的x坐标（模板匹配返回的坐标）
            y: 相对于截图区域的y坐标（模板匹配返回的坐标）
            window_region: 窗口区域，用于坐标转换
        """
        try:
            # 应用DPR修正 - 模板匹配在高分辨率图像上找到的坐标需要除以DPR
            corrected_x = x / self.dpr
            corrected_y = y / self.dpr
            
            self.logger.debug(f"DPR修正: 原始坐标({x}, {y}) -> 修正坐标({corrected_x:.1f}, {corrected_y:.1f}), DPR={self.dpr}")

            # 如果有窗口区域信息，需要转换坐标
            if window_region:
                # 窗口区域坐标也需要DPR修正
                window_x = window_region[0] / self.dpr
                window_y = window_region[1] / self.dpr
                click_x = window_x + corrected_x
                click_y = window_y + corrected_y
            else:
                click_x = corrected_x
                click_y = corrected_y

            # 转换为整数坐标
            click_x = int(round(click_x))
            click_y = int(round(click_y))
            
            self.logger.info(f"准备点击位置: ({click_x}, {click_y}) [DPR修正后]")
            
            # 确保Spine窗口处于活动状态
            self._ensure_spine_window_active()
            
            # 先移动鼠标到目标位置
            self.logger.info(f"移动鼠标到位置: ({click_x}, {click_y})")
            pyautogui.moveTo(click_x, click_y, duration=0.3)
            time.sleep(0.2)  # 等待鼠标移动完成
            
            # 使用增强的点击方法
            success = self._enhanced_click(click_x, click_y)
            
            if success:
                self.logger.info(f"点击成功: ({click_x}, {click_y})")
                time.sleep(self.config_manager.get("click_delay", 5.0))
                return [click_x, click_y]
            else:
                self.logger.error(f"点击失败: ({click_x}, {click_y})")
                return None
            
        except Exception as e:
            self.logger.error(f"点击操作异常: {e}")
            return None
    
    def _ensure_spine_window_active(self):
        """确保Spine窗口处于活动状态（跨平台）"""
        try:
            if platform.system() == "Darwin":
                self._ensure_window_active_macos(None)
            elif platform.system() == "Windows":
                self._ensure_window_active_windows(None)
            else:
                self._ensure_window_active_linux(None)
                
        except Exception as e:
            self.logger.warning(f"激活窗口时出错: {e}")
    
    def _ensure_window_active_macos(self, app_name: str):
        """macOS窗口激活（支持多个应用名称）"""
        app_names = self.config_manager.get_app_names()
        
        for name in app_names:
            try:
                # 使用AppleScript激活窗口
                activate_script = f'''
                try
                    tell application "{name}"
                        activate
                    end tell
                    delay 0.3
                    return "success"
                on error errMsg
                    return "error: " & errMsg
                end try
                '''
                
                result = subprocess.run(['osascript', '-e', activate_script], 
                                       capture_output=True, text=True, timeout=3)
                
                if result.returncode == 0 and "success" in result.stdout:
                    self.logger.debug(f"{name}窗口已激活")
                    return
                else:
                    self.logger.debug(f"macOS激活{name}失败: {result.stdout}")
                    
            except Exception as e:
                self.logger.debug(f"macOS激活{name}出错: {e}")
                continue
    
    def _ensure_window_active_windows(self, app_name: str):
        """Windows窗口激活（支持多个标题匹配）"""
        try:
            import pygetwindow as gw
            
            window_titles = self.config_manager.get_window_titles()
            
            # 尝试pygetwindow
            for window_title in window_titles:
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    window = windows[0]
                    if window.isMinimized:
                        window.restore()
                    window.activate()
                    self.logger.debug(f"通过pygetwindow激活窗口: {window_title}")
                    return
            
            # 尝试使用Windows API
            try:
                import win32gui
                import win32con
                
                def enum_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        for title in window_titles:
                            if title.lower() in window_text.lower():
                                windows.append((hwnd, window_text, title))
                                return True
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_callback, windows)
                
                if windows:
                    hwnd, window_text, matched_title = windows[0]
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    self.logger.debug(f"通过Windows API激活窗口: {window_text} (匹配: {matched_title})")
                    
            except ImportError:
                self.logger.warning("pywin32未安装，无法使用Windows API激活窗口")
            except Exception as e:
                self.logger.warning(f"Windows API激活失败: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Windows窗口激活出错: {e}")
    
    def _ensure_window_active_linux(self, app_name: str):
        """Linux窗口激活（支持多个标题匹配）"""
        try:
            import pygetwindow as gw
            
            window_titles = self.config_manager.get_window_titles()
            
            # 尝试pygetwindow
            for window_title in window_titles:
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    window = windows[0]
                    window.activate()
                    self.logger.debug(f"Linux窗口激活成功: {window_title}")
                    return
            
            # 尝试使用xdotool
            for window_title in window_titles:
                try:
                    subprocess.run(['xdotool', 'search', '--name', window_title, 'windowactivate'], 
                                  check=True, timeout=3)
                    self.logger.debug(f"通过xdotool激活窗口: {window_title}")
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.logger.debug(f"xdotool激活{window_title}失败")
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Linux窗口激活出错: {e}")
    
    def _enhanced_click(self, x: int, y: int) -> bool:
        """
        增强的点击方法，尝试多种点击策略
        
        Args:
            x: 点击的x坐标
            y: 点击的y坐标
            
        Returns:
            点击是否成功
        """
        strategies = [
            ("PyAutoGUI标准点击", self._pyautogui_click),
            ("PyAutoGUI双击", self._pyautogui_double_click),
            ("AppleScript点击", self._applescript_click),
            ("PyAutoGUI按下释放", self._pyautogui_press_release)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                self.logger.info(f"尝试{strategy_name}: ({x}, {y})")
                
                # 移动鼠标到目标位置
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
                
                # 执行点击策略
                success = strategy_func(x, y)
                
                if success:
                    self.logger.info(f"{strategy_name}成功")
                    return True
                else:
                    self.logger.warning(f"{strategy_name}失败，尝试下一种方法")
                    time.sleep(0.5)  # 短暂等待后尝试下一种方法
                    
            except Exception as e:
                self.logger.warning(f"{strategy_name}异常: {e}")
                continue
        
        self.logger.error("所有点击策略都失败了")
        return False
    
    def _pyautogui_click(self, x: int, y: int) -> bool:
        """PyAutoGUI标准点击"""
        try:
            pyautogui.click(x, y)
            return True
        except Exception as e:
            self.logger.debug(f"PyAutoGUI标准点击失败: {e}")
            return False
    
    def _pyautogui_double_click(self, x: int, y: int) -> bool:
        """PyAutoGUI双击"""
        try:
            pyautogui.doubleClick(x, y)
            return True
        except Exception as e:
            self.logger.debug(f"PyAutoGUI双击失败: {e}")
            return False
    
    def _pyautogui_press_release(self, x: int, y: int) -> bool:
        """PyAutoGUI按下释放方式"""
        try:
            pyautogui.mouseDown(x, y)
            time.sleep(0.1)
            pyautogui.mouseUp(x, y)
            return True
        except Exception as e:
            self.logger.debug(f"PyAutoGUI按下释放失败: {e}")
            return False
    
    def select_all(self) -> bool:
        """
        执行Ctrl+A全选操作
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info("执行Ctrl+A全选操作")
            pyautogui.hotkey('ctrl', 'a')
            return True
        except Exception as e:
            self.logger.error(f"Ctrl+A全选操作失败: {e}")
            return False
    
    def _applescript_click(self, x: int, y: int) -> bool:
        """使用AppleScript点击（仅macOS）"""
        try:
            if platform.system() != "Darwin":
                return False
                
            click_script = f'''
            tell application "System Events"
                click at {{{x}, {y}}}
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', click_script], 
                                   capture_output=True, text=True, timeout=3)
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.debug(f"AppleScript点击失败: {e}")
            return False
    
    def verify_click_effect(self, x: int, y: int, timeout: float = 2.0) -> bool:
        """
        验证点击效果（通过检测界面变化）
        
        Args:
            x: 点击的x坐标
            y: 点击的y坐标
            timeout: 等待超时时间
            
        Returns:
            是否检测到界面变化
        """
        try:
            # 点击前截图
            before_screenshot = pyautogui.screenshot()
            
            # 等待界面可能的变化
            time.sleep(timeout)
            
            # 点击后截图
            after_screenshot = pyautogui.screenshot()
            
            # 简单的像素差异检测
            import numpy as np
            before_array = np.array(before_screenshot)
            after_array = np.array(after_screenshot)
            
            # 计算差异
            diff = np.sum(np.abs(before_array.astype(int) - after_array.astype(int)))
            total_pixels = before_array.shape[0] * before_array.shape[1] * before_array.shape[2]
            diff_ratio = diff / (total_pixels * 255)
            
            self.logger.debug(f"界面变化比例: {diff_ratio:.4f}")
            
            # 如果变化超过0.1%，认为点击有效果
            return diff_ratio > 0.001
            
        except Exception as e:
            self.logger.warning(f"验证点击效果失败: {e}")
            return False
    
    def test_click_functionality(self):
        """增强的点击功能测试"""
        print("\n=== 增强点击功能测试 ===")
        print("这将测试多种点击方法的有效性")
        
        # 选择测试位置
        print("\n请选择测试位置:")
        print("1. 屏幕中央（安全）")
        print("2. 自定义位置")
        print("3. 当前鼠标位置")
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == "1":
            screen_width, screen_height = pyautogui.size()
            test_x = screen_width // 2
            test_y = screen_height // 2
        elif choice == "2":
            try:
                test_x = int(input("请输入X坐标: "))
                test_y = int(input("请输入Y坐标: "))
            except ValueError:
                print("❌ 坐标格式错误")
                return
        elif choice == "3":
            test_x, test_y = pyautogui.position()
        else:
            print("❌ 无效选择")
            return
        
        print(f"\n测试位置: ({test_x}, {test_y})")
        
        if input("是否继续测试？(y/N): ").lower() != 'y':
            return
        
        try:
            print("🔍 3秒后开始测试...")
            time.sleep(3)
            
            # 测试各种点击方法
            strategies = [
                ("PyAutoGUI标准点击", self._pyautogui_click),
                ("PyAutoGUI双击", self._pyautogui_double_click),
                ("PyAutoGUI按下释放", self._pyautogui_press_release),
                ("AppleScript点击", self._applescript_click)
            ]
            
            for strategy_name, strategy_func in strategies:
                print(f"\n测试 {strategy_name}...")
                
                # 移动到测试位置
                pyautogui.moveTo(test_x, test_y, duration=0.2)
                time.sleep(0.1)
                
                # 执行点击
                success = strategy_func(test_x, test_y)
                
                if success:
                    print(f"✅ {strategy_name} - 执行成功")
                else:
                    print(f"❌ {strategy_name} - 执行失败")
                
                time.sleep(1)  # 等待观察效果
            
            print("\n=== 测试完成 ===")
            print("请观察是否有界面响应或变化")
                
        except Exception as e:
            print(f"❌ 点击功能测试失败: {e}")
    
    def debug_click_issue(self, x: int, y: int):
        """
        调试点击问题的详细信息
        
        Args:
            x: 点击的x坐标
            y: 点击的y坐标
        """
        print(f"\n=== 点击问题调试 ===")
        print(f"目标坐标: ({x}, {y})")
        
        # 检查坐标是否在屏幕范围内
        screen_width, screen_height = pyautogui.size()
        print(f"屏幕尺寸: {screen_width}x{screen_height}")
        
        if 0 <= x <= screen_width and 0 <= y <= screen_height:
            print("✅ 坐标在屏幕范围内")
        else:
            print("❌ 坐标超出屏幕范围")
        
        # 检查DPR设置
        print(f"当前DPR: {self.dpr}")
        
        # 检查PyAutoGUI设置
        print(f"PyAutoGUI FAILSAFE: {pyautogui.FAILSAFE}")
        print(f"PyAutoGUI PAUSE: {pyautogui.PAUSE}")
        
        # 检查鼠标当前位置
        current_x, current_y = pyautogui.position()
        print(f"当前鼠标位置: ({current_x}, {current_y})")
        
        # 测试鼠标移动
        print("\n测试鼠标移动...")
        try:
            pyautogui.moveTo(x, y, duration=0.5)
            new_x, new_y = pyautogui.position()
            print(f"移动后鼠标位置: ({new_x}, {new_y})")
            
            if abs(new_x - x) < 5 and abs(new_y - y) < 5:
                print("✅ 鼠标移动正常")
            else:
                print("❌ 鼠标移动异常")
        except Exception as e:
            print(f"❌ 鼠标移动失败: {e}")
        
        # 检查应用程序状态
        app_name = self.config_manager.get("app_name", "Spine")
        print(f"\n目标应用程序: {app_name}")
        
        try:
            check_script = f'''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', check_script], 
                                   capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                current_app = result.stdout.strip()
                print(f"当前前台应用程序: {current_app}")
                
                if app_name.lower() in current_app.lower():
                    print("✅ 目标应用程序在前台")
                else:
                    print("❌ 目标应用程序不在前台")
            else:
                print("❌ 无法检查前台应用程序")
                
        except Exception as e:
            print(f"❌ 检查应用程序状态失败: {e}")
        
        print("\n=== 调试完成 ===")
    
    def scroll_down(self, x: int, y: int, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        在指定位置向下滚动固定一个单位
        
        Args:
            x: 滚动位置的x坐标
            y: 滚动位置的y坐标
            window_region: 窗口区域，用于坐标转换
            
        Returns:
            bool: 滚动是否成功
        """
        try:
            # 应用DPR修正
            corrected_x = x / self.dpr
            corrected_y = y / self.dpr
            
            # 如果有窗口区域信息，需要转换坐标
            if window_region:
                window_x = window_region[0] / self.dpr
                window_y = window_region[1] / self.dpr
                scroll_x = window_x + corrected_x
                scroll_y = window_y + corrected_y
            else:
                scroll_x = corrected_x
                scroll_y = corrected_y

            # 转换为整数坐标
            scroll_x = int(round(scroll_x))
            scroll_y = int(round(scroll_y))
            
            self.logger.info(f"准备在位置 ({scroll_x}, {scroll_y}) 向下滚动一个单位")
            
            # 移动鼠标到滚动位置
            pyautogui.moveTo(scroll_x, scroll_y, duration=0.1)
            time.sleep(0.1)
            
            # 向下滚动固定一个单位（-1表示向下滚动一次）
            pyautogui.scroll(-1, x=scroll_x, y=scroll_y)
            
            # 等待滚动完成
            time.sleep(0.3)
            
            self.logger.info(f"滚动完成：在 ({scroll_x}, {scroll_y}) 向下滚动了 1 个单位")
            return True
            
        except Exception as e:
            self.logger.warning(f"滚动操作失败: {e}")
            return False