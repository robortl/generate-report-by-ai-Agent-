#!/usr/bin/env python
"""
测试执行脚本 - 运行所有测试
"""
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

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

def run_unit_tests(args):
    """运行单元测试"""
    if args.skip_unit:
        print("跳过单元测试")
        return True
    
    command = [sys.executable, "tests/run_tests.py"]
    if args.coverage:
        command.extend(["--cov=app", "--cov-report=term", "--cov-report=html:coverage_html"])
    
    return run_command(command, "单元测试")

def run_functional_tests(args):
    """运行功能测试"""
    if args.skip_functional:
        print("跳过功能测试")
        return True
    
    # 确保功能测试目录存在
    os.makedirs("tests/functional", exist_ok=True)
    
    success = True
    
    # 运行报告生成功能测试
    if os.path.exists("tests/functional/test_report_generation.py"):
        command = [sys.executable, "tests/functional/test_report_generation.py"]
        success = run_command(command, "报告生成功能测试") and success
    
    return success

def run_integration_tests(args):
    """运行集成测试"""
    if args.skip_integration:
        print("跳过集成测试")
        return True
    
    # 确保集成测试目录存在
    os.makedirs("tests/integration", exist_ok=True)
    
    # 检查后端服务是否运行
    import requests
    try:
        response = requests.get("http://localhost:5000/health")
        if response.status_code != 200:
            print("警告: 后端服务未正常运行，集成测试可能会失败")
    except requests.exceptions.ConnectionError:
        print("警告: 无法连接到后端服务，集成测试可能会失败")
    
    command = [sys.executable, "tests/integration/test_api_integration.py"]
    return run_command(command, "集成测试")

def run_performance_tests(args):
    """运行性能测试"""
    if args.skip_performance:
        print("跳过性能测试")
        return True
    
    # 确保性能测试目录存在
    os.makedirs("tests/performance", exist_ok=True)
    
    command = [sys.executable, "tests/performance/test_api_performance.py"]
    return run_command(command, "性能测试")

def run_security_tests(args):
    """运行安全测试"""
    if args.skip_security:
        print("跳过安全测试")
        return True
    
    # 确保安全测试目录存在
    os.makedirs("tests/security", exist_ok=True)
    
    command = [sys.executable, "tests/security/test_api_security.py"]
    return run_command(command, "安全测试")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行所有测试")
    parser.add_argument("--skip-unit", action="store_true", help="跳过单元测试")
    parser.add_argument("--skip-functional", action="store_true", help="跳过功能测试")
    parser.add_argument("--skip-integration", action="store_true", help="跳过集成测试")
    parser.add_argument("--skip-performance", action="store_true", help="跳过性能测试")
    parser.add_argument("--skip-security", action="store_true", help="跳过安全测试")
    parser.add_argument("--coverage", action="store_true", help="生成代码覆盖率报告")
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*80}")
    print(f"=== 开始测试 ({timestamp}) ===")
    print(f"{'='*80}\n")
    
    # 添加项目根目录到 Python 路径
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    
    # 运行各类测试
    unit_success = run_unit_tests(args)
    functional_success = run_functional_tests(args)
    integration_success = run_integration_tests(args)
    performance_success = run_performance_tests(args)
    security_success = run_security_tests(args)
    
    # 记录结束时间
    end_time = time.time()
    total_time = end_time - start_time
    
    # 输出测试结果摘要
    print(f"\n{'='*80}")
    print(f"=== 测试结果摘要 ===")
    print(f"{'='*80}")
    print(f"单元测试: {'通过' if unit_success else '失败'}")
    print(f"功能测试: {'通过' if functional_success else '失败'}")
    print(f"集成测试: {'通过' if integration_success else '失败'}")
    print(f"性能测试: {'通过' if performance_success else '失败'}")
    print(f"安全测试: {'通过' if security_success else '失败'}")
    print(f"{'='*80}")
    print(f"总测试时间: {total_time:.2f} 秒")
    print(f"{'='*80}\n")
    
    # 返回退出码
    all_success = unit_success and functional_success and integration_success and performance_success and security_success
    sys.exit(0 if all_success else 1)

if __name__ == "__main__":
    main() 