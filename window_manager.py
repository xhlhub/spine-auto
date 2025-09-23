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
    
    def find_spine_window(self) -> Optional[dict]:
        """
        查找Spine窗口（跨平台，支持多个标题匹配）
        
        Returns:
            窗口信息字典 {
                'title': str,           # 窗口标题
                'app_name': str,        # 应用程序名称
                'region': tuple,        # 窗口位置和大小 (x, y, width, height)，Windows上可用
                'matched_config': str   # 匹配的配置标题
            } 或 None
        """
        try:
            import pygetwindow as gw
            
            # 获取所有窗口标题
            all_titles = gw.getAllTitles()
            self.logger.debug(f"所有窗口: {all_titles}")
            
            # 获取配置的窗口标题列表
            window_titles = self.config_manager.get_window_titles()
            self.logger.info(f"查找窗口标题: {window_titles}")
            
            # 尝试匹配每个可能的标题，优先选择最精确的匹配
            matched_window = None
            matched_title = None
            best_score = 0
            
            for window_title in window_titles:
                spine_windows = [title for title in all_titles if window_title.lower() in title.lower()]
                for window in spine_windows:
                    # 计算匹配得分：更精确的匹配得分更高
                    score = 0
                    window_lower = window.lower()
                    
                    # 如果窗口标题以"spine"开头，得分更高
                    if window_lower.startswith('spine'):
                        score += 10
                    
                    # 如果包含项目文件名，得分更高
                    if any(ext in window_lower for ext in ['.spine', '-pro', 'trial']):
                        score += 5
                    
                    # 如果不包含编辑器或文件管理器关键词，得分更高
                    if not any(keyword in window_lower for keyword in ['cursor', '文件资源管理器', 'explorer', 'vscode', 'code']):
                        score += 3
                    
                    # 选择得分最高的窗口
                    if score > best_score:
                        best_score = score
                        matched_window = window
                        matched_title = window_title
                        self.logger.info(f"找到更优的Spine窗口: '{matched_window}' (匹配标题: '{matched_title}', 得分: {score})")
            
            if matched_window:
                self.logger.info(f"最终选择Spine窗口: '{matched_window}' (得分: {best_score})")
            
            if matched_window:
                # 自动检测和保存应用程序名称
                detected_app_name = self.detect_app_name_from_title(matched_window)
                if detected_app_name:
                    # 添加到配置中
                    self.config_manager.add_app_name(detected_app_name)
                    self.config_manager.add_window_title(matched_title)
                    self.config_manager.save_config()
                    self.logger.info(f"自动检测并保存应用程序名称: {detected_app_name}")
                
                # 构建窗口信息字典
                window_info = {
                    'title': matched_window,
                    'app_name': detected_app_name or "Spine",
                    'matched_config': matched_title,
                    'region': None
                }
                
                # Windows上可以获取窗口几何信息
                if platform.system() == "Windows":
                    try:
                        window = gw.getWindowsWithTitle(matched_window)[0]
                        window_info['region'] = (window.left, window.top, window.width, window.height)
                        self.logger.info(f"获取到Windows窗口几何信息: {window_info['region']}")
                    except Exception as e:
                        self.logger.warning(f"获取Windows窗口几何信息失败: {e}")
                
                return window_info
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
    
    def activate_window_by_title(self, window_title: str, app_name: str = None) -> bool:
        """根据具体的窗口标题激活窗口（更精确的激活方法）"""
        try:
            if not window_title:
                self.logger.warning("窗口标题为空，无法激活")
                return False
                
            app_name = app_name or "Spine"
            self.logger.info(f"🔄 尝试激活指定窗口: '{window_title}'")
            
            # 记录激活前的状态
            initial_window = self._get_current_foreground_window()
            if initial_window:
                self.logger.info(f"当前前台窗口: {initial_window}")
            
            # 根据平台选择激活方法
            if platform.system() == "Darwin":
                success = self._activate_specific_window_macos(window_title, app_name)
            elif platform.system() == "Windows":
                success = self._activate_specific_window_windows(window_title)
            else:
                success = self._activate_specific_window_linux(window_title, app_name)
            
            # 验证激活结果
            if success:
                # 额外验证：检查激活后的状态
                time.sleep(0.5)  # 等待激活生效
                final_window = self._get_current_foreground_window()
                
                if final_window and (window_title.lower() in final_window.lower() or final_window.lower() in window_title.lower()):
                    self.logger.info(f"✅ 窗口激活成功并验证: {final_window}")
                    return True
                else:
                    self.logger.warning(f"⚠️ 窗口激活成功但验证失败，期望: {window_title}，实际: {final_window}")
                    # 仍然返回True，因为激活方法报告成功
                    return True
            else:
                self.logger.warning(f"❌ 窗口激活失败: {window_title}")
                return False
                
        except Exception as e:
            self.logger.warning(f"激活窗口'{window_title}'过程中出现异常: {e}")
            return False

    def activate_spine_window(self):
        """跨平台的激活Spine窗口方法 - 增强版（向后兼容）"""
        try:
            app_name = self.config_manager.get("app_name", "Spine")
            self.logger.info(f"🔄 尝试激活{app_name}窗口...")
            
            # 记录激活前的状态
            initial_window = self._get_current_foreground_window()
            if initial_window:
                self.logger.info(f"当前前台窗口: {initial_window}")
            
            # 根据平台选择激活方法
            if platform.system() == "Darwin":
                success = self._activate_window_macos(app_name)
            elif platform.system() == "Windows":
                success = self._activate_window_windows(app_name)
            else:
                success = self._activate_window_linux(app_name)
            
            # 验证激活结果
            if success:
                # 额外验证：检查激活后的状态
                time.sleep(0.5)  # 等待激活生效
                final_window = self._get_current_foreground_window()
                
                if final_window and self._is_spine_window(final_window):
                    self.logger.info(f"✅ {app_name}窗口激活成功并验证: {final_window}")
                    return True
                else:
                    self.logger.warning(f"⚠️ {app_name}窗口激活成功但验证失败，当前前台窗口: {final_window}")
                    # 即使验证失败，仍然返回True，因为激活方法报告成功
                    return True
            else:
                self.logger.warning(f"❌ {app_name}窗口激活失败")
                return False
                
        except Exception as e:
            self.logger.warning(f"激活{app_name}窗口过程中出现异常: {e}")
            return False
    
    def _get_current_foreground_window(self) -> Optional[str]:
        """获取当前前台窗口标题"""
        try:
            if platform.system() == "Windows":
                try:
                    import win32gui
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd:
                        return win32gui.GetWindowText(hwnd)
                except ImportError:
                    pass
                    
                # 备用方法：使用pygetwindow
                try:
                    import pygetwindow as gw
                    active_window = gw.getActiveWindow()
                    if active_window and hasattr(active_window, 'title'):
                        return active_window.title
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"获取前台窗口失败: {e}")
        
        return None
    
    def _is_spine_window(self, window_title: str) -> bool:
        """判断窗口标题是否属于Spine"""
        if not window_title:
            return False
            
        window_titles = self.config_manager.get_window_titles()
        for title in window_titles:
            if title.lower() in window_title.lower():
                return True
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
        """Windows窗口激活（支持多个标题匹配）- 增强版"""
        try:
            import pygetwindow as gw
            
            # 获取所有可能的窗口标题
            window_titles = self.config_manager.get_window_titles()
            
            # 方法1: 使用pygetwindow查找并激活窗口
            activated_window = None
            for window_title in window_titles:
                # 使用部分匹配来查找窗口
                all_windows = gw.getAllWindows()
                matching_windows = []
                
                for win in all_windows:
                    if hasattr(win, 'title') and win.title and window_title.lower() in win.title.lower():
                        matching_windows.append(win)
                
                if matching_windows:
                    window = matching_windows[0]  # 取第一个匹配的窗口
                    try:
                        self.logger.info(f"尝试激活窗口: '{window.title}' (匹配规则: '{window_title}')")
                        
                        # 强制激活步骤
                        if hasattr(window, 'isMinimized') and window.isMinimized:
                            self.logger.info("窗口已最小化，正在还原...")
                            window.restore()
                            time.sleep(0.3)
                        
                        # 多重激活策略
                        window.activate()
                        time.sleep(0.2)
                        
                        # 验证激活结果
                        try:
                            if hasattr(window, 'isActive') and window.isActive:
                                self.logger.info(f"✅ pygetwindow激活窗口成功: {window.title}")
                                activated_window = window
                                break
                            else:
                                self.logger.warning(f"窗口激活状态检查失败: {window.title}")
                        except:
                            # 如果无法检查激活状态，假设激活成功
                            self.logger.info(f"✅ pygetwindow激活窗口成功 (无法验证状态): {window.title}")
                            activated_window = window
                            break
                            
                    except Exception as e:
                        self.logger.debug(f"pygetwindow激活'{window.title}'失败: {e}")
                        continue
            
            # 如果pygetwindow成功激活，进行额外验证
            if activated_window:
                # 额外等待时间确保窗口完全激活
                time.sleep(0.5)
                return True
            
            # 方法2: 使用Windows API (更强大的激活方法)
            try:
                import win32gui
                import win32con
                import win32api
                
                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        for title in window_titles:
                            if title.lower() in window_text.lower():
                                windows.append((hwnd, window_text, title))
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)
                
                if windows:
                    hwnd, window_text, matched_title = windows[0]
                    self.logger.info(f"找到目标窗口，准备使用Windows API激活: {window_text}")
                    
                    try:
                        # 强制激活窗口的步骤序列
                        # 1. 恢复窗口（如果最小化）
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        time.sleep(0.1)
                        
                        # 2. 将窗口带到前台
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(0.1)
                        
                        # 3. 确保窗口处于正常状态
                        win32gui.ShowWindow(hwnd, win32con.SW_NORMAL)
                        time.sleep(0.1)
                        
                        # 4. 再次设置为前台窗口
                        try:
                            # 获取当前前台窗口
                            current_hwnd = win32gui.GetForegroundWindow()
                            
                            # 如果当前前台窗口不是目标窗口，强制切换
                            if current_hwnd != hwnd:
                                # 使用AttachThreadInput技巧来强制激活
                                current_thread = win32api.GetCurrentThreadId()
                                target_thread = win32gui.GetWindowThreadProcessId(hwnd)[0]
                                
                                if current_thread != target_thread:
                                    win32gui.AttachThreadInput(current_thread, target_thread, True)
                                    win32gui.SetForegroundWindow(hwnd)
                                    win32gui.AttachThreadInput(current_thread, target_thread, False)
                                else:
                                    win32gui.SetForegroundWindow(hwnd)
                                    
                        except Exception as thread_error:
                            self.logger.debug(f"线程附加方法失败，使用基本方法: {thread_error}")
                            win32gui.SetForegroundWindow(hwnd)
                        
                        # 验证激活结果
                        time.sleep(0.3)
                        final_hwnd = win32gui.GetForegroundWindow()
                        if final_hwnd == hwnd:
                            self.logger.info(f"✅ Windows API激活窗口成功: {window_text}")
                            return True
                        else:
                            self.logger.warning(f"Windows API激活验证失败: 目标窗口未成为前台窗口")
                            
                    except Exception as api_error:
                        self.logger.warning(f"Windows API激活过程中出错: {api_error}")
                    
            except ImportError:
                self.logger.warning("pywin32未安装，无法使用Windows API")
            except Exception as e:
                self.logger.warning(f"Windows API激活失败: {e}")
            
            # 方法3: 手动激活提示（最后的备用方案）
            self.logger.warning("所有自动激活方法都失败，需要用户手动激活窗口")
            return self._prompt_manual_activation(window_titles)
            
        except Exception as e:
            self.logger.error(f"Windows窗口激活失败: {e}")
            return self._prompt_manual_activation(self.config_manager.get_window_titles())
    
    def _prompt_manual_activation(self, window_titles: list) -> bool:
        """提示用户手动激活窗口"""
        print("\n" + "="*60)
        print("🔄 需要手动激活Spine窗口")
        print("="*60)
        print("⚠️  自动激活窗口失败，请按以下步骤手动操作:")
        print()
        print("1. 请用鼠标点击Spine应用窗口，将其切换到前台")
        print("2. 确保Spine窗口完全可见并处于活动状态")
        print("3. 脚本将在15秒后自动继续执行")
        print()
        print(f"📝 寻找包含以下关键词的窗口: {', '.join(window_titles)}")
        print()
        
        for i in range(15, 0, -1):
            print(f"\r⏳ 等待手动激活窗口... {i}秒后继续", end="", flush=True)
            time.sleep(1)
        
        print("\n")
        print("✅ 继续执行自动化流程...")
        return True  # 假设用户已经手动激活了窗口
    
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
    
    # ===== 新增：基于具体窗口标题的精确激活方法 =====
    
    def _activate_specific_window_windows(self, window_title: str) -> bool:
        """Windows平台：根据具体窗口标题激活窗口"""
        try:
            import pygetwindow as gw
            
            self.logger.info(f"Windows: 激活窗口 '{window_title}'")
            
            # 直接查找指定标题的窗口
            windows = gw.getWindowsWithTitle(window_title)
            if windows:
                target_window = windows[0]  # 取第一个匹配的窗口
                self.logger.info(f"找到目标窗口: {target_window.title}")
                
                # 激活窗口
                target_window.activate()
                time.sleep(0.3)  # 等待激活生效
                
                self.logger.info(f"✅ Windows窗口激活成功: {target_window.title}")
                return True
            else:
                # 如果精确标题找不到，尝试模糊匹配
                all_windows = gw.getAllWindows()
                for window in all_windows:
                    if window_title.lower() in window.title.lower():
                        self.logger.info(f"模糊匹配找到窗口: {window.title}")
                        window.activate()
                        time.sleep(0.3)
                        return True
                
                self.logger.warning(f"Windows: 未找到窗口 '{window_title}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Windows窗口激活失败: {e}")
            return False
    
    def _activate_specific_window_macos(self, window_title: str, app_name: str) -> bool:
        """macOS平台：根据具体窗口标题激活窗口"""
        try:
            self.logger.info(f"macOS: 激活窗口 '{window_title}' (应用: {app_name})")
            
            # 尝试激活应用程序
            activate_script = f'''
            try
                tell application "{app_name}"
                    activate
                end tell
                delay 0.5
                return "success"
            on error errMsg
                return "error: " & errMsg
            end try
            '''
            
            result = subprocess.run(['osascript', '-e', activate_script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "success" in result.stdout:
                self.logger.info(f"✅ macOS应用激活成功: {app_name}")
                return True
            else:
                self.logger.warning(f"macOS应用激活失败: {result.stdout}")
                return False
                
        except Exception as e:
            self.logger.error(f"macOS窗口激活失败: {e}")
            return False
    
    def _activate_specific_window_linux(self, window_title: str, app_name: str) -> bool:
        """Linux平台：根据具体窗口标题激活窗口"""
        try:
            import pygetwindow as gw
            
            self.logger.info(f"Linux: 激活窗口 '{window_title}'")
            
            # 尝试使用pygetwindow
            windows = gw.getWindowsWithTitle(window_title)
            if windows:
                target_window = windows[0]
                target_window.activate()
                time.sleep(0.3)
                self.logger.info(f"✅ Linux窗口激活成功: {target_window.title}")
                return True
            
            # 备用方案：使用wmctrl
            try:
                result = subprocess.run(['wmctrl', '-a', window_title], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    self.logger.info(f"✅ Linux wmctrl激活成功: {window_title}")
                    return True
                else:
                    self.logger.warning(f"wmctrl激活失败: {result.stderr}")
            except FileNotFoundError:
                self.logger.warning("wmctrl未安装，跳过")
            
            self.logger.warning(f"Linux: 未找到窗口 '{window_title}'")
            return False
            
        except Exception as e:
            self.logger.error(f"Linux窗口激活失败: {e}")
            return False
