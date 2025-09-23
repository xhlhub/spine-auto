#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spine UI自动化脚本 - 快速启动版本

功能: 直接运行自动化流程，无需菜单选择
作者: Assistant
"""

from spine_automation import SpineAutomation
import sys
import os
import traceback


def main():
    """快速启动主函数"""
    print("=== Spine UI自动化脚本 - 快速启动 ===")
    
    # 修正工作目录到脚本所在位置（解决打包后路径问题）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_cwd = os.getcwd()
    
    # 如果是PyInstaller打包的exe，获取正确的资源路径
    if hasattr(sys, '_MEIPASS'):
        # 打包后的临时目录
        resource_dir = sys._MEIPASS
        print(f"检测到PyInstaller环境，资源目录: {resource_dir}")
        os.chdir(resource_dir)
    else:
        # 开发环境，使用脚本所在目录
        os.chdir(script_dir)
    
    # 打印调试信息
    print(f"原始工作目录: {original_cwd}")
    print(f"脚本文件位置: {script_dir}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查关键文件是否存在
    config_path = "config.json"
    templates_dir = "templates_win"
    
    print(f"\n检查关键文件:")
    if os.path.exists(config_path):
        print(f"✅ 配置文件存在: {config_path}")
    else:
        print(f"❌ 配置文件不存在: {config_path}")
        
    if os.path.exists(templates_dir):
        print(f"✅ 模板目录存在: {templates_dir}")
        template_files = os.listdir(templates_dir)
        print(f"   模板文件数量: {len(template_files)}")
    else:
        print(f"❌ 模板目录不存在: {templates_dir}")
        
    print("\n请选择操作:")
    print("1. 🚀 运行自动化流程")
    print("2. 📁 查看日志文件夹")
    print("3. 📊 查看日志摘要")
    print("4. 📋 查看最新日志")
    print("5. 🚪 退出")
    
    try:
        # 创建自动化实例
        automation = SpineAutomation()
        
        while True:
            print("\n" + "="*50)
            choice = input("请输入选择 (1-5): ").strip()
            
            if choice == "1":
                print("\n正在启动自动化流程...")
                try:
                    automation.run_automation()
                    print("\n✅ 自动化流程执行完成！")
                except Exception as e:
                    print(f"\n❌ 自动化流程执行失败: {e}")
                    print("详细错误信息:")
                    traceback.print_exc()
            
            elif choice == "2":
                print("\n📁 正在打开日志文件夹...")
                automation.open_logs_folder()
            
            elif choice == "3":
                automation.show_log_summary()
            
            elif choice == "4":
                lines = input("显示最新多少行日志? (默认50行): ").strip()
                try:
                    lines = int(lines) if lines else 50
                    automation.view_latest_log(lines)
                except ValueError:
                    automation.view_latest_log(50)
            
            elif choice == "5":
                print("\n👋 再见！")
                break
            
            else:
                print("❌ 无效选择，请输入 1-5")
                continue
                
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断了程序")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ 程序执行出现错误: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        print(f"\n如果需要帮助，请将上述错误信息提供给开发者")
        
        # 提示用户可以使用完整版本进行调试
        print(f"\n💡 提示: 如果遇到问题，可以运行 main.py 使用完整菜单进行调试")
        
        # 暂停程序，让用户能看到错误信息
        print(f"\n按 Enter 键退出...")
        input()
        sys.exit(1)


if __name__ == "__main__":
    main()
