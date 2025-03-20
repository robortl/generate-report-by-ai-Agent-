#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接测试Flask应用的API端点
"""

import os
import sys
import json
import logging
import requests

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加应用程序目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API配置
API_BASE_URL = "http://127.0.0.1:5000"
TEST_FILE_ID = "36f4fc32-122a-475c-803d-ee3e183e9c5d"

def test_api_direct():
    """直接测试Flask应用的API端点"""
    logger.info(f"=== 直接测试Flask应用的API端点 ===")
    
    # 首先检查DynamoDB中的数据
    try:
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
        table = dynamodb.Table("report_files")
        
        response = table.get_item(Key={'file_id': TEST_FILE_ID})
        item = response.get('Item')
        
        logger.info(f"DynamoDB中的数据:")
        if item:
            logger.info(f"找到文件: {json.dumps(item, indent=2, ensure_ascii=False)}")
        else:
            logger.warning(f"未找到文件")
    except Exception as e:
        logger.error(f"检查DynamoDB时出错: {str(e)}")
    
    # 测试API端点
    try:
        # 设置环境变量
        os.environ['USE_LOCAL_MOCK'] = 'false'
        logger.info(f"设置USE_LOCAL_MOCK为false")
        
        # 使用查询参数方式
        query_url = f"{API_BASE_URL}/api/files?file_id={TEST_FILE_ID}"
        logger.info(f"请求URL (查询参数方式): {query_url}")
        
        response = requests.get(query_url)
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"响应内容:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            logger.info(f"响应类型: {type(result)}")
            if isinstance(result, dict):
                logger.info(f"响应键: {list(result.keys())}")
        else:
            logger.error(f"请求失败: {response.text}")
        
        # 直接导入Flask应用
        logger.info(f"\n直接导入Flask应用并测试")
        from app import create_app
        
        # 创建测试客户端
        app = create_app()
        with app.test_client() as client:
            # 设置环境变量
            app.config['USE_LOCAL_MOCK'] = 'false'
            logger.info(f"设置app.config['USE_LOCAL_MOCK']为false")
            
            # 使用测试客户端发送请求
            logger.info(f"使用测试客户端请求 /api/files?file_id={TEST_FILE_ID}")
            response = client.get(f"/api/files?file_id={TEST_FILE_ID}")
            
            logger.info(f"状态码: {response.status_code}")
            if response.status_code == 200:
                result = json.loads(response.data)
                logger.info(f"响应内容:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
                logger.info(f"响应类型: {type(result)}")
                if isinstance(result, dict):
                    logger.info(f"响应键: {list(result.keys())}")
            else:
                logger.error(f"请求失败: {response.data}")
        
        return True
    except Exception as e:
        logger.error(f"测试API端点时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    try:
        test_api_direct()
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 