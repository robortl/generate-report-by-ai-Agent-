#!/usr/bin/env python
"""
从根目录运行测试的简单脚本
"""
import os
import sys
import subprocess

if __name__ == '__main__':
    # 获取命令行参数
    args = sys.argv[1:]
    
    # 构建命令
    command = [sys.executable, "tests/run_tests.py"] + args
    
    # 运行命令
    result = subprocess.run(command)
    
    # 返回退出码
    sys.exit(result.returncode) 