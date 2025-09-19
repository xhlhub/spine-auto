# Windows系统改进说明

## 问题背景

在Windows系统上使用Spine自动化脚本时，发现了以下两个主要问题：

1. **截图保存的一开始是黑屏** - 截图功能无法正确捕获当前屏幕内容
2. **后来一张还是当前应用而不是Spine** - 截图捕获的是脚本运行的应用而不是Spine应用

## 解决方案

### 1. 自动Spine应用激活

在 `automation.py` 中的 `run_automation()` 方法中，添加了新的步骤：

```python
# 步骤0.5: 激活Spine应用窗口（Windows上特别重要）
if not self.activate_spine_application():
    self.logger.warning("无法激活Spine应用，继续执行但可能影响截图效果")
```

#### 新增的 `activate_spine_application()` 方法特点：

- **智能激活**: 使用 `WindowManager` 的跨平台窗口激活功能
- **Windows特殊处理**: 在Windows上等待10秒确保窗口完全激活
- **容错机制**: 即使激活失败，也会给用户手动切换的机会
- **用户友好**: 提供清晰的状态提示和操作建议

### 2. 截图功能优化

在 `template_manager.py` 中重写了 `take_screenshot()` 方法：

#### 主要改进：

1. **Windows特殊处理**:
   - 添加短暂延时确保窗口渲染完成
   - 优先使用Windows API截图方法
   - 降级到标准pyautogui方法作为备选

2. **Windows API截图**:
   - 使用 `win32gui`, `win32ui`, `win32con` 等Windows API
   - 直接从桌面设备上下文获取截图
   - 避免应用切换导致的截图问题

3. **黑屏检测**:
   - 自动检测截图是否为黑屏
   - 计算图像平均亮度判断截图质量
   - 提供相应的警告和建议

#### 新增方法：

- `_take_screenshot_standard()`: 标准截图方法
- `_take_screenshot_windows_optimized()`: Windows优化截图方法
- `_is_screenshot_black()`: 黑屏检测方法

## 使用方法

### 自动使用（推荐）

直接运行主程序，改进功能会自动生效：

```bash
python main.py
```

选择 "2. 运行自动化流程"，脚本会：

1. 检查系统权限
2. **自动激活Spine应用**（新功能）
3. **等待10秒确保激活完成**（Windows）
4. 查找Spine窗口
5. 使用优化的截图方法执行自动化流程

### 测试改进功能

运行测试脚本验证改进效果：

```bash
python test_windows_improvements.py
```

测试内容包括：
- Spine应用激活功能
- 截图改进功能
- 黑屏检测功能
- 完整工作流程

## 配置要求

### Windows系统要求

1. **管理员权限**: 建议以管理员权限运行脚本
2. **pywin32库**: 用于Windows API截图（可选，会自动降级）
3. **Spine应用**: 确保Spine应用已启动

### 配置文件设置

在 `config.json` 中确保正确配置：

```json
{
  "app_names": ["Spine", "Esoteric Software Spine"],
  "window_titles": ["Spine", "Esoteric Software Spine"],
  "debug_mode": true
}
```

## 工作流程

### 改进后的执行流程

1. **权限检查** ✅
2. **🆕 激活Spine应用** ⭐
3. **🆕 等待10秒确保激活** ⭐ (Windows)
4. **查找Spine窗口** ✅
5. **🆕 优化截图方法** ⭐
6. **🆕 黑屏检测** ⭐
7. **执行自动化流程** ✅

### Windows上的特殊处理

- **激活成功**: 等待10秒 → 继续执行
- **激活失败**: 提示用户手动切换 → 等待10秒 → 继续执行
- **截图黑屏**: 警告用户检查窗口状态 → 继续执行

## 故障排除

### 如果仍然出现黑屏截图

1. **手动激活**: 在脚本运行前手动切换到Spine应用
2. **检查权限**: 确保以管理员权限运行
3. **安装pywin32**: `pip install pywin32` 获得更好的Windows支持
4. **启用调试**: 在config.json中设置 `"debug_mode": true`

### 如果无法激活Spine应用

1. **检查应用名称**: 确认config.json中的app_names正确
2. **检查窗口标题**: 确认config.json中的window_titles正确
3. **手动启动**: 确保Spine应用已经启动
4. **权限问题**: 尝试以管理员权限运行

## 日志信息

启用调试模式后，会看到详细的日志信息：

```
INFO - 正在激活Spine应用窗口...
INFO - Windows系统检测到，等待10秒确保窗口完全激活...
INFO - ✅ 窗口激活等待完成
DEBUG - 使用Windows API截图成功
WARNING - 检测到黑屏截图，可能需要激活目标应用窗口
```

## 技术细节

### Windows API截图原理

```python
# 获取桌面设备上下文
hdesktop = win32gui.GetDesktopWindow()
desktop_dc = win32gui.GetWindowDC(hdesktop)

# 创建兼容的内存设备上下文
img_dc = win32ui.CreateDCFromHandle(desktop_dc)
mem_dc = img_dc.CreateCompatibleDC()

# 复制屏幕内容到内存
mem_dc.BitBlt((0, 0), (width, height), img_dc, (x, y), win32con.SRCCOPY)
```

### 黑屏检测算法

```python
# 计算图像平均亮度
gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
mean_brightness = np.mean(gray)

# 判断是否为黑屏
is_black = mean_brightness < 10  # 阈值可调整
```

## 总结

这些改进专门针对Windows系统的截图问题，通过以下方式解决：

1. **主动激活Spine应用** - 确保截图目标正确
2. **充足的等待时间** - 确保窗口完全激活
3. **多种截图方法** - 提高截图成功率
4. **智能质量检测** - 及时发现问题

这些改进使得Windows用户能够获得更稳定、更可靠的自动化体验。
