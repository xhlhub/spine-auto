#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速窗口检测测试
"""

import pygetwindow as gw
from config_manager import ConfigManager

def main():
    print("🔍 当前所有窗口列表:")
    print("=" * 50)
    
    config = ConfigManager("config.json")
    search_titles = config.get_window_titles()
    
    all_windows = gw.getAllWindows()
    spine_windows = []
    
    for i, window in enumerate(all_windows):
        if hasattr(window, 'title') and window.title:
            print(f"{i+1:2d}. '{window.title}'")
            
            # 检查是否匹配Spine
            for search_title in search_titles:
                if search_title.lower() in window.title.lower():
                    spine_windows.append((window.title, search_title))
    
    print("\n🎯 匹配到的Spine相关窗口:")
    print("=" * 50)
    if spine_windows:
        for title, matched in spine_windows:
            print(f"✅ '{title}' (匹配: '{matched}')")
    else:
        print("❌ 未找到匹配的窗口")
    
    print(f"\n📝 搜索关键词: {search_titles}")
    print("\n💡 请确保真正的Spine应用程序正在运行!")

if __name__ == "__main__":
    main()
