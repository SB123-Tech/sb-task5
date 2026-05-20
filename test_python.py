#!/usr/bin/env python3
"""环境验证测试脚本 — 验证 Python 及常用深度学习包是否正常安装。"""

import sys

def check_package(name):
    """尝试导入一个包，返回版本号或失败信息。"""
    try:
        mod = __import__(name)
        version = getattr(mod, '__version__', '已安装（无版本号）')
        return True, version
    except ImportError:
        return False, None

def main():
    print("=" * 50)
    print("   环境验证测试")
    print("=" * 50)
    print(f"Python 版本: {sys.version}")
    print()

    packages = ['numpy', 'pandas', 'torch', 'matplotlib', 'sklearn', 'requests']
    all_ok = True

    for pkg in packages:
        ok, version = check_package(pkg)
        status = "OK" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{status}] {pkg:15s} {version or '未安装'}")

    print()
    print("=" * 50)

    if all_ok:
        print("所有包安装成功！环境验证通过！")
    else:
        print("部分包未安装，请检查 requirements.txt 和安装过程。")
        sys.exit(1)

    print("=" * 50)

if __name__ == '__main__':
    main()
