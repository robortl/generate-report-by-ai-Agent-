#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试获取文件元数据API
专门测试/api/files?file_id=36f4fc32-122a-475c-803d-ee3e183e9c5d接口
"""

import requests
import json
import boto3
import os

# API配置
API_BASE_URL = "http://127.0.0.1:5000"
TEST_FILE_ID = "74632379-0db7-4065-aa46-ff0890b1b4c4"
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1')

def check_dynamodb_directly():
    """直接检查DynamoDB中是否存在该文件"""
    print("\n=== 直接检查DynamoDB ===")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table("report_files")
        
        # 获取表中的所有项目
        print("获取表中的所有项目:")
        response = table.scan(Limit=10)
        items = response.get('Items', [])
        
        print(f"表中共有 {len(items)} 个项目")
        for item in items:
            print(f"- {item.get('file_id')}: {item.get('original_filename')}")
        
        # 尝试获取特定文件
        print(f"\n尝试获取特定文件 {TEST_FILE_ID}:")
        response = table.get_item(Key={'file_id': TEST_FILE_ID})
        item = response.get('Item')
        
        if item:
            print(f"找到文件: {json.dumps(item, indent=2, ensure_ascii=False)}")
        else:
            print(f"未找到文件")
        
        # 创建一个测试文件
        print("\n创建一个测试文件:")
        test_item = {
            'file_id': TEST_FILE_ID,
            'original_filename': 'test_file.txt',
            'category': 'test',
            'created_at': '2025-03-07T12:00:00',
            'status': 'uploaded',
            's3_key': f'uploads/{TEST_FILE_ID}/test_file.txt',
            's3_url': f'https://example.com/uploads/{TEST_FILE_ID}/test_file.txt'
        }
        
        table.put_item(Item=test_item)
        print(f"测试文件已创建: {json.dumps(test_item, indent=2, ensure_ascii=False)}")
        
        # 再次尝试获取特定文件
        print(f"\n再次尝试获取特定文件 {TEST_FILE_ID}:")
        response = table.get_item(Key={'file_id': TEST_FILE_ID})
        item = response.get('Item')
        
        if item:
            print(f"找到文件: {json.dumps(item, indent=2, ensure_ascii=False)}")
        else:
            print(f"未找到文件")
        
    except Exception as e:
        print(f"检查DynamoDB时出错: {str(e)}")

def main():
    """主函数"""
    print(f"=== 测试获取文件元数据API ===")
    print(f"测试文件ID: {TEST_FILE_ID}")
    
    # 首先直接检查DynamoDB
    check_dynamodb_directly()
    
    # 使用查询参数方式
    query_url = f"{API_BASE_URL}/api/files?file_id={TEST_FILE_ID}"
    print(f"\n请求URL (查询参数方式): {query_url}")
    
    try:
        response = requests.get(query_url)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应内容 (查询参数方式):\n{json.dumps(result, indent=2, ensure_ascii=False)}")
                print(f"响应类型: {type(result)}")
                if isinstance(result, dict):
                    print(f"响应键: {list(result.keys())}")
            except json.JSONDecodeError:
                print(f"响应不是有效的JSON: {response.text}")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    
    # 使用路径参数方式
    path_url = f"{API_BASE_URL}/api/files/{TEST_FILE_ID}"
    print(f"\n请求URL (路径参数方式): {path_url}")
    
    try:
        response = requests.get(path_url)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应内容 (路径参数方式):\n{json.dumps(result, indent=2, ensure_ascii=False)}")
                print(f"响应类型: {type(result)}")
                if isinstance(result, dict):
                    print(f"响应键: {list(result.keys())}")
            except json.JSONDecodeError:
                print(f"响应不是有效的JSON: {response.text}")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    
    # 获取所有文件
    all_files_url = f"{API_BASE_URL}/api/files"
    print(f"\n请求URL (获取所有文件): {all_files_url}")
    
    try:
        response = requests.get(all_files_url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容 (获取所有文件):\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")

if __name__ == "__main__":
    main() 