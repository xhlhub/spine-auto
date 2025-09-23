@echo off
echo ======================================
echo     Spine自动化工具 - 可执行版本
echo ======================================
echo.

REM 检查可执行文件是否存在
if not exist "dist\SpineAutomation\SpineAutomation.exe" (
    echo ❌ 错误: 找不到可执行文件！
    echo    请确保已经运行打包命令: pyinstaller quick_start.spec
    echo.
    pause
    exit /b 1
)

echo ✅ 找到可执行文件: dist\SpineAutomation\SpineAutomation.exe
echo.
echo 🚀 正在启动Spine自动化工具...
echo    - 请确保Spine编辑器已经启动
echo    - 运行期间请勿移动鼠标或使用键盘
echo    - 紧急停止: 移动鼠标到屏幕左上角
echo.

REM 切换到可执行文件目录并运行
cd "dist\SpineAutomation"
start "" "SpineAutomation.exe"

echo 程序已启动，请查看新打开的窗口...
echo.
pause


