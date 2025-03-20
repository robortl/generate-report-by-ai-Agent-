#!/usr/bin/env python
"""
API 安全测试 - 测试 API 的安全性
"""
import os
import sys
import json
import requests
import unittest
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 导入测试环境变量设置
from set_test_env import set_test_env

# 设置测试环境变量
set_test_env()

# API 基础 URL
BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000')

class APISecurityTest(unittest.TestCase):
    """API 安全测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 测试文件路径
        self.test_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'meeting_minutes_test.txt')
        
        # 如果测试文件不存在，则跳过测试
        if not os.path.exists(self.test_file_path):
            self.skipTest(f"测试文件不存在: {self.test_file_path}")
        
        # 测试结果
        self.results = []
        
        # 检查 API 服务是否可用
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                self.skipTest("API 服务不可用")
        except requests.exceptions.ConnectionError:
            self.skipTest("无法连接到 API 服务")
    
    def test_sql_injection(self):
        """测试 SQL 注入漏洞"""
        print("\n=== 测试 SQL 注入漏洞 ===")
        
        # SQL 注入测试向量
        sql_injection_vectors = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users; --",
            "' OR '1'='1' --",
            "admin' --"
        ]
        
        # 测试端点
        endpoints = [
            {'url': 'files', 'method': 'GET', 'param': 'category'},
            {'url': 'report/1', 'method': 'GET'}
        ]
        
        for endpoint in endpoints:
            url = f"{BASE_URL}/{endpoint['url']}"
            method = endpoint['method']
            
            print(f"\n测试端点: {method} {url}")
            
            for vector in sql_injection_vectors:
                try:
                    if method == 'GET' and 'param' in endpoint:
                        test_url = f"{url}?{endpoint['param']}={vector}"
                        response = requests.get(test_url)
                    else:
                        response = requests.get(url.replace('1', vector))
                    
                    # 检查响应
                    if response.status_code == 500:
                        self.results.append({
                            'test': 'SQL 注入',
                            'endpoint': f"{method} {url}",
                            'vector': vector,
                            'status_code': response.status_code,
                            'result': '可能存在漏洞',
                            'details': '服务器返回 500 错误'
                        })
                        print(f"向量 '{vector}': 可能存在漏洞 (状态码: {response.status_code})")
                    elif 'error' in response.text.lower() and 'sql' in response.text.lower():
                        self.results.append({
                            'test': 'SQL 注入',
                            'endpoint': f"{method} {url}",
                            'vector': vector,
                            'status_code': response.status_code,
                            'result': '可能存在漏洞',
                            'details': '响应中包含 SQL 错误信息'
                        })
                        print(f"向量 '{vector}': 可能存在漏洞 (响应包含 SQL 错误)")
                    else:
                        self.results.append({
                            'test': 'SQL 注入',
                            'endpoint': f"{method} {url}",
                            'vector': vector,
                            'status_code': response.status_code,
                            'result': '未发现漏洞',
                            'details': '响应正常'
                        })
                        print(f"向量 '{vector}': 未发现漏洞 (状态码: {response.status_code})")
                
                except Exception as e:
                    self.results.append({
                        'test': 'SQL 注入',
                        'endpoint': f"{method} {url}",
                        'vector': vector,
                        'result': '测试失败',
                        'details': str(e)
                    })
                    print(f"向量 '{vector}': 测试失败 - {str(e)}")
    
    def test_xss(self):
        """测试跨站脚本 (XSS) 漏洞"""
        print("\n=== 测试跨站脚本 (XSS) 漏洞 ===")
        
        # XSS 测试向量
        xss_vectors = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(\"XSS\")'>",
            "<body onload='alert(\"XSS\")'>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>"
        ]
        
        # 测试上传文件名中的 XSS
        with open(self.test_file_path, 'rb') as f:
            for vector in xss_vectors:
                try:
                    # 创建带有 XSS 向量的文件名
                    files = {'file': (f"test{vector}.txt", f, 'text/plain')}
                    data = {'category': 'meeting'}
                    
                    response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
                    
                    # 检查响应
                    if response.status_code == 201:
                        self.results.append({
                            'test': 'XSS',
                            'endpoint': 'POST /upload',
                            'vector': vector,
                            'status_code': response.status_code,
                            'result': '可能存在漏洞',
                            'details': '服务器接受了带有 XSS 向量的文件名'
                        })
                        print(f"向量 '{vector}': 可能存在漏洞 (状态码: {response.status_code})")
                    else:
                        self.results.append({
                            'test': 'XSS',
                            'endpoint': 'POST /upload',
                            'vector': vector,
                            'status_code': response.status_code,
                            'result': '未发现漏洞',
                            'details': '服务器拒绝了带有 XSS 向量的文件名'
                        })
                        print(f"向量 '{vector}': 未发现漏洞 (状态码: {response.status_code})")
                
                except Exception as e:
                    self.results.append({
                        'test': 'XSS',
                        'endpoint': 'POST /upload',
                        'vector': vector,
                        'result': '测试失败',
                        'details': str(e)
                    })
                    print(f"向量 '{vector}': 测试失败 - {str(e)}")
        
        # 测试报告内容中的 XSS
        for vector in xss_vectors:
            try:
                # 创建带有 XSS 向量的报告内容
                data = {
                    'content': f"Test report with XSS: {vector}"
                }
                
                response = requests.put(f"{BASE_URL}/report/test-report-id", json=data)
                
                # 检查响应
                if response.status_code < 400:
                    self.results.append({
                        'test': 'XSS',
                        'endpoint': 'PUT /report/{report_id}',
                        'vector': vector,
                        'status_code': response.status_code,
                        'result': '可能存在漏洞',
                        'details': '服务器接受了带有 XSS 向量的报告内容'
                    })
                    print(f"向量 '{vector}': 可能存在漏洞 (状态码: {response.status_code})")
                else:
                    self.results.append({
                        'test': 'XSS',
                        'endpoint': 'PUT /report/{report_id}',
                        'vector': vector,
                        'status_code': response.status_code,
                        'result': '未发现漏洞',
                        'details': '服务器拒绝了带有 XSS 向量的报告内容'
                    })
                    print(f"向量 '{vector}': 未发现漏洞 (状态码: {response.status_code})")
            
            except Exception as e:
                self.results.append({
                    'test': 'XSS',
                    'endpoint': 'PUT /report/{report_id}',
                    'vector': vector,
                    'result': '测试失败',
                    'details': str(e)
                })
                print(f"向量 '{vector}': 测试失败 - {str(e)}")
    
    def test_file_upload_security(self):
        """测试文件上传安全性"""
        print("\n=== 测试文件上传安全性 ===")
        
        # 恶意文件类型
        malicious_file_types = [
            {'name': 'test.php', 'content': '<?php echo "Malicious PHP code"; ?>', 'type': 'application/x-php'},
            {'name': 'test.js', 'content': 'alert("Malicious JavaScript code");', 'type': 'application/javascript'},
            {'name': 'test.html', 'content': '<script>alert("Malicious HTML");</script>', 'type': 'text/html'},
            {'name': 'test.exe', 'content': b'MZ\x90\x00\x03\x00\x00\x00\x04\x00', 'type': 'application/octet-stream'},
            {'name': 'test.txt.php', 'content': '<?php echo "Hidden PHP code"; ?>', 'type': 'text/plain'}
        ]
        
        for file_type in malicious_file_types:
            try:
                # 创建临时文件
                if isinstance(file_type['content'], str):
                    content = file_type['content'].encode('utf-8')
                else:
                    content = file_type['content']
                
                files = {'file': (file_type['name'], content, file_type['type'])}
                data = {'category': 'meeting'}
                
                response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
                
                # 检查响应
                if response.status_code == 201:
                    self.results.append({
                        'test': '文件上传安全性',
                        'file_type': file_type['name'],
                        'status_code': response.status_code,
                        'result': '可能存在漏洞',
                        'details': f"服务器接受了恶意文件类型: {file_type['name']}"
                    })
                    print(f"文件类型 '{file_type['name']}': 可能存在漏洞 (状态码: {response.status_code})")
                else:
                    self.results.append({
                        'test': '文件上传安全性',
                        'file_type': file_type['name'],
                        'status_code': response.status_code,
                        'result': '未发现漏洞',
                        'details': f"服务器拒绝了恶意文件类型: {file_type['name']}"
                    })
                    print(f"文件类型 '{file_type['name']}': 未发现漏洞 (状态码: {response.status_code})")
            
            except Exception as e:
                self.results.append({
                    'test': '文件上传安全性',
                    'file_type': file_type['name'],
                    'result': '测试失败',
                    'details': str(e)
                })
                print(f"文件类型 '{file_type['name']}': 测试失败 - {str(e)}")
    
    def test_cors_security(self):
        """测试 CORS 安全配置"""
        print("\n=== 测试 CORS 安全配置 ===")
        
        # 测试端点
        endpoints = [
            {'url': 'health', 'method': 'GET'},
            {'url': 'upload/categories', 'method': 'GET'},
            {'url': 'files', 'method': 'GET'}
        ]
        
        for endpoint in endpoints:
            url = f"{BASE_URL}/{endpoint['url']}" if endpoint['url'] == 'health' else f"{BASE_URL}/{endpoint['url']}"
            
            try:
                # 发送带有 Origin 头的请求
                headers = {'Origin': 'https://malicious-site.com'}
                response = requests.get(url, headers=headers)
                
                # 检查 CORS 头
                if 'Access-Control-Allow-Origin' in response.headers:
                    allow_origin = response.headers['Access-Control-Allow-Origin']
                    
                    if allow_origin == '*' or allow_origin == 'https://malicious-site.com':
                        self.results.append({
                            'test': 'CORS 安全配置',
                            'endpoint': f"{endpoint['method']} {url}",
                            'result': '可能存在漏洞',
                            'details': f"服务器允许来自任意源的请求: {allow_origin}"
                        })
                        print(f"端点 '{url}': 可能存在漏洞 (Access-Control-Allow-Origin: {allow_origin})")
                    else:
                        self.results.append({
                            'test': 'CORS 安全配置',
                            'endpoint': f"{endpoint['method']} {url}",
                            'result': '未发现漏洞',
                            'details': f"服务器限制了允许的源: {allow_origin}"
                        })
                        print(f"端点 '{url}': 未发现漏洞 (Access-Control-Allow-Origin: {allow_origin})")
                else:
                    self.results.append({
                        'test': 'CORS 安全配置',
                        'endpoint': f"{endpoint['method']} {url}",
                        'result': '未发现漏洞',
                        'details': "服务器未设置 CORS 头"
                    })
                    print(f"端点 '{url}': 未发现漏洞 (未设置 CORS 头)")
            
            except Exception as e:
                self.results.append({
                    'test': 'CORS 安全配置',
                    'endpoint': f"{endpoint['method']} {url}",
                    'result': '测试失败',
                    'details': str(e)
                })
                print(f"端点 '{url}': 测试失败 - {str(e)}")
    
    def save_results(self):
        """保存测试结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"security_test_results_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试结果已保存到: {filepath}")
        
        # 统计结果
        vulnerabilities = [r for r in self.results if r.get('result') == '可能存在漏洞']
        print(f"\n发现 {len(vulnerabilities)} 个潜在安全问题")
        
        if vulnerabilities:
            print("\n潜在安全问题:")
            for v in vulnerabilities:
                print(f"- {v.get('test')}: {v.get('endpoint', v.get('file_type', ''))} - {v.get('details')}")

def run_tests():
    """运行安全测试"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(APISecurityTest))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 保存测试结果
    if hasattr(result, 'security_test') and isinstance(result.security_test, APISecurityTest):
        result.security_test.save_results()

if __name__ == '__main__':
    run_tests() 