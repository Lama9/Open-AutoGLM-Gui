# Open-AutoGLM GUI 使用说明文档

本文档详细介绍了 Open-AutoGLM 图形化界面 (GUI) 的功能、使用方法以及开发/编译环境的搭建步骤。

---

## 1. 功能特性 (Features)

GUI 版本旨在简化命令行操作，提供即开即用的便捷体验。主要功能包括：

### 1.1 界面可视化
- **直观布局**: 只需要在一个窗口中即可配置所有核心参数（API Key、Base URL、Model、Device ID 等）。
- **任务管理**: 提供了专门的任务输入框和清晰的日志输出窗口。
- **自定义图标**: 程序使用了全新的 Logo 图标，界面更加美观。

### 1.2 智能自动化
- **自动连接设备 (ADB)**:
    - 只需在 "Device ID" 输入框中填写 `IP:端口` (例如 `192.168.1.5:5555`)。
    - 失去焦点后，程序会自动断开旧设备并连接新设备。
- **ADB Keyboard 自动配置**:
    - 连接成功后，程序会自动检查手机上是否安装了 `ADBKeyboard`。
    - 如果未安装，会自动安装内置的 APK 文件。
    - 安装后会自动启用该输入法，无需人工干预。
- **API 连通性校验**:
    - 修改 Base URL、Model 或 API Key 后，程序会自动发送测试请求。
    - 界面底部会实时提示校验成功或失败的信息。

### 1.3 状态记忆 (Persistence)
- **配置保存**: 所有有效的配置项（API Key、Device ID、Language 等）在通过校验后会自动保存。
- **自动恢复**: 下次启动程序时，会自动恢复上次的配置，无需重复输入。
- **配置文件**: 配置存储在程序同级目录下的 `gui_config.json` 文件中。

### 1.4 便携与独立
- **Env 不依赖**: 打包后的程序内置了 Python 运行时和 ADB 工具集。
- **零干扰**: 不会修改用户系统的 PATH 环境变量，拥有完全独立的运行环境。
- **帮助文档**: 界面内置了详细的“使用帮助”文档，点击顶部按钮即可查看。

---

## 2. 编译环境搭建 (Development Setup)

如果您希望从源码运行或自行编译，请按以下步骤操作。

### 2.1 前置要求
- **操作系统**: Windows 10/11
- **Python**: 推荐 Python 3.10+ (建议使用 Anaconda 或 Miniconda 管理环境)
- **Git**: 用于拉取代码

### 2.2 安装步骤
1.  **克隆代码**:
    ```powershell
    git clone https://github.com/Lama9/Open-AutoGLM-Gui.git
    cd Open-AutoGLM-Gui
    ```

2.  **创建虚拟环境 (推荐)**:
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **安装依赖**:
    ```powershell
    pip install -r requirements.txt
    ```
    *注意: `requirements.txt` 中已包含 GUI 核心库 `flet` 和打包工具 `pyinstaller`。*

---

## 3. 编译步骤 (Build Executable)

我们提供了一个一键编译脚本 `build_exe.py`，它可以将 Python 脚本打包为独立的 `.exe` 可执行文件。

### 3.1 执行编译
在虚拟环境激活状态下，运行：

```powershell
python build_exe.py
```

### 3.2 编译产物
脚本运行完成后，生成的文件位于 `dist` 目录下：

- **路径**: `.\dist\OpenAutoGLMGui\OpenAutoGLMGui.exe`
- **分发**: 您可以将整个 `OpenAutoGLMGui` 文件夹压缩发送给其他用户。

### 3.3 编译脚本说明
`build_exe.py` 自动处理了以下复杂逻辑：
- 自动识别并打包 Anaconda 或系统环境中的关键 DLL (`ffi.dll`, `libssl`, `libcrypto` 等)。
- 自动打包 `platform-tools` (ADB) 和 `ADBKeyboard.apk`。
- 自动配置 PyInstaller 的 Hidden Imports。
- 自动设置程序图标和资源文件路径。

---

## 4. 常见问题 (FAQ)

- **Q: 运行 exe 时提示找不到 ADB?**
  - A: 请确保不要随意移动 exe 文件，它必须和内部的 `_internal` 文件夹保持相对位置关系。请移动整个文件夹。

- **Q: 窗口无法滚动?**
  - A: 在最新版本中已修复，输出日志和帮助文档均支持滚动查看。

- **Q: 连接手机失败?**
  - A: 请检查手机是否开启了“USB 调试”，如果是小米手机还需要开启“USB 调试 (安全设置)”。
