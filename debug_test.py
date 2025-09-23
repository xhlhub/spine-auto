#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简单的调试测试脚本
"""

import sys
import os
import traceback

def main():
    """最简单的测试主函数"""
    try:
        print("=== 调试测试开始 ===")
        print(f"Python版本: {sys.version}")
        print(f"当前工作目录: {os.getcwd()}")
        print(f"sys.path: {sys.path[:3]}...")  # 只显示前3个路径
        
        # 检查是否在PyInstaller环境
        if hasattr(sys, '_MEIPASS'):
            print(f"PyInstaller环境: {sys._MEIPASS}")
        else:
            print("开发环境")
        
        print("\n=== 测试导入基本模块 ===")
        
        # 测试基本导入
        import json
        print("✅ json 导入成功")
        
        import logging
        print("✅ logging 导入成功")
        
        # 测试关键第三方库
        try:
            import pyautogui
            print("✅ pyautogui 导入成功")
        except Exception as e:
            print(f"❌ pyautogui 导入失败: {e}")
            
        try:
            import cv2
            print("✅ cv2 导入成功")
        except Exception as e:
            print(f"❌ cv2 导入失败: {e}")
            
        try:
            import numpy
            print("✅ numpy 导入成功")
        except Exception as e:
            print(f"❌ numpy 导入失败: {e}")
        
        print("\n=== 测试项目模块 ===")
        
        # 测试项目模块导入
        try:
            from config_manager import ConfigManager
            print("✅ config_manager 导入成功")
        except Exception as e:
            print(f"❌ config_manager 导入失败: {e}")
            traceback.print_exc()
            
        try:
            from template_manager import TemplateManager
            print("✅ template_manager 导入成功")
        except Exception as e:
            print(f"❌ template_manager 导入失败: {e}")
            
        try:
            from spine_automation import SpineAutomation
            print("✅ spine_automation 导入成功")
        except Exception as e:
            print(f"❌ spine_automation 导入失败: {e}")
            traceback.print_exc()
        
        print("\n✅ 基础测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
    
    # 无论如何都要暂停
    print(f"\n按 Enter 键退出...")
    try:
        input()
    except:
        import time
        time.sleep(5)


if __name__ == "__main__":
    main()
