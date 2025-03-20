#!/usr/bin/env python
"""
统一的测试运行脚本 - 运行所有类型的测试
"""
import os
import sys
import time
import argparse
import pytest
import coverage
import unittest
import subprocess
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 导入测试环境变量设置
try:
    from tests.utils.set_test_env import set_test_env
except ImportError:
    from utils.set_test_env import set_test_env

def run_command(command, description):
    """运行命令并返回结果"""
    print(f"\n{'='*80}")
    print(f"=== {description} ===")
    print(f"{'='*80}")
    print(f"命令: {' '.join(command)}")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"=== {description} 完成 ===")
    print(f"耗时: {end_time - start_time:.2f} 秒")
    print(f"退出码: {result.returncode}")
    print(f"{'='*80}\n")
    
    if result.stdout:
        print("输出:")
        print(result.stdout)
    
    if result.stderr:
        print("错误:")
        print(result.stderr)
    
    return result.returncode == 0

def run_unit_tests(coverage_enabled=False):
    """运行单元测试"""
    print("\n=== 运行单元测试 ===\n")
    
    # 设置测试环境变量
    set_test_env()
    
    # 构建命令
    command = [sys.executable, "-m", "pytest", "-xvs"]
    
    # 添加覆盖率参数
    if coverage_enabled:
        command.extend(["--cov=app", "--cov-report=term", "--cov-report=html:coverage_html"])
    
    # 添加测试文件
    command.extend(['tests/test_report.py', 'tests/test_files.py'])
    
    # 运行命令
    return run_command(command, "单元测试")

def run_functional_tests():
    """运行功能测试"""
    print("\n=== 运行功能测试 ===\n")
    
    # 设置测试环境变量
    set_test_env()
    
    # 使用unittest运行功能测试
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/functional', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_integration_tests():
    """运行集成测试"""
    print("\n=== 运行集成测试 ===\n")
    
    # 设置测试环境变量
    set_test_env()
    
    # 使用unittest运行集成测试
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/integration', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_api_tests():
    """运行API测试"""
    print("\n=== 运行API测试 ===\n")
    
    # 设置测试环境变量
    set_test_env()
    
    # 使用unittest运行API测试
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests/api', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_all_tests(coverage_enabled=False):
    """运行所有测试"""
    results = []
    results.append(run_unit_tests(coverage_enabled))
    results.append(run_functional_tests())
    results.append(run_integration_tests())
    results.append(run_api_tests())
    
    return all(results)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行测试')
    parser.add_argument('--unit', action='store_true', help='只运行单元测试')
    parser.add_argument('--functional', action='store_true', help='只运行功能测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--api', action='store_true', help='只运行API测试')
    parser.add_argument('--coverage', action='store_true', help='启用代码覆盖率测量')
    args = parser.parse_args()
    
    # 如果没有指定任何测试类型，则运行所有测试
    if not (args.unit or args.functional or args.integration or args.api):
        success = run_all_tests(args.coverage)
    else:
        results = []
        if args.unit:
            results.append(run_unit_tests(args.coverage))
        if args.functional:
            results.append(run_functional_tests())
        if args.integration:
            results.append(run_integration_tests())
        if args.api:
            results.append(run_api_tests())
        success = all(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 