#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock模型配置脚本
Bedrock Model Configuration Script
Bedrockモデル設定スクリプト
"""

import os
import sys
import json
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
        'dynamodb_models_table': os.getenv('DYNAMODB_MODELS_TABLE', 'report_models')
    }
    
    return config

def create_bedrock_client(config, profile=None):
    """创建Bedrock客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    bedrock_client = session.client('bedrock-runtime')
    
    return bedrock_client

def create_dynamodb_client(config, profile=None):
    """创建DynamoDB客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    dynamodb_client = session.client('dynamodb')
    
    return dynamodb_client

def list_available_models(config, profile=None):
    """列出可用的Bedrock模型"""
    try:
        # 创建Bedrock管理客户端
        session_kwargs = {
            'region_name': config['aws_region']
        }
        
        if profile:
            session = boto3.Session(profile_name=profile, **session_kwargs)
        else:
            session_kwargs.update({
                'aws_access_key_id': config['aws_access_key_id'],
                'aws_secret_access_key': config['aws_secret_access_key']
            })
            session = boto3.Session(**session_kwargs)
        
        bedrock_management = session.client('bedrock')
        
        # 获取模型列表
        response = bedrock_management.list_foundation_models()
        
        models = []
        for model in response.get('modelSummaries', []):
            models.append({
                'modelId': model.get('modelId'),
                'provider': model.get('providerName'),
                'name': model.get('modelName'),
                'inputModalities': model.get('inputModalities', []),
                'outputModalities': model.get('outputModalities', []),
                'customizationsSupported': model.get('customizationsSupported', [])
            })
        
        return models
    except Exception as e:
        logger.error(f"列出模型时出错: {e}")
        
        # 如果API调用失败，返回一些常见的模型
        return [
            {'modelId': 'anthropic.claude-v2', 'provider': 'Anthropic', 'name': 'Claude V2', 'inputModalities': ['TEXT'], 'outputModalities': ['TEXT']},
            {'modelId': 'anthropic.claude-instant-v1', 'provider': 'Anthropic', 'name': 'Claude Instant V1', 'inputModalities': ['TEXT'], 'outputModalities': ['TEXT']},
            {'modelId': 'amazon.titan-text-express-v1', 'provider': 'Amazon', 'name': 'Titan Text Express V1', 'inputModalities': ['TEXT'], 'outputModalities': ['TEXT']},
            {'modelId': 'ai21.j2-ultra-v1', 'provider': 'AI21', 'name': 'Jurassic-2 Ultra', 'inputModalities': ['TEXT'], 'outputModalities': ['TEXT']},
            {'modelId': 'cohere.command-text-v14', 'provider': 'Cohere', 'name': 'Command Text V14', 'inputModalities': ['TEXT'], 'outputModalities': ['TEXT']}
        ]

def verify_model_access(bedrock_client, model_id):
    """验证对模型的访问权限"""
    try:
        # 尝试使用简单提示调用模型
        test_prompt = "Hello, this is a test."
        
        # 根据模型提供商确定请求格式
        if 'anthropic' in model_id:
            request_body = {
                "prompt": f"\n\nHuman: {test_prompt}\n\nAssistant:",
                "max_tokens_to_sample": 10,
                "temperature": 0.7
            }
        elif 'amazon' in model_id:
            request_body = {
                "inputText": test_prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 10,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
        elif 'ai21' in model_id:
            request_body = {
                "prompt": test_prompt,
                "maxTokens": 10,
                "temperature": 0.7
            }
        elif 'cohere' in model_id:
            request_body = {
                "prompt": test_prompt,
                "max_tokens": 10,
                "temperature": 0.7
            }
        else:
            # 默认格式
            request_body = {
                "prompt": test_prompt,
                "max_tokens": 10,
                "temperature": 0.7
            }
        
        # 发送请求
        bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'AccessDeniedException' or error_code == 'ValidationException':
            logger.warning(f"无法访问模型 {model_id}: {e}")
            return False
        else:
            logger.error(f"验证模型访问时出错: {e}")
            return False
    except Exception as e:
        logger.error(f"验证模型访问时出错: {e}")
        return False

def save_models_to_dynamodb(dynamodb_client, table_name, models):
    """将模型信息保存到DynamoDB表"""
    try:
        # 检查表是否存在
        try:
            dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"表 {table_name} 已存在")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"表 {table_name} 不存在，正在创建...")
                # 创建表
                dynamodb_client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'modelId', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'modelId', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                # 等待表创建完成
                waiter = dynamodb_client.get_waiter('table_exists')
                waiter.wait(TableName=table_name)
                logger.info(f"表 {table_name} 创建完成")
            else:
                raise
        
        # 保存模型信息
        for model in models:
            item = {
                'modelId': {'S': model['modelId']},
                'provider': {'S': model['provider']},
                'name': {'S': model['name']},
                'accessible': {'BOOL': model.get('accessible', False)},
                'lastChecked': {'S': model.get('lastChecked', '')},
                'inputModalities': {'SS': model.get('inputModalities', ['TEXT'])},
                'outputModalities': {'SS': model.get('outputModalities', ['TEXT'])},
                'customizationsSupported': {'SS': model.get('customizationsSupported', [])} if model.get('customizationsSupported') else {'NULL': True}
            }
            
            dynamodb_client.put_item(
                TableName=table_name,
                Item=item
            )
        
        logger.info(f"已将 {len(models)} 个模型信息保存到表 {table_name}")
        return True
    except Exception as e:
        logger.error(f"保存模型信息到DynamoDB时出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='配置Bedrock模型访问')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--verify-all', action='store_true', help='验证所有模型的访问权限')
    parser.add_argument('--verify-model', help='验证特定模型的访问权限')
    parser.add_argument('--save-to-dynamodb', action='store_true', help='将模型信息保存到DynamoDB')
    parser.add_argument('--table-name', help='DynamoDB表名称')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 如果指定了表名，覆盖配置中的表名
    if args.table_name:
        config['dynamodb_models_table'] = args.table_name
    
    # 创建Bedrock客户端
    bedrock_client = create_bedrock_client(config, args.profile)
    
    # 列出可用的模型
    models = list_available_models(config, args.profile)
    logger.info(f"找到 {len(models)} 个Bedrock模型")
    
    # 验证模型访问权限
    if args.verify_all or args.verify_model:
        if args.verify_model:
            # 验证特定模型
            model_id = args.verify_model
            logger.info(f"验证模型 {model_id} 的访问权限...")
            accessible = verify_model_access(bedrock_client, model_id)
            logger.info(f"模型 {model_id} {'可访问' if accessible else '不可访问'}")
            
            # 更新模型列表中的访问状态
            for model in models:
                if model['modelId'] == model_id:
                    model['accessible'] = accessible
                    model['lastChecked'] = datetime.datetime.now().isoformat()
        else:
            # 验证所有模型
            logger.info("验证所有模型的访问权限...")
            for i, model in enumerate(models):
                model_id = model['modelId']
                logger.info(f"[{i+1}/{len(models)}] 验证模型 {model_id} 的访问权限...")
                accessible = verify_model_access(bedrock_client, model_id)
                logger.info(f"模型 {model_id} {'可访问' if accessible else '不可访问'}")
                model['accessible'] = accessible
                model['lastChecked'] = datetime.datetime.now().isoformat()
    
    # 保存模型信息到DynamoDB
    if args.save_to_dynamodb:
        logger.info(f"将模型信息保存到DynamoDB表 {config['dynamodb_models_table']}...")
        dynamodb_client = create_dynamodb_client(config, args.profile)
        save_models_to_dynamodb(dynamodb_client, config['dynamodb_models_table'], models)
    
    # 打印模型信息
    logger.info("Bedrock模型信息:")
    for model in models:
        accessible_str = "✓" if model.get('accessible', False) else "✗"
        logger.info(f"- [{accessible_str}] {model['modelId']} ({model['provider']}: {model['name']})")
    
    return 0

if __name__ == '__main__':
    import datetime
    sys.exit(main()) 