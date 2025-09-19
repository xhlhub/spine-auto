# Spine UI 自动化脚本

自动化Spine软件中的筛选操作，循环点击附件子节点的跨平台Python脚本。

## 功能特性

- ✅ 自动点击筛选图标并选择网格选项
- ✅ 自动点击附件节点展开子节点
- ✅ 循环点击所有配置的附件子节点
- ✅ 基于图像识别，适应窗口位置变化
- ✅ 可配置的操作参数和目标子节点
- ✅ 详细的操作日志记录
- ✅ 错误处理和重试机制
- ✅ **跨平台支持** (Windows, macOS, Linux)
- ✅ **智能DPI检测** (自动适配高分辨率显示器)
- ✅ **多种窗口激活策略** (确保兼容性)

## 自动化流程

脚本按以下顺序执行操作：
1. **点击筛选图标** - 点击工具栏中的筛选（漏斗形状）图标
2. **选择网格选项** - 在下拉菜单中点击"网格"选项
3. **点击附件节点** - 在左侧树中点击"附件"节点展开子项
4. **循环点击子节点** - 依次点击所有配置的附件子节点

## 系统支持

| 操作系统 | 支持状态 | 特殊说明 |
|---------|---------|---------|
| **Windows 10/11** | ✅ 完全支持 | 推荐以管理员权限运行 |
| **macOS** | ✅ 完全支持 | 需要辅助功能权限 |
| **Linux** | ✅ 基本支持 | 可能需要xdotool |

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

**自动安装的平台特定依赖：**
- Windows: `pywin32` (Windows API支持)
- 所有平台: `psutil` (进程管理)

### 2. 平台特定设置

#### Windows用户
详细设置请参考 [Windows设置指南](WINDOWS_SETUP.md)

#### macOS用户
```bash
# 如果遇到pygetwindow安装问题，可以尝试：
pip install pyobjc-framework-Quartz
```

#### Linux用户
```bash
# 可选：安装xdotool以获得更好的窗口管理
sudo apt-get install xdotool  # Ubuntu/Debian
# 或
sudo yum install xdotool      # CentOS/RHEL
```

## 使用方法

### 第一步：准备模板图片

1. 运行脚本：
   ```bash
   python spine_automation.py
   ```

2. 选择 "1. 设置模板图片"

3. 手动截取以下模板图片并保存到 `templates/` 文件夹：

   **核心流程模板：**
   - `img_filter_icon.png` - 筛选图标（漏斗形状）的截图
   - `img_menu_option.png` - 下拉菜单中"网格"选项的截图
   - `attachment_node.png` - 左侧树中"附件"节点的截图

   **附件子节点模板：**
   - `raptor-body.png` - raptor-body子节点的截图
   - `raptor-back-arm.png` - raptor-back-arm子节点的截图
   - `raptor-front-leg.png` - raptor-front-leg子节点的截图
   - `raptor-hindleg-back.png` - raptor-hindleg-back子节点的截图
   - `raptor-horn.png` - raptor-horn子节点的截图
   - `raptor-jaw.png` - raptor-jaw子节点的截图
   - `raptor-jaw2.png` - raptor-jaw2子节点的截图
   - `raptor-jaw-tooth.png` - raptor-jaw-tooth子节点的截图
   - `raptor-mouth-inside.png` - raptor-mouth-inside子节点的截图
   - `raptor-saddle-w-shadow.png` - raptor-saddle-w-shadow子节点的截图
   - `raptor-tail-shadow.png` - raptor-tail-shadow子节点的截图
   - `raptor-tongue.png` - raptor-tongue子节点的截图
   - `stirrup-strap.png` - stirrup-strap子节点的截图

### 第二步：配置参数

编辑 `config.json` 文件（首次运行后自动生成）：

```json
{
  "window_title": "Spine",
  "click_delay": 1.0,
  "operation_delay": 2.0,
  "confidence_threshold": 0.8,
  "max_retries": 3,
}
```

### 第三步：运行自动化

1. 打开Spine软件并加载项目
2. 运行脚本并选择 "2. 运行自动化流程"
3. 脚本将自动执行以下操作：
   - 查找并激活Spine窗口
   - 点击筛选图标打开下拉菜单
   - 选择"网格"选项
   - 点击"附件"节点展开子项
   - 依次点击所有配置的附件子节点

## 配置说明

### config.json 参数详解

| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| `window_titles` | array | 多个窗口标题列表 | ["Spine", "Spine Trial", "Spine Pro"] |
| `app_names` | array | 多个应用程序名称列表 | ["Spine", "Spine Trial", "Spine Pro"] |
| `click_delay` | float | 点击操作间隔(秒) | 1.0 |
| `operation_delay` | float | 完成一个节点操作后的等待时间(秒) | 2.0 |
| `confidence_threshold` | float | 图像匹配置信度阈值 | 0.8 |
| `max_retries` | int | 操作失败最大重试次数 | 3 |

### 多窗口标题配置

配置多个窗口标题和应用名称，脚本会自动尝试匹配任意一个：

```json
{
  "window_titles": [
    "Spine",
    "Spine Trial", 
    "Spine Pro",
    "Spine Esoteric Software"
  ],
  "app_names": [
    "Spine",
    "Spine Trial",
    "Spine Pro", 
    "Spine Esoteric Software"
  ]
}
```

**匹配规则**：
- 脚本会按数组顺序尝试匹配窗口标题
- 找到第一个匹配的窗口就会使用
- 建议将最常用的标题放在数组前面

## 模板制作指南

### 1. 截图要求
- **精确性**: 模板图片要准确包含目标元素
- **唯一性**: 确保模板在界面中是唯一的
- **稳定性**: 选择不会频繁变化的UI元素

### 2. 筛选图标模板 (img_filter_icon.png)
- 截取工具栏中的筛选图标（漏斗形状）
- 包含图标的完整外观和边框
- 建议尺寸：30x30像素左右

### 3. 网格菜单选项模板 (img_menu_option.png)
- 截取下拉菜单中的"网格"文字选项
- 包含完整的文字和背景
- 建议尺寸：60x25像素左右

### 4. 附件节点模板 (attachment_node.png)
- 截取左侧树中"附件"节点的文字
- 包含节点名称的完整文字
- 建议尺寸：50x20像素左右

### 5. 子节点模板
- 截取附件展开后各个子节点的文字
- 每个子节点需要单独的模板文件
- 只包含文字部分，不需要图标
- 建议尺寸：120x20像素左右

### 6. 模板命名规则
- 文件名必须与配置中的子节点名称完全一致
- 使用PNG格式
- 例如：`raptor-body.png`，`raptor-back-arm.png`，`stirrup-strap.png`

## 故障排除

### 常见问题

1. **找不到窗口**
   - 确保Spine软件已打开
   - 检查窗口标题是否包含"Spine"
   - 可以修改config.json中的window_title参数

2. **模板匹配失败**
   - 检查模板图片是否准确
   - 降低confidence_threshold参数
   - 确保Spine界面没有被其他窗口遮挡

3. **点击位置不准确**
   - 重新制作更精确的模板
   - 检查屏幕分辨率和缩放设置
   - 确保Spine窗口完全可见

4. **权限问题**
   - **macOS**: 在系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能中，添加终端或Python的权限
   - **Windows**: 以管理员权限运行，检查杀毒软件设置
   - **Linux**: 确保有足够的X11权限

### 调试技巧

1. **查看日志**
   - 脚本会生成 `spine_automation.log` 文件
   - 包含详细的操作记录和错误信息

2. **测试模板**
   - 可以单独测试某个模板的匹配效果
   - 调整置信度阈值找到最佳参数

3. **手动验证**
   - 先手动执行一遍操作流程
   - 确保每个步骤都能正常工作

## 安全提示

- 脚本启用了PyAutoGUI的FAILSAFE功能
- 鼠标快速移动到屏幕左上角可紧急停止脚本
- 建议在测试环境中先验证脚本功能
- 使用前请保存重要的Spine项目文件

## 扩展功能

如需添加更多自动化功能，可以扩展以下部分：

1. **自定义操作序列**: 修改SpineAutomation类的run_automation方法
2. **添加键盘操作**: 使用pyautogui的键盘功能
3. **批处理多个文件**: 扩展文件管理功能
4. **支持其他附件类型**: 修改脚本支持不同的附件节点

## 版本信息

- 版本: 2.0.0
- Python要求: 3.8+
- 支持平台: Windows, macOS, Linux
- 主要依赖: pyautogui, opencv-python, pillow, pygetwindow
- Windows特定: pywin32, psutil

## 更新日志

### v2.0.0 - 跨平台支持
- ✅ 添加完整的Windows支持
- ✅ 智能DPI/缩放检测 (Windows + macOS)
- ✅ 多种窗口激活策略
- ✅ 跨平台权限检查
- ✅ Windows API集成
- ✅ 改进的错误处理和调试信息

### v1.0.0 - 初始版本
- ✅ 基础macOS支持
- ✅ 图像识别和自动点击
- ✅ 配置文件管理

---

如有问题或建议，请查看日志文件或联系技术支持。
# spine-auto
