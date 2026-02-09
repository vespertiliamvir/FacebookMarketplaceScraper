# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect any hidden imports that PyInstaller might miss
# dynamic imports or imports inside functions often get missed
hidden_imports = [
    'scraper.auth',
    'scraper.parallel_manager',
    'scraper.config',
    'scraper.facebook_scraper',
    'scraper.preferences',
    'scraper.utils',
    'scraper.price_comparator',
    'scraper.data_processor',
    'scraper.csv_exporter',
    'scraper.description_scraper',
    'selenium',
    'webdriver_manager',
    'colorama',
    'tqdm',
    'bs4',
    'requests',
    'pandas'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FacebookMarketplaceScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
