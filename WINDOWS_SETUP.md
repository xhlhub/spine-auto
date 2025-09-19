# Windows 系统设置指南

本文档专门针对Windows用户，提供详细的安装和配置步骤。

## 系统要求

- Windows 10/11 (推荐)
- Python 3.8+ 
- 管理员权限（推荐）

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

**注意**: Windows系统会自动安装以下额外依赖：
- `pywin32` - Windows API支持
- `psutil` - 进程管理

### 2. Windows特定配置

#### 权限设置
1. **以管理员身份运行**：右键点击命令提示符或PowerShell，选择"以管理员身份运行"
2. **Windows Defender设置**：
   - 打开Windows Defender安全中心
   - 转到"病毒和威胁防护" > "病毒和威胁防护设置"
   - 添加排除项，将脚本目录添加到排除列表
3. **第三方杀毒软件**：将脚本添加到白名单

#### 显示器缩放设置
Windows系统支持自动检测显示器DPI缩放，但如果检测不准确，可以手动配置：

在 `config.json` 中添加：
```json
{
  "manual_dpr": 1.25,  // 125% 缩放
  // 或者
  "manual_dpr": 1.5,   // 150% 缩放
  // 或者  
  "manual_dpr": 2.0    // 200% 缩放
}
```

常见Windows缩放比例：
- 100% → `"manual_dpr": 1.0`
- 125% → `"manual_dpr": 1.25`
- 150% → `"manual_dpr": 1.5`
- 175% → `"manual_dpr": 1.75`
- 200% → `"manual_dpr": 2.0`

## Windows特定功能

### 窗口管理
- **自动窗口检测**：支持通过窗口标题查找Spine应用
- **窗口激活**：使用Windows API激活和恢复窗口
- **多显示器支持**：自动处理多显示器环境

### 点击功能
- **多种点击策略**：PyAutoGUI + Windows API
- **DPI感知**：自动适配高DPI显示器
- **窗口状态管理**：自动处理最小化/恢复

## 故障排除

### 常见问题

#### 1. 权限被拒绝
**症状**：脚本无法控制鼠标或键盘
**解决方案**：
- 以管理员权限运行脚本
- 检查杀毒软件设置
- 临时禁用Windows Defender实时保护进行测试

#### 2. 找不到窗口
**症状**：提示"未找到Spine窗口"
**解决方案**：
- 确保Spine应用正在运行
- 检查 `config.json` 中的 `window_title` 设置
- 尝试设置完整的窗口标题

#### 3. 点击位置不准确
**症状**：点击位置偏移
**解决方案**：
- 检查显示器缩放设置
- 手动设置 `manual_dpr` 值
- 确保Spine窗口没有被其他窗口遮挡

#### 4. DPI检测失败
**症状**：显示"DPR检测失败"
**解决方案**：
```json
{
  "manual_dpr": 1.25  // 根据你的显示器缩放设置
}
```

### 调试模式

启用调试模式获取更多信息：
```json
{
  "debug_mode": true
}
```

### 性能优化

#### Windows特定优化
1. **关闭不必要的后台程序**
2. **设置高性能电源模式**
3. **关闭Windows动画效果**：
   - 控制面板 > 系统 > 高级系统设置
   - 性能设置 > 调整为最佳性能

## 配置示例

Windows系统推荐配置 (`config.json`)：
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
  ],
  "confidence_threshold": 0.8,
  "click_delay": 3.0,
  "operation_delay": 2.0,
  "node_height": 20,
  "debug_mode": false,
  "manual_dpr": 1.25,
  "confidence_diff_threshold": 0.05
}
```

### 多窗口标题配置

Windows版本支持多个窗口标题匹配，适用于不同版本的Spine应用：

**常见的Spine窗口标题**：
- `"Spine"` - 基础版本
- `"Spine Trial"` - 试用版本  
- `"Spine Pro"` - 专业版本
- `"Spine Esoteric Software"` - 完整标题
- `"Spine 4.2"` - 带版本号的标题

**配置建议**：
```json
{
  "window_titles": [
    "你的实际窗口标题",
    "Spine Trial",
    "Spine Pro", 
    "Spine"
  ]
}
```

脚本会按顺序尝试匹配，找到第一个匹配的窗口就会使用。

## 兼容性说明

### 支持的Windows版本
- ✅ Windows 11 (推荐)
- ✅ Windows 10 (1903+)
- ⚠️ Windows 8.1 (基本支持)
- ❌ Windows 7 (不支持)

### Spine版本兼容性
- ✅ Spine 4.x
- ✅ Spine 3.8+
- ⚠️ 更早版本可能需要调整模板

## 获取帮助

如果遇到Windows特定问题：
1. 检查本文档的故障排除部分
2. 启用调试模式查看详细日志
3. 确认系统权限和安全软件设置
4. 验证Spine应用程序状态

## 更新日志

- **v1.0**: 初始Windows支持
  - Windows API窗口管理
  - 自动DPI检测
  - 跨平台权限检查
  - Windows特定错误处理
