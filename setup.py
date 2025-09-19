#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速安装和设置脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """安装Python依赖"""
    print("正在安装Python依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("正在创建目录结构...")
    try:
        Path("templates").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        print("✅ 目录创建完成")
        return True
    except Exception as e:
        print(f"❌ 目录创建失败: {e}")
        return False

def check_system_permissions():
    """检查系统权限（跨平台）"""
    import platform
    
    if platform.system() == "Darwin":
        print("\n⚠️  macOS权限提示:")
        print("请确保在'系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能'中")
        print("添加Python或终端的权限，否则脚本无法控制鼠标和键盘")
        print("\n按回车键继续...")
        input()
    elif platform.system() == "Windows":
        print("\n⚠️  Windows权限提示:")
        print("为了获得最佳兼容性，建议:")
        print("1. 以管理员权限运行此脚本")
        print("2. 确保Windows Defender没有阻止脚本运行")
        print("3. 如果使用第三方杀毒软件，请将脚本添加到白名单")
        print("4. 确保Spine应用程序正在运行")
        print("\n按回车键继续...")
        input()
    else:
        print(f"\n⚠️  {platform.system()}系统提示:")
        print("请确保有足够的权限运行自动化脚本")
        print("\n按回车键继续...")
        input()

def main():
    print("=== Spine UI自动化脚本 - 快速设置 ===\n")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 创建目录
    if not create_directories():
        sys.exit(1)
    
    # 权限检查
    check_system_permissions()
    
    print("\n🎉 设置完成！")
    print("\n下一步:")
    print("1. 运行 'python spine_automation.py'")
    print("2. 选择 '1. 设置模板图片' 创建所需的模板")
    print("3. 选择 '2. 运行自动化流程' 开始自动化操作")
    print("\n详细说明请查看 README.md 文件")

if __name__ == "__main__":
    main()
