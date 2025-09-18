#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spine UI自动化脚本
自动点击骨骼树节点并点击网格按钮

作者: Assistant
功能: 循环点击Spine右侧树节点 → 点击网格按钮 → 重复操作
"""

import pyautogui
import cv2
import numpy as np
import time
import os
import json
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

# 配置pyautogui
pyautogui.FAILSAFE = True  # 鼠标移到左上角停止
pyautogui.PAUSE = 0.5  # 操作间隔


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
        self.config_path = config_path
        self.config = {}
        self.templates_dir = Path("templates")
        self.templates_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 加载配置
        self.load_config()
        
        # 检测和设置DPR
        if "manual_dpr" in self.config and self.config["manual_dpr"]:
            self.dpr = self.config["manual_dpr"]
            self.logger.info(f"使用手动设置的DPR: {self.dpr}")
        else:
            self.dpr = self.detect_display_scaling()
            self.logger.info(f"自动检测到显示器缩放比例: {self.dpr}")
        
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
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.create_default_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        self.config = {
            "window_title": "Spine",  # Spine窗口标题关键词
            "app_name": None,  # 应用程序名称，None时自动检测
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
            "attachment_subnodes": [  # 要点击的附件子节点名称列表
                "raptor-body",
                "raptor-back-arm", 
                "raptor-front-leg",
                "raptor-hindleg-back",
                "raptor-horn",
                "raptor-jaw",
                "raptor-jaw2",
                "raptor-jaw-tooth",
                "raptor-mouth-inside",
                "raptor-saddle-w-shadow",
                "raptor-tail-shadow", 
                "raptor-tongue",
                "stirrup-strap"
            ]
        }
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info("配置文件已保存")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def detect_display_scaling(self) -> float:
        """
        检测Mac显示器的缩放比例（DPR）
        
        Returns:
            显示器缩放比例
        """
        try:
            import subprocess
            import platform
            
            # 检查是否为macOS
            if platform.system() != "Darwin":
                self.logger.info("非macOS系统，使用默认缩放比例1.0")
                return 1.0
            
            # 方法1: 使用system_profiler获取显示器信息
            try:
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
                                if 'Retina' in resolution or '@ 2x' in resolution:
                                    self.logger.info("检测到Retina显示器，设置DPR为2.0")
                                    return 2.0
                                elif '@ 3x' in resolution:
                                    self.logger.info("检测到3x显示器，设置DPR为3.0")
                                    return 3.0
                                
            except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
                pass
            
            # 方法2: 使用AppleScript获取屏幕信息
            try:
                script = '''
                tell application "System Events"
                    set screenSize to size of first desktop
                    set screenBounds to bounds of first desktop
                    return {item 1 of screenSize, item 2 of screenSize, item 3 of screenBounds, item 4 of screenBounds}
                end tell
                '''
                
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    # 解析返回的尺寸信息
                    output = result.stdout.strip()
                    # AppleScript返回格式类似: "1440, 900, 2880, 1800"
                    values = [float(x.strip()) for x in output.split(',')]
                    if len(values) >= 4:
                        logical_width, logical_height = values[0], values[1]
                        physical_width, physical_height = values[2], values[3]
                        
                        # 计算缩放比例
                        width_ratio = physical_width / logical_width if logical_width > 0 else 1.0
                        height_ratio = physical_height / logical_height if logical_height > 0 else 1.0
                        
                        # 取平均值并四舍五入到最近的整数或0.5
                        avg_ratio = (width_ratio + height_ratio) / 2
                        
                        if avg_ratio >= 2.75:
                            dpr = 3.0
                        elif avg_ratio >= 1.75:
                            dpr = 2.0
                        elif avg_ratio >= 1.25:
                            dpr = 1.5
                        else:
                            dpr = 1.0
                        
                        self.logger.info(f"通过AppleScript检测到DPR: {dpr} (逻辑尺寸: {logical_width}x{logical_height}, 物理尺寸: {physical_width}x{physical_height})")
                        return dpr
                        
            except (subprocess.TimeoutExpired, ValueError, IndexError):
                pass
            
            # 方法3: 使用pyautogui检测屏幕尺寸差异
            try:
                import tkinter as tk
                
                # 创建临时窗口获取DPI信息
                root = tk.Tk()
                root.withdraw()  # 隐藏窗口
                
                # 获取屏幕的DPI
                dpi = root.winfo_fpixels('1i')  # 每英寸像素数
                root.destroy()
                
                # 标准DPI是72，Retina通常是144或更高
                if dpi >= 216:  # 3x
                    dpr = 3.0
                elif dpi >= 144:  # 2x
                    dpr = 2.0
                elif dpi >= 108:  # 1.5x
                    dpr = 1.5
                else:
                    dpr = 1.0
                
                self.logger.info(f"通过DPI检测到DPR: {dpr} (DPI: {dpi})")
                return dpr
                
            except Exception:
                pass
            
            # 方法4: 通过pyautogui屏幕尺寸推测
            try:
                screen_width, screen_height = pyautogui.size()
                
                # 常见的Retina分辨率模式
                retina_resolutions = [
                    (2880, 1800),  # MacBook Pro 15" Retina
                    (2560, 1600),  # MacBook Pro 13" Retina
                    (2304, 1440),  # MacBook 12" Retina
                    (5120, 2880),  # iMac 27" 5K Retina
                    (4096, 2304),  # iMac 21.5" 4K Retina
                ]
                
                # 检查是否匹配已知的Retina分辨率
                for retina_w, retina_h in retina_resolutions:
                    if (abs(screen_width - retina_w) <= 100 and abs(screen_height - retina_h) <= 100) or \
                       (abs(screen_width - retina_w//2) <= 50 and abs(screen_height - retina_h//2) <= 50):
                        self.logger.info(f"根据屏幕分辨率 {screen_width}x{screen_height} 推测为Retina显示器")
                        return 2.0
                
                # 如果屏幕宽度大于2000，很可能是高DPI显示器
                if screen_width >= 2000:
                    self.logger.info(f"高分辨率屏幕 {screen_width}x{screen_height}，推测DPR为2.0")
                    return 2.0
                    
            except Exception:
                pass
            
            # 默认返回1.0
            self.logger.info("无法检测显示器缩放比例，使用默认值1.0")
            return 1.0
            
        except Exception as e:
            self.logger.error(f"检测显示器缩放比例失败: {e}")
            return 1.0
    
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
            spine_windows = [title for title in all_titles if self.config["window_title"] in title]
            
            if spine_windows:
                self.logger.info(f"找到Spine窗口: {spine_windows[0]}")
                
                # 自动检测应用程序名称
                if self.config.get("app_name") is None:
                    detected_app_name = self.detect_app_name_from_title(spine_windows[0])
                    if detected_app_name:
                        self.config["app_name"] = detected_app_name
                        self.save_config()  # 保存检测到的应用程序名称
                        self.logger.info(f"自动检测到应用程序名称: {detected_app_name}")
                
                # 注意：在macOS上，pygetwindow的功能有限
                # 我们暂时返回None，让脚本使用全屏模式
                # 这是因为macOS版本的pygetwindow无法获取窗口几何信息
                return None
            else:
                self.logger.warning(f"未找到包含'{self.config['window_title']}'的窗口")
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
            import subprocess
            
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
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        截取屏幕或指定区域
        
        Args:
            region: 截图区域 (x, y, width, height)
            
        Returns:
            截图的numpy数组
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # 转换为opencv格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 新增：将截图保存为本地图片，文件名带时间戳
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            save_path = f"screenshot_{timestamp}.png"
            cv2.imwrite(save_path, screenshot_cv)
            self.logger.info(f"截图已保存到本地: {save_path}")

            return screenshot_cv
            
        except Exception as e:

            self.logger.error(f"截图失败: {e}")
            return None
    
    def find_template(self, screenshot: np.ndarray, template_path: str, 
                     confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        智能模板匹配方法，根据配置选择不同的匹配策略
        
        Args:
            screenshot: 屏幕截图
            template_path: 模板图片路径
            confidence: 匹配置信度
            
        Returns:
            匹配位置的中心点坐标 (x, y) 或 None
        """
        if not os.path.exists(template_path):
            self.logger.warning(f"模板文件不存在: {template_path}")
            return None
            
        try:
            template = cv2.imread(template_path)
            if template is None:
                self.logger.error(f"无法加载模板图片: {template_path}")
                return None
            
            # 自适应置信度调整
            if self.config.get("adaptive_confidence", True):
                confidence = self._adjust_confidence(template_path, confidence)
            
            # 根据配置选择匹配算法
            algorithm = self.config.get("matching_algorithm", "enhanced")
            
            if algorithm == "basic":
                return self._basic_template_matching(screenshot, template, confidence, template_path)
            elif algorithm == "multi_method":
                return self._multi_method_matching(screenshot, template, confidence, template_path)
            else:  # enhanced
                return self._enhanced_matching_pipeline(screenshot, template, confidence, template_path)
                
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return None
    
    def _adjust_confidence(self, template_path: str, base_confidence: float) -> float:
        """
        根据模板类型自适应调整置信度
        
        Args:
            template_path: 模板路径
            base_confidence: 基础置信度
            
        Returns:
            调整后的置信度
        """
        template_name = os.path.basename(template_path).lower()
        
        # 不同类型模板的置信度调整
        adjustments = {
            "filter_icon": -0.1,  # 筛选图标通常较小，降低要求
            "grid_menu": -0.05,   # 菜单选项可能有变化
            "attachment": 0.0,    # 附件节点保持默认
            "raptor": -0.05       # 子节点可能有细微差异
        }
        
        for key, adjustment in adjustments.items():
            if key in template_name:
                adjusted = base_confidence + adjustment
                self.logger.debug(f"为模板 {template_name} 调整置信度: {base_confidence:.3f} -> {adjusted:.3f}")
                return max(0.5, min(0.95, adjusted))  # 限制在合理范围内
        
        return base_confidence
    
    def _basic_template_matching(self, screenshot: np.ndarray, template: np.ndarray, 
                                confidence: float, template_path: str) -> Optional[Tuple[int, int]]:
        """基础模板匹配"""
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= confidence:
            template_h, template_w = template.shape[:2]
            center_x = max_loc[0] + template_w // 2
            center_y = max_loc[1] + template_h // 2
            
            self.logger.info(f"基础匹配成功: {template_path}, 置信度: {max_val:.3f}, 位置: ({center_x}, {center_y})")
            return (center_x, center_y)
        
        return None
    
    def _multi_method_matching(self, screenshot: np.ndarray, template: np.ndarray, 
                              confidence: float, template_path: str) -> Optional[Tuple[int, int]]:
        """多方法模板匹配"""
        matching_methods = [
            (cv2.TM_CCOEFF_NORMED, "相关系数"),
            (cv2.TM_CCORR_NORMED, "相关性"),
            (cv2.TM_SQDIFF_NORMED, "平方差")
        ]
        
        best_confidence = 0
        best_location = None
        best_method = None
        
        for method, method_name in matching_methods:
            result = cv2.matchTemplate(screenshot, template, method)
            
            if method == cv2.TM_SQDIFF_NORMED:
                min_val, _, min_loc, _ = cv2.minMaxLoc(result)
                current_confidence = 1 - min_val
                current_loc = min_loc
            else:
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                current_confidence = max_val
                current_loc = max_loc
            
            if current_confidence > best_confidence:
                best_confidence = current_confidence
                best_location = current_loc
                best_method = method_name
        
        if best_confidence >= confidence and best_location is not None:
            template_h, template_w = template.shape[:2]
            center_x = best_location[0] + template_w // 2
            center_y = best_location[1] + template_h // 2
            
            self.logger.info(f"多方法匹配成功 ({best_method}): {template_path}, 置信度: {best_confidence:.3f}, 位置: ({center_x}, {center_y})")
            return (center_x, center_y)
        
        return None
    
    def _enhanced_matching_pipeline(self, screenshot: np.ndarray, template: np.ndarray, 
                                   confidence: float, template_path: str) -> Optional[Tuple[int, int]]:
        """增强匹配管道，结合多种技术"""
        # 步骤1: 多方法匹配
        result = self._multi_method_matching(screenshot, template, confidence, template_path)
        if result:
            return result
        
        # 步骤2: 多尺度匹配
        if self.config.get("enable_multi_scale", True):
            result = self._multi_scale_matching(screenshot, template, confidence, template_path)
            if result:
                return result
        
        # 步骤3: 图像预处理匹配
        if self.config.get("enable_preprocessing", True):
            result = self._enhanced_template_matching(screenshot, template, confidence)
            if result:
                self.logger.info(f"预处理匹配成功: {template_path}")
                return result
        
        # 步骤4: 降低置信度重试
        if confidence > 0.6:
            lower_confidence = max(0.5, confidence - 0.2)
            self.logger.debug(f"降低置信度重试: {confidence:.3f} -> {lower_confidence:.3f}")
            return self._multi_method_matching(screenshot, template, lower_confidence, template_path)
        
        return None
    
    def _multi_scale_matching(self, screenshot: np.ndarray, template: np.ndarray, 
                             confidence: float, template_path: str) -> Optional[Tuple[int, int]]:
        """多尺度模板匹配"""
        scale_range = self.config.get("scale_range", [0.8, 1.2])
        scales = np.linspace(scale_range[0], scale_range[1], 9)  # 9个尺度
        
        best_confidence = 0
        best_location = None
        best_scale = 1.0
        
        for scale in scales:
            # 缩放模板
            scaled_template = cv2.resize(template, None, fx=scale, fy=scale)
            
            # 检查缩放后的模板是否超出截图尺寸
            if (scaled_template.shape[0] > screenshot.shape[0] or 
                scaled_template.shape[1] > screenshot.shape[1]):
                continue
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot, scaled_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_location = max_loc
                best_scale = scale
        
        if best_confidence >= confidence and best_location is not None:
            # 计算中心点（考虑缩放）
            scaled_template = cv2.resize(template, None, fx=best_scale, fy=best_scale)
            template_h, template_w = scaled_template.shape[:2]
            center_x = best_location[0] + template_w // 2
            center_y = best_location[1] + template_h // 2
            
            self.logger.info(f"多尺度匹配成功 (缩放: {best_scale:.2f}): {template_path}, 置信度: {best_confidence:.3f}, 位置: ({center_x}, {center_y})")
            
            # 调试模式下保存匹配结果
            if self.config.get("debug_mode", False):
                self._save_debug_match_result(screenshot, scaled_template, best_location, template_path)
            
            return (center_x, center_y)
        
        return None
    
    def _enhanced_template_matching(self, screenshot: np.ndarray, template: np.ndarray, 
                                   confidence: float) -> Optional[Tuple[int, int]]:
        """
        增强的模板匹配，使用图像预处理技术
        
        Args:
            screenshot: 屏幕截图
            template: 模板图像
            confidence: 置信度阈值
            
        Returns:
            匹配位置的中心点坐标 (x, y) 或 None
        """
        try:
            # 转换为灰度图
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # 应用高斯模糊减少噪声
            screenshot_blur = cv2.GaussianBlur(screenshot_gray, (3, 3), 0)
            template_blur = cv2.GaussianBlur(template_gray, (3, 3), 0)
            
            # 直方图均衡化
            screenshot_eq = cv2.equalizeHist(screenshot_blur)
            template_eq = cv2.equalizeHist(template_blur)
            
            # 边缘检测
            screenshot_edges = cv2.Canny(screenshot_eq, 50, 150)
            template_edges = cv2.Canny(template_eq, 50, 150)
            
            # 在预处理后的图像上进行匹配
            preprocessing_methods = [
                (screenshot_gray, template_gray, "灰度"),
                (screenshot_blur, template_blur, "模糊"),
                (screenshot_eq, template_eq, "直方图均衡"),
                (screenshot_edges, template_edges, "边缘检测")
            ]
            
            best_confidence = 0
            best_location = None
            best_template = None
            
            for screen_proc, temp_proc, method_name in preprocessing_methods:
                result = cv2.matchTemplate(screen_proc, temp_proc, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_location = max_loc
                    best_template = temp_proc
                    self.logger.debug(f"预处理方法 '{method_name}' 获得更好匹配: {max_val:.3f}")
            
            if best_confidence >= confidence and best_location is not None:
                template_h, template_w = best_template.shape[:2]
                center_x = best_location[0] + template_w // 2
                center_y = best_location[1] + template_h // 2
                
                self.logger.info(f"增强匹配成功，置信度: {best_confidence:.3f}, 位置: ({center_x}, {center_y})")
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            self.logger.error(f"增强模板匹配失败: {e}")
            return None
    
    def _save_debug_match_result(self, screenshot: np.ndarray, template: np.ndarray, 
                                location: Tuple[int, int], template_path: str):
        """
        保存调试匹配结果
        
        Args:
            screenshot: 屏幕截图
            template: 匹配的模板
            location: 匹配位置
            template_path: 模板路径
        """
        try:
            import datetime
            
            # 在截图上标记匹配位置
            debug_img = screenshot.copy()
            template_h, template_w = template.shape[:2]
            
            # 绘制匹配框
            cv2.rectangle(debug_img, location, 
                         (location[0] + template_w, location[1] + template_h), 
                         (0, 255, 0), 2)
            
            # 绘制中心点
            center_x = location[0] + template_w // 2
            center_y = location[1] + template_h // 2
            cv2.circle(debug_img, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # 保存调试图像
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            template_name = os.path.basename(template_path).split('.')[0]
            debug_path = f"debug_match_{template_name}_{timestamp}.png"
            cv2.imwrite(debug_path, debug_img)
            
            self.logger.debug(f"调试匹配结果已保存: {debug_path}")
            
        except Exception as e:
            self.logger.error(f"保存调试匹配结果失败: {e}")
    
    def analyze_template_quality(self, template_path: str) -> Dict[str, any]:
        """
        分析模板质量并提供优化建议
        
        Args:
            template_path: 模板路径
            
        Returns:
            包含分析结果和建议的字典
        """
        try:
            if not os.path.exists(template_path):
                return {"error": "模板文件不存在"}
            
            template = cv2.imread(template_path)
            if template is None:
                return {"error": "无法加载模板图片"}
            
            analysis = {
                "path": template_path,
                "size": template.shape,
                "recommendations": []
            }
            
            # 尺寸分析
            height, width = template.shape[:2]
            if width < 20 or height < 20:
                analysis["recommendations"].append("模板尺寸过小，建议至少20x20像素")
            elif width > 200 or height > 200:
                analysis["recommendations"].append("模板尺寸过大，可能影响匹配速度")
            
            # 转换为灰度进行分析
            gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # 对比度分析
            contrast = gray.std()
            analysis["contrast"] = float(contrast)
            if contrast < 20:
                analysis["recommendations"].append("模板对比度较低，建议选择对比度更高的区域")
            
            # 边缘特征分析
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (width * height)
            analysis["edge_density"] = float(edge_density)
            if edge_density < 0.1:
                analysis["recommendations"].append("模板边缘特征较少，建议包含更多边缘信息")
            
            # 纹理分析
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            analysis["texture_variance"] = float(laplacian_var)
            if laplacian_var < 100:
                analysis["recommendations"].append("模板纹理变化较小，可能导致误匹配")
            
            # 颜色分析
            mean_color = np.mean(template, axis=(0, 1))
            analysis["mean_color"] = mean_color.tolist()
            
            # 整体质量评分
            quality_score = 0
            if contrast >= 20:
                quality_score += 25
            if edge_density >= 0.1:
                quality_score += 25
            if laplacian_var >= 100:
                quality_score += 25
            if 20 <= width <= 200 and 20 <= height <= 200:
                quality_score += 25
            
            analysis["quality_score"] = quality_score
            
            if quality_score >= 75:
                analysis["quality_level"] = "优秀"
            elif quality_score >= 50:
                analysis["quality_level"] = "良好"
            elif quality_score >= 25:
                analysis["quality_level"] = "一般"
            else:
                analysis["quality_level"] = "较差"
            
            return analysis
            
        except Exception as e:
            return {"error": f"分析模板质量失败: {e}"}
    
    def optimize_template_matching_settings(self):
        """
        根据模板质量自动优化匹配设置
        """
        try:
            template_files = [
                "filter_icon.png",
                "grid_menu_option.png", 
                "attachment_node.png"
            ]
            
            optimizations = {}
            
            for template_file in template_files:
                template_path = self.templates_dir / template_file
                if template_path.exists():
                    analysis = self.analyze_template_quality(str(template_path))
                    
                    if "error" not in analysis:
                        # 根据质量调整设置
                        template_name = template_file.split('.')[0]
                        optimizations[template_name] = {}
                        
                        # 根据质量分数调整置信度
                        if analysis["quality_score"] < 50:
                            optimizations[template_name]["confidence_adjustment"] = -0.1
                        elif analysis["quality_score"] > 75:
                            optimizations[template_name]["confidence_adjustment"] = 0.05
                        
                        # 根据对比度调整算法选择
                        if analysis["contrast"] < 20:
                            optimizations[template_name]["preferred_algorithm"] = "enhanced"
                        
                        # 根据尺寸调整多尺度设置
                        width, height = analysis["size"][1], analysis["size"][0]
                        if width < 30 or height < 30:
                            optimizations[template_name]["enable_multi_scale"] = True
                            optimizations[template_name]["scale_range"] = [0.7, 1.3]
            
            # 应用优化设置
            if optimizations:
                self.config["template_optimizations"] = optimizations
                self.save_config()
                self.logger.info(f"已应用模板优化设置: {optimizations}")
            
        except Exception as e:
            self.logger.error(f"优化模板匹配设置失败: {e}")
    
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
            if not self.activate_spine_window():
                self.logger.warning("窗口激活可能失败，但继续尝试点击")
            
            # 使用pyautogui点击
            # 先移动鼠标到目标位置
            pyautogui.moveTo(click_x, click_y, duration=0.2)
            time.sleep(0.1)
            
            # 执行点击
            pyautogui.click(click_x, click_y)
            self.logger.info(f"PyAutoGUI点击完成: ({click_x}, {click_y})")
            
            time.sleep(self.config["click_delay"])
            
        except Exception as e:
            self.logger.error(f"点击失败: {e}")
            # 尝试紧急恢复点击
            try:
                pyautogui.click(click_x, click_y)
                self.logger.info("紧急恢复点击已执行")
            except:
                pass
    
    def check_accessibility_permissions(self):
        """检查辅助功能权限"""
        try:
            import subprocess
            
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
            import subprocess
            
            # 获取应用程序名称
            app_name = self.config.get("app_name", "Spine")
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
            self.logger.warning(f"激活{app_name}窗口失败: {e}")
            return False
    
    def save_template_from_selection(self, name: str, region: Tuple[int, int, int, int]):
        """
        保存选定区域作为模板
        
        Args:
            name: 模板名称
            region: 选择区域 (x, y, width, height)
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            template_path = self.templates_dir / f"{name}.png"
            screenshot.save(template_path)
            self.logger.info(f"模板已保存: {template_path}")
            return str(template_path)
        except Exception as e:
            self.logger.error(f"保存模板失败: {e}")
            return None
    
    def setup_templates(self):
        """设置模板图片（需要用户手动截图）"""
        print("\n=== 模板设置向导 ===")
        print("请按照提示手动截取模板图片并保存到templates文件夹中")
        print(f"模板保存路径: {self.templates_dir.absolute()}")
        print("\n需要的模板:")
        print("1. filter_icon.png - 筛选图标（漏斗形状）的截图")
        print("2. grid_menu_option.png - 下拉菜单中'网格'选项的截图")
        print("3. attachment_node.png - '附件'节点的截图")
        
        print("\n附件子节点模板:")
        for i, node_name in enumerate(self.config["attachment_subnodes"], 4):
            print(f"{i}. {node_name}.png - {node_name}子节点的截图")
        
        print("\n请手动创建这些模板文件后，按回车继续...")
        input()
    
    def run_automation(self):
        """运行自动化流程"""
        self.logger.info("开始执行Spine自动化流程")
        
        # 步骤0: 检查系统权限
        if not self.check_accessibility_permissions():
            self.logger.error("系统权限检查失败，请配置辅助功能权限后重试")
            print("\n❌ 权限检查失败!")
            print("请按以下步骤配置权限:")
            print("1. 打开 系统偏好设置 > 安全性与隐私 > 隐私")
            print("2. 选择左侧的 '辅助功能'")
            print("3. 点击锁图标并输入密码")
            print("4. 添加并勾选你的终端应用程序 (如 Terminal 或 iTerm)")
            print("5. 重新运行此脚本")
            return
        else:
            self.logger.info("✅ 辅助功能权限检查通过")
        
        # 查找Spine窗口
        window_region = self.find_spine_window()
        print(window_region)
        if window_region:
            self.logger.info(f"找到Spine窗口: {window_region}")
        else:
            self.logger.info("未找到Spine窗口，将使用全屏操作")
        
        # 检查必需的模板文件
        required_templates = [
            "filter_icon.png",
            "grid_menu_option.png", 
            "attachment_node.png"
        ]
        
        missing_templates = []
        for template_name in required_templates:
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                missing_templates.append(template_name)
        
        if missing_templates:
            self.logger.error(f"缺少必需的模板文件: {missing_templates}")
            self.setup_templates()
            return
        
        # 执行主要流程
        try:
            # # 步骤1: 点击筛选图标
            if not self.click_filter_icon(window_region):
                self.logger.error("点击筛选图标失败")
                return
            
            # 步骤2: 点击网格菜单选项
            if not self.click_grid_menu_option(window_region):
                self.logger.error("点击网格菜单选项失败")
                return
            
            # 步骤3: 点击附件节点
            if not self.click_attachment_node(window_region):
                self.logger.error("点击附件节点失败")
                return
            
            # 步骤4: 循环点击附件子节点
            self.process_attachment_subnodes(window_region)
            
        except Exception as e:
            self.logger.error(f"自动化流程执行失败: {e}")
        
        self.logger.info("自动化流程完成")
    
    def click_filter_icon(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击筛选图标"""
        self.logger.info("步骤1: 点击筛选图标")
        
        try:
            screenshot = self.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            filter_template = str(self.templates_dir / "filter_icon.png")
            filter_pos = self.find_template(screenshot, filter_template, self.config["confidence_threshold"])
            self.logger.info("filter_pos: " + str(filter_pos[0]) + " " + str(filter_pos[1]))
            if filter_pos is None:
                self.logger.warning("未找到筛选图标")
                return False
            
            # 使用配置中的点击方式
            self.click_at_position(
                filter_pos[0], filter_pos[1], 
                window_region
            )
            
            # 调试模式下额外检查
            if self.config.get("debug_mode", False):
                self.logger.info("等待点击效果生效...")
                time.sleep(1.0)
                # 可以在这里添加验证点击是否成功的逻辑
            
            time.sleep(self.config["click_delay"])
            return True
            
        except Exception as e:
            self.logger.error(f"点击筛选图标失败: {e}")
            return False
    
    def click_grid_menu_option(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击下拉菜单中的网格选项"""
        self.logger.info("步骤2: 点击网格菜单选项")
        
        try:
            # 等待下拉菜单出现
            time.sleep(0.5)
            screenshot = self.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            grid_menu_template = str(self.templates_dir / "grid_menu_option.png")
            grid_pos = self.find_template(screenshot, grid_menu_template, self.config["confidence_threshold"])
            
            if grid_pos is None:
                self.logger.warning("未找到网格菜单选项")
                return False
            
            self.click_at_position(
                grid_pos[0], grid_pos[1], 
                window_region
            )
            
            if self.config.get("debug_mode", False):
                self.logger.info("网格菜单点击完成，等待界面更新...")
                
            time.sleep(self.config["click_delay"])
            return True
            
        except Exception as e:
            self.logger.error(f"点击网格菜单选项失败: {e}")
            return False
    
    def click_attachment_node(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击附件节点"""
        self.logger.info("步骤3: 点击附件节点")
        
        try:
            # 等待界面更新
            time.sleep(0.5)
            screenshot = self.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            attachment_template = str(self.templates_dir / "attachment_node.png")
            attachment_pos = self.find_template(screenshot, attachment_template, self.config["confidence_threshold"])
            
            if attachment_pos is None:
                self.logger.warning("未找到附件节点")
                return False
            
            self.click_at_position(
                attachment_pos[0], attachment_pos[1], 
                window_region
            )
            
            if self.config.get("debug_mode", False):
                self.logger.info("附件节点点击完成，等待子节点展开...")
                
            time.sleep(self.config["operation_delay"])  # 等待子节点展开
            return True
            
        except Exception as e:
            self.logger.error(f"点击附件节点失败: {e}")
            return False
    
    def process_attachment_subnodes(self, window_region: Optional[Tuple[int, int, int, int]] = None):
        """处理附件子节点"""
        self.logger.info("步骤4: 开始处理附件子节点")
        
        for i, subnode_name in enumerate(self.config["attachment_subnodes"]):
            self.logger.info(f"处理子节点 {i+1}/{len(self.config['attachment_subnodes'])}: {subnode_name}")
            
            subnode_template = self.templates_dir / f"{subnode_name}.png"
            if not subnode_template.exists():
                self.logger.warning(f"子节点模板不存在: {subnode_template}")
                continue
            
            success = self.click_subnode(str(subnode_template), window_region)
            
            if success:
                self.logger.info(f"成功处理子节点: {subnode_name}")
            else:
                self.logger.warning(f"处理子节点失败: {subnode_name}")
            
            # 子节点操作间隔
            time.sleep(self.config["operation_delay"])
    
    def click_subnode(self, subnode_template: str, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击单个子节点"""
        try:
            screenshot = self.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            subnode_pos = self.find_template(screenshot, subnode_template, self.config["confidence_threshold"])
            
            if subnode_pos is None:
                self.logger.debug(f"未找到子节点模板: {subnode_template}")
                return False
            
            self.click_at_position(subnode_pos[0], subnode_pos[1], window_region)
            return True
            
        except Exception as e:
            self.logger.error(f"点击子节点失败: {e}")
            return False
    
    def click_node_and_grid(self, node_template: str, grid_template: str, 
                           window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        点击节点和网格按钮
        
        Args:
            node_template: 节点模板路径
            grid_template: 网格按钮模板路径
            window_region: 窗口区域
            
        Returns:
            操作是否成功
        """
        try:
            # 截取当前屏幕
            if window_region:
                screenshot = self.take_screenshot(window_region)
            else:
                screenshot = self.take_screenshot()
            
            if screenshot is None:
                return False
            
            # 查找节点
            node_pos = self.find_template(
                screenshot, 
                node_template, 
                self.config["confidence_threshold"]
            )
            
            if node_pos is None:
                self.logger.warning(f"未找到节点模板: {node_template}")
                return False
            
            # 点击节点
            self.click_at_position(node_pos[0], node_pos[1], window_region)
            
            # 等待界面更新
            time.sleep(0.5)
            
            # 重新截图查找网格按钮
            if window_region:
                screenshot = self.take_screenshot(window_region)
            else:
                screenshot = self.take_screenshot()
            
            # 查找网格按钮
            grid_pos = self.find_template(
                screenshot,
                grid_template,
                self.config["confidence_threshold"] 
            )
            
            if grid_pos is None:
                self.logger.warning("未找到网格按钮")
                return False
            
            # 点击网格按钮
            self.click_at_position(grid_pos[0], grid_pos[1], window_region)
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行点击操作失败: {e}")
            return False
    
    def test_click_functionality(self):
        """测试点击功能"""
        print("\n=== 点击功能测试 ===")
        print("这将在屏幕中央执行一次测试点击")
        print("请确保点击位置是安全的（比如桌面空白区域）")
        
        if input("是否继续测试？(y/N): ").lower() != 'y':
            return
        
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            print(f"屏幕尺寸: {screen_width}x{screen_height}")
            print(f"测试点击位置: ({center_x}, {center_y})")
            
            # 检查权限
            if not self.check_accessibility_permissions():
                print("❌ 权限检查失败，请先配置辅助功能权限")
                return
            
            print("🔍 3秒后开始测试点击...")
            time.sleep(3)
            
            # 测试PyAutoGUI点击
            print("测试PyAutoGUI点击...")
            pyautogui.click(center_x, center_y)
            print("✅ PyAutoGUI点击测试完成")
                
        except Exception as e:
            print(f"❌ 点击功能测试失败: {e}")


def main():
    """主函数"""
    print("=== Spine UI自动化脚本 ===")
    print("功能: 自动点击骨骼树节点并点击网格按钮")
    print()
    
    # 创建自动化实例
    automation = SpineAutomation()
    
    while True:
        print("\n请选择操作:")
        print("1. 设置模板图片")
        print("2. 运行自动化流程") 
        print("3. 编辑配置")
        print("4. 测试点击功能")
        print("5. 检查系统权限")
        print("6. 分析模板质量")
        print("7. 优化匹配设置")
        print("8. 测试DPR检测")
        print("9. 退出")
        
        choice = input("请输入选择 (1-9): ").strip()
        
        if choice == "1":
            automation.setup_templates()
        elif choice == "2":
            automation.run_automation()
        elif choice == "3":
            print(f"请编辑配置文件: {automation.config_path}")
            input("编辑完成后按回车继续...")
            automation.load_config()
        elif choice == "4":
            automation.test_click_functionality()
        elif choice == "5":
            if automation.check_accessibility_permissions():
                print("✅ 辅助功能权限正常")
            else:
                print("❌ 辅助功能权限不足")
        elif choice == "6":
            # 分析模板质量
            template_files = ["filter_icon.png", "grid_menu_option.png", "attachment_node.png"]
            print("\n=== 模板质量分析 ===")
            for template_file in template_files:
                template_path = automation.templates_dir / template_file
                if template_path.exists():
                    analysis = automation.analyze_template_quality(str(template_path))
                    if "error" not in analysis:
                        print(f"\n📊 {template_file}:")
                        print(f"  质量等级: {analysis['quality_level']}")
                        print(f"  质量分数: {analysis['quality_score']}/100")
                        print(f"  尺寸: {analysis['size'][1]}x{analysis['size'][0]}")
                        print(f"  对比度: {analysis['contrast']:.2f}")
                        print(f"  边缘密度: {analysis['edge_density']:.3f}")
                        print(f"  纹理方差: {analysis['texture_variance']:.2f}")
                        if analysis['recommendations']:
                            print("  建议:")
                            for rec in analysis['recommendations']:
                                print(f"    • {rec}")
                    else:
                        print(f"\n❌ {template_file}: {analysis['error']}")
                else:
                    print(f"\n❌ {template_file}: 文件不存在")
            input("\n按回车继续...")
        elif choice == "7":
            # 优化匹配设置
            print("\n=== 优化匹配设置 ===")
            automation.optimize_template_matching_settings()
            print("✅ 匹配设置优化完成")
            input("按回车继续...")
        elif choice == "8":
            # 测试DPR检测
            print("\n=== DPR检测测试 ===")
            print(f"当前检测到的DPR: {automation.dpr}")
            
            # 获取屏幕信息
            try:
                screen_width, screen_height = pyautogui.size()
                print(f"PyAutoGUI报告的屏幕尺寸: {screen_width}x{screen_height}")
                
                # 测试坐标转换
                test_coords = [(100, 100), (500, 300), (1000, 600)]
                print("\n坐标转换测试:")
                for orig_x, orig_y in test_coords:
                    corrected_x = orig_x / automation.dpr
                    corrected_y = orig_y / automation.dpr
                    print(f"  原始: ({orig_x}, {orig_y}) -> DPR修正: ({corrected_x:.1f}, {corrected_y:.1f})")
                
                # 提供手动设置DPR的选项
                print(f"\n当前DPR设置: {automation.dpr}")
                manual_dpr = input("如需手动设置DPR，请输入数值（直接回车保持当前值）: ").strip()
                if manual_dpr:
                    try:
                        new_dpr = float(manual_dpr)
                        if 0.5 <= new_dpr <= 4.0:
                            automation.dpr = new_dpr
                            automation.config["manual_dpr"] = new_dpr
                            automation.save_config()
                            print(f"✅ DPR已手动设置为: {new_dpr}")
                        else:
                            print("❌ DPR值应在0.5-4.0之间")
                    except ValueError:
                        print("❌ 请输入有效的数值")
                        
            except Exception as e:
                print(f"❌ 测试失败: {e}")
            
            input("\n按回车继续...")
        elif choice == "9":
            print("退出程序")
            break
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
