
import PyInstaller.__main__
import os

# 确保在当前目录下
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("开始打包 Open-AutoGLM GUI...")

PyInstaller.__main__.run([
    'gui.py',
    '--name=OpenAutoGLMGui',
    '--onedir',  # 使用单文件夹模式，排查问题更方便，也更稳定
    '--windowed', # 不显示控制台窗口
    '--noconfirm',
    '--clean',
    '--icon=resources/logo.ico', # 设置 EXE 图标
    # 添加数据文件 (如果 main.py 依赖某些资源文件，需要在这里添加)
    # 比如 resources 文件夹: '--add-data=resources;resources'
    # 暂时添加 resources 文件夹作为示例，如果不存在会警告但不会失败 (取决于具体的 PyInstaller 版本行为)
    # '--add-data=resources;resources', 
    
    # Hidden imports: 因为 main.py 是动态导入的或者 flet 可能有的隐式依赖
    '--hidden-import=flet',
    '--hidden-import=phone_agent',
    # main.py 的依赖
    '--hidden-import=openai',
    '--hidden-import=PIL',
    
    # Bundle ADB Keyboard APK
    f'--add-data={r"ADBKeyboard.apk"};.',
    
    # Bundle Resources (for window icon etc)
    f'--add-data={r"resources"};resources',
    
    # 显式添加 Anaconda 的 DLLs (根据用户报错调整)
    # 注意: windows下分隔符是 ;
    f'--add-binary={r"C:\ProgramData\anaconda3\Library\bin\libssl-3-x64.dll"};.',
    f'--add-binary={r"C:\ProgramData\anaconda3\Library\bin\libcrypto-3-x64.dll"};.',
    f'--add-binary={r"C:\ProgramData\anaconda3\Library\bin\ffi.dll"};.', # ctypes 需要这个 (名称可能是 ffi.dll)
    
    # 包含了用户指定的 ADB 工具
    # f'--add-binary={r"E:\code\Android\SDK\android-sdk-windows\platform-tools\adb.exe"};platform-tools',
    # f'--add-binary={r"E:\code\Android\SDK\android-sdk-windows\platform-tools\AdbWinApi.dll"};platform-tools',
    # f'--add-binary={r"E:\code\Android\SDK\android-sdk-windows\platform-tools\AdbWinUsbApi.dll"};platform-tools',
    # f'--add-binary={r"E:\code\Android\SDK\android-sdk-windows\platform-tools\libwinpthread-1.dll"};platform-tools',
    f'--add-binary={r"platform-tools\adb.exe"};platform-tools',
    f'--add-binary={r"platform-tools\AdbWinApi.dll"};platform-tools',
    f'--add-binary={r"platform-tools\AdbWinUsbApi.dll"};platform-tools',
    f'--add-binary={r"platform-tools\libwinpthread-1.dll"};platform-tools',
])

print("打包完成！")
print("生成的可执行文件位于 .\\dist\\OpenAutoGLMGui\\OpenAutoGLMGui.exe")
