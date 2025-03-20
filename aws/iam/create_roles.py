#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
IAM角色创建脚本
IAM Role Creation Script
IAMロール作成スクリプト
"""

import os
import sys
import argparse
import logging
import json
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
        's3_bucket_name': os.getenv('S3_BUCKET_NAME'),
        'dynamodb_files_table': os.getenv('DYNAMODB_FILES_TABLE', 'report_files'),
        'dynamodb_reports_table': os.getenv('DYNAMODB_REPORTS_TABLE', 'report_reports'),
        'dynamodb_models_table': os.getenv('DYNAMODB_MODELS_TABLE', 'report_models'),
        'lambda_role_name': os.getenv('LAMBDA_ROLE_NAME', 'report-lambda-execution-role')
    }
    
    return config

def create_iam_client(config, profile=None):
    """创建IAM客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    iam_client = session.client('iam')
    
    return iam_client

def create_lambda_execution_role(iam_client, role_name, config):
    """创建Lambda执行角色"""
    try:
        # 检查角色是否已存在
        try:
            response = iam_client.get_role(RoleName=role_name)
            logger.info(f"角色 {role_name} 已存在")
            return response['Role']['Arn']
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchEntity':
                logger.error(f"检查角色时出错: {e}")
                return None
            
            # 创建角色
            logger.info(f"创建角色 {role_name}")
            
            # 信任关系策略
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Role for Report Generator Lambda functions'
            )
            
            role_arn = response['Role']['Arn']
            logger.info(f"角色 {role_name} 创建成功，ARN: {role_arn}")
            
            # 附加AWS托管策略
            managed_policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
                'arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess'
            ]
            
            for policy_arn in managed_policies:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                logger.info(f"已附加策略 {policy_arn} 到角色 {role_name}")
            
            # 创建自定义策略
            create_custom_policies(iam_client, role_name, config)
            
            return role_arn
    except Exception as e:
        logger.error(f"创建Lambda执行角色时出错: {e}")
        return None

def create_custom_policies(iam_client, role_name, config):
    """创建自定义策略"""
    try:
        # S3写入策略
        s3_policy_name = f"{role_name}-s3-write-policy"
        s3_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{config['s3_bucket_name']}/*"
                    ]
                }
            ]
        }
        
        try:
            iam_client.create_policy(
                PolicyName=s3_policy_name,
                PolicyDocument=json.dumps(s3_policy_document),
                Description='Allow S3 write access for Report Generator'
            )
            logger.info(f"已创建策略 {s3_policy_name}")
            
            # 获取策略ARN
            account_id = boto3.client('sts').get_caller_identity().get('Account')
            s3_policy_arn = f"arn:aws:iam::{account_id}:policy/{s3_policy_name}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"策略 {s3_policy_name} 已存在")
                account_id = boto3.client('sts').get_caller_identity().get('Account')
                s3_policy_arn = f"arn:aws:iam::{account_id}:policy/{s3_policy_name}"
            else:
                logger.error(f"创建策略时出错: {e}")
                return False
        
        # 附加S3写入策略
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=s3_policy_arn
        )
        logger.info(f"已附加策略 {s3_policy_arn} 到角色 {role_name}")
        
        # DynamoDB写入策略
        dynamodb_policy_name = f"{role_name}-dynamodb-write-policy"
        dynamodb_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:*:*:table/{config['dynamodb_files_table']}",
                        f"arn:aws:dynamodb:*:*:table/{config['dynamodb_reports_table']}",
                        f"arn:aws:dynamodb:*:*:table/{config['dynamodb_models_table']}"
                    ]
                }
            ]
        }
        
        try:
            iam_client.create_policy(
                PolicyName=dynamodb_policy_name,
                PolicyDocument=json.dumps(dynamodb_policy_document),
                Description='Allow DynamoDB write access for Report Generator'
            )
            logger.info(f"已创建策略 {dynamodb_policy_name}")
            
            # 获取策略ARN
            account_id = boto3.client('sts').get_caller_identity().get('Account')
            dynamodb_policy_arn = f"arn:aws:iam::{account_id}:policy/{dynamodb_policy_name}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"策略 {dynamodb_policy_name} 已存在")
                account_id = boto3.client('sts').get_caller_identity().get('Account')
                dynamodb_policy_arn = f"arn:aws:iam::{account_id}:policy/{dynamodb_policy_name}"
            else:
                logger.error(f"创建策略时出错: {e}")
                return False
        
        # 附加DynamoDB写入策略
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=dynamodb_policy_arn
        )
        logger.info(f"已附加策略 {dynamodb_policy_arn} 到角色 {role_name}")
        
        # Bedrock调用策略
        bedrock_policy_name = f"{role_name}-bedrock-invoke-policy"
        bedrock_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:ListFoundationModels"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            iam_client.create_policy(
                PolicyName=bedrock_policy_name,
                PolicyDocument=json.dumps(bedrock_policy_document),
                Description='Allow Bedrock model invocation for Report Generator'
            )
            logger.info(f"已创建策略 {bedrock_policy_name}")
            
            # 获取策略ARN
            account_id = boto3.client('sts').get_caller_identity().get('Account')
            bedrock_policy_arn = f"arn:aws:iam::{account_id}:policy/{bedrock_policy_name}"
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"策略 {bedrock_policy_name} 已存在")
                account_id = boto3.client('sts').get_caller_identity().get('Account')
                bedrock_policy_arn = f"arn:aws:iam::{account_id}:policy/{bedrock_policy_name}"
            else:
                logger.error(f"创建策略时出错: {e}")
                return False
        
        # 附加Bedrock调用策略
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=bedrock_policy_arn
        )
        logger.info(f"已附加策略 {bedrock_policy_arn} 到角色 {role_name}")
        
        return True
    except Exception as e:
        logger.error(f"创建自定义策略时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='创建IAM角色')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--role-name', default='report-lambda-execution-role', help='Lambda执行角色名称')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 创建IAM客户端
    iam_client = create_iam_client(config, args.profile)
    
    # 创建Lambda执行角色
    role_arn = create_lambda_execution_role(iam_client, args.role_name, config)
    
    if role_arn:
        logger.info(f"Lambda执行角色ARN: {role_arn}")
        logger.info(f"请将此ARN添加到.env文件中的LAMBDA_ROLE_ARN变量")
        return 0
    else:
        logger.error("创建Lambda执行角色失败")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 