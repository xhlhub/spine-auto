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
    
    def detect_attachment_node_state_with_confidence(self, screenshot) -> Tuple[Optional[str], Optional[Tuple[int, int]], float]:
        """
        通过比较置信度检测附件节点状态
        
        Args:
            screenshot: 屏幕截图
            
        Returns:
            (状态, 位置, 最高置信度) - 状态可能是 'open', 'close', 或 None
        """
        import cv2
        import numpy as np
        
        confidence_threshold = self.config_manager.get("confidence_threshold", 0.8)
        
        # 准备模板路径
        open_template_path = str(self.template_manager.templates_dir / "attachment_node_open.png")
        close_template_path = str(self.template_manager.templates_dir / "attachment_node.png")
        
        open_confidence = 0.0
        close_confidence = 0.0
        open_pos = None
        close_pos = None
        
        # 检测打开状态的置信度
        try:
            if self.template_manager.templates_dir.joinpath("attachment_node_open.png").exists():
                open_template = cv2.imread(open_template_path)
                if open_template is not None:
                    result = cv2.matchTemplate(screenshot, open_template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    open_confidence = max_val
                    if max_val >= confidence_threshold:
                        template_h, template_w = open_template.shape[:2]
                        open_pos = (max_loc[0] + template_w // 2, max_loc[1] + template_h // 2)
                        
        except Exception as e:
            self.logger.warning(f"检测打开状态失败: {e}")
        
        # 检测关闭状态的置信度
        try:
            if self.template_manager.templates_dir.joinpath("attachment_node.png").exists():
                close_template = cv2.imread(close_template_path)
                if close_template is not None:
                    result = cv2.matchTemplate(screenshot, close_template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    close_confidence = max_val
                    if max_val >= confidence_threshold:
                        template_h, template_w = close_template.shape[:2]
                        close_pos = (max_loc[0] + template_w // 2, max_loc[1] + template_h // 2)
                        
        except Exception as e:
            self.logger.warning(f"检测关闭状态失败: {e}")
        
        # 记录置信度信息
        self.logger.info(f"附件节点状态检测 - 打开状态置信度: {open_confidence:.3f}, 关闭状态置信度: {close_confidence:.3f}")
        
        # 比较置信度，选择更高的那个
        confidence_diff_threshold = self.config_manager.get("confidence_diff_threshold", 0.05)  # 置信度差异阈值
        
        if open_confidence > close_confidence + confidence_diff_threshold:
            # 打开状态的置信度明显更高
            if open_pos is not None:
                self.logger.info(f"节点状态判定为：打开 (置信度差异: {open_confidence - close_confidence:.3f})")
                return ('open', open_pos, open_confidence)
        elif close_confidence > open_confidence + confidence_diff_threshold:
            # 关闭状态的置信度明显更高
            if close_pos is not None:
                self.logger.info(f"节点状态判定为：关闭 (置信度差异: {close_confidence - open_confidence:.3f})")
                return ('close', close_pos, close_confidence)
        else:
            # 置信度差异不大，使用更保守的策略
            if max(open_confidence, close_confidence) >= confidence_threshold:
                if open_confidence >= close_confidence and open_pos is not None:
                    self.logger.info(f"节点状态判定为：打开 (置信度相近，选择打开: {open_confidence:.3f})")
                    return ('open', open_pos, open_confidence)
                elif close_pos is not None:
                    self.logger.info(f"节点状态判定为：关闭 (置信度相近，选择关闭: {close_confidence:.3f})")
                    return ('close', close_pos, close_confidence)
        
        self.logger.warning("无法确定附件节点状态")
        return (None, None, max(open_confidence, close_confidence))

    def click_attachment_node(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """点击附件节点并返回节点位置（只在节点为关闭状态时点击）"""
        self.logger.info("步骤3: 智能检查并点击附件节点")
        
        try:
            # 等待界面更新
            time.sleep(0.5)
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return None
            
            # 使用置信度比较检测节点状态
            state, position, confidence = self.detect_attachment_node_state_with_confidence(screenshot)
            
            if state is None:
                self.logger.warning("未找到附件节点或无法确定状态")
                return None
            elif state == 'open':
                self.logger.info(f"附件节点已经是打开状态，无需点击，位置: {position}，置信度: {confidence:.3f}")
                return position
            else:  # state == 'close'
                self.logger.info(f"附件节点是关闭状态，点击打开，位置: {position}，置信度: {confidence:.3f}")
                self.click_manager.click_at_position(position[0], position[1], window_region)
                
                if self.config_manager.get("debug_mode", False):
                    self.logger.info("附件节点点击完成，等待子节点展开...")
                    
                time.sleep(self.config_manager.get("operation_delay", 2.0))  # 等待子节点展开
                return position
            
        except Exception as e:
            self.logger.error(f"智能检查并点击附件节点失败: {e}")
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
                    # 点击子节点
                    self.click_manager.click_at_position(click_pos[0], click_pos[1], window_region)
                    success_count += 1
                    time.sleep(self.config_manager.get("click_delay", 5.0))
                    
                    # 在每次点击子节点后，执行4个依次的点击流程
                    self.logger.info(f"开始执行子节点 {i+1} 的网格操作流程")
                    
                    # 1. 点击勾选网格
                    if self.click_grid_check(window_region):
                        self.logger.info(f"子节点 {i+1}: 勾选网格成功")
                    else:
                        self.logger.warning(f"子节点 {i+1}: 勾选网格失败")
                    
                    # 2. 点击编辑网格
                    if self.click_grid_edit(window_region):
                        self.logger.info(f"子节点 {i+1}: 编辑网格成功")
                    else:
                        self.logger.warning(f"子节点 {i+1}: 编辑网格失败")
                    
                    # 3. 点击描绘
                    if self.click_grid_draw(window_region):
                        self.logger.info(f"子节点 {i+1}: 描绘成功")
                    else:
                        self.logger.warning(f"子节点 {i+1}: 描绘失败")
                    
                    # 4. 点击确定
                    if self.click_draw_sure(window_region):
                        self.logger.info(f"子节点 {i+1}: 确定成功")
                    else:
                        self.logger.warning(f"子节点 {i+1}: 确定失败")
                    
                    self.logger.info(f"子节点 {i+1} 的网格操作流程完成")
                    
                except Exception as e:
                    self.logger.warning(f"点击子节点 {i+1} 失败: {e}")
            
            self.logger.info(f"子节点点击完成，成功 {success_count}/3 次")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"点击子节点失败: {e}")
            return False
    
    def click_grid_check(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击勾选网格"""
        self.logger.info("执行操作: 点击勾选网格")
        
        try:
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            grid_check_template = str(self.template_manager.templates_dir / "grid_check.png")
            grid_check_pos = self.template_manager.find_template(
                screenshot, 
                grid_check_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if grid_check_pos is None:
                self.logger.warning("未找到勾选网格按钮")
                return False
            
            self.click_manager.click_at_position(
                grid_check_pos[0], grid_check_pos[1], 
                window_region
            )
            
            time.sleep(self.config_manager.get("click_delay", 5.0))
            return True
            
        except Exception as e:
            self.logger.error(f"点击勾选网格失败: {e}")
            return False
    
    def click_grid_edit(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击编辑网格"""
        self.logger.info("执行操作: 点击编辑网格")
        
        try:
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            grid_edit_template = str(self.template_manager.templates_dir / "grid_edit.png")
            grid_edit_pos = self.template_manager.find_template(
                screenshot, 
                grid_edit_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if grid_edit_pos is None:
                self.logger.warning("未找到编辑网格按钮")
                return False
            
            self.click_manager.click_at_position(
                grid_edit_pos[0], grid_edit_pos[1], 
                window_region
            )
            
            time.sleep(self.config_manager.get("click_delay", 5.0))
            return True
            
        except Exception as e:
            self.logger.error(f"点击编辑网格失败: {e}")
            return False
    
    def click_grid_draw(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击描绘按钮"""
        self.logger.info("执行操作: 点击描绘")
        
        try:
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            grid_draw_template = str(self.template_manager.templates_dir / "grid_draw.png")
            grid_draw_pos = self.template_manager.find_template(
                screenshot, 
                grid_draw_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if grid_draw_pos is None:
                self.logger.warning("未找到描绘按钮")
                return False
            
            self.click_manager.click_at_position(
                grid_draw_pos[0], grid_draw_pos[1], 
                window_region
            )
            
            time.sleep(self.config_manager.get("click_delay", 5.0))
            return True
            
        except Exception as e:
            self.logger.error(f"点击描绘失败: {e}")
            return False
    
    def click_draw_sure(self, window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击确定按钮"""
        self.logger.info("执行操作: 点击确定")
        
        try:
            screenshot = self.template_manager.take_screenshot(window_region)
            if screenshot is None:
                return False
            
            draw_sure_template = str(self.template_manager.templates_dir / "draw_sure.png")
            draw_sure_pos = self.template_manager.find_template(
                screenshot, 
                draw_sure_template, 
                self.config_manager.get("confidence_threshold", 0.8)
            )
            
            if draw_sure_pos is None:
                self.logger.warning("未找到确定按钮")
                return False
            
            self.click_manager.click_at_position(
                draw_sure_pos[0], draw_sure_pos[1], 
                window_region
            )
            
            time.sleep(self.config_manager.get("click_delay", 5.0))
            return True
            
        except Exception as e:
            self.logger.error(f"点击确定失败: {e}")
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