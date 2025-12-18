import re
import flet as ft
import subprocess
import threading
import os
import shutil
from openai import OpenAI

import json

# Logic to get bundled ADB path
def get_bundled_adb_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        # Check standard location (root of dist)
        p1 = os.path.join(base_path, 'platform-tools', 'adb.exe')
        if os.path.exists(p1):
            return p1
        # Check _internal location (PyInstaller 6+ default)
        p2 = os.path.join(base_path, '_internal', 'platform-tools', 'adb.exe')
        if os.path.exists(p2):
            return p2
    return "adb" # Default to system adb if not frozen

bundled_adb = get_bundled_adb_path()

# Config Logic
CONFIG_FILE = "gui_config.json"

def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, CONFIG_FILE)
    return os.path.join(os.getcwd(), CONFIG_FILE)

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def save_config(config_data):
    path = get_config_path()
    try:
        # Load existing first to preserve other keys if any
        existing = load_config()
        existing.update(config_data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")


# Monkeypatch shutil.which to find our bundled ADB
_original_which = shutil.which
def custom_which(cmd, mode=os.F_OK | os.X_OK, path=None):
    if cmd == "adb":
        # If we have a bundled adb, check if it exists
        if os.path.exists(bundled_adb):
            return bundled_adb
    return _original_which(cmd, mode, path)

shutil.which = custom_which

# Monkeypatch subprocess.Popen
if sys.platform == "win32":
    _original_Popen = subprocess.Popen
    
    class Popen(subprocess.Popen):
        def __init__(self, args, **kwargs):
            # 1. Suppress Window
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = 0x08000000 # CREATE_NO_WINDOW
            
            # 2. Redirect ADB command
            # args is usually the first positional argument. 
            # It can be a list ["adb", "devices"] or a string "adb devices"
            
            new_args = args
            if os.path.isabs(bundled_adb) and os.path.exists(bundled_adb):
                if isinstance(args, list) and len(args) > 0 and args[0] == "adb":
                    # Modify list copy to be safe (though args is usually consumed immediately)
                    new_args = list(args)
                    new_args[0] = bundled_adb
                elif isinstance(args, str) and args.startswith("adb "):
                    # Replace string command
                    new_args = bundled_adb + args[3:]
            
            # Call original
            super().__init__(new_args, **kwargs)
            
    subprocess.Popen = Popen

import main as main_script # Import global

class OutputRedirector:
    def __init__(self, callback):
        self.callback = callback
    def write(self, buf):
        if buf:
            self.callback(buf)
    def flush(self):
        pass

def main(page: ft.Page):
    # Load Config
    config = load_config()

    page.title = "Open-AutoGLM Controller"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 1000
    page.window.height = 800
    
    # Set Window Icon
    # Note: Flet usually expects a path relative to the assets_dir, or an absolute path.
    # We will try to resolve the absolute path using our helper.
    icon_path = ""
    if getattr(sys, 'frozen', False):
         base_path = os.path.dirname(sys.executable)
         # Try standard or _internal
         p1 = os.path.join(base_path, 'resources', 'logo.ico')
         p2 = os.path.join(base_path, '_internal', 'resources', 'logo.ico')
         if os.path.exists(p1): icon_path = p1
         elif os.path.exists(p2): icon_path = p2
    else:
         icon_path = os.path.join(os.getcwd(), 'resources', 'logo.ico')
         
    if icon_path and os.path.exists(icon_path):
        page.window.icon = icon_path

    # Center the window
    page.window.center()
    
    # Help Documentation
    HELP_MD = """
# Open-AutoGLM Controller 使用指南

## 1. 简介
这是一个为 Open-AutoGLM 设计的图形化控制台，旨在简化命令行操作，提供更直观的任务管理和设备连接体验。

## 2. 快速开始
1.  **连接设备**: 
    - 确保手机已开启 **USB 调试**。
    - 在 "Device ID" 输入框中输入 `IP:端口` (如 `192.168.1.5:5555`)。
    - 失去焦点后，无需手动确认，程序会自动连接。
    - **自动配置**: 程序还会自动检测并安装/启用 `ADB Keyboard` 输入法。

2.  **配置 API**:
    - 输入您的 **Base URL** (智普 API 地址)。
    - 输入 **API Key** (点击上方 "获取智普Key" 按钮获取)。
    - 输入 **Model** 名称 (如 `autoglm-phone`)。
    - 配置完成后，程序会自动验证连通性。

3.  **运行任务**:
    - 在 "Task" 输入框中描述任务 (如 "打开微信发送消息给张三")。
    - 点击 **Run** 开始运行。
    - 底部日志窗口会实时显示 Agent 的执行过程。

## 3. 功能特性
- **自动保存**: 您的 API 配置和设备 ID 会在验证成功后自动保存，下次打开无需重新输入。
- **日志自动滚动**: 勾选 "Auto Scroll" 可跟随最新日志，取消勾选可查看历史记录。
- **一键清理**: 支持一键清除日志和任务输入。
- **便携运行**: 本程序内置 ADB 和 Python 环境，无需额外安装即可在任意 Windows 电脑运行。

## 4. 常见问题
- **Q: 连接失败?**
  - A: 检查手机是否要在屏幕上点击 "允许调试"。检查 IP 是否正确，确保电脑和手机在同一 Wi-Fi 下。
- **Q: 任务无反应?**
  - A: 检查 API Key 是否过期，Base URL 是否正确。

## 5. 关于
- **原始项目地址**: https://github.com/zai-org/Open-AutoGLM
- **GUI 项目地址**: https://github.com/Lama9/Open-AutoGLM-Gui
- **版本**: GUI v0.0.1
"""

    def open_help(e):
        dlg = ft.AlertDialog(
            title=ft.Text("帮助文档"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Markdown(
                            HELP_MD, 
                            selectable=True, 
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                ),
                width=600,
                height=400,
                padding=10,
            ),
        )
        page.open(dlg)


    # API Validation Logic
    def validate_api_thread(base_url, model, api_key):
        try:
            client = OpenAI(base_url=base_url, api_key=api_key if api_key else "EMPTY", timeout=5.0)
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                stream=False
            )
            page.open(ft.SnackBar(content=ft.Text("API Connection Verified!"), bgcolor=ft.Colors.GREEN))
            
            # Save Valid Config
            save_config({
                "base_url": base_url,
                "model": model,
                "api_key": api_key
            })
            
        except Exception as e:
             # Simplify error message
             err_msg = str(e)
             if "ConnectTimeout" in err_msg: err_msg = "Connection Timed Out"
             elif "401" in err_msg: err_msg = "Authentication Failed (401)"
             elif "404" in err_msg: err_msg = "Model/Endpoint Not Found (404)"
             
             page.open(ft.SnackBar(content=ft.Text(f"API Check Failed: {err_msg}"), bgcolor=ft.Colors.RED))
        page.update()

    # Store last check params to avoid repeated checks on same values
    last_api_params = ["", "", ""] # url, model, key

    def on_api_config_blur(e):
        url = base_url_input.value.strip()
        model = model_input.value.strip()
        key = api_key_input.value.strip()
        
        # Only check if URL and Model are present (Key can be empty)
        if not url or not model:
            return
            
        current_params = [url, model, key]
        if current_params == last_api_params:
            return
            
        last_api_params[:] = current_params # Update last checked
        
        # Run check in thread
        threading.Thread(target=validate_api_thread, args=(url, model, key), daemon=True).start()

    # Configuration Controls
    base_url_input = ft.TextField(
        label="Base URL", 
        value=config.get("base_url", "https://open.bigmodel.cn/api/paas/v4"), 
        expand=True,
        on_blur=on_api_config_blur
    )
    model_input = ft.TextField(
        label="Model", 
        value=config.get("model", "autoglm-phone"), 
        expand=True,
        on_blur=on_api_config_blur
    )
    api_key_input = ft.TextField(
        label="API Key", 
        value=config.get("api_key", ""),
        password=True, 
        can_reveal_password=True, 
        expand=True,
        on_blur=on_api_config_blur
    )
    
    def on_lang_change(e):
        save_config({"language": lang_dropdown.value})

    lang_dropdown = ft.Dropdown(
        label="Language",
        options=[
            ft.dropdown.Option("", text="Default (None)"),
            ft.dropdown.Option("cn", text="Chinese (cn)"),
            ft.dropdown.Option("en", text="English (en)"),
        ],
        value=config.get("language", ""),
        width=150,
        on_change=on_lang_change
    )
    


    # ... inputs ...
    
    device_id_input = ft.TextField(
        label="Device ID (IP:Port or Serial)", 
        value=config.get("device_id", ""),
        hint_text="e.g. 192.168.1.5:5555",
        expand=True
        # on_blur handler is attached below
    )
    
    # Store last valid value to detect changes
    last_device_id = [""] 

    def on_device_id_blur(e):
        current_val = device_id_input.value.strip()
        
        # Only proceed if value changed and is not empty
        if current_val == last_device_id[0] or not current_val:
            last_device_id[0] = current_val
            return

        # Validate IP format (Simple regex for IP or IP:Port)
        # Matches: 192.168.1.1 or 192.168.1.1:5555
        pattern = r"^(\d{1,3}\.){3}\d{1,3}(:\d{1,5})?$"
        if not re.match(pattern, current_val):
             page.open(ft.SnackBar(content=ft.Text(f"Invalid IP Format: {current_val}")))
             device_id_input.error_text = "Invalid IP Format"
             page.update()
             return
        
        device_id_input.error_text = None
        last_device_id[0] = current_val
        page.update()

        def connect_thread():
             try:
                 # 1. Disconnect all
                 subprocess.run(["adb", "disconnect"], capture_output=True, text=True)
                 
                 # 2. Connect to new device
                 res = subprocess.run(["adb", "connect", current_val], capture_output=True, text=True)
                 output = res.stdout.strip()
                 
                 if "connected to" in output:
                     page.open(ft.SnackBar(content=ft.Text(f"Successfully connected to {current_val}"), bgcolor=ft.Colors.GREEN))
                     save_config({"device_id": current_val})
                     
                     # 3. Check and Install ADB Keyboard
                     try:
                        # Check bundle path for APK
                        apk_path = "ADBKeyboard.apk" # Default for dev
                        if getattr(sys, 'frozen', False):
                            base_path = os.path.dirname(sys.executable)
                            p1 = os.path.join(base_path, 'ADBKeyboard.apk')
                            p2 = os.path.join(base_path, '_internal', 'ADBKeyboard.apk')
                            if os.path.exists(p1): apk_path = p1
                            elif os.path.exists(p2): apk_path = p2
                        
                        # Check instalation
                        ime_res = subprocess.run(["adb", "shell", "ime", "list", "-s"], capture_output=True, text=True)
                        if "com.android.adbkeyboard/.AdbIME" not in ime_res.stdout:
                            page.open(ft.SnackBar(content=ft.Text("ADB Keyboard not found. Installing..."), bgcolor=ft.Colors.ORANGE))
                            page.update()
                            
                            if os.path.exists(apk_path):
                                # Install
                                install_res = subprocess.run(["adb", "install", "-r", apk_path], capture_output=True, text=True)
                                if install_res.returncode == 0:
                                    # Enable
                                    subprocess.run(["adb", "shell", "ime", "enable", "com.android.adbkeyboard/.AdbIME"], capture_output=True, text=True)
                                    # Set as default (Optional but recommended, though user only asked for enable)
                                    subprocess.run(["adb", "shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"], capture_output=True, text=True)
                                    
                                    page.open(ft.SnackBar(content=ft.Text("ADB Keyboard Installed & Enabled!"), bgcolor=ft.Colors.GREEN))
                                else:
                                    page.open(ft.SnackBar(content=ft.Text(f"Failed to install ADB Keyboard: {install_res.stderr}"), bgcolor=ft.Colors.RED))
                            else:
                                page.open(ft.SnackBar(content=ft.Text(f"ADBKeyboard.apk not found at {apk_path}"), bgcolor=ft.Colors.RED))
                        else:
                            # Ensure enabled
                             subprocess.run(["adb", "shell", "ime", "enable", "com.android.adbkeyboard/.AdbIME"], capture_output=True, text=True)
                             # Optional: Set as default
                             subprocess.run(["adb", "shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"], capture_output=True, text=True)
                     except Exception as e:
                        print(f"ADB Keyboard Error: {e}")
                        
                 else:
                     page.open(ft.SnackBar(content=ft.Text(f"Connection Failed: {output}"), bgcolor=ft.Colors.RED))
             except Exception as ex:
                 page.open(ft.SnackBar(content=ft.Text(f"ADB Error: {ex}"), bgcolor=ft.Colors.RED))
             page.update()

        # Run connection in background to avoid freezing UI
        threading.Thread(target=connect_thread, daemon=True).start()

    device_id_input.on_blur = on_device_id_blur

    def clear_task(e):
        task_input.value = ""
        page.update()

    # Task Input
    task_input = ft.TextField(
        label="Task Description",
        multiline=True,
        min_lines=3,
        max_lines=5,
        expand=False, # Fixed: Do not expand, let output take remaining space
        suffix=ft.IconButton(ft.Icons.CLEAR, on_click=clear_task)
    )

    # Output Log
    # Using Column + Text(selectable=True) to allow programmatic scrolling (auto-scroll)
    output_text = ft.Text(
        value="", 
        font_family="Consolas", 
        size=12,
        selectable=True,
    )
    
    output_column = ft.Column(
        [output_text],
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
        auto_scroll=False, # We handle manually with scroll_to for toggle behavior
    )

    output_container = ft.Container(
        content=output_column,
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=5,
        padding=10,
        expand=True, 
        bgcolor=ft.Colors.WHITE
    )

    # Status Indicator
    status_text = ft.Text("Ready", color=ft.Colors.GREEN)

    # Auto Scroll Toggle
    auto_scroll_checkbox = ft.Checkbox(label="Auto Scroll", value=True)

    def append_output(text):
        output_text.value += text
        page.update()
        if auto_scroll_checkbox.value:
            output_column.scroll_to(offset=-1, duration=10)


    def clear_output(e):
        output_text.value = ""
        page.update()

    def run_process_thread(cmd_args):
        # We need to simulate running the script with arguments
        # Save original sys
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_argv = sys.argv
        
        # Redirect
        sys.stdout = OutputRedirector(append_output)
        sys.stderr = sys.stdout # Capture stderr too
        sys.argv = cmd_args

        return_code = 0
        try:
            main_script.main()
        except SystemExit as e:
            return_code = e.code if e.code is not None else 0
        except Exception as e:
            sys.stdout = old_stdout # Restore to print error
            print(f"Error in execution: {e}")
            append_output(f"\nError: {e}\n")
            return_code = 1
        finally:
            # Restore
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.argv = old_argv
            
            # Update UI on main thread
            status_text.value = f"Finished (Exit Code: {return_code})"
            status_text.color = ft.Colors.BLUE if return_code == 0 else ft.Colors.RED
            run_btn.disabled = False
            page.update()

    def on_run_click(e):
        if not task_input.value:
            page.open(ft.SnackBar(content=ft.Text("Please enter a task!")))
            return

        api_key = api_key_input.value.strip()
        
        status_text.value = "Running..."
        status_text.color = ft.Colors.ORANGE
        run_btn.disabled = True
        page.update()
        
        # Build Arguments List (Mocking sys.argv)
        # First arg is script name
        args = ["main.py"]
        
        args.extend(["--base-url", base_url_input.value.strip()])
        args.extend(["--model", model_input.value.strip()])
        
        if lang_dropdown.value:
            args.extend(["--lang", lang_dropdown.value])
        
        if api_key:
            args.extend(["--apikey", api_key])
            
        device_id = device_id_input.value.strip()
        if device_id:
            args.extend(["--device-id", device_id])

        args.append(task_input.value.strip())

        append_output(f"\n> Executing internal: {' '.join(args)}\n\n")

        thread = threading.Thread(target=run_process_thread, args=(args,), daemon=True)
        thread.start()

    def on_stop_click(e):
        # Stopping a thread is unsafe in Python. 
        # For now, we just notify the user.
        page.open(ft.SnackBar(content=ft.Text("Stopping is not supported in this mode."), bgcolor=ft.Colors.GREY))

        
        
    # Buttons
    run_btn = ft.ElevatedButton(
        "Run Task", 
        icon=ft.Icons.PLAY_ARROW, 
        on_click=on_run_click,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE)
    )
    stop_btn = ft.ElevatedButton(
        "Stop", 
        icon=ft.Icons.STOP, 
        on_click=on_stop_click,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED)
    )
    clear_btn = ft.ElevatedButton(
        "Clear Output",
        icon=ft.Icons.CLEAR_ALL,
        on_click=clear_output
    )

    # Layout Construction
    # We use a Column. To achieve the "Fixed Header, Expanded Content" layout:
    # 1. Provide expand=True to the items that should grow (output_container).
    # 2. Dont provide expand to others.
    
    page.add(
        ft.Column(
            controls=[
                # Header Section (Fixed height)
                ft.Row([ft.Image(src=icon_path, width=30, height=30) if icon_path else ft.Icon(ft.Icons.ANDROID, size=30), ft.Text("Open-AutoGLM Controller", size=24, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    [
                        ft.TextButton("使用帮助", icon=ft.Icons.HELP, on_click=open_help),
                        ft.TextButton("获取智普Key", icon=ft.Icons.KEY, on_click=lambda _: page.launch_url("https://docs.bigmodel.cn/cn/api/introduction")),
                        ft.TextButton("Github项目地址", icon=ft.Icons.CODE, on_click=lambda _: page.launch_url("https://github.com/Lama9/Open-AutoGLM-Gui")),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(),
                ft.Row([base_url_input, model_input]),
                ft.Row([api_key_input, lang_dropdown]),
                ft.Row([device_id_input]),
                ft.Divider(),
                ft.Text("Task:", weight=ft.FontWeight.BOLD),
                task_input,
                ft.Row([run_btn, stop_btn, clear_btn, auto_scroll_checkbox, status_text], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(),
                ft.Text("Output:", weight=ft.FontWeight.BOLD),
                
                # Expandable content
                output_container
            ],
            expand=True # The output container inside this column also needs expand=True, which it has. 
                        # But wait, if we put everything in one column and expand only the container, the column should stretch to page.
                        # Actually page.add adds to the page's main view.
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
