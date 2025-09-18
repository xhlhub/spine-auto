#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化流程模块

包含run_automation相关的核心自动化流程
"""

import time
import logging
from typing import Optional, Tuple


class AutomationRunner:
    """自动化流程执行器"""
    
    def __init__(self, config_manager, template_manager, window_manager, click_manager):
        """
        初始化自动化流程执行器
        
        Args:
            config_manager: 配置管理器实例
            template_manager: 模板管理器实例
            window_manager: 窗口管理器实例
            click_manager: 点击管理器实例
        """
        self.config_manager = config_manager
        self.template_manager = template_manager
        self.window_manager = window_manager
        self.click_manager = click_manager
        self.logger = logging.getLogger(__name__)
    
    def run_automation(self):
        """运行自动化流程"""
        self.logger.info("开始执行Spine自动化流程")
        
        # 步骤0: 检查系统权限
        if not self.window_manager.check_accessibility_permissions():
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
        window_region = self.window_manager.find_spine_window()
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
            template_path = self.template_manager.templates_dir / template_name
            if not template_path.exists():
                missing_templates.append(template_name)
        
        if missing_templates:
            self.logger.error(f"缺少必需的模板文件: {missing_templates}")
            self.setup_templates()
            return
        
        # 执行主要流程
        try:
            # 步骤1: 点击筛选图标
            if not self.click_filter_icon(window_region):
                self.logger.error("点击筛选图标失败")
                return
            
            # 步骤2: 点击网格菜单选项
            if not self.click_grid_menu_option(window_region):
                self.logger.error("点击网格菜单选项失败")
                return
            
            # 步骤3: 点击附件节点
            attachment_pos = self.click_attachment_node(window_region)
            if attachment_pos is None:
                self.logger.error("点击附件节点失败")
                return
            
            # 步骤4: 循环点击附件子节点
            self.process_attachment_subnodes(attachment_pos, window_region)
            
        except Exception as e:
            self.logger.error(f"自动化流程执行失败: {e}")
        
        self.logger.info("自动化流程完成")
    
    def click_filter_icon(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击筛选图标"""
        self.logger.info("步骤1: 点击筛选图标")
        
        try:
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            filter_template = str(self.template_manager.templates_dir / "filter_icon.png")
            filter_pos = self.template_manager.find_template(
                screenshot, 
                filter_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if filter_pos is None:
                self.logger.warning("未找到筛选图标")
                return False
            
            self.logger.info("filter_pos: " + str(filter_pos[0]) + " " + str(filter_pos[1]))
            
            # 使用配置中的点击方式
            self.click_manager.click_at_position(
                filter_pos[0], filter_pos[1], 
                window_region
            )
            
            # 调试模式下额外检查
            if self.config_manager.get("debug_mode", False):
                self.logger.info("等待点击效果生效...")
                time.sleep(1.0)
                # 可以在这里添加验证点击是否成功的逻辑
            
            time.sleep(self.config_manager.get("click_delay", 5.0))
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
            screenshot = self.template_manager.take_screenshot(window_region, "grid_menu_option")
            if screenshot is None:
                return False
            
            grid_menu_template = str(self.template_manager.templates_dir / "grid_menu_option.png")
            grid_pos = self.template_manager.find_template(
                screenshot, 
                grid_menu_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if grid_pos is None:
                self.logger.warning("未找到网格菜单选项")
                return False
            
            self.click_manager.click_at_position(
                grid_pos[0], grid_pos[1], 
                window_region
            )
            
            if self.config_manager.get("debug_mode", False):
                self.logger.info("网格菜单点击完成，等待界面更新...")
                
            time.sleep(self.config_manager.get("click_delay", 5.0))
            return True
            
        except Exception as e:
            self.logger.error(f"点击网格菜单选项失败: {e}")
            return False
    
    def click_attachment_node(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """点击附件节点并返回节点位置"""
        self.logger.info("步骤3: 点击附件节点")
        
        try:
            # 等待界面更新
            time.sleep(0.5)
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return None
            
            attachment_template = str(self.template_manager.templates_dir / "attachment_node.png")
            attachment_pos = self.template_manager.find_template(
                screenshot, 
                attachment_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if attachment_pos is None:
                self.logger.warning("未找到附件节点")
                return None
            
            self.click_manager.click_at_position(
                attachment_pos[0], attachment_pos[1], 
                window_region
            )
            
            if self.config_manager.get("debug_mode", False):
                self.logger.info("附件节点点击完成，等待子节点展开...")
                
            time.sleep(self.config_manager.get("operation_delay", 2.0))  # 等待子节点展开
            return attachment_pos
            
        except Exception as e:
            self.logger.error(f"点击附件节点失败: {e}")
            return None
    
    def process_attachment_subnodes(self, attachment_pos: Tuple[int, int], window_region: Optional[Tuple[int, int, int, int]] = None):
        """处理附件子节点"""
        self.logger.info("步骤4: 开始处理附件子节点")
        
        attachment_subnodes = self.config_manager.get("attachment_subnodes", [])
        for i, subnode_name in enumerate(attachment_subnodes):
            self.logger.info(f"处理子节点 {i+1}/{len(attachment_subnodes)}: {subnode_name}")
            
            subnode_template = self.template_manager.templates_dir / f"{subnode_name}.png"
            if not subnode_template.exists():
                self.logger.warning(f"子节点模板不存在: {subnode_template}")
                continue
            
            success = self.click_subnode(attachment_pos, window_region)
            
            if success:
                self.logger.info(f"成功处理子节点: {subnode_name}")
            else:
                self.logger.warning(f"处理子节点失败: {subnode_name}")
            
            # 子节点操作间隔
            time.sleep(self.config_manager.get("operation_delay", 2.0))
    
    def click_subnode(self, attachment_pos: Tuple[int, int], window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """循环点击子节点"""
        try:
            node_height = self.config_manager.get("node_height", 20)
            success_count = 0
            
            # 循环点击3次
            for i in range(3):
                # 计算当前子节点的y坐标
                current_y = attachment_pos[1] + (i + 1) * node_height * self.click_manager.dpr
                click_pos = (attachment_pos[0], current_y)
                
                self.logger.info(f"点击子节点 {i+1}/3，坐标: ({click_pos[0]}, {click_pos[1]})")
                
                try:
                    self.click_manager.click_at_position(click_pos[0], click_pos[1], window_region)
                    success_count += 1
                    time.sleep(self.config_manager.get("click_delay", 5.0))
                except Exception as e:
                    self.logger.warning(f"点击子节点 {i+1} 失败: {e}")
            
            self.logger.info(f"子节点点击完成，成功 {success_count}/3 次")
            return success_count > 0
            
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
                screenshot = self.template_manager.take_screenshot(window_region)
            else:
                screenshot = self.template_manager.take_screenshot()
            
            if screenshot is None:
                return False
            
            # 查找节点
            node_pos = self.template_manager.find_template(
                screenshot, 
                node_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if node_pos is None:
                self.logger.warning(f"未找到节点模板: {node_template}")
                return False
            
            # 点击节点
            self.click_manager.click_at_position(node_pos[0], node_pos[1], window_region)
            
            # 等待界面更新
            time.sleep(0.5)
            
            # 重新截图查找网格按钮
            if window_region:
                screenshot = self.template_manager.take_screenshot(window_region)
            else:
                screenshot = self.template_manager.take_screenshot()
            
            # 查找网格按钮
            grid_pos = self.template_manager.find_template(
                screenshot,
                grid_template,
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if grid_pos is None:
                self.logger.warning("未找到网格按钮")
                return False
            
            # 点击网格按钮
            self.click_manager.click_at_position(grid_pos[0], grid_pos[1], window_region)
            
            return True
            
        except Exception as e:
            self.logger.error(f"执行点击操作失败: {e}")
            return False

    def setup_templates(self):
        """设置模板图片（需要用户手动截图）"""
        print("\n=== 模板设置向导 ===")
        print("请按照提示手动截取模板图片并保存到templates文件夹中")
        print(f"模板保存路径: {self.template_manager.templates_dir.absolute()}")
        print("\n需要的模板:")
        print("1. filter_icon.png - 筛选图标（漏斗形状）的截图")
        print("2. grid_menu_option.png - 下拉菜单中'网格'选项的截图")
        print("3. attachment_node.png - '附件'节点的截图")
        
        print("\n附件子节点模板:")
        attachment_subnodes = self.config_manager.get("attachment_subnodes", [])
        for i, node_name in enumerate(attachment_subnodes, 4):
            print(f"{i}. {node_name}.png - {node_name}子节点的截图")
        
        print("\n请手动创建这些模板文件后，按回车继续...")
        input()