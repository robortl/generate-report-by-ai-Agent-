#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agent创建脚本
Bedrock Agent Creation Script
Bedrock Agentの作成スクリプト
"""

import os
import sys
import json
import argparse
import logging
import boto3
import time
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import traceback
from datetime import datetime
import uuid

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,  # 将日志级别设置为DEBUG以获取更详细的输出
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """加载配置"""
    # 加载.env文件
    load_dotenv()
    
    # 必須環境変数のチェック
    required_vars = ['LAMBDA_ROLE_ARN', 'LAMBDA_FUNCTION_ARN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.error("请在.env文件中设置这些变量")
        sys.exit(1)
    
    # 获取环境变量
    config = {
        'aws_region': os.getenv('AWS_REGION', 'ap-northeast-1'),
        'aws_profile': os.getenv('AWS_PROFILE', 'default'),
        'agent_name': os.getenv('BEDROCK_AGENT_NAME', 'report-generator-agent'),
        'agent_description': os.getenv('BEDROCK_AGENT_DESCRIPTION', 'An agent for generating reports based on document analysis'),
        'agent_instruction': os.getenv('BEDROCK_AGENT_INSTRUCTION', 'You are a helpful assistant that generates reports based on document analysis.'),
        'foundation_model': os.getenv('BEDROCK_FOUNDATION_MODEL', 'amazon.titan-text-express-v1'),
        's3_bucket_name': os.getenv('S3_BUCKET_NAME', 'report-langchain-haystack-files'),
        'lambda_role_arn': os.getenv('LAMBDA_ROLE_ARN'),
        'dynamodb_table_prefix': os.getenv('DYNAMODB_TABLE_PREFIX', 'report_'),
        'lambda_function_arn': os.getenv('LAMBDA_FUNCTION_ARN')
    }
    
    # 任意の環境変数
    if os.getenv('CUSTOMER_ENCRYPTION_KEY_ARN'):
        config['customer_encryption_key_arn'] = os.getenv('CUSTOMER_ENCRYPTION_KEY_ARN')
    
    logger.debug(f"加载的配置: {json.dumps(config, indent=2)}")
    
    return config

def create_bedrock_agent_client(config, profile=None):
    """创建Bedrock Agent客户端"""
    session = boto3.Session(
        profile_name=profile if profile else config.get('aws_profile'),
        region_name=config.get('aws_region')
    )
    
    client = session.client('bedrock-agent')
    logger.info("已创建Bedrock Agent客户端")
    return client

def create_bedrock_agent_runtime_client(config, profile=None):
    """创建Bedrock Agent Runtime客户端"""
    session = boto3.Session(
        profile_name=profile if profile else config.get('aws_profile'),
        region_name=config.get('aws_region')
    )
    
    client = session.client('bedrock-agent-runtime')
    logger.info("已创建Bedrock Agent Runtime客户端")
    return client

def create_agent(bedrock_agent_client, config):
    """创建Bedrock Agent"""
    try:
        logger.info(f"开始创建Bedrock Agent: {config['agent_name']}")
        
        # 创建Agent
        response = bedrock_agent_client.create_agent(
            agentName=config['agent_name'],
            agentResourceRoleArn=config['lambda_role_arn'],
            foundationModel=config['foundation_model'],
            description="An agent for generating reports based on document analysis",
            instruction="You are a helpful assistant that generates reports based on document analysis.",
            idleSessionTTLInSeconds=1800,
            tags={
                'Project': 'report-generator',
                'Environment': 'development'
            }
        )
        
        agent_id = response['agent']['agentId']
        
        logger.info(f"Agent创建成功: ID={agent_id}")
        
        # 等待Agent准备就绪
        wait_for_agent_ready(bedrock_agent_client, agent_id)
        
        return {
            'agent_id': agent_id,
            'agent_name': config['agent_name'],
            'status': 'created'
        }
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        
        # 如果Agent已存在，尝试获取它
        if error_code == 'ConflictException' and 'already exists' in error_message:
            logger.warning(f"Agent {config['agent_name']} 已存在")
            
            # 获取现有Agent
            agents_response = bedrock_agent_client.list_agents()
            
            for agent in agents_response.get('agentSummaries', []):
                if agent['agentName'] == config['agent_name']:
                    logger.info(f"找到现有Agent: ID={agent['agentId']}")
                    return {
                        'agent_id': agent['agentId'],
                        'agent_name': config['agent_name'],
                        'status': 'exists'
                    }
        
        logger.error(f"创建Agent时出错: {error_code} - {error_message}")
        return {
            'status': 'error',
            'error_code': error_code,
            'error_message': error_message
        }
    
    except Exception as e:
        logger.error(f"创建Agent时出错: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }

def wait_for_agent_ready(bedrock_agent_client, agent_id, max_attempts=30, delay_seconds=10):
    """等待Agent准备就绪"""
    for attempt in range(max_attempts):
        try:
            response = bedrock_agent_client.get_agent(
                agentId=agent_id
            )
            
            status = response['agent']['agentStatus']
            logger.info(f"Agent状态: {status} (尝试 {attempt+1}/{max_attempts})")
            
            if status == 'PREPARED':
                logger.info("Agent已准备就绪")
                return True
            
            if status in ['FAILED', 'DELETING', 'DELETED']:
                logger.error(f"Agent处于终止状态: {status}")
                return False
            
            # 等待一段时间后再次检查
            time.sleep(delay_seconds)
        
        except Exception as e:
            logger.error(f"检查Agent状态时出错: {str(e)}")
            time.sleep(delay_seconds)
    
    logger.warning(f"等待Agent准备就绪超时，已尝试 {max_attempts} 次")
    return False

def list_agents(bedrock_agent_client):
    """列出所有Bedrock Agents"""
    try:
        response = bedrock_agent_client.list_agents()
        return response.get('agentSummaries', [])
    except Exception as e:
        logger.error(f"列出Agents时出错: {str(e)}")
        return []

def create_knowledge_base(bedrock_agent_client, config, agent_id):
    """创建知识库"""
    try:
        kb_name = f"{config['agent_name']}-knowledge-base"
        logger.info(f"开始创建知识库: {kb_name}")
        
        # 创建知识库 - 使用OpenSearch Serverless存储
        response = bedrock_agent_client.create_knowledge_base(
            name=kb_name,
            description="Knowledge base for report generation",
            roleArn=config['lambda_role_arn'],
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f"arn:aws:bedrock:{config['aws_region']}::foundation-model/amazon.titan-embed-text-v1"
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'vectorIndexName': f"{config['agent_name']}-vector-index",
                    'fieldMapping': {
                        'vectorField': 'embedding',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            },
            tags={
                'Project': 'report-generator',
                'Environment': 'development'
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        kb_status = response['knowledgeBase']['status']
        
        logger.info(f"知识库创建成功: ID={kb_id}, 状态={kb_status}")
        
        # 等待知识库准备就绪
        logger.info("等待知识库准备就绪...")
        wait_for_knowledge_base_ready(bedrock_agent_client, kb_id)
        
        # 将知识库关联到Agent
        associate_knowledge_base_to_agent(bedrock_agent_client, agent_id, kb_id, config)
        
        return {
            'knowledge_base_id': kb_id,
            'knowledge_base_name': kb_name,
            'status': 'created'
        }
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        error_message = e.response.get('Error', {}).get('Message')
        
        logger.error(f"创建知识库时出错: {error_code} - {error_message}")
        return {
            'status': 'error',
            'error_code': error_code,
            'error_message': error_message
        }
    
    except Exception as e:
        logger.error(f"创建知识库时出错: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }

def wait_for_knowledge_base_ready(bedrock_agent_client, kb_id, max_attempts=30, delay_seconds=10):
    """等待知识库准备就绪"""
    for attempt in range(max_attempts):
        try:
            response = bedrock_agent_client.get_knowledge_base(
                knowledgeBaseId=kb_id
            )
            
            status = response['knowledgeBase']['status']
            logger.info(f"知识库状态: {status} (尝试 {attempt+1}/{max_attempts})")
            
            if status == 'ACTIVE':
                logger.info("知识库已准备就绪")
                return True
            
            if status in ['FAILED', 'DELETING', 'DELETED']:
                logger.error(f"知识库处于终止状态: {status}")
                return False
            
            # 等待一段时间后再次检查
            time.sleep(delay_seconds)
        
        except Exception as e:
            logger.error(f"检查知识库状态时出错: {str(e)}")
            time.sleep(delay_seconds)
    
    logger.warning(f"等待知识库准备就绪超时，已尝试 {max_attempts} 次")
    return False

def associate_knowledge_base_to_agent(bedrock_agent_client, agent_id, kb_id, config):
    """将知识库关联到Agent"""
    try:
        logger.info(f"将知识库 {kb_id} 关联到Agent {agent_id}")
        
        response = bedrock_agent_client.associate_knowledge_base_to_agent(
            agentId=agent_id,
            knowledgeBaseId=kb_id,
            description="Knowledge base for report generation"
        )
        
        logger.info("知识库成功关联到Agent")
        return True
    
    except Exception as e:
        logger.error(f"关联知识库到Agent时出错: {str(e)}")
        return False

def create_action_group(client, agent_id, agent_version="DRAFT"):
    """
    Create an action group for the agent
    """
    logging.info(f"开始创建操作组: report-generator-agent-action-group")
    
    # 使用最新的agent版本
    if agent_version == "DRAFT":
        try:
            # 获取最新的agent版本
            response = client.list_agent_versions(
                agentId=agent_id,
                maxResults=1
            )
            if response.get('agentVersionSummaries'):
                agent_version = response['agentVersionSummaries'][0].get('agentVersion', 'DRAFT')
                logging.info(f"使用Agent版本: {agent_version}")
        except Exception as e:
            logging.warning(f"获取Agent版本失败，使用默认版本DRAFT: {str(e)}")
    
    # 创建OpenAPI schema
    api_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Report Generator API",
            "description": "API for generating various types of reports",
            "version": "1.0.0"
        },
        "paths": {
            "/generate-report": {
                "post": {
                    "summary": "Generate a report",
                    "description": "Generate a report based on the provided parameters",
                    "operationId": "generateReport",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "report_type": {
                                            "type": "string",
                                            "description": "Type of report to generate (e.g., financial, sales, marketing)"
                                        },
                                        "data_source": {
                                            "type": "string",
                                            "description": "Source of data for the report (e.g., database, file)"
                                        },
                                        "time_period": {
                                            "type": "string",
                                            "description": "Time period for the report (e.g., daily, weekly, monthly, quarterly, yearly)"
                                        }
                                    },
                                    "required": ["report_type"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Report generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "report_id": {
                                                "type": "string",
                                                "description": "ID of the generated report"
                                            },
                                            "status": {
                                                "type": "string",
                                                "description": "Status of the report generation"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        response = client.create_agent_action_group(
            agentId=agent_id,
            agentVersion=agent_version,
            actionGroupName="report-generator-agent-action-group",
            description="Action group for report generation",
            actionGroupExecutor={
                "lambda": "arn:aws:lambda:ap-northeast-1:458532992416:function:report_generator"
            },
            apiSchema={
                "payload": json.dumps(api_schema)
            },
            clientToken=str(uuid.uuid4())
        )
        
        action_group_id = response.get('actionGroupId')
        action_group_status = response.get('actionGroupStatus')
        logging.info(f"操作组创建成功: ID={action_group_id}, 状态={action_group_status}")
        
        return {
            'action_group_id': action_group_id,
            'action_group_name': "report-generator-agent-action-group",
            'status': 'created'
        }
    except Exception as e:
        logging.error(f"创建操作组时出错: {e.__class__.__name__} - {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }

def create_actions(bedrock_agent_client, agent_id, action_group_id):
    """创建操作"""
    try:
        # 定义操作
        actions = [
            {
                'name': 'GenerateReport',
                'description': 'Generate a report based on document analysis',
                'parameters': [
                    {
                        'name': 'documentId',
                        'description': 'The ID of the document to analyze',
                        'required': True,
                        'type': 'STRING'
                    },
                    {
                        'name': 'reportType',
                        'description': 'The type of report to generate',
                        'required': True,
                        'type': 'STRING',
                        'enum': ['summary', 'detailed', 'analysis']
                    }
                ]
            },
            {
                'name': 'ListDocuments',
                'description': 'List available documents',
                'parameters': []
            },
            {
                'name': 'GetReportStatus',
                'description': 'Get the status of a report generation task',
                'parameters': [
                    {
                        'name': 'reportId',
                        'description': 'The ID of the report',
                        'required': True,
                        'type': 'STRING'
                    }
                ]
            }
        ]
        
        # 创建每个操作
        for action in actions:
            logger.info(f"创建操作: {action['name']}")
            
            # 准备参数
            api_schema = {
                'actions': [
                    {
                        'name': action['name'],
                        'description': action['description'],
                        'parameters': action.get('parameters', [])
                    }
                ]
            }
            
            # 更新操作组API架构
            response = bedrock_agent_client.update_agent_action_group(
                agentId=agent_id,
                agentActionGroupId=action_group_id,
                apiSchema={
                    'payload': json.dumps(api_schema)
                }
            )
        
        logger.info(f"成功创建 {len(actions)} 个操作")
        return True
    
    except Exception as e:
        logger.error(f"创建操作时出错: {str(e)}")
        return False

def get_account_id():
    """获取AWS账户ID"""
    try:
        sts_client = boto3.client('sts')
        return sts_client.get_caller_identity()['Account']
    except Exception as e:
        logger.error(f"获取AWS账户ID时出错: {str(e)}")
        return "unknown"

def prepare_agent_for_alias(bedrock_agent_client, agent_id):
    """准备Agent以创建别名"""
    try:
        logger.info(f"准备Agent {agent_id} 以创建别名")
        
        response = bedrock_agent_client.prepare_agent(
            agentId=agent_id
        )
        
        logger.info("Agent准备成功")
        return True
    
    except Exception as e:
        logger.error(f"准备Agent时出错: {str(e)}")
        return False

def create_agent_alias(bedrock_agent_client, agent_id, config):
    """创建Agent别名"""
    try:
        alias_name = f"{config['agent_name']}-alias"
        logger.info(f"开始创建Agent别名: {alias_name}")
        
        # 首先准备Agent
        prepare_success = prepare_agent_for_alias(bedrock_agent_client, agent_id)
        if not prepare_success:
            logger.error("Agent准备失败，无法创建别名")
            return {
                'status': 'error',
                'error_message': "Agent准备失败，无法创建别名"
            }
        
        # 等待Agent准备完成
        logger.info("等待Agent准备完成...")
        time.sleep(10)  # 等待10秒
        
        # 获取Agent版本
        try:
            # 获取Agent的最新版本
            versions_response = bedrock_agent_client.list_agent_versions(
                agentId=agent_id,
                maxResults=10
            )
            
            agent_versions = versions_response.get('agentVersionSummaries', [])
            
            if agent_versions:
                # 使用最新的非DRAFT版本
                for version in agent_versions:
                    if version['agentVersion'] != 'DRAFT':
                        agent_version = version['agentVersion']
                        logger.info(f"使用Agent版本: {agent_version}")
                        break
                else:
                    # 如果没有找到非DRAFT版本，则跳过创建别名
                    logger.warning("没有找到非DRAFT版本，跳过创建别名")
                    return {
                        'status': 'skipped',
                        'error_message': "没有找到非DRAFT版本，跳过创建别名"
                    }
            else:
                # 如果没有版本，则跳过创建别名
                logger.warning("没有找到任何版本，跳过创建别名")
                return {
                    'status': 'skipped',
                    'error_message': "没有找到任何版本，跳过创建别名"
                }
            
            # 创建别名
            response = bedrock_agent_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description="Production alias for report generator agent",
                routingConfiguration=[
                    {
                        'agentVersion': agent_version
                    }
                ]
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            
            logger.info(f"Agent别名创建成功: ID={alias_id}")
            
            return {
                'alias_id': alias_id,
                'alias_name': alias_name,
                'status': 'created'
            }
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message')
            
            # 如果别名已存在，尝试获取它
            if error_code == 'ConflictException' and 'already exists' in error_message:
                try:
                    # 获取现有别名
                    aliases_response = bedrock_agent_client.list_agent_aliases(
                        agentId=agent_id,
                        maxResults=10
                    )
                    
                    for alias in aliases_response.get('agentAliasSummaries', []):
                        if alias['agentAliasName'] == alias_name:
                            logger.info(f"使用现有别名: ID={alias['agentAliasId']}")
                            return {
                                'alias_id': alias['agentAliasId'],
                                'alias_name': alias_name,
                                'status': 'exists'
                            }
                
                except Exception as inner_e:
                    logger.error(f"获取现有别名时出错: {str(inner_e)}")
            
            logger.error(f"创建Agent别名时出错: {error_code} - {error_message}")
            return {
                'status': 'error',
                'error_code': error_code,
                'error_message': error_message
            }
        
        except Exception as e:
            logger.error(f"获取或创建Agent版本时出错: {str(e)}")
            return {
                'status': 'error',
                'error_message': f"获取或创建Agent版本时出错: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"创建Agent别名时出错: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }

def update_deployment_status(agent_info, kb_info=None, action_group_info=None, alias_info=None):
    """更新部署状态"""
    try:
        # 获取部署状态文件路径
        status_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'deploy',
            'deployment_status.json'
        )
        
        # 确保目录存在
        os.makedirs(os.path.dirname(status_file_path), exist_ok=True)
        
        # 读取现有状态（如果存在）
        status_data = {}
        if os.path.exists(status_file_path):
            try:
                with open(status_file_path, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            except Exception as e:
                logger.warning(f"读取部署状态文件时出错: {str(e)}")
        
        # 确保bedrock部分存在
        if 'bedrock' not in status_data:
            status_data['bedrock'] = {}
        
        # 更新Agent信息
        if agent_info:
            status_data['bedrock']['agent'] = {
                'id': agent_info.get('agent_id'),
                'name': agent_info.get('agent_name'),
                'status': agent_info.get('status'),
                'timestamp': datetime.now().isoformat()
            }
            
            if agent_info.get('status') == 'error':
                status_data['bedrock']['agent']['error'] = agent_info.get('error_message', '')
        
        # 更新知识库信息
        if kb_info:
            if kb_info.get('status') == 'skipped':
                status_data['bedrock']['knowledge_base'] = {
                    'status': 'skipped',
                    'message': kb_info.get('message', '知识库创建已跳过'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                status_data['bedrock']['knowledge_base'] = {
                    'id': kb_info.get('knowledge_base_id'),
                    'name': kb_info.get('knowledge_base_name'),
                    'status': kb_info.get('status'),
                    'timestamp': datetime.now().isoformat()
                }
                
                if kb_info.get('status') == 'error':
                    status_data['bedrock']['knowledge_base']['error'] = kb_info.get('error_message', '')
        
        # 更新操作组信息
        if action_group_info:
            status_data['bedrock']['action_group'] = {
                'id': action_group_info.get('action_group_id'),
                'name': action_group_info.get('action_group_name'),
                'status': action_group_info.get('status'),
                'timestamp': datetime.now().isoformat()
            }
            
            if action_group_info.get('status') == 'error':
                status_data['bedrock']['action_group']['error'] = action_group_info.get('error_message', '')
        
        # 更新别名信息
        if alias_info:
            status_data['bedrock']['alias'] = {
                'id': alias_info.get('alias_id'),
                'name': alias_info.get('alias_name'),
                'status': alias_info.get('status'),
                'timestamp': datetime.now().isoformat()
            }
            
            if alias_info.get('status') == 'error':
                status_data['bedrock']['alias']['error'] = alias_info.get('error_message', '')
        
        # 写入状态文件
        with open(status_file_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"部署状态已更新: {status_file_path}")
        
    except Exception as e:
        logger.error(f"更新部署状态时出错: {str(e)}")
        traceback.print_exc()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='创建Bedrock Agent')
    
    # AWS配置
    parser.add_argument('--profile', type=str, help='AWS配置文件名称')
    
    return parser.parse_args()

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 加载配置
        config = load_config()
        
        # 使用命令行参数中的配置文件（如果提供）
        profile = args.profile
        if profile:
            logger.info(f"使用AWS配置文件: {profile}")
        
        # 创建Bedrock Agent客户端
        bedrock_agent_client = create_bedrock_agent_client(config, profile)
        
        # 创建Agent
        agent_info = create_agent(bedrock_agent_client, config)
        
        if agent_info['status'] == 'error':
            logger.error(f"创建Agent失败: {agent_info.get('error_message', '未知错误')}")
            update_deployment_status(agent_info)
            return 1
        
        agent_id = agent_info['agent_id']
        
        # 跳过知识库创建
        kb_info = {
            'status': 'skipped',
            'message': '知识库创建已跳过'
        }
        logger.info("知识库创建已跳过")
        
        # 创建动作组
        action_group_info = create_action_group(bedrock_agent_client, agent_id)
        
        if action_group_info['status'] == 'error':
            logger.error(f"创建动作组失败: {action_group_info.get('error_message', '未知错误')}")
            update_deployment_status(agent_info, kb_info, action_group_info)
            return 1
        
        # 准备Agent别名
        prepare_result = prepare_agent_for_alias(bedrock_agent_client, agent_id)
        
        if not prepare_result:
            logger.error("准备Agent别名失败")
            update_deployment_status(agent_info, kb_info, action_group_info, {'status': 'error', 'error_message': '准备Agent别名失败'})
            return 1
        
        # 创建Agent别名
        alias_info = create_agent_alias(bedrock_agent_client, agent_id, config)
        
        if alias_info['status'] == 'error':
            logger.error(f"创建Agent别名失败: {alias_info.get('error_message', '未知错误')}")
            update_deployment_status(agent_info, kb_info, action_group_info, alias_info)
            return 1
        
        # 更新部署状态
        update_deployment_status(agent_info, kb_info, action_group_info, alias_info)
        
        logger.info("Bedrock Agent部署完成")
        return 0
        
    except Exception as e:
        logger.error(f"部署过程中出错: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main()) 