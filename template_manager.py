#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理器模块

处理模板匹配、图像处理和模板质量分析
"""

import cv2
import numpy as np
import os
import logging
import datetime
import pyautogui
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


class TemplateManager:
    """模板管理器类"""
    
    def __init__(self, config_manager):
        """
        初始化模板管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.templates_dir = Path("templates")
        self.templates_dir.mkdir(exist_ok=True)
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None, name: Optional[str] = None) -> np.ndarray:
        """
        截取屏幕或指定区域
        
        Args:
            region: 截图区域 (x, y, width, height)
            name: 截图名称（用于调试）
            
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

            # 新增：将截图保存为本地图片，文件名带时间戳（调试模式下）
            # if self.config_manager.get("debug_mode", False) and name:
            #     timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            #     save_path = f"screenshot_{name}_{timestamp}.png"
            #     cv2.imwrite(save_path, screenshot_cv)
            #     self.logger.info(f"截图已保存到本地: {save_path}")

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
            if self.config_manager.get("adaptive_confidence", True):
                confidence = self._adjust_confidence(template_path, confidence)
            
            # 根据配置选择匹配算法
            algorithm = self.config_manager.get("matching_algorithm", "enhanced")
            
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
        print("confidence: " + str(confidence))
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
        if self.config_manager.get("enable_multi_scale", True):
            result = self._multi_scale_matching(screenshot, template, confidence, template_path)
            if result:
                return result
        
        # 步骤3: 图像预处理匹配
        if self.config_manager.get("enable_preprocessing", True):
            result = self._enhanced_template_matching(screenshot, template, confidence)
            if result:
                self.logger.info(f"预处理匹配成功: {template_path}")
                return result
        
        # 步骤4: 降低置信度重试
        if confidence > 0.6 and self.config_manager.get("adaptive_confidence", True):
            lower_confidence = max(0.5, confidence - 0.2)
            self.logger.debug(f"降低置信度重试: {confidence:.3f} -> {lower_confidence:.3f}")
            return self._multi_method_matching(screenshot, template, lower_confidence, template_path)
        
        return None
    
    def _multi_scale_matching(self, screenshot: np.ndarray, template: np.ndarray, 
                             confidence: float, template_path: str) -> Optional[Tuple[int, int]]:
        """多尺度模板匹配"""
        scale_range = self.config_manager.get("scale_range", [0.8, 1.2])
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
            if self.config_manager.get("debug_mode", False):
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
    
    def analyze_template_quality(self, template_path: str) -> Dict[str, Any]:
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
    
    def optimize_template_matching_settings(self, config_manager):
        """
        根据模板质量自动优化匹配设置
        """
        try:
            template_files = [
                "img_filter_icon.png",
                "img_menu_option.png", 
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
                config_manager.set("template_optimizations", optimizations)
                config_manager.save_config()
                self.logger.info(f"已应用模板优化设置: {optimizations}")
            
        except Exception as e:
            self.logger.error(f"优化模板匹配设置失败: {e}")
    
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
