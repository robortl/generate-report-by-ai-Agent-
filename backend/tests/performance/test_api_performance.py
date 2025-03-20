#!/usr/bin/env python
"""
API 性能测试 - 测试 API 在不同负载下的性能表现
"""
import os
import sys
import time
import json
import requests
import statistics
import concurrent.futures
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 导入测试环境变量设置
from set_test_env import set_test_env

# 设置测试环境变量
set_test_env()

# API 基础 URL
BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000/api')

class APIPerformanceTest:
    """API 性能测试类"""
    
    def __init__(self):
        """初始化性能测试"""
        # 测试文件路径
        self.test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'meeting_minutes_test.txt')
        
        # 检查测试文件是否存在
        if not os.path.exists(self.test_file_path):
            print(f"错误: 测试文件不存在: {self.test_file_path}")
            sys.exit(1)
        
        # 测试结果
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'endpoints': {}
        }
    
    def test_endpoint(self, endpoint, method='GET', data=None, files=None, iterations=10):
        """测试单个端点的性能"""
        url = f"{BASE_URL}/{endpoint}"
        response_times = []
        
        print(f"\n=== 测试端点: {method} {url} ===")
        print(f"迭代次数: {iterations}")
        
        # 执行多次请求并记录响应时间
        for i in range(iterations):
            start_time = time.time()
            
            try:
                if method == 'GET':
                    response = requests.get(url)
                elif method == 'POST':
                    if files:
                        response = requests.post(url, data=data, files=files)
                    else:
                        response = requests.post(url, json=data)
                else:
                    print(f"不支持的方法: {method}")
                    return
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                # 只有成功的请求才计入响应时间
                if response.status_code < 400:
                    response_times.append(response_time)
                    print(f"请求 {i+1}/{iterations}: {response.status_code} - {response_time:.2f} ms")
                else:
                    print(f"请求 {i+1}/{iterations}: 失败 ({response.status_code}) - {response.text}")
            
            except Exception as e:
                print(f"请求 {i+1}/{iterations}: 错误 - {str(e)}")
        
        # 计算统计数据
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            median_time = statistics.median(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
            
            result = {
                'endpoint': f"{method} {endpoint}",
                'iterations': iterations,
                'success_count': len(response_times),
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'median_time': median_time,
                'p95_time': p95_time
            }
            
            self.results['endpoints'][f"{method} {endpoint}"] = result
            
            print(f"\n结果:")
            print(f"平均响应时间: {avg_time:.2f} ms")
            print(f"最小响应时间: {min_time:.2f} ms")
            print(f"最大响应时间: {max_time:.2f} ms")
            print(f"中位数响应时间: {median_time:.2f} ms")
            print(f"95 百分位响应时间: {p95_time:.2f} ms")
            print(f"成功率: {len(response_times)}/{iterations} ({len(response_times)/iterations*100:.2f}%)")
        else:
            print("没有成功的请求")
    
    def test_concurrent_requests(self, endpoint, method='GET', data=None, files=None, concurrency=10):
        """测试并发请求"""
        url = f"{BASE_URL}/{endpoint}"
        response_times = []
        
        print(f"\n=== 测试并发请求: {method} {url} ===")
        print(f"并发数: {concurrency}")
        
        def make_request():
            start_time = time.time()
            
            try:
                if method == 'GET':
                    response = requests.get(url)
                elif method == 'POST':
                    if files:
                        response = requests.post(url, data=data, files=files)
                    else:
                        response = requests.post(url, json=data)
                else:
                    return None
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                return {
                    'status_code': response.status_code,
                    'response_time': response_time
                }
            
            except Exception as e:
                return {
                    'status_code': 0,
                    'error': str(e)
                }
        
        # 使用线程池并发执行请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrency)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 处理结果
        success_count = 0
        for i, result in enumerate(results):
            if result and 'status_code' in result and result['status_code'] < 400:
                success_count += 1
                response_times.append(result['response_time'])
                print(f"请求 {i+1}/{concurrency}: {result['status_code']} - {result['response_time']:.2f} ms")
            else:
                error = result.get('error', f"状态码: {result.get('status_code')}") if result else "未知错误"
                print(f"请求 {i+1}/{concurrency}: 失败 - {error}")
        
        # 计算统计数据
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            median_time = statistics.median(response_times)
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) >= 20 else max_time
            
            result = {
                'endpoint': f"{method} {endpoint} (并发)",
                'concurrent': concurrency,
                'success_count': success_count,
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'median_time': median_time,
                'p95_time': p95_time
            }
            
            self.results['endpoints'][f"{method} {endpoint} (并发)"] = result
            
            print(f"\n结果:")
            print(f"平均响应时间: {avg_time:.2f} ms")
            print(f"最小响应时间: {min_time:.2f} ms")
            print(f"最大响应时间: {max_time:.2f} ms")
            print(f"中位数响应时间: {median_time:.2f} ms")
            print(f"95 百分位响应时间: {p95_time:.2f} ms")
            print(f"成功率: {success_count}/{concurrency} ({success_count/concurrency*100:.2f}%)")
        else:
            print("没有成功的请求")
    
    def run_all_tests(self):
        """运行所有性能测试"""
        print("=== 开始 API 性能测试 ===")
        start_time = time.time()
        
        # 测试健康检查端点
        self.test_endpoint('health', method='GET', iterations=20)
        
        # 测试获取分类端点
        self.test_endpoint('upload/categories', method='GET', iterations=20)
        
        # 测试获取文件列表端点
        self.test_endpoint('files?limit=10', method='GET', iterations=20)
        
        # 测试文件上传端点
        with open(self.test_file_path, 'rb') as f:
            files = {'file': f}
            data = {'category': 'meeting'}
            self.test_endpoint('upload', method='POST', data=data, files=files, iterations=5)
        
        # 测试并发请求
        self.test_concurrent_requests('upload/categories', method='GET', concurrency=20)
        self.test_concurrent_requests('files?limit=10', method='GET', concurrency=20)
        
        # 输出总结
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n=== 性能测试总结 ===")
        print(f"总测试时间: {total_time:.2f} 秒")
        print(f"测试的端点数: {len(self.results['endpoints'])}")
        
        # 输出每个端点的平均响应时间
        print("\n端点响应时间 (ms):")
        for endpoint, result in self.results['endpoints'].items():
            print(f"{endpoint}: {result['avg_time']:.2f} ms (成功率: {result['success_count']}/{result.get('iterations', result.get('concurrent'))})")
        
        # 保存结果到文件
        self.save_results()
    
    def save_results(self):
        """保存测试结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_test_results_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试结果已保存到: {filepath}")

def main():
    """主函数"""
    test = APIPerformanceTest()
    test.run_all_tests()

if __name__ == '__main__':
    main() 