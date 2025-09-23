@echo off
REM 以管理员权限运行 SpineAutomation.exe
echo ======================================
echo 以管理员权限启动 Spine 自动化工具
echo ======================================

REM 检查是否在正确目录
if exist "dist\SpineAutomation\SpineAutomation.exe" (
    echo 找到程序文件，正在以管理员权限启动...
    echo.
    powershell -Command "Start-Process 'dist\SpineAutomation\SpineAutomation.exe' -Verb RunAs"
) else (
    echo ❌ 错误: 找不到 dist\SpineAutomation\SpineAutomation.exe
    echo 请确保在项目根目录运行此脚本
    echo.
    pause
)

echo.
echo 程序启动完成
pause
