# Spine自动化工具 - 可执行版本

## 📦 打包完成！

您的Spine UI自动化工具已经成功打包为可执行文件。

## 📁 文件位置

可执行文件位于：`dist/SpineAutomation/`

```
dist/
└── SpineAutomation/
    ├── SpineAutomation.exe    # 主执行文件
    └── _internal/             # 依赖文件和资源
        ├── config.json        # 配置文件
        ├── templates/         # Linux/Mac模板图片
        ├── templates_win/     # Windows模板图片
        └── [其他依赖文件...]
```

## 🚀 如何使用

### 方法1：直接运行
1. 打开文件管理器，导航到 `dist/SpineAutomation/` 目录
2. 双击 `SpineAutomation.exe` 启动程序
3. 程序将自动开始Spine UI自动化流程

### 方法2：命令行运行
1. 打开命令提示符(CMD)或PowerShell
2. 切换到可执行文件目录：
   ```cmd
   cd "C:\Users\yangz\Desktop\code\spinauto\dist\SpineAutomation"
   ```
3. 运行程序：
   ```cmd
   SpineAutomation.exe
   ```

## 📋 运行要求

### 系统要求
- **操作系统**: Windows 10/11 (64位)
- **权限**: 建议以管理员身份运行
- **Spine应用**: 确保Spine编辑器正在运行

### 使用前准备
1. **启动Spine编辑器**: 确保Spine应用程序已经启动并加载了项目
2. **检查模板**: 程序会使用`templates_win/`目录下的图片模板进行UI识别
3. **配置检查**: 如需调整配置，可编辑`_internal/config.json`文件

## ⚠️ 注意事项

### 安全提醒
- 杀毒软件可能会误报，请将程序添加到白名单
- Windows Defender可能阻止运行，选择"仍要运行"
- 首次运行可能需要管理员权限

### 使用建议
1. **备份数据**: 运行前请备份重要的Spine项目文件
2. **关闭其他程序**: 避免干扰自动化操作
3. **保持专注**: 运行期间请勿移动鼠标或使用键盘
4. **紧急停止**: 移动鼠标到屏幕左上角可紧急停止程序

## 🔧 故障排除

### 常见问题

#### 1. 程序无法启动
- 检查是否以管理员身份运行
- 确认杀毒软件没有阻止程序
- 检查Windows版本兼容性

#### 2. 找不到Spine窗口
- 确保Spine编辑器已启动
- 检查窗口标题是否包含"Spine"
- 尝试重新启动Spine编辑器

#### 3. 模板匹配失败
- 检查`_internal/templates_win/`目录下的图片文件
- 确保Spine界面语言和模板一致
- 可能需要重新截取模板图片

#### 4. 权限错误
- 以管理员身份运行程序
- 检查Windows用户账户控制(UAC)设置
- 确认对程序目录有读写权限

## 📞 技术支持

如果遇到问题：
1. 查看程序运行时的控制台输出
2. 检查生成的日志文件
3. 联系开发者并提供错误信息

## 📦 分发说明

如果需要分发给其他用户：
1. **完整复制**: 必须复制整个`SpineAutomation`文件夹
2. **保持结构**: 不要改变文件夹内部结构
3. **提供说明**: 向用户提供本说明文档
4. **系统要求**: 确保目标系统满足运行要求

## 🔄 更新说明

如果需要更新程序：
1. 重新运行打包命令: `pyinstaller quick_start.spec`
2. 新的可执行文件会生成在`dist/SpineAutomation/`目录
3. 可以直接替换旧的可执行文件

---

**版本信息**: 基于`quick_start.py`打包  
**打包时间**: 2025年9月22日  
**PyInstaller版本**: 6.16.0  


