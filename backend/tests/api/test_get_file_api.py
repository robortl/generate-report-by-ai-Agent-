#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试获取文件元数据API
专门测试/api/files?file_id=36f4fc32-122a-475c-803d-ee3e183e9c5d接口
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加应用程序目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API配置
API_BASE_URL = "http://127.0.0.1:5000"
TEST_FILE_ID = "74632379-0db7-4065-aa46-ff0890b1b4c4"

def test_get_file_metadata():
    """测试获取文件元数据API"""
    logger.info(f"=== 测试获取文件元数据API ===")
    logger.info(f"测试文件ID: {TEST_FILE_ID}")
    
    try:
        # 使用查询参数方式
        query_url = f"{API_BASE_URL}/api/files?file_id={TEST_FILE_ID}"
        logger.info(f"请求URL (查询参数方式): {query_url}")
        
        response = requests.get(query_url)
        logger.info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"响应内容 (查询参数方式):\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            logger.error(f"请求失败: {response.text}")
        
        # 使用路径参数方式
        path_url = f"{API_BASE_URL}/api/files/{TEST_FILE_ID}"
        logger.info(f"请求URL (路径参数方式): {path_url}")
        
        response = requests.get(path_url)
        logger.info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"响应内容 (路径参数方式):\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            logger.error(f"请求失败: {response.text}")
        
        # 检查DynamoDB中是否存在该文件
        logger.info("检查DynamoDB中是否存在该文件")
        from app.services.storage import get_metadata_from_dynamodb
        
        try:
            metadata = get_metadata_from_dynamodb(TEST_FILE_ID)
            if metadata:
                logger.info(f"DynamoDB中存在该文件:\n{json.dumps(metadata, indent=2, ensure_ascii=False)}")
            else:
                logger.warning(f"DynamoDB中不存在该文件")
        except Exception as e:
            logger.error(f"检查DynamoDB时出错: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"测试获取文件元数据API时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    try:
        test_get_file_metadata()
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 