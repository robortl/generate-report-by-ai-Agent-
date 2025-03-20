#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
部署所有AWS资源的脚本
Deploy All AWS Resources Script
すべてのAWSリソースをデプロイするスクリプト
"""

import os
import sys
import argparse
import logging
import subprocess
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

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
        'aws_profile': os.getenv('AWS_PROFILE'),
        'aws_region': os.getenv('AWS_REGION', 'ap-northeast-1'),
        's3_bucket_name': os.getenv('S3_BUCKET_NAME'),
        'lambda_role_arn': os.getenv('LAMBDA_ROLE_ARN'),
        'deploy_bedrock_agent': os.getenv('DEPLOY_BEDROCK_AGENT', 'true').lower() == 'true'
    }
    
    return config

def run_script(script_path, args=None):
    """运行脚本"""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"运行脚本: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"脚本运行失败: {e}")
        return False

def deploy_iam_resources(config, args):
    """部署IAM资源"""
    logger.info("部署IAM资源...")
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'iam', 'create_roles.py')
    script_args = []
    
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    return run_script(script_path, script_args)

def deploy_s3_resources(config, args):
    """部署S3资源"""
    logger.info("部署S3资源...")
    
    # 创建S3存储桶
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 's3', 'create_buckets.py')
    script_args = []
    
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    if args.bucket:
        script_args.extend(['--bucket', args.bucket])
    elif config['s3_bucket_name']:
        script_args.extend(['--bucket', config['s3_bucket_name']])
    
    if args.public:
        script_args.append('--public')
    
    if not run_script(script_path, script_args):
        return False
    
    # 配置S3 CORS
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 's3', 'configure_cors.py')
    script_args = []
    
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    if args.bucket:
        script_args.extend(['--bucket', args.bucket])
    elif config['s3_bucket_name']:
        script_args.extend(['--bucket', config['s3_bucket_name']])
    
    if args.origins:
        script_args.extend(['--origins'] + args.origins)
    
    return run_script(script_path, script_args)

def deploy_dynamodb_resources(config, args):
    """部署DynamoDB资源"""
    logger.info("部署DynamoDB资源...")
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dynamodb', 'create_tables.py')
    script_args = []
    
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    return run_script(script_path, script_args)

def deploy_lambda_resources(config, args):
    """部署Lambda资源"""
    logger.info("部署Lambda资源...")
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lambda', 'deploy.py')
    script_args = []
    
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    if args.role_arn:
        script_args.extend(['--role-arn', args.role_arn])
    elif config['lambda_role_arn']:
        script_args.extend(['--role-arn', config['lambda_role_arn']])
    
    return run_script(script_path, script_args)

def deploy_bedrock_resources(config, args):
    """部署Bedrock资源"""
    logger.info("配置Bedrock资源...")
    
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bedrock', 'configure_models.py')
    script_args = []
    
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    # 添加验证所有模型访问权限的参数
    script_args.append('--verify-all')
    
    # 添加保存到DynamoDB的参数
    script_args.append('--save-to-dynamodb')
    
    # 如果配置中有DynamoDB模型表名，添加表名参数
    if 'dynamodb_models_table' in config:
        script_args.extend(['--table-name', config['dynamodb_models_table']])
    
    return run_script(script_path, script_args)

def deploy_bedrock_agent(config, args):
    """部署Bedrock Agent"""
    logger.info("开始部署Bedrock Agent...")
    
    # 构建脚本路径
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'bedrock',
        'create_agent.py'
    )
    
    # 构建参数
    script_args = []
    if args.profile:
        script_args.extend(['--profile', args.profile])
    elif config['aws_profile']:
        script_args.extend(['--profile', config['aws_profile']])
    
    # 运行脚本
    return run_script(script_path, script_args)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='部署所有AWS资源')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--bucket', help='S3存储桶名称')
    parser.add_argument('--public', action='store_true', help='设置S3存储桶为公共读取')
    parser.add_argument('--origins', nargs='+', help='S3 CORS允许的源列表')
    parser.add_argument('--role-arn', help='Lambda执行角色ARN')
    parser.add_argument('--skip-iam', action='store_true', help='跳过IAM资源部署')
    parser.add_argument('--skip-s3', action='store_true', help='跳过S3资源部署')
    parser.add_argument('--skip-dynamodb', action='store_true', help='跳过DynamoDB资源部署')
    parser.add_argument('--skip-lambda', action='store_true', help='跳过Lambda资源部署')
    parser.add_argument('--skip-bedrock', action='store_true', help='跳过Bedrock资源部署')
    parser.add_argument('--skip-bedrock-agent', action='store_true', help='跳过Bedrock Agent部署')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 部署IAM资源
    if not args.skip_iam:
        if not deploy_iam_resources(config, args):
            logger.error("IAM资源部署失败")
            return 1
    
    # 部署S3资源
    if not args.skip_s3:
        if not deploy_s3_resources(config, args):
            logger.error("S3资源部署失败")
            return 1
    
    # 部署DynamoDB资源
    if not args.skip_dynamodb:
        if not deploy_dynamodb_resources(config, args):
            logger.error("DynamoDB资源部署失败")
            return 1
    
    # 部署Lambda资源
    if not args.skip_lambda:
        if not deploy_lambda_resources(config, args):
            logger.error("Lambda资源部署失败")
            return 1
    
    # 部署Bedrock资源
    if not args.skip_bedrock:
        if not deploy_bedrock_resources(config, args):
            logger.error("Bedrock资源配置失败")
            return 1
    
    # 部署Bedrock Agent
    if not args.skip_bedrock_agent and config['deploy_bedrock_agent']:
        if not deploy_bedrock_agent(config, args):
            logger.error("Bedrock Agent部署失败")
            return 1
    
    logger.info("所有AWS资源部署完成")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 