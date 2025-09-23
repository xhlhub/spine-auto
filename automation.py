#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化流程模块

包含run_automation相关的核心自动化流程
"""

import time
import logging
from datetime import datetime
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
            self.logger.error("系统权限检查失败，请配置权限后重试")
            print("\n❌ 权限检查失败!")
            
            import platform
            if platform.system() == "Darwin":
                print("请按以下步骤配置macOS权限:")
                print("1. 打开 系统偏好设置 > 安全性与隐私 > 隐私")
                print("2. 选择左侧的 '辅助功能'")
                print("3. 点击锁图标并输入密码")
                print("4. 添加并勾选你的终端应用程序 (如 Terminal 或 iTerm)")
                print("5. 重新运行此脚本")
            elif platform.system() == "Windows":
                print("请按以下步骤配置Windows权限:")
                print("1. 建议以管理员权限运行此脚本")
                print("2. 确保Windows Defender或其他安全软件没有阻止脚本")
                print("3. 如果使用杀毒软件，请将此脚本添加到白名单")
                print("4. 重新运行此脚本")
            else:
                print("请确保有足够的系统权限运行此脚本")
            
            return
        else:
            self.logger.info("✅ 系统权限检查通过")
        
        # 步骤0.5: 先查找Spine窗口，再决定是否需要激活
        window_info = self.window_manager.find_spine_window()
        print(f"查找窗口结果: {window_info}")
        
        if window_info:
            self.logger.info(f"✅ 找到Spine窗口: {window_info}")
            
            # 根据找到的具体窗口信息进行精确激活
            window_title = window_info.get('title')
            app_name = window_info.get('app_name')
            window_region = window_info.get('region')  # 用于后续截图操作
            
            if window_title:
                self.logger.info(f"🔄 激活找到的Spine窗口: '{window_title}'")
                if self.window_manager.activate_window_by_title(window_title, app_name):
                    self.logger.info("✅ Spine窗口已精确激活")
                else:
                    self.logger.warning("⚠️ 精确激活失败，尝试通用激活方法")
                    if not self.activate_spine_application():
                        self.logger.warning("⚠️ 通用激活也失败，但将继续执行（可能影响截图效果）")
            else:
                self.logger.warning("⚠️ 窗口信息不完整，使用通用激活方法")
                if not self.activate_spine_application():
                    self.logger.warning("⚠️ 窗口激活失败，但将继续执行（可能影响截图效果）")
        else:
            self.logger.warning("❌ 未找到Spine窗口")
            print("⚠️  未找到Spine应用窗口")
            print("请确保：")
            print("1. Spine应用已经启动")
            print("2. Spine应用窗口可见（未最小化）")
            print("3. 窗口标题包含'Spine'相关字样")
            
            # 尝试激活，也许用户忘记启动了应用
            print("🔄 尝试激活Spine应用...")
            if self.activate_spine_application():
                self.logger.info("✅ 应用激活成功，重新查找窗口")
                # 重新查找窗口
                window_info = self.window_manager.find_spine_window()
                if window_info:
                    self.logger.info(f"✅ 重新找到Spine窗口: {window_info}")
                    window_region = window_info.get('region')  # 更新窗口区域
                else:
                    self.logger.warning("⚠️ 激活后仍未找到窗口，将使用全屏操作")
                    window_region = None
            else:
                self.logger.info("ℹ️ 未找到Spine窗口，将使用全屏操作")
                window_region = None
        
        # 检查必需的模板文件
        required_templates = [
            "img_filter_icon.png",
            "img_menu_option.png", 
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
            #图片勾选☑️网格流程
            self.logger.info("🔄 开始执行图片勾选网格流程...")

            # 步骤1: 点击筛选图标
            self.logger.info("📍 阶段1: 准备点击筛选图标（图像处理模式）")
            if not self.click_filter_icon(window_region, isImgProcess=True):
                self.logger.error("❌ 图像处理模式 - 点击筛选图标失败")
                return
            
            # 阶段间隔等待
            inter_step_delay = 2.0
            self.logger.info(f"⏳ 阶段间隔等待 ({inter_step_delay}秒)，确保界面完全响应...")
            time.sleep(inter_step_delay)
            
            # 步骤2: 点击网格菜单选项
            self.logger.info("📍 阶段2: 准备点击网格菜单选项（图像处理模式）")
            if not self.click_grid_menu_option(window_region, isImgProcess=True):
                self.logger.error("❌ 图像处理模式 - 点击网格菜单选项失败")
                return
            
            # 步骤3: 点击附件节点
            attachment_pos = self.click_attachment_node(window_region, isImgProcess=True)
            if attachment_pos is None:
                self.logger.error("点击附件节点失败")
                return
            
            # 步骤4: 循环点击附件子节点
            self.process_attachment_subnodes(attachment_pos, window_region, isImgProcess=True)
            
            self.logger.info("✅ 图片勾选网格流程完成")
            
            # 两个主要流程之间的间隔
            # workflow_gap_delay = 5.0
            # self.logger.info(f"🔄 准备切换到网格编辑流程，等待 ({workflow_gap_delay}秒)...")
            # time.sleep(workflow_gap_delay)

            #网格编辑流程
            self.logger.info("🔄 开始执行网格编辑流程...")
            
            # 步骤1: 点击筛选图标
            self.logger.info("📍 阶段1: 准备点击筛选图标（网格编辑模式）")
            if not self.click_filter_icon(window_region, isImgProcess=False):
                self.logger.error("❌ 网格编辑模式 - 点击筛选图标失败")
                return
            
            # 阶段间隔等待
            # inter_step_delay = 2.0
            # self.logger.info(f"⏳ 阶段间隔等待 ({inter_step_delay}秒)，确保界面完全响应...")
            # time.sleep(inter_step_delay)
            
            # 步骤2: 点击网格菜单选项
            self.logger.info("📍 阶段2: 准备点击网格菜单选项（网格编辑模式）")
            if not self.click_grid_menu_option(window_region, isImgProcess=False):
                self.logger.error("❌ 网格编辑模式 - 点击网格菜单选项失败")
                return
            
            # 步骤3: 点击附件节点
            attachment_pos = self.click_attachment_node(window_region, isImgProcess=False)
            if attachment_pos is None:
                self.logger.error("点击附件节点失败")
                return
            
            # 步骤4: 循环点击附件子节点
            self.process_attachment_subnodes(attachment_pos, window_region, isImgProcess=False)            
            
            self.logger.info("✅ 网格编辑流程完成")
            self.logger.info("🎉 所有自动化流程执行完成")
            
        except Exception as e:
            self.logger.error(f"❌ 自动化流程执行失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
        
        self.logger.info("🏁 自动化流程结束")
    
    def activate_spine_application(self) -> bool:
        """
        激活Spine应用窗口（Windows上特别重要，解决截图黑屏问题）
        
        Returns:
            bool: 激活成功返回True，失败返回False
        """
        import platform
        
        self.logger.info("正在激活Spine应用窗口...")
        
        try:
            # 使用WindowManager的激活方法
            success = self.window_manager.activate_spine_window()
            
            if success:
                self.logger.info("✅ Spine应用窗口激活成功")
                
                # 在Windows上添加额外的延时确保窗口完全激活
                if platform.system() == "Windows":
                    self.logger.info("Windows系统检测到，等待2秒确保窗口完全激活...")
                    print("⏳ 正在等待Spine应用完全激活（2秒）...")
                    time.sleep(2.0)
                    self.logger.info("✅ 窗口激活等待完成")
                else:
                    # 其他系统等待较短时间
                    time.sleep(2.0)
                
                return True
            else:
                self.logger.warning("❌ Spine应用窗口激活失败")
                
                # 在Windows上，即使激活失败也等待一段时间，给用户手动切换的机会
                if platform.system() == "Windows":
                    self.logger.info("Windows系统上建议手动切换到Spine应用")
                    print("⚠️  无法自动激活Spine应用")
                    print("请手动切换到Spine应用窗口，脚本将在10秒后继续...")
                    time.sleep(10.0)
                
                return False
                
        except Exception as e:
            self.logger.error(f"激活Spine应用时发生错误: {e}")
            
            # 发生错误时，在Windows上也给用户手动切换的机会
            if platform.system() == "Windows":
                print("⚠️  激活Spine应用时发生错误")
                print("请手动切换到Spine应用窗口，脚本将在10秒后继续...")
                time.sleep(10.0)
            
            return False
    
    def click_filter_icon(self, window_region: Optional[Tuple[int, int, int, int]] = None, isImgProcess: bool = False) -> bool:
        """点击筛选图标"""
        import os
        from datetime import datetime
        
        mode_str = "图像处理模式" if isImgProcess else "网格编辑模式"
        self.logger.info(f"步骤1: 点击筛选图标 ({mode_str})")
        
        try:
            # 记录截图前的状态
            self.logger.info(f"📸 准备截图 - 模式: {mode_str}, 时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            
            screenshot = self.template_manager.take_screenshot(window_region,"filter_icon")
            if screenshot is None:
                self.logger.error("❌ 截图失败，无法继续")
                return False
            
            self.logger.info(f"✅ 截图成功，尺寸: {screenshot.shape}")
            
            # 选择对应的模板文件
            if isImgProcess:
                filter_template = str(self.template_manager.templates_dir / "img_filter_icon.png")
                template_type = "img_filter_icon.png"
            else:
                filter_template = str(self.template_manager.templates_dir / "grid_filter_icon.png")
                template_type = "grid_filter_icon.png"
            
            # 检查模板文件是否存在
            if not os.path.exists(filter_template):
                self.logger.error(f"❌ 模板文件不存在: {filter_template}")
                return False
            
            self.logger.info(f"🔍 使用模板文件: {template_type}")
            
            confidence_threshold = self.config_manager.get("confidence_threshold", 0.8)
            self.logger.info(f"🎯 置信度阈值: {confidence_threshold}")

            filter_pos = self.template_manager.find_template(
                screenshot, 
                filter_template, 
                confidence_threshold
            )
            
            if filter_pos is None:
                self.logger.warning(f"⚠️ 未找到筛选图标，模板: {template_type}")
                self.logger.info("💡 建议检查：1) 模板图片是否准确 2) 界面状态是否正确 3) 置信度阈值是否过高")
                return False
            
            self.logger.info(f"🎯 找到筛选图标位置: ({filter_pos[0]}, {filter_pos[1]})")
            
            # 点击前记录状态
            self.logger.info(f"👆 即将点击筛选图标 - 坐标: ({filter_pos[0]}, {filter_pos[1]})")
            
            # 使用配置中的点击方式
            self.click_manager.click_at_position(
                filter_pos[0], filter_pos[1], 
                window_region
            )
            
            self.logger.info("✅ 筛选图标点击完成")
            
            # 等待界面响应
            initial_wait = 1.0  # 初始等待时间
            self.logger.info(f"⏳ 初始等待界面响应 ({initial_wait}秒)...")
            time.sleep(initial_wait)
            
            # 验证点击效果 - 检查下拉菜单是否出现
            self.logger.info("🔍 验证点击效果：检查下拉菜单是否出现...")
            
            verification_success = self._verify_dropdown_menu_appeared(window_region, mode_str)
            
            if verification_success:
                self.logger.info("✅ 验证成功：下拉菜单已出现")
            else:
                self.logger.warning("⚠️ 验证失败：下拉菜单可能未出现，但继续执行流程")
                self.logger.info("💡 尝试增加等待时间...")
                time.sleep(2.0)  # 额外等待时间给Spine渲染
            
            # 额外等待时间确保界面稳定
            remaining_delay = self.config_manager.get("click_delay", 5.0) - initial_wait
            if remaining_delay > 0:
                self.logger.info(f"⏳ 等待界面稳定 ({remaining_delay}秒)...")
                time.sleep(remaining_delay)
            
            self.logger.info(f"🏁 筛选图标点击流程完成 - 模式: {mode_str}, 验证结果: {'成功' if verification_success else '失败'}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 点击筛选图标失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def _verify_dropdown_menu_appeared(self, window_region: Optional[Tuple[int, int, int, int]] = None, mode_str: str = "") -> bool:
        """
        验证下拉菜单是否出现（Spine应用优化版）
        
        Args:
            window_region: 窗口区域
            mode_str: 模式字符串（用于日志）
            
        Returns:
            bool: 菜单出现返回True，否则返回False
        """
        import os
        
        try:
            self.logger.info("🔍 开始验证下拉菜单状态（Spine优化模式）...")
            
            # 多次尝试截图，以应对Spine的渲染特性
            verification_screenshots = []
            for attempt in range(3):
                self.logger.info(f"📷 截图尝试 {attempt + 1}/3...")
                
                # 每次截图前稍作等待
                time.sleep(0.3 * (attempt + 1))  # 0.3s, 0.6s, 0.9s
                
                screenshot = self.template_manager.take_screenshot(window_region, f"verification_{mode_str}_attempt_{attempt}")
                if screenshot is not None:
                    verification_screenshots.append(screenshot)
                    self.logger.info(f"  ✅ 截图{attempt + 1}成功，尺寸: {screenshot.shape}")
                else:
                    self.logger.warning(f"  ❌ 截图{attempt + 1}失败")
            
            if not verification_screenshots:
                self.logger.warning("❌ 所有验证截图都失败")
                return False
            
            # 准备检查的模板
            templates_to_check = []
            
            # 根据模式添加对应模板
            if "图像处理" in mode_str:
                img_template = str(self.template_manager.templates_dir / "img_menu_option.png")
                if os.path.exists(img_template):
                    templates_to_check.append(("img_menu_option.png", img_template))
            else:
                grid_template = str(self.template_manager.templates_dir / "grid_menu_option.png")
                if os.path.exists(grid_template):
                    templates_to_check.append(("grid_menu_option.png", grid_template))
            
            # 也检查通用菜单元素
            common_menu_template = str(self.template_manager.templates_dir / "dropdown_menu.png")
            if os.path.exists(common_menu_template):
                templates_to_check.append(("dropdown_menu.png", common_menu_template))
            
            if not templates_to_check:
                self.logger.warning("⚠️ 没有找到用于验证的菜单模板文件")
                return False
            
            # 使用多个置信度阈值尝试
            confidence_thresholds = [
                self.config_manager.get("confidence_threshold", 0.8),
                0.7,  # 降低置信度
                0.6   # 进一步降低
            ]
            
            # 在每张截图上，用每个模板，用每个置信度阈值尝试
            for screenshot_idx, screenshot in enumerate(verification_screenshots):
                self.logger.info(f"🔍 在截图{screenshot_idx + 1}上检测菜单...")
                
                for template_name, template_path in templates_to_check:
                    for threshold in confidence_thresholds:
                        self.logger.info(f"  🎯 模板: {template_name}, 置信度: {threshold}")
                        
                        menu_pos = self.template_manager.find_template(
                            screenshot,
                            template_path,
                            threshold
                        )
                        
                        if menu_pos is not None:
                            self.logger.info(f"✅ 找到菜单元素: {template_name} 位置: {menu_pos} (置信度: {threshold})")
                            return True
                        else:
                            self.logger.info(f"    ❌ 未匹配")
            
            self.logger.warning("⚠️ 在所有截图和置信度下都未找到菜单元素")
            
            # 最后的尝试：保存验证截图供手动检查到logs目录
            if verification_screenshots:
                # 确保logs目录存在
                from pathlib import Path
                logs_dir = Path("logs")
                logs_dir.mkdir(exist_ok=True)
                debug_path = logs_dir / f"debug_verification_{mode_str}_{datetime.now().strftime('%H%M%S')}.png"
                import cv2
                cv2.imwrite(str(debug_path), verification_screenshots[-1])
                self.logger.info(f"💡 调试截图已保存到logs目录: {debug_path}")
                self.logger.info("💡 建议手动检查此截图，确认菜单是否真的显示")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 验证下拉菜单时出错: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def _verify_grid_view_appeared(self, window_region: Optional[Tuple[int, int, int, int]] = None, mode_str: str = "") -> bool:
        """
        验证网格视图是否出现
        
        Args:
            window_region: 窗口区域
            mode_str: 模式字符串（用于日志）
            
        Returns:
            bool: 网格视图出现返回True，否则返回False
        """
        import os
        
        try:
            self.logger.info("🔍 开始验证网格视图状态...")
            
            # 截图检查网格视图状态
            verification_screenshot = self.template_manager.take_screenshot(window_region, f"grid_verification_{mode_str}")
            if verification_screenshot is None:
                self.logger.warning("❌ 网格视图验证截图失败")
                return False
            
            self.logger.info(f"📸 网格视图验证截图成功，尺寸: {verification_screenshot.shape}")
            
            # 检查可能的网格视图指示器
            templates_to_check = []
            
            # 检查附件节点（网格视图应该显示附件节点）
            attachment_template = str(self.template_manager.templates_dir / "attachment_node.png")
            if os.path.exists(attachment_template):
                templates_to_check.append(("attachment_node.png", attachment_template))
            
            # 检查网格相关的UI元素
            if "图像处理" in mode_str:
                grid_check_template = str(self.template_manager.templates_dir / "grid_check.png")
                if os.path.exists(grid_check_template):
                    templates_to_check.append(("grid_check.png", grid_check_template))
            else:
                grid_edit_template = str(self.template_manager.templates_dir / "grid_edit.png")
                if os.path.exists(grid_edit_template):
                    templates_to_check.append(("grid_edit.png", grid_edit_template))
            
            # 检查通用网格视图指示器
            grid_view_template = str(self.template_manager.templates_dir / "grid_view_indicator.png")
            if os.path.exists(grid_view_template):
                templates_to_check.append(("grid_view_indicator.png", grid_view_template))
            
            if not templates_to_check:
                self.logger.warning("⚠️ 没有找到用于验证网格视图的模板文件")
                # 尝试基本的像素差异检测
                return self._verify_interface_changed(verification_screenshot)
            
            confidence_threshold = self.config_manager.get("confidence_threshold", 0.8)
            
            # 检查每个模板
            found_count = 0
            for template_name, template_path in templates_to_check:
                self.logger.info(f"🔍 检查网格视图元素: {template_name}")
                
                element_pos = self.template_manager.find_template(
                    verification_screenshot,
                    template_path,
                    confidence_threshold
                )
                
                if element_pos is not None:
                    self.logger.info(f"✅ 找到网格视图元素: {template_name} 位置: {element_pos}")
                    found_count += 1
                else:
                    self.logger.info(f"❌ 未找到网格视图元素: {template_name}")
            
            # 如果找到任何一个元素，认为网格视图已出现
            if found_count > 0:
                self.logger.info(f"✅ 网格视图验证成功，找到 {found_count} 个相关元素")
                return True
            else:
                self.logger.warning("⚠️ 未找到网格视图相关元素")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 验证网格视图时出错: {e}")
            return False
    
    def _verify_interface_changed(self, current_screenshot) -> bool:
        """
        通过比较截图验证界面是否发生变化（备用验证方法）
        
        Args:
            current_screenshot: 当前截图
            
        Returns:
            bool: 界面发生变化返回True
        """
        try:
            self.logger.info("🔍 使用备用方法：检测界面变化...")
            
            # 这里可以实现更复杂的界面变化检测逻辑
            # 目前先返回True，假设界面已变化
            self.logger.info("ℹ️ 备用验证方法暂时返回True（假设界面已变化）")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 备用验证方法出错: {e}")
            return False
    
    def click_grid_menu_option(self, window_region: Optional[Tuple[int, int, int, int]] = None, isImgProcess: bool = False) -> bool:
        """点击下拉菜单中的网格选项"""
        import os
        from datetime import datetime
        
        mode_str = "图像处理模式" if isImgProcess else "网格编辑模式"
        self.logger.info(f"步骤2: 点击网格菜单选项 ({mode_str})")
        
        try:
            # 等待下拉菜单出现
            menu_wait_time = 0.5
            self.logger.info(f"⏳ 等待下拉菜单出现 ({menu_wait_time}秒)...")
            time.sleep(menu_wait_time)
            
            # 记录截图前的状态  
            self.logger.info(f"📸 准备截图网格菜单 - 模式: {mode_str}, 时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            
            screenshot = self.template_manager.take_screenshot(window_region, "grid_menu_option")
            if screenshot is None:
                self.logger.error("❌ 网格菜单截图失败，无法继续")
                return False
            
            self.logger.info(f"✅ 网格菜单截图成功，尺寸: {screenshot.shape}")
            
            # 选择对应的模板文件
            if isImgProcess:
                grid_menu_template = str(self.template_manager.templates_dir / "img_menu_option.png")
                template_type = "img_menu_option.png"
            else:
                grid_menu_template = str(self.template_manager.templates_dir / "grid_menu_option.png")
                template_type = "grid_menu_option.png"
            
            # 检查模板文件是否存在
            if not os.path.exists(grid_menu_template):
                self.logger.error(f"❌ 模板文件不存在: {grid_menu_template}")
                return False
            
            self.logger.info(f"🔍 使用模板文件: {template_type}")
            
            confidence_threshold = self.config_manager.get("confidence_threshold", 0.8)
            self.logger.info(f"🎯 置信度阈值: {confidence_threshold}")

            grid_pos = self.template_manager.find_template(
                screenshot, 
                grid_menu_template, 
                confidence_threshold
            )
            
            if grid_pos is None:
                self.logger.warning(f"⚠️ 未找到网格菜单选项，模板: {template_type}")
                self.logger.info("💡 建议检查：1) 下拉菜单是否已展开 2) 模板图片是否准确 3) 界面状态是否正确")
                return False
            
            self.logger.info(f"🎯 找到网格菜单选项位置: ({grid_pos[0]}, {grid_pos[1]})")
            
            # 点击前记录状态
            self.logger.info(f"👆 即将点击网格菜单选项 - 坐标: ({grid_pos[0]}, {grid_pos[1]})")
            
            self.click_manager.click_at_position(
                grid_pos[0], grid_pos[1], 
                window_region
            )
            
            self.logger.info("✅ 网格菜单选项点击完成")
            
            # 等待界面响应
            initial_wait = 1.0
            self.logger.info(f"⏳ 初始等待界面更新 ({initial_wait}秒)...")
            time.sleep(initial_wait)
            
            # 验证点击效果 - 检查界面是否切换到网格视图
            self.logger.info("🔍 验证点击效果：检查界面是否切换到网格视图...")
            verification_success = self._verify_grid_view_appeared(window_region, mode_str)
            
            if verification_success:
                self.logger.info("✅ 验证成功：界面已切换到网格视图")
            else:
                self.logger.warning("⚠️ 验证失败：界面可能未切换到网格视图，但继续执行流程")
            
            # 额外等待时间确保界面稳定
            remaining_delay = self.config_manager.get("click_delay", 5.0) - initial_wait
            if remaining_delay > 0:
                self.logger.info(f"⏳ 等待界面稳定 ({remaining_delay}秒)...")
                time.sleep(remaining_delay)
            
            self.logger.info(f"🏁 网格菜单选项点击流程完成 - 模式: {mode_str}, 验证结果: {'成功' if verification_success else '失败'}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 点击网格菜单选项失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
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

    def click_attachment_node(self, window_region: Optional[Tuple[int, int, int, int]] = None, isImgProcess: bool = False) -> Optional[Tuple[int, int]]:
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
                self.logger.warning("未找到附件节点，尝试调整鼠标位置和滚动后重试")
                
                try:
                    import pyautogui
                    
                    # 获取当前鼠标位置
                    current_x, current_y = pyautogui.position()
                    self.logger.info(f"当前鼠标位置: ({current_x}, {current_y})")
                    
                    # 将鼠标位置左移80*dpr
                    new_x = current_x - int(100 * self.click_manager.dpr)
                    self.logger.info(f"将鼠标左移至: ({new_x}, {current_y})")
                    pyautogui.moveTo(new_x, current_y, duration=0.3)
                    
                    # 滚动条滚动到最上面（使用较大的正数进行多次向上滚动）
                    self.logger.info("滚动到最上面")
                    limit = 10 if isImgProcess else 100
                    for _ in range(limit):  # 连续向上滚动10次确保到达顶部
                        pyautogui.scroll(1, x=new_x, y=current_y)
                        time.sleep(0.1)
                    
                    # 等待滚动完成
                    time.sleep(0.5)
                    
                    # 重新截图并检测
                    screenshot = self.template_manager.take_screenshot(window_region)
                    if screenshot is None:
                        self.logger.error("重新截图失败")
                        return None
                        
                    # 再次尝试检测附件节点状态
                    state, position, confidence = self.detect_attachment_node_state_with_confidence(screenshot)
                    
                    if state is None:
                        self.logger.warning("调整位置和滚动后仍未找到附件节点，返回当前鼠标位置继续执行")
                        # 获取当前鼠标位置作为返回位置
                        current_x, current_y = pyautogui.position()
                        fallback_position = (new_x - 60, current_y)
                        # 设置假定状态为已打开，置信度为1
                        state = 'open'
                        position = fallback_position
                        confidence = 1.0
                        self.logger.info(f"使用fallback位置: {position}，假定状态: {state}，置信度: {confidence}")
                        return position
                    else:
                        self.logger.info(f"调整后成功找到附件节点，状态: {state}，位置: {position}，置信度: {confidence:.3f}")
                        
                except Exception as e:
                    self.logger.error(f"调整鼠标位置和滚动时发生错误: {e}")
                    return None
            
            # 如果state仍然是None（调整后仍未找到），则退出
            if state is None:
                return None
                
            if state == 'open':
                self.logger.info(f"附件节点已经是打开状态，无需点击，位置: {position}，置信度: {confidence:.3f}")
                return position
            elif state == 'close':
                self.logger.info(f"附件节点是关闭状态，点击打开，位置: {position}，置信度: {confidence:.3f}")
                self.click_manager.click_at_position(position[0], position[1], window_region)
                
                if self.config_manager.get("debug_mode", False):
                    self.logger.info("附件节点点击完成，等待子节点展开...")
                    
                time.sleep(self.config_manager.get("operation_delay", 2.0))  # 等待子节点展开
                return position
            
        except Exception as e:
            self.logger.error(f"智能检查并点击附件节点失败: {e}")
            return None
    
    def process_attachment_subnodes(self, attachment_pos: Tuple[int, int], window_region: Optional[Tuple[int, int, int, int]] = None, isImgProcess: bool = False):
        """处理附件子节点"""
        mode_str = "图像处理模式" if isImgProcess else "网格编辑模式"
        self.logger.info(f"步骤4: 开始处理附件子节点 ({mode_str})")
        
        if isImgProcess:
            success = self.click_subnode_img(attachment_pos, window_region)
        else:
            success = self.click_subnode_grid(attachment_pos, window_region)
        
        if success:
            self.logger.info(f"成功处理附件子节点 ({mode_str})")
        else:
            self.logger.warning(f"处理附件子节点失败 ({mode_str})")
    
    def click_subnode_img(self, attachment_pos: Tuple[int, int], window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """点击子节点 - 图像处理模式（点击第一个子节点，执行Ctrl+A全选，然后勾选网格）"""
        try:
            node_height = self.config_manager.get("node_height", 20)
            
            # 计算第一个子节点的y坐标
            current_y = attachment_pos[1] + node_height * self.click_manager.dpr
            click_pos = (attachment_pos[0], current_y)
            
            self.logger.info(f"[图像处理模式] 点击第一个子节点，坐标: ({click_pos[0]}, {click_pos[1]})")
            
            # 点击第一个子节点
            self.click_manager.click_at_position(click_pos[0], click_pos[1], window_region)
            time.sleep(self.config_manager.get("click_delay", 5.0))
            
            self.logger.info("第一次点击子节点后，增加Ctrl+A全选操作")
            
            # 执行Ctrl+A全选
            if self.click_manager.select_all():
                self.logger.info("✅ Ctrl+A全选操作成功")
            else:
                self.logger.warning("⚠️ Ctrl+A全选操作失败")
            
            # 延时1秒
            self.logger.info("延时1秒后执行勾选网格操作")
            time.sleep(1.0)
            
            # 执行勾选网格操作
            self.logger.info("开始执行勾选网格操作")
            grid_check_result = self.click_grid_check(window_region)
            
            if grid_check_result:
                self.logger.info("✅ 勾选网格操作成功")
                self.logger.info("🎉 图像处理模式任务完成")
                return True
            else:
                self.logger.warning("❌ 勾选网格操作失败")
                return False
                
        except Exception as e:
            self.logger.error(f"[图像处理模式] 点击子节点失败: {e}")
            return False
    
    def click_subnode_grid(self, attachment_pos: Tuple[int, int], window_region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """循环点击子节点 - 网格编辑模式（执行完整的网格操作流程）"""
        try:
            node_height = self.config_manager.get("node_height", 20)
            success_count = 0
            consecutive_failures = 0  # 连续失败计数器
            i = 0  # 循环计数器
            end_scroll_offset = 0
            end_scroll_i = 0
            should_scroll = True
            # 循环直到连续失败
            while consecutive_failures < 1:
                if(i <= 9):
                    current_y = attachment_pos[1] + (i + 1) * node_height * self.click_manager.dpr
                else:
                    if(should_scroll):

                        if (i - 9) % 3 == 0:
                            self.logger.info(f"[网格编辑模式] 第 {i+1} 次点击，需要滚动")
                            scroll_success = self.click_manager.scroll_down(attachment_pos[0], attachment_pos[1], window_region)
                            if scroll_success:
                                self.logger.info("滚动成功，点击位置")
                            else:
                                self.logger.warning("滚动失败，改为点击位置递增")
                                should_scroll = False
                                end_scroll_offset = (i % 3)
                            current_y = attachment_pos[1] + ((i % 3) + 9) * node_height * self.click_manager.dpr
                        else:
                            current_y = attachment_pos[1] + ((i % 3) + 1 + 9) * node_height * self.click_manager.dpr
                            
                    else:

                        end_scroll_i+=1
                        current_y = attachment_pos[1] + (end_scroll_i  + end_scroll_offset) * node_height * self.click_manager.dpr
                click_pos = (attachment_pos[0], current_y)
                
                try:
                    # 点击子节点
                    self.click_manager.click_at_position(click_pos[0], click_pos[1], window_region)
                    success_count += 1
                    time.sleep(self.config_manager.get("click_delay", 5.0))
                    
                    self.logger.info(f"开始执行子节点 {i+1} 的完整网格操作流程")
                    
                    # 网格编辑模式: 执行完整的网格操作流程
                    self.logger.info(f"子节点 {i+1}: 执行完整网格操作模式")
                    # 2. 点击编辑网格
                    if self.click_grid_edit(window_region):
                        self.logger.info(f"子节点 {i+1}: 编辑网格成功")
                        
                        # 3. 点击描绘
                        if self.click_grid_draw(window_region):
                            self.logger.info(f"子节点 {i+1}: 描绘成功")
                            
                            # 4. 点击确定
                            if self.click_draw_sure(window_region):
                                self.logger.info(f"子节点 {i+1}: 确定成功")
                                self.logger.info(f"子节点 {i+1} 的完整网格操作流程完成")
                                consecutive_failures = 0  # 重置连续失败计数器
                            else:
                                self.logger.warning(f"子节点 {i+1}: 确定失败，流程中断")
                                consecutive_failures += 1
                        else:
                            self.logger.warning(f"子节点 {i+1}: 描绘失败，流程中断")
                            consecutive_failures += 1
                    else:
                        self.logger.warning(f"子节点 {i+1}: 编辑网格失败，流程中断")
                        consecutive_failures += 1  # 增加连续失败计数
                        self.logger.info(f"连续失败次数: {consecutive_failures}/1")
                    
                except Exception as e:
                    self.logger.warning(f"[网格编辑模式] 点击子节点 {i+1} 失败: {e}")
                    consecutive_failures += 1  # 异常也算作失败
                    self.logger.info(f"连续失败次数: {consecutive_failures}/1")
                
                i += 1  # 增加循环计数器
            
            self.logger.info(f"[网格编辑模式] 子节点点击完成，总共尝试 {i} 次，成功 {success_count} 次，使用新的滚动模式（i=0-8位置递增，i=9/12/15等滚动并点击位置9，其他位置递增），因连续失败而终止")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"[网格编辑模式] 点击子节点失败: {e}")
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
        print(f"请按照提示手动截取模板图片并保存到{self.template_manager.templates_dir.name}文件夹中")
        print(f"模板保存路径: {self.template_manager.templates_dir.absolute()}")
        print("\n需要的模板:")
        print("1. img_filter_icon.png - 筛选图标（漏斗形状）的截图")
        print("2. img_menu_option.png - 下拉菜单中'网格'选项的截图")
        print("3. attachment_node.png - '附件'节点的截图")
        
        
        print("\n请手动创建这些模板文件后，按回车继续...")
        input()
    
    def run_diagnostic_report(self):
        """运行诊断报告，帮助用户理解问题所在"""
        print("\n" + "="*60)
        print("🔍 SPINE自动化诊断报告")
        print("="*60)
        
        self.logger.info("开始生成诊断报告...")
        
        # 检查模板文件
        self._check_template_files()
        
        # 检查配置
        self._check_configuration()
        
        # 检查权限
        self._check_system_permissions()
        
        # 提供解决方案建议
        self._provide_solutions()
        
        print("="*60)
        print("📋 诊断报告完成")
        print("="*60)
    
    def _check_template_files(self):
        """检查模板文件状态"""
        print("\n📁 模板文件检查:")
        
        required_templates = {
            "图像处理模式": ["img_filter_icon.png", "img_menu_option.png"],
            "网格编辑模式": ["grid_filter_icon.png", "grid_menu_option.png"],
            "通用模板": ["attachment_node.png", "grid_check.png", "grid_edit.png", "grid_draw.png", "draw_sure.png"]
        }
        
        for category, templates in required_templates.items():
            print(f"\n  {category}:")
            for template in templates:
                template_path = self.template_manager.templates_dir / template
                if template_path.exists():
                    file_size = template_path.stat().st_size
                    print(f"    ✅ {template} (大小: {file_size} bytes)")
                else:
                    print(f"    ❌ {template} - 文件缺失")
    
    def _check_configuration(self):
        """检查配置状态"""
        print("\n⚙️  配置检查:")
        
        key_configs = [
            ("confidence_threshold", "置信度阈值"),
            ("click_delay", "点击延迟"),
            ("debug_mode", "调试模式"),
            ("operation_delay", "操作延迟")
        ]
        
        for key, desc in key_configs:
            value = self.config_manager.get(key, "未设置")
            print(f"    {desc}: {value}")
    
    def _check_system_permissions(self):
        """检查系统权限"""
        print("\n🔐 系统权限检查:")
        
        has_permission = self.window_manager.check_accessibility_permissions()
        if has_permission:
            print("    ✅ 系统权限正常")
        else:
            print("    ❌ 系统权限不足")
    
    def _provide_solutions(self):
        """提供解决方案建议"""
        print("\n💡 常见问题解决方案:")
        
        print("\n  🔸 如果截图完全一样:")
        print("    1. 检查筛选图标模板是否正确")
        print("    2. 确认点击后界面确实发生了变化")
        print("    3. 增加操作间隔时间")
        print("    4. 检查置信度阈值设置")
        
        print("\n  🔸 如果找不到模板:")
        print("    1. 重新截取更精确的模板图片")
        print("    2. 降低置信度阈值 (如从0.8改为0.7)")
        print("    3. 确保模板图片包含独特特征")
        
        print("\n  🔸 如果权限问题:")
        print("    1. Windows: 以管理员身份运行")
        print("    2. macOS: 在系统偏好设置中添加辅助功能权限")
        print("    3. 检查防病毒软件是否阻止")
        
        print("\n请手动创建这些模板文件后，按回车继续...")
        input()