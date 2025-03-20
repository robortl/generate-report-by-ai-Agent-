#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agent测试脚本
Bedrock Agent Testing Script
Bedrock Agentテストスクリプト
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
        'agent_name': os.getenv('BEDROCK_AGENT_NAME', 'report-generator-agent'),
        'agent_alias_name': os.getenv('BEDROCK_AGENT_ALIAS_NAME', 'report-generator-agent-alias')
    }
    
    return config

def create_bedrock_agent_runtime_client(config, profile=None):
    """创建Bedrock Agent Runtime客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session_kwargs = {
        'region_name': config['aws_region']
    }
    session = boto3.Session(profile_name=profile_to_use, **session_kwargs)
    
    bedrock_agent_runtime_client = session.client('bedrock-agent-runtime')
    
    return bedrock_agent_runtime_client

def create_bedrock_agent_client(config, profile=None):
    """创建Bedrock Agent客户端"""
    # 优先使用传入的配置文件，其次使用环境变量中的配置文件
    profile_to_use = profile or config['aws_profile']
    logger.info(f"使用AWS配置文件: {profile_to_use}")
    session_kwargs = {
        'region_name': config['aws_region']
    }
    session = boto3.Session(profile_name=profile_to_use, **session_kwargs)
    
    bedrock_agent_client = session.client('bedrock-agent')
    
    return bedrock_agent_client

def get_agent_alias_id(bedrock_agent_client, agent_name, alias_name):
    """获取Agent别名ID和Agent ID"""
    try:
        # 首先获取Agent ID
        response = bedrock_agent_client.list_agents()
        agent_id = None
        
        for agent in response.get('agentSummaries', []):
            if agent['agentName'] == agent_name:
                agent_id = agent['agentId']
                break
        
        if not agent_id:
            logger.error(f"未找到名为 {agent_name} 的Agent")
            return None, None
        
        # 获取Agent别名ID
        response = bedrock_agent_client.list_agent_aliases(
            agentId=agent_id
        )
        
        for alias in response.get('agentAliasSummaries', []):
            if alias['agentAliasName'] == alias_name:
                return alias['agentAliasId'], agent_id
        
        logger.error(f"未找到名为 {alias_name} 的Agent别名")
        return None, None
    
    except Exception as e:
        logger.error(f"获取Agent别名ID时出错: {str(e)}")
        return None, None

def test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, agent_alias_id, prompt):
    """使用提示测试Agent"""
    try:
        logger.info(f"使用提示测试Agent: {prompt}")
        
        # 调用Agent
        response = bedrock_agent_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId='test-session-' + str(hash(prompt))[:8],
            inputText=prompt,
            enableTrace=True
        )
        
        # 处理EventStream响应
        if hasattr(response, 'read'):
            # 如果是可读的流对象
            full_response = ""
            for event in response:
                # 检查事件类型
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        # 解码字节数据
                        text = chunk['bytes'].decode('utf-8')
                        full_response += text
                        print(text, end='', flush=True)
                elif 'trace' in event:
                    # 处理跟踪信息
                    trace_data = event['trace']
                    logger.info(f"跟踪信息: {trace_data}")
            
            logger.info(f"\nAgent完整响应:\n{full_response}")
            return full_response
        else:
            # 解析普通响应
            completion = response.get('completion', '')
            trace = response.get('trace', {})
            
            logger.info(f"Agent响应:\n{completion}")
            
            if trace:
                logger.info("Agent执行跟踪:")
                logger.info(json.dumps(trace, indent=2))
            
            return completion
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        
        logger.error(f"调用Agent时出错: {error_code} - {error_message}")
        return None
    
    except Exception as e:
        logger.error(f"调用Agent时出错: {str(e)}")
        return None

def test_agent_conversation(bedrock_agent_runtime_client, agent_id, agent_alias_id):
    """与Agent进行对话测试"""
    try:
        session_id = 'test-conversation-' + str(hash(agent_alias_id))[:8]
        logger.info(f"开始与Agent对话测试 (会话ID: {session_id})")
        
        # 预定义的对话流程
        conversation = [
            "你好，我需要生成一份报告。",
            "我有一个文档ID为DOC-123，我想生成一份摘要报告。",
            "报告生成后，我如何查看它的状态？",
            "谢谢你的帮助。"
        ]
        
        # 进行对话
        for i, prompt in enumerate(conversation):
            logger.info(f"\n[用户消息 {i+1}/{len(conversation)}]: {prompt}")
            
            # 调用Agent
            response = bedrock_agent_runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=prompt,
                enableTrace=True
            )
            
            # 处理EventStream响应
            if hasattr(response, 'read'):
                # 如果是可读的流对象
                full_response = ""
                print(f"[Agent响应 {i+1}/{len(conversation)}]:", end='', flush=True)
                for event in response:
                    # 检查事件类型
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            # 解码字节数据
                            text = chunk['bytes'].decode('utf-8')
                            full_response += text
                            print(text, end='', flush=True)
                    elif 'trace' in event:
                        # 处理跟踪信息
                        trace_data = event['trace']
                        logger.debug(f"跟踪信息: {trace_data}")
                
                logger.info(f"\n[Agent完整响应 {i+1}/{len(conversation)}]:\n{full_response}")
            else:
                # 解析普通响应
                completion = response.get('completion', '')
                logger.info(f"[Agent响应 {i+1}/{len(conversation)}]:\n{completion}")
        
        logger.info("对话测试完成")
        return True
    
    except Exception as e:
        logger.error(f"对话测试时出错: {str(e)}")
        return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='测试AWS Bedrock Agent')
    parser.add_argument('--profile', help='AWS配置文件名称')
    parser.add_argument('--agent-name', help='Agent名称')
    parser.add_argument('--alias-name', help='Agent别名名称')
    parser.add_argument('--prompt', help='测试提示')
    parser.add_argument('--conversation', action='store_true', help='进行对话测试')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    config = load_config()
    
    # 使用命令行参数覆盖配置
    if args.agent_name:
        config['agent_name'] = args.agent_name
    if args.alias_name:
        config['agent_alias_name'] = args.alias_name
    
    # 创建Bedrock Agent客户端
    bedrock_agent_client = create_bedrock_agent_client(config, args.profile)
    bedrock_agent_runtime_client = create_bedrock_agent_runtime_client(config, args.profile)
    
    # 获取Agent别名ID和Agent ID
    agent_alias_id, agent_id = get_agent_alias_id(bedrock_agent_client, config['agent_name'], config['agent_alias_name'])
    
    if not agent_alias_id or not agent_id:
        logger.error("无法获取Agent别名ID或Agent ID，测试终止")
        return 1
    
    logger.info(f"获取到Agent ID: {agent_id}, Agent别名ID: {agent_alias_id}")
    
    # 测试Agent
    if args.conversation:
        # 进行对话测试
        test_agent_conversation(bedrock_agent_runtime_client, agent_id, agent_alias_id)
    elif args.prompt:
        # 使用提示测试Agent
        test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, agent_alias_id, args.prompt)
    else:
        # 默认测试提示
        default_prompt = "你好，请介绍一下你自己和你的功能。"
        test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, agent_alias_id, default_prompt)
    
    logger.info("Bedrock Agent测试完成")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 