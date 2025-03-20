#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试上传文件API接口
先清理测试数据，然后上传文件，最后验证文件元数据是否正确保存到DynamoDB
"""

import os
import sys
import json
import requests
import logging
import time
import boto3
from datetime import datetime
import uuid

# 导入清理脚本
from clean_test_data import clean_all_data

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API基础URL
API_BASE_URL = 'http://127.0.0.1:5000'

# AWS资源配置
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'report-langchain-haystack-files')
DYNAMODB_TABLE_PREFIX = 'report'  # 表前缀，实际表名为report_files, report_models, report_reports
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1')

def create_test_file():
    """创建测试文件"""
    logger.info("创建测试文件")
    
    # 创建一个临时文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"test_record_{timestamp}.txt"
    file_path = f"test_record_{timestamp}.txt"
    
    # 写入一些测试内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件，用于API集成测试。\n")
        f.write(f"创建时间: {timestamp}\n")
        f.write("会议内容：\n")
        f.write("张三：大家好，今天我们讨论一下项目进度。\n")
        f.write("李四：好的，我这边的模块已经完成了80%。\n")
        f.write("王五：我负责的部分也已经测试通过了。\n")
        f.write("张三：太好了，看来我们可以按时交付了。\n")
    
    logger.info(f"测试文件已创建: {file_path}")
    return file_path, file_name

def upload_file(file_path, file_name, category="meeting"):
    """上传文件到API"""
    logger.info(f"上传文件: {file_path}, 分类: {category}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            data = {'category': category}
            response = requests.post(f"{API_BASE_URL}/api/upload", files=files, data=data)
        
        if response.status_code not in [200, 201]:
            logger.error(f"上传文件失败: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return None
        
        result = response.json()
        file_id = result.get('file_id')
        logger.info(f"文件上传成功，ID: {file_id}")
        return file_id
    except Exception as e:
        logger.error(f"上传文件时出错: {str(e)}")
        return None

def verify_file_in_s3(file_id):
    """验证文件是否存在于S3存储桶中"""
    logger.info(f"验证文件是否存在于S3: {file_id}")
    
    try:
        s3 = boto3.client('s3', region_name=AWS_REGION)
        
        # 列出存储桶中的对象
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=f"uploads/{file_id}")
        
        if 'Contents' in response and len(response['Contents']) > 0:
            logger.info(f"文件存在于S3: {response['Contents'][0]['Key']}")
            return True
        else:
            logger.error(f"文件不存在于S3: {file_id}")
            return False
    except Exception as e:
        logger.error(f"验证S3文件时出错: {str(e)}")
        return False

def verify_metadata_in_dynamodb(file_id):
    """验证文件元数据是否存在于DynamoDB中"""
    logger.info(f"验证文件元数据是否存在于DynamoDB: {file_id}")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}_files")
        
        # 获取文件元数据
        response = table.get_item(Key={'file_id': file_id})
        
        if 'Item' in response:
            metadata = response['Item']
            logger.info(f"文件元数据存在于DynamoDB: {json.dumps(metadata, indent=2)}")
            return metadata
        else:
            logger.error(f"文件元数据不存在于DynamoDB: {file_id}")
            return None
    except Exception as e:
        logger.error(f"验证DynamoDB元数据时出错: {str(e)}")
        return None

def get_file_metadata_via_api(file_id):
    """通过API获取文件元数据"""
    logger.info(f"通过API获取文件元数据: {file_id}")
    
    try:
        # 使用单个文件API
        response = requests.get(f"{API_BASE_URL}/api/files/{file_id}")
        
        if response.status_code != 200:
            logger.error(f"通过API获取文件元数据失败: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            
            # 尝试使用查询参数API
            response = requests.get(f"{API_BASE_URL}/api/files?file_id={file_id}")
            
            if response.status_code != 200:
                logger.error(f"通过查询参数API获取文件元数据失败: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
                return None
        
        result = response.json()
        logger.info(f"API返回的文件元数据: {json.dumps(result, indent=2)}")
        
        # 处理返回的数据格式
        if isinstance(result, dict) and 'items' in result:
            # 返回的是文件列表，尝试在列表中找到匹配的文件
            file_metadata = None
            for item in result['items']:
                if item.get('file_id') == file_id:
                    file_metadata = item
                    break
            
            if not file_metadata:
                logger.error(f"在API返回的文件列表中未找到匹配的文件ID: {file_id}")
                return None
            
            return file_metadata
        else:
            # 返回的是单个文件的元数据
            return result
    except Exception as e:
        logger.error(f"通过API获取文件元数据时出错: {str(e)}")
        return None

def test_upload_workflow():
    """测试上传文件工作流程"""
    logger.info("=== 开始测试上传文件工作流程 ===")
    
    # 清理测试数据
    logger.info("清理测试数据")
    clean_all_data()
    
    # 创建测试文件
    file_path, file_name = create_test_file()
    
    try:
        # 上传文件
        file_id = upload_file(file_path, file_name)
        if not file_id:
            logger.error("上传文件失败")
            return False
        
        # 等待一段时间，确保数据已经保存
        logger.info("等待3秒，确保数据已经保存")
        time.sleep(3)
        
        # 验证文件是否存在于S3
        s3_result = verify_file_in_s3(file_id)
        if not s3_result:
            logger.error("文件不存在于S3")
            return False
        
        # 验证文件元数据是否存在于DynamoDB
        dynamodb_result = verify_metadata_in_dynamodb(file_id)
        if not dynamodb_result:
            logger.error("文件元数据不存在于DynamoDB")
            return False
        
        # 通过API获取文件元数据
        api_result = get_file_metadata_via_api(file_id)
        if not api_result:
            logger.error("通过API获取文件元数据失败")
            return False
        
        # 验证元数据是否一致
        if dynamodb_result.get('file_id') != api_result.get('file_id'):
            logger.error(f"文件ID不一致: DynamoDB={dynamodb_result.get('file_id')}, API={api_result.get('file_id')}")
            return False
        
        logger.info("测试上传文件工作流程成功")
        return True
    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"临时文件已删除: {file_path}")

def main():
    """主函数"""
    try:
        result = test_upload_workflow()
        if result:
            logger.info("测试成功")
            sys.exit(0)
        else:
            logger.error("测试失败")
            sys.exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生未预期的错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 