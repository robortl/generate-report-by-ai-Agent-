#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
部署状态工具脚本
Deployment Status Utility Script
デプロイ状態ユーティリティスクリプト
"""

import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 部署状态文件路径
DEPLOYMENT_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deployment_status.json')

def load_deployment_status():
    """加载部署状态"""
    try:
        with open(DEPLOYMENT_STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"部署状态文件不存在: {DEPLOYMENT_STATUS_FILE}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"部署状态文件格式错误: {DEPLOYMENT_STATUS_FILE}, 错误: {e}")
        return None
    except Exception as e:
        logger.error(f"加载部署状态文件时出错: {e}")
        return None

def is_deployment_successful():
    """检查部署是否成功"""
    status = load_deployment_status()
    if not status:
        return False
    return status.get('deployment_status') == 'success'

def get_lambda_function_status(function_name):
    """获取Lambda函数的部署状态"""
    status = load_deployment_status()
    if not status:
        return None
    
    lambda_functions = status.get('resources', {}).get('lambda', {}).get('functions', {})
    return lambda_functions.get(function_name, {}).get('status')

def is_lambda_function_deployed(function_name):
    """检查Lambda函数是否已部署"""
    return get_lambda_function_status(function_name) == 'deployed'

def get_s3_bucket_name():
    """获取S3存储桶名称"""
    status = load_deployment_status()
    if not status:
        return None
    
    return status.get('environment', {}).get('s3_bucket_name')

def get_dynamodb_table_name(table_suffix):
    """获取DynamoDB表名"""
    status = load_deployment_status()
    if not status:
        return None
    
    prefix = status.get('environment', {}).get('dynamodb_table_prefix', 'report_')
    return f"{prefix}{table_suffix}"

def get_lambda_role_arn():
    """获取Lambda执行角色ARN"""
    status = load_deployment_status()
    if not status:
        return None
    
    return status.get('resources', {}).get('iam', {}).get('roles', {}).get('report-lambda-execution-role', {}).get('arn')

def get_available_bedrock_models():
    """获取可用的Bedrock模型列表"""
    status = load_deployment_status()
    if not status:
        return []
    
    models = status.get('resources', {}).get('bedrock', {}).get('models', {})
    return [model_id for model_id, model_info in models.items() if model_info.get('status') == 'available']

def get_pending_tasks():
    """获取待处理任务列表"""
    status = load_deployment_status()
    if not status:
        return []
    
    return status.get('pending_tasks', [])

def print_deployment_summary():
    """打印部署摘要"""
    status = load_deployment_status()
    if not status:
        logger.error("无法加载部署状态")
        return
    
    print("\n===== 部署摘要 =====")
    print(f"部署日期: {status.get('deployment_date')}")
    print(f"部署状态: {'成功' if status.get('deployment_status') == 'success' else '失败'}")
    
    # IAM资源
    print("\n--- IAM资源 ---")
    iam_roles = status.get('resources', {}).get('iam', {}).get('roles', {})
    for role_name, role_info in iam_roles.items():
        print(f"角色: {role_name} - {'已部署' if role_info.get('status') == 'deployed' else '未部署'}")
        if 'arn' in role_info:
            print(f"  ARN: {role_info['arn']}")
    
    # S3资源
    print("\n--- S3资源 ---")
    s3_buckets = status.get('resources', {}).get('s3', {}).get('buckets', {})
    for bucket_name, bucket_info in s3_buckets.items():
        print(f"存储桶: {bucket_name} - {'已部署' if bucket_info.get('status') == 'deployed' else '未部署'}")
        if 'folders' in bucket_info:
            print(f"  文件夹: {', '.join(bucket_info['folders'])}")
        if bucket_info.get('cors_enabled'):
            print(f"  CORS: 已启用，允许源: {', '.join(bucket_info.get('cors_origins', []))}")
    
    # DynamoDB资源
    print("\n--- DynamoDB资源 ---")
    dynamodb_tables = status.get('resources', {}).get('dynamodb', {}).get('tables', {})
    for table_name, table_info in dynamodb_tables.items():
        print(f"表: {table_name} - {'已部署' if table_info.get('status') == 'deployed' else '未部署'}")
    
    # Lambda资源
    print("\n--- Lambda资源 ---")
    lambda_functions = status.get('resources', {}).get('lambda', {}).get('functions', {})
    for function_name, function_info in lambda_functions.items():
        status_str = '已部署' if function_info.get('status') == 'deployed' else '未部署'
        if function_info.get('status') == 'not_deployed' and 'reason' in function_info:
            status_str += f" ({function_info['reason']})"
        print(f"函数: {function_name} - {status_str}")
        if function_info.get('status') == 'deployed':
            print(f"  运行时: {function_info.get('runtime')}")
            print(f"  内存: {function_info.get('memory_size')}MB")
            print(f"  超时: {function_info.get('timeout')}秒")
            if 'dependencies' in function_info:
                print(f"  依赖项: {', '.join(function_info['dependencies'])}")
    
    # Bedrock资源
    print("\n--- Bedrock资源 ---")
    bedrock_models = status.get('resources', {}).get('bedrock', {}).get('models', {})
    for model_id, model_info in bedrock_models.items():
        status_str = '可用' if model_info.get('status') == 'available' else '不可用'
        print(f"模型: {model_id} - {status_str}")
        if 'display_name' in model_info:
            print(f"  显示名称: {model_info['display_name']}")
    
    # 待处理任务
    print("\n--- 待处理任务 ---")
    for task in status.get('pending_tasks', []):
        print(f"- {task}")
    
    print("\n===================")

if __name__ == '__main__':
    # 打印部署摘要
    print_deployment_summary() 