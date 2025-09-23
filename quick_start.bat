@echo off
chcp 65001 >nul
title Spine UI自动化 - 快速启动

echo 正在启动Spine UI自动化脚本 - 快速启动版本...
echo.

REM 检查虚拟环境是否存在
if exist venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo 虚拟环境不存在，使用系统Python...
)

REM 运行快速启动脚本
python quick_start.py

echo.
echo 按任意键退出...
pause >nul
