#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
S3 CORS配置脚本
S3 CORS Configuration Script
S3 CORS設定スクリプト
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
        's3_bucket_name': os.getenv('S3_BUCKET_NAME', 'report-langchain-haystack-files'),
        'cors_allowed_origins': os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
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

def configure_cors(s3_client, bucket_name, allowed_origins=None):
    """配置CORS策略"""
    if not allowed_origins:
        allowed_origins = ['*']
    
    try:
        # 设置CORS配置
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                    'AllowedOrigins': allowed_origins,
                    'ExposeHeaders': ['ETag', 'Content-Length', 'Content-Type'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        # 应用CORS配置
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        
        logger.info(f"已为存储桶 {bucket_name} 设置CORS策略")
        logger.info(f"允许的源: {allowed_origins}")
        return True
    except Exception as e:
        logger.error(f"设置CORS策略时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='配置S3存储桶的CORS策略')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--bucket', help='存储桶名称（覆盖环境变量）')
    parser.add_argument('--origins', nargs='+', help='允许的源列表，例如 http://localhost:3000')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 命令行参数覆盖环境变量
    if args.bucket:
        config['s3_bucket_name'] = args.bucket
    
    # 检查必要的配置
    if not config['s3_bucket_name']:
        logger.error("未指定存储桶名称。请在.env文件中设置S3_BUCKET_NAME或使用--bucket参数")
        return 1
    
    # 创建S3客户端
    s3_client = create_s3_client(config, args.profile)
    
    # 设置允许的源
    allowed_origins = args.origins if args.origins else config['cors_allowed_origins']
    
    # 配置CORS策略
    if not configure_cors(s3_client, config['s3_bucket_name'], allowed_origins):
        return 1
    
    logger.info(f"存储桶 {config['s3_bucket_name']} 的CORS策略设置完成")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 