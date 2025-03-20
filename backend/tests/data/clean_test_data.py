#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清理测试数据脚本
用于清理S3存储桶和DynamoDB表中的数据，避免测试干扰
"""

import os
import boto3
import logging
from botocore.exceptions import ClientError
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS资源配置
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'report-langchain-haystack-files')
DYNAMODB_TABLE_PREFIX = 'report'  # 表前缀，实际表名为report_files, report_models, report_reports
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1')

def clean_s3_bucket(preserve_directories=True):
    """清理S3存储桶中的所有对象，但保留目录结构
    
    Args:
        preserve_directories (bool): 是否保留S3目录结构，默认为True
    """
    logger.info(f"开始清理S3存储桶: {S3_BUCKET_NAME}")
    
    # 需要保留的目录前缀
    preserved_prefixes = [
        'uploads/',
        'reports/',
        'temp/',
        'models/'
    ]
    
    try:
        s3 = boto3.resource('s3', region_name=AWS_REGION)
        bucket = s3.Bucket(S3_BUCKET_NAME)
        
        # 列出所有对象
        object_count = 0
        skipped_count = 0
        
        for obj in bucket.objects.all():
            # 如果不需要保留目录结构，直接删除所有对象
            if not preserve_directories:
                obj.delete()
                object_count += 1
                if object_count % 100 == 0:
                    logger.info(f"已删除 {object_count} 个对象")
                continue
                
            # 检查是否是目录对象（以/结尾且大小为0）
            is_directory = obj.key.endswith('/') and obj.size == 0
            
            # 检查是否是需要保留的目录前缀
            should_preserve = False
            for prefix in preserved_prefixes:
                # 保留目录本身或者是目录对象
                if obj.key == prefix or (is_directory and obj.key.startswith(prefix)):
                    should_preserve = True
                    break
            
            if should_preserve:
                logger.debug(f"保留目录: {obj.key}")
                skipped_count += 1
                continue
            
            # 删除非目录对象
            obj.delete()
            object_count += 1
            if object_count % 100 == 0:
                logger.info(f"已删除 {object_count} 个对象")
        
        if preserve_directories:
            logger.info(f"S3存储桶清理完成，共删除 {object_count} 个对象，保留 {skipped_count} 个目录对象")
            
            # 确保所有必要的目录结构存在
            s3_client = boto3.client('s3', region_name=AWS_REGION)
            for prefix in preserved_prefixes:
                try:
                    s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=prefix)
                    logger.debug(f"目录已存在: {prefix}")
                except ClientError:
                    # 如果目录不存在，创建它
                    logger.info(f"创建目录: {prefix}")
                    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=prefix)
        else:
            logger.info(f"S3存储桶清理完成，共删除 {object_count} 个对象")
        
        return True
    except ClientError as e:
        logger.error(f"清理S3存储桶时出错: {str(e)}")
        return False

def clean_dynamodb_table(table_name):
    """清理DynamoDB表中的所有数据"""
    logger.info(f"开始清理DynamoDB表: {table_name}")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table(table_name)
        
        # 获取表的主键
        key_schema = table.key_schema
        if not key_schema:
            logger.error(f"无法获取表 {table_name} 的主键信息")
            return False
        
        hash_key = next((item['AttributeName'] for item in key_schema if item['KeyType'] == 'HASH'), None)
        range_key = next((item['AttributeName'] for item in key_schema if item['KeyType'] == 'RANGE'), None)
        
        if not hash_key:
            logger.error(f"表 {table_name} 没有哈希键")
            return False
        
        # 扫描表中的所有项目
        response = table.scan()
        items = response.get('Items', [])
        
        # 删除所有项目
        item_count = 0
        with table.batch_writer() as batch:
            for item in items:
                key = {hash_key: item[hash_key]}
                if range_key and range_key in item:
                    key[range_key] = item[range_key]
                batch.delete_item(Key=key)
                item_count += 1
        
        logger.info(f"DynamoDB表 {table_name} 清理完成，共删除 {item_count} 个项目")
        return True
    except ClientError as e:
        logger.error(f"清理DynamoDB表 {table_name} 时出错: {str(e)}")
        return False

def clean_all_data(preserve_directories=True):
    """清理所有测试数据
    
    Args:
        preserve_directories (bool): 是否保留S3目录结构，默认为True
    """
    logger.info("开始清理所有测试数据")
    
    # 清理S3存储桶
    s3_result = clean_s3_bucket(preserve_directories)
    
    # 清理DynamoDB表
    dynamodb_tables = [
        f"{DYNAMODB_TABLE_PREFIX}_files",   # 文件元数据表
        f"{DYNAMODB_TABLE_PREFIX}_models",  # 模型表
        f"{DYNAMODB_TABLE_PREFIX}_reports"  # 报告表
    ]
    
    dynamodb_results = []
    for table_name in dynamodb_tables:
        result = clean_dynamodb_table(table_name)
        dynamodb_results.append(result)
    
    # 检查结果
    if s3_result and all(dynamodb_results):
        logger.info("所有测试数据清理完成")
        return True
    else:
        logger.warning("部分测试数据清理失败")
        return False

def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='清理测试数据')
    parser.add_argument('--no-preserve-dirs', action='store_true', 
                        help='不保留S3目录结构（默认保留）')
    args = parser.parse_args()
    
    try:
        clean_all_data(not args.no_preserve_dirs)
    except Exception as e:
        logger.error(f"清理测试数据时发生未预期的错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 