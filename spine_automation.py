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
            "force_click": True,  # 是否使用强制点击（AppleScript）
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
            # import datetime
            # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            # save_path = f"screenshot_{timestamp}.png"
            # cv2.imwrite(save_path, screenshot_cv)
            # self.logger.info(f"截图已保存到本地: {save_path}")

            return screenshot_cv
            
        except Exception as e:

            self.logger.error(f"截图失败: {e}")
            return None
    
    def find_template(self, screenshot: np.ndarray, template_path: str, 
                     confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        在截图中查找模板匹配
        
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
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                # 返回匹配区域的中心点
                template_h, template_w = template.shape[:2]
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2
                
                self.logger.info(f"找到模板匹配: {template_path}, 置信度: {max_val:.3f}, 位置: ({center_x}, {center_y})")
                return (center_x, center_y)
            else:
                self.logger.debug(f"模板匹配置信度不足: {template_path}, 置信度: {max_val:.3f}")
                return None
                
        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return None
    
    def click_at_position(self, x: int, y: int, window_region: Optional[Tuple[int, int, int, int]] = None, force_click: bool = True):
        """
        在指定位置点击（改进版本，支持强制点击）
        
        Args:
            x: 相对于截图区域的x坐标
            y: 相对于截图区域的y坐标
            window_region: 窗口区域，用于坐标转换
            force_click: 是否使用强制点击（通过AppleScript）
        """

        try:

            # 如果有窗口区域信息，需要转换坐标
            if window_region:
                click_x = window_region[0] + x
                click_y = window_region[1] + y
            else:

                click_x = x
                click_y = y

            click_x = 1281
            click_y = 295
            
            self.logger.info(f"准备点击位置: ({click_x}, {click_y})")
            
            # 确保Spine窗口处于活动状态
            if not self.activate_spine_window():
                self.logger.warning("窗口激活可能失败，但继续尝试点击")
            
            # 方法1: 使用pyautogui点击
            if not force_click:
                # 先移动鼠标到目标位置
                pyautogui.moveTo(click_x , click_y, duration=0.2)
                time.sleep(0.1)
                
                # 执行点击
                pyautogui.click(click_x, click_y)
                self.logger.info(f"PyAutoGUI点击完成: ({click_x}, {click_y})")
                
            else:
                # 方法2: 使用AppleScript强制点击（更可靠）
                success = self.force_click_with_applescript(click_x, click_y)
                if not success:
                    # 如果AppleScript失败，回退到pyautogui
                    self.logger.warning("AppleScript点击失败，回退到PyAutoGUI")
                    pyautogui.moveTo(click_x, click_y, duration=0.2)
                    time.sleep(0.1)
                    pyautogui.click(click_x, click_y)
                    self.logger.info(f"PyAutoGUI备用点击完成: ({click_x}, {click_y})")
            
            time.sleep(self.config["click_delay"])
            
        except Exception as e:
            self.logger.error(f"点击失败: {e}")
            # 尝试紧急恢复点击
            try:
                pyautogui.click(click_x, click_y)
                self.logger.info("紧急恢复点击已执行")
            except:
                pass
    
    def force_click_with_applescript(self, x: int, y: int) -> bool:
        """
        使用AppleScript执行强制点击
        
        Args:
            x: 屏幕x坐标
            y: 屏幕y坐标
            
        Returns:
            点击是否成功
        """
        try:
            import subprocess
            
            # 获取应用程序名称
            app_name = self.config.get("app_name", "Spine")
            
            # 使用AppleScript进行点击
            click_script = f'''
            try
                tell application "System Events"
                    -- 确保Spine处于前台
                    tell application "{app_name}" to activate
                    delay 0.3
                    
                    -- 执行点击
                    click at {{{x}, {y}}}
                    delay 0.1
                end tell
                return "success"
            on error errMsg
                return "error: " & errMsg
            end try
            '''
            
            result = subprocess.run(['osascript', '-e', click_script], 
                                   capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and "success" in result.stdout:
                self.logger.info(f"AppleScript点击成功: ({x}, {y})")
                return True
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                self.logger.warning(f"AppleScript点击失败: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("AppleScript点击超时")
            return False
        except Exception as e:
            self.logger.error(f"AppleScript点击异常: {e}")
            return False
    
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
            
            if filter_pos is None:
                self.logger.warning("未找到筛选图标")
                return False
            
            # 使用配置中的点击方式
            self.click_at_position(
                filter_pos[0], filter_pos[1], 
                window_region, 
                force_click=False
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
                window_region,
                force_click=self.config.get("force_click", True)
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
                window_region,
                force_click=self.config.get("force_click", True)
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
            
            # 测试AppleScript点击
            print("测试AppleScript点击...")
            success = self.force_click_with_applescript(center_x, center_y)
            if success:
                print("✅ AppleScript点击测试成功")
            else:
                print("❌ AppleScript点击测试失败")
                
                # 尝试pyautogui点击
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
        print("6. 退出")
        
        choice = input("请输入选择 (1-6): ").strip()
        
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
            print("退出程序")
            break
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
