#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock模型测试脚本
Bedrock Model Testing Script
Bedrockモデルテストスクリプト
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

def list_available_models(bedrock_client):
    """列出可用的Bedrock模型"""
    try:
        # 注意：这里使用bedrock而不是bedrock-runtime
        bedrock_management = boto3.client('bedrock', region_name=bedrock_client._client_config.region_name)
        response = bedrock_management.list_foundation_models()
        
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
            {'modelId': 'anthropic.claude-v2', 'provider': 'Anthropic', 'name': 'Claude V2'},
            {'modelId': 'anthropic.claude-instant-v1', 'provider': 'Anthropic', 'name': 'Claude Instant V1'},
            {'modelId': 'amazon.titan-text-express-v1', 'provider': 'Amazon', 'name': 'Titan Text Express V1'},
            {'modelId': 'ai21.j2-ultra-v1', 'provider': 'AI21', 'name': 'Jurassic-2 Ultra'},
            {'modelId': 'cohere.command-text-v14', 'provider': 'Cohere', 'name': 'Command Text V14'}
        ]

def test_model_with_prompt(bedrock_client, model_id, prompt, max_tokens=1000):
    """使用提示测试模型"""
    try:
        # 根据模型提供商确定请求格式
        if 'anthropic' in model_id:
            request_body = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": max_tokens,
                "temperature": 0.7
            }
        elif 'amazon' in model_id:
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
        elif 'ai21' in model_id:
            request_body = {
                "prompt": prompt,
                "maxTokens": max_tokens,
                "temperature": 0.7
            }
        elif 'cohere' in model_id:
            request_body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
        else:
            # 默认格式
            request_body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
        
        # 发送请求
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # 解析响应
        response_body = json.loads(response['body'].read())
        
        # 根据模型提供商解析输出
        if 'anthropic' in model_id:
            output = response_body.get('completion', '')
        elif 'amazon' in model_id:
            output = response_body.get('results', [{}])[0].get('outputText', '')
        elif 'ai21' in model_id:
            output = response_body.get('completions', [{}])[0].get('data', {}).get('text', '')
        elif 'cohere' in model_id:
            output = response_body.get('generations', [{}])[0].get('text', '')
        else:
            # 尝试通用解析
            output = str(response_body)
        
        return output
    except Exception as e:
        logger.error(f"测试模型时出错: {e}")
        return None

def test_with_langchain(model_id, prompt):
    """使用LangChain测试模型"""
    try:
        from langchain.llms import Bedrock
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        
        # 加载配置
        config = load_config()
        
        # 创建Bedrock客户端
        bedrock_client = create_bedrock_client(config)
        
        # 创建Bedrock LLM
        llm = Bedrock(
            model_id=model_id,
            client=bedrock_client,
            model_kwargs={"temperature": 0.7, "max_tokens_to_sample": 1000}
        )
        
        # 创建提示模板
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="{query}"
        )
        
        # 创建链
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        # 生成响应
        response = chain.run(query=prompt)
        
        return response
    except Exception as e:
        logger.error(f"使用LangChain测试模型时出错: {e}")
        return None

def test_with_haystack(model_id, prompt):
    """使用Haystack测试模型"""
    try:
        from haystack.nodes import PromptNode, PromptTemplate
        
        # 加载配置
        config = load_config()
        
        # 创建提示模板
        prompt_template = PromptTemplate(
            prompt="{query}",
            output_parser=None
        )
        
        # 创建PromptNode
        prompt_node = PromptNode(
            model_name_or_path=model_id,
            api_key=config['aws_access_key_id'],
            aws_secret_key=config['aws_secret_access_key'],
            aws_region=config['aws_region'],
            default_prompt_template=prompt_template
        )
        
        # 生成响应
        result = prompt_node({"query": prompt})
        response = result[0]
        
        return response
    except Exception as e:
        logger.error(f"使用Haystack测试模型时出错: {e}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试Bedrock模型')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--model', default='anthropic.claude-v2', help='要测试的模型ID')
    parser.add_argument('--prompt', default='Hello, how are you today?', help='测试提示')
    parser.add_argument('--framework', choices=['direct', 'langchain', 'haystack'], default='direct', help='使用的框架')
    parser.add_argument('--list-models', action='store_true', help='列出可用的模型')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    # 创建Bedrock客户端
    bedrock_client = create_bedrock_client(config, args.profile)
    
    # 如果需要列出模型
    if args.list_models:
        models = list_available_models(bedrock_client)
        logger.info("可用的Bedrock模型:")
        for model in models:
            logger.info(f"- {model['modelId']} ({model['provider']}: {model['name']})")
        return 0
    
    # 测试模型
    logger.info(f"使用模型 {args.model} 测试提示: {args.prompt}")
    
    if args.framework == 'direct':
        output = test_model_with_prompt(bedrock_client, args.model, args.prompt)
    elif args.framework == 'langchain':
        output = test_with_langchain(args.model, args.prompt)
    elif args.framework == 'haystack':
        output = test_with_haystack(args.model, args.prompt)
    
    if output:
        logger.info(f"模型响应:\n{output}")
        return 0
    else:
        logger.error("测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 