#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spine UI自动化脚本 - 主入口文件

作者: Assistant
功能: 主菜单和程序入口
"""

from spine_automation import SpineAutomation
import pyautogui


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
        print("3. 📋 运行诊断报告（推荐：发现问题时使用）")
        print("4. 编辑配置")
        print("5. 测试点击功能")
        print("6. 检查系统权限")
        print("7. 分析模板质量")
        print("8. 优化匹配设置")
        print("9. 测试DPR检测")
        print("10. 调试点击问题")
        print("0. 退出")
        
        choice = input("请输入选择 (0-10): ").strip()
        
        if choice == "1":
            automation.setup_templates()
        elif choice == "2":
            automation.run_automation()
        elif choice == "3":
            # 运行诊断报告
            automation.automation_runner.run_diagnostic_report()
        elif choice == "4":
            print(f"请编辑配置文件: {automation.config_manager.config_path}")
            input("编辑完成后按回车继续...")
            automation.config_manager.load_config()
        elif choice == "5":
            automation.test_click_functionality()
        elif choice == "6":
            if automation.window_manager.check_accessibility_permissions():
                print("✅ 辅助功能权限正常")
            else:
                print("❌ 辅助功能权限不足")
        elif choice == "7":
            # 分析模板质量
            template_files = ["img_filter_icon.png", "img_menu_option.png", "attachment_node.png"]
            print("\n=== 模板质量分析 ===")
            for template_file in template_files:
                template_path = automation.template_manager.templates_dir / template_file
                if template_path.exists():
                    analysis = automation.template_manager.analyze_template_quality(str(template_path))
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
        elif choice == "8":
            # 优化匹配设置
            print("\n=== 优化匹配设置 ===")
            automation.template_manager.optimize_template_matching_settings(automation.config_manager)
            print("✅ 匹配设置优化完成")
            input("按回车继续...")
        elif choice == "9":
            # 测试DPR检测
            print("\n=== DPR检测测试 ===")
            print(f"当前检测到的DPR: {automation.click_manager.dpr}")
            
            # 获取屏幕信息
            try:
                screen_width, screen_height = pyautogui.size()
                print(f"PyAutoGUI报告的屏幕尺寸: {screen_width}x{screen_height}")
                
                # 测试坐标转换
                test_coords = [(100, 100), (500, 300), (1000, 600)]
                print("\n坐标转换测试:")
                for orig_x, orig_y in test_coords:
                    corrected_x = orig_x / automation.click_manager.dpr
                    corrected_y = orig_y / automation.click_manager.dpr
                    print(f"  原始: ({orig_x}, {orig_y}) -> DPR修正: ({corrected_x:.1f}, {corrected_y:.1f})")
                
                # 提供手动设置DPR的选项
                print(f"\n当前DPR设置: {automation.click_manager.dpr}")
                manual_dpr = input("如需手动设置DPR，请输入数值（直接回车保持当前值）: ").strip()
                if manual_dpr:
                    try:
                        new_dpr = float(manual_dpr)
                        if 0.5 <= new_dpr <= 4.0:
                            automation.click_manager.dpr = new_dpr
                            automation.config_manager.config["manual_dpr"] = new_dpr
                            automation.config_manager.save_config()
                            print(f"✅ DPR已手动设置为: {new_dpr}")
                        else:
                            print("❌ DPR值应在0.5-4.0之间")
                    except ValueError:
                        print("❌ 请输入有效的数值")
                        
            except Exception as e:
                print(f"❌ 测试失败: {e}")
            
            input("\n按回车继续...")
        elif choice == "10":
            # 调试点击问题
            print("\n=== 调试点击问题 ===")
            print("请先移动鼠标到您想要测试的位置，然后按回车")
            input("准备好后按回车...")
            
            # 获取当前鼠标位置
            import pyautogui
            test_x, test_y = pyautogui.position()
            print(f"将测试位置: ({test_x}, {test_y})")
            
            # 执行调试
            automation.click_manager.debug_click_issue(test_x, test_y)
            input("\n按回车继续...")
        elif choice == "0":
            print("退出程序")
            break
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
