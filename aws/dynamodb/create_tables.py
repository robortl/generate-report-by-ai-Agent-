#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DynamoDB表创建脚本
DynamoDB Table Creation Script
DynamoDBテーブル作成スクリプト
"""

import os
import sys
import argparse
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """加载配置"""
    # 加载.env文件
    load_dotenv()
    
    # 获取环境变量
    config = {
        'aws_region': os.getenv('AWS_REGION', 'ap-northeast-1'),
        'aws_profile': os.getenv('AWS_PROFILE', 'default'),
        'dynamodb_table_prefix': os.getenv('DYNAMODB_TABLE_PREFIX', 'report_')
    }
    
    return config

def create_dynamodb_client(config, profile=None):
    """创建DynamoDB客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    dynamodb_client = session.client('dynamodb')
    
    return dynamodb_client

def create_files_table(dynamodb_client, table_name):
    """创建文件表"""
    try:
        # 检查表是否已存在
        try:
            dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"表 {table_name} 已存在")
            return True
        except ClientError as e:
            # 如果表不存在，则创建
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"创建表 {table_name}")
                
                # 创建表
                response = dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'file_id', 'KeyType': 'HASH'},  # 分区键
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'file_id', 'AttributeType': 'S'},
                        {'AttributeName': 'upload_date', 'AttributeType': 'S'},
                        {'AttributeName': 'category', 'AttributeType': 'S'},
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'upload_date-index',
                            'KeySchema': [
                                {'AttributeName': 'upload_date', 'KeyType': 'HASH'},
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        },
                        {
                            'IndexName': 'category-index',
                            'KeySchema': [
                                {'AttributeName': 'category', 'KeyType': 'HASH'},
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                
                logger.info(f"表 {table_name} 创建成功")
                return True
            else:
                logger.error(f"检查表时出错: {e}")
                return False
    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        return False

def create_reports_table(dynamodb_client, table_name):
    """创建报告表"""
    try:
        # 检查表是否已存在
        try:
            dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"表 {table_name} 已存在")
            return True
        except ClientError as e:
            # 如果表不存在，则创建
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"创建表 {table_name}")
                
                # 创建表
                response = dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'report_id', 'KeyType': 'HASH'},  # 分区键
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'report_id', 'AttributeType': 'S'},
                        {'AttributeName': 'file_id', 'AttributeType': 'S'},
                        {'AttributeName': 'creation_date', 'AttributeType': 'S'},
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'file_id-index',
                            'KeySchema': [
                                {'AttributeName': 'file_id', 'KeyType': 'HASH'},
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        },
                        {
                            'IndexName': 'creation_date-index',
                            'KeySchema': [
                                {'AttributeName': 'creation_date', 'KeyType': 'HASH'},
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                
                logger.info(f"表 {table_name} 创建成功")
                return True
            else:
                logger.error(f"检查表时出错: {e}")
                return False
    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        return False

def create_models_table(dynamodb_client, table_name):
    """创建模型表"""
    try:
        # 检查表是否已存在
        try:
            dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"表 {table_name} 已存在")
            return True
        except ClientError as e:
            # 如果表不存在，则创建
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"创建表 {table_name}")
                
                # 创建表
                response = dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'model_id', 'KeyType': 'HASH'},  # 分区键
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'model_id', 'AttributeType': 'S'},
                        {'AttributeName': 'provider', 'AttributeType': 'S'},
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'provider-index',
                            'KeySchema': [
                                {'AttributeName': 'provider', 'KeyType': 'HASH'},
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                
                logger.info(f"表 {table_name} 创建成功")
                return True
            else:
                logger.error(f"检查表时出错: {e}")
                return False
    except Exception as e:
        logger.error(f"创建表时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='创建和配置DynamoDB表')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--files-table', help='文件表名称（覆盖环境变量）')
    parser.add_argument('--reports-table', help='报告表名称（覆盖环境变量）')
    parser.add_argument('--models-table', help='模型表名称（覆盖环境变量）')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 命令行参数覆盖环境变量
    if args.files_table:
        config['files_table_name'] = args.files_table
    if args.reports_table:
        config['reports_table_name'] = args.reports_table
    if args.models_table:
        config['models_table_name'] = args.models_table
    
    # 创建DynamoDB客户端
    dynamodb_client = create_dynamodb_client(config, args.profile)
    
    # 创建文件表
    if not create_files_table(dynamodb_client, config['files_table_name']):
        return 1
    
    # 创建报告表
    if not create_reports_table(dynamodb_client, config['reports_table_name']):
        return 1
    
    # 创建模型表
    if not create_models_table(dynamodb_client, config['models_table_name']):
        return 1
    
    logger.info("所有DynamoDB表设置完成")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 