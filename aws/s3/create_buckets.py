#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
S3存储桶创建脚本
S3 Bucket Creation Script
S3バケット作成スクリプト
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
        's3_bucket_name': os.getenv('S3_BUCKET_NAME', 'report-langchain-haystack-files')
    }
    
    return config

def create_s3_client(config, profile=None):
    """创建S3客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    s3_client = session.client('s3')
    
    return s3_client

def create_bucket(s3_client, bucket_name, region):
    """创建S3存储桶"""
    try:
        # 检查存储桶是否已存在
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"存储桶 {bucket_name} 已存在")
            return True
        except ClientError as e:
            # 如果存储桶不存在，则创建
            if e.response['Error']['Code'] == '404':
                logger.info(f"创建存储桶 {bucket_name}")
                
                # 在非us-east-1区域创建存储桶需要LocationConstraint
                if region != 'us-east-1':
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                else:
                    s3_client.create_bucket(Bucket=bucket_name)
                
                logger.info(f"存储桶 {bucket_name} 创建成功")
                return True
            else:
                logger.error(f"检查存储桶时出错: {e}")
                return False
    except Exception as e:
        logger.error(f"创建存储桶时出错: {e}")
        return False

def configure_bucket_policy(s3_client, bucket_name):
    """配置存储桶策略"""
    try:
        # 设置公共读取权限的存储桶策略
        bucket_policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Sid': 'PublicReadGetObject',
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': f'arn:aws:s3:::{bucket_name}/*'
            }]
        }
        
        # 将策略转换为JSON字符串
        import json
        bucket_policy = json.dumps(bucket_policy)
        
        # 应用策略
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
        logger.info(f"已为存储桶 {bucket_name} 设置公共读取策略")
        return True
    except Exception as e:
        logger.error(f"设置存储桶策略时出错: {e}")
        return False

def create_folder_structure(s3_client, bucket_name):
    """创建文件夹结构"""
    folders = [
        'uploads/',
        'reports/',
        'temp/',
        'models/'
    ]
    
    try:
        for folder in folders:
            s3_client.put_object(Bucket=bucket_name, Key=folder)
            logger.info(f"已在存储桶 {bucket_name} 中创建文件夹 {folder}")
        return True
    except Exception as e:
        logger.error(f"创建文件夹结构时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='创建和配置S3存储桶')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--bucket', help='存储桶名称（覆盖环境变量）')
    parser.add_argument('--region', help='AWS区域（覆盖环境变量）')
    parser.add_argument('--public', action='store_true', help='设置公共读取权限')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 命令行参数覆盖环境变量
    if args.bucket:
        config['s3_bucket_name'] = args.bucket
    if args.region:
        config['aws_region'] = args.region
    
    # 检查必要的配置
    if not config['s3_bucket_name']:
        logger.error("未指定存储桶名称。请在.env文件中设置S3_BUCKET_NAME或使用--bucket参数")
        return 1
    
    # 创建S3客户端
    s3_client = create_s3_client(config, args.profile)
    
    # 创建存储桶
    if not create_bucket(s3_client, config['s3_bucket_name'], config['aws_region']):
        return 1
    
    # 如果需要，设置公共读取权限
    if args.public:
        if not configure_bucket_policy(s3_client, config['s3_bucket_name']):
            return 1
    
    # 创建文件夹结构
    if not create_folder_structure(s3_client, config['s3_bucket_name']):
        return 1
    
    logger.info(f"存储桶 {config['s3_bucket_name']} 设置完成")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 