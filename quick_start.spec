# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['quick_start.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('templates', 'templates'),
        ('templates_win', 'templates_win'),
        ('logs', 'logs'),
        ('requirements.txt', '.'),
        ('spine_automation.py', '.'),
        ('automation.py', '.'),
        ('click_manager.py', '.'),
        ('config_manager.py', '.'),
        ('template_manager.py', '.'),
        ('window_manager.py', '.'),
    ],
    hiddenimports=[
        'pyautogui',
        'opencv-python',
        'cv2',
        'pillow',
        'PIL',
        'pygetwindow',
        'numpy',
        'pywin32',
        'psutil',
        'logging',
        'json',
        'pathlib',
        'typing',
        'dataclasses',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='spAutomation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='spAutomation',
)
