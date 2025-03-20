#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock设置脚本
Bedrock Setup Script
Bedrockセットアップスクリプト
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
        'aws_profile': os.getenv('AWS_PROFILE', 'default')
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

def create_bedrock_management_client(config, profile=None):
    """创建Bedrock管理客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    bedrock_management_client = session.client('bedrock')
    
    return bedrock_management_client

def list_available_models(bedrock_client):
    """列出可用的Bedrock模型"""
    try:
        response = bedrock_client.list_foundation_models()
        
        models = []
        for model in response.get('modelSummaries', []):
            models.append({
                'modelId': model.get('modelId'),
                'provider': model.get('providerName'),
                'name': model.get('modelName')
            })
        
        return models
    except Exception as e:
        logger.error(f"列出模型时出错: {e}")
        
        # 如果API调用失败，返回一些常见的模型
        return [
            {'modelId': 'anthropic.claude-3-sonnet-20240229-v1:0', 'provider': 'Anthropic', 'name': 'Claude 3 Sonnet'},
            {'modelId': 'anthropic.claude-3-haiku-20240307-v1:0', 'provider': 'Anthropic', 'name': 'Claude 3 Haiku'},
            {'modelId': 'anthropic.claude-v2', 'provider': 'Anthropic', 'name': 'Claude V2'},
            {'modelId': 'anthropic.claude-instant-v1', 'provider': 'Anthropic', 'name': 'Claude Instant V1'},
            {'modelId': 'amazon.titan-text-express-v1', 'provider': 'Amazon', 'name': 'Titan Text Express V1'},
            {'modelId': 'ai21.j2-ultra-v1', 'provider': 'AI21', 'name': 'Jurassic-2 Ultra'},
            {'modelId': 'cohere.command-text-v14', 'provider': 'Cohere', 'name': 'Command Text V14'}
        ]

def verify_model_access(bedrock_client, model_id):
    """验证模型访问权限"""
    try:
        # 构建一个简单的请求来测试访问权限
        prompt = "Hello, this is a test."
        
        # 根据模型提供商确定请求格式
        if 'anthropic' in model_id:
            request_body = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": 10,
                "temperature": 0.7
            }
        elif 'amazon' in model_id:
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 10,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
        elif 'ai21' in model_id:
            request_body = {
                "prompt": prompt,
                "maxTokens": 10,
                "temperature": 0.7
            }
        elif 'cohere' in model_id:
            request_body = {
                "prompt": prompt,
                "max_tokens": 10,
                "temperature": 0.7
            }
        else:
            # 默认格式
            request_body = {
                "prompt": prompt,
                "max_tokens": 10,
                "temperature": 0.7
            }
        
        # 发送请求
        bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        logger.info(f"模型 {model_id} 访问权限验证成功")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            logger.warning(f"无法访问模型 {model_id}，请在AWS控制台请求访问权限")
        else:
            logger.error(f"验证模型 {model_id} 访问权限时出错: {e}")
        return False
    except Exception as e:
        logger.error(f"验证模型 {model_id} 访问权限时出错: {e}")
        return False

def setup_bedrock_for_langchain():
    """为LangChain设置Bedrock"""
    try:
        # 检查是否安装了langchain
        import importlib.util
        if importlib.util.find_spec("langchain") is None:
            logger.warning("未安装LangChain，请使用pip install langchain安装")
            return False
        
        from langchain.llms import Bedrock
        logger.info("LangChain已安装，可以使用Bedrock集成")
        return True
    except ImportError:
        logger.warning("未安装LangChain，请使用pip install langchain安装")
        return False
    except Exception as e:
        logger.error(f"设置LangChain时出错: {e}")
        return False

def setup_bedrock_for_haystack():
    """为Haystack设置Bedrock"""
    try:
        # 检查是否安装了haystack
        import importlib.util
        if importlib.util.find_spec("haystack") is None:
            logger.warning("未安装Haystack，请使用pip install farm-haystack安装")
            return False
        
        from haystack.nodes import PromptNode
        logger.info("Haystack已安装，可以使用Bedrock集成")
        return True
    except ImportError:
        logger.warning("未安装Haystack，请使用pip install farm-haystack安装")
        return False
    except Exception as e:
        logger.error(f"设置Haystack时出错: {e}")
        return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='设置AWS Bedrock')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--list-models', action='store_true', help='列出可用的模型')
    parser.add_argument('--verify-model', help='验证特定模型的访问权限')
    parser.add_argument('--verify-all', action='store_true', help='验证所有模型的访问权限')
    parser.add_argument('--setup-langchain', action='store_true', help='设置LangChain集成')
    parser.add_argument('--setup-haystack', action='store_true', help='设置Haystack集成')
    parser.add_argument('--setup-all', action='store_true', help='设置所有集成')
    parser.add_argument('--test-model', help='测试特定模型并获取响应')
    parser.add_argument('--prompt', help='测试模型时使用的提示')
    return parser.parse_args()

def test_model_with_prompt(bedrock_client, model_id, prompt):
    """测试模型并获取响应"""
    logger.info(f"测试模型 {model_id} 使用提示: {prompt}")
    
    try:
        # 根据模型ID确定提供商
        provider = model_id.split('.')[0].lower()
        
        if 'anthropic' in provider:
            # Anthropic Claude模型
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        elif 'amazon' in provider and 'titan' in model_id.lower():
            # Amazon Titan模型
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
        elif 'cohere' in provider:
            # Cohere模型
            request_body = {
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.7,
                "p": 0.9
            }
        else:
            logger.error(f"不支持的模型类型: {model_id}")
            return None
        
        # 调用模型
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # 解析响应
        response_body = json.loads(response['body'].read())
        
        if 'anthropic' in provider:
            result = response_body.get('content', [{}])[0].get('text', '')
        elif 'amazon' in provider and 'titan' in model_id.lower():
            result = response_body.get('results', [{}])[0].get('outputText', '')
        elif 'cohere' in provider:
            result = response_body.get('generations', [{}])[0].get('text', '')
        else:
            result = str(response_body)
        
        logger.info(f"模型响应:\n{result}")
        return result
    
    except Exception as e:
        logger.error(f"测试模型时出错: {str(e)}")
        return None

def main():
    """主函数"""
    args = parse_args()
    config = load_config()
    
    # 创建Bedrock客户端
    bedrock_client = create_bedrock_client(config, args.profile)
    bedrock_mgmt_client = create_bedrock_management_client(config, args.profile)
    
    # 列出可用模型
    if args.list_models:
        list_available_models(bedrock_mgmt_client)
    
    # 验证特定模型
    if args.verify_model:
        verify_model_access(bedrock_client, args.verify_model)
    
    # 验证所有模型
    if args.verify_all:
        verify_all_models_access(bedrock_client, bedrock_mgmt_client)
    
    # 测试特定模型
    if args.test_model and args.prompt:
        test_model_with_prompt(bedrock_client, args.test_model, args.prompt)
    
    # 设置LangChain集成
    if args.setup_langchain or args.setup_all:
        setup_bedrock_for_langchain()
    
    # 设置Haystack集成
    if args.setup_haystack or args.setup_all:
        setup_bedrock_for_haystack()
    
    logger.info("AWS Bedrock设置完成")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 