#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agentバージョン作成スクリプト
"""

import os
import sys
import json
import logging
import boto3
import time
import uuid
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# 設定ログ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """設定を読み込む"""
    # .envファイルを読み込む
    load_dotenv()
    
    # 環境変数を取得
    config = {
        'aws_region': os.getenv('AWS_REGION', 'ap-northeast-1'),
        'aws_profile': os.getenv('AWS_PROFILE', 'default'),
        'agent_name': os.getenv('BEDROCK_AGENT_NAME', 'report-generator-agent'),
    }
    
    return config

def create_bedrock_agent_client(config):
    """Bedrock Agentクライアントを作成"""
    session = boto3.Session(
        profile_name=config.get('aws_profile'),
        region_name=config.get('aws_region')
    )
    
    client = session.client('bedrock-agent')
    logger.info("Bedrock Agentクライアントを作成しました")
    return client

def get_agent_id(bedrock_agent_client, agent_name):
    """エージェント名からIDを取得"""
    try:
        response = bedrock_agent_client.list_agents()
        agents = response.get('agentSummaries', [])
        
        for agent in agents:
            if agent.get('agentName') == agent_name:
                return agent.get('agentId')
        
        logger.error(f"エージェント '{agent_name}' が見つかりませんでした")
        return None
    except Exception as e:
        logger.error(f"エージェントID取得エラー: {str(e)}")
        return None

def prepare_agent(bedrock_agent_client, agent_id):
    """エージェントを準備"""
    try:
        logger.info(f"エージェント {agent_id} を準備中...")
        response = bedrock_agent_client.prepare_agent(
            agentId=agent_id
        )
        
        prepare_job_id = response.get('prepareJobId')
        logger.info(f"準備ジョブID: {prepare_job_id}")
        
        # 準備完了を待機
        status = None
        max_attempts = 12  # 1分間（5秒 x 12）
        attempts = 0
        
        while status != 'PREPARED' and attempts < max_attempts:
            time.sleep(5)
            attempts += 1
            
            try:
                response = bedrock_agent_client.get_agent(agentId=agent_id)
                status = response.get('agentStatus')
                logger.info(f"エージェントステータス: {status}")
                
                if status == 'PREPARED':
                    logger.info("エージェントの準備が完了しました")
                    return True
                elif status == 'FAILED':
                    logger.error("エージェントの準備に失敗しました")
                    return False
            except Exception as e:
                logger.warning(f"ステータス確認エラー: {str(e)}")
        
        if status != 'PREPARED':
            logger.warning("タイムアウト: エージェントの準備が完了しませんでした")
            return False
            
        return True
    except Exception as e:
        logger.error(f"エージェント準備エラー: {str(e)}")
        return False

def create_agent_version(bedrock_agent_client, agent_id):
    """エージェントバージョンを作成"""
    try:
        # エージェントを準備
        if not prepare_agent(bedrock_agent_client, agent_id):
            logger.error("エージェントの準備に失敗したため、バージョン作成をスキップします")
            return None
        
        # バージョンを作成
        logger.info(f"エージェント {agent_id} のバージョンを作成中...")
        response = bedrock_agent_client.create_agent_version(
            agentId=agent_id,
            clientToken=str(uuid.uuid4())
        )
        
        agent_version = response.get('agentVersion')
        agent_status = response.get('agentStatus')
        
        logger.info(f"バージョン作成成功: バージョン={agent_version}, ステータス={agent_status}")
        
        return agent_version
    except ClientError as e:
        logger.error(f"バージョン作成エラー: {e.__class__.__name__} - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"バージョン作成エラー: {str(e)}")
        return None

def create_agent_alias(bedrock_agent_client, agent_id, agent_version):
    """エージェントエイリアスを作成"""
    try:
        alias_name = f"report-generator-agent-alias"
        
        # エイリアスを作成
        logger.info(f"エイリアス '{alias_name}' を作成中...")
        response = bedrock_agent_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name,
            description=f"Alias for report generator agent",
            routingConfiguration=[
                {
                    'agentVersion': agent_version
                }
            ],
            clientToken=str(uuid.uuid4())
        )
        
        alias_id = response.get('agentAliasId')
        alias_status = response.get('agentAliasStatus')
        
        logger.info(f"エイリアス作成成功: ID={alias_id}, ステータス={alias_status}")
        
        return {
            'alias_id': alias_id,
            'alias_name': alias_name,
            'status': 'created'
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            logger.warning(f"エイリアス '{alias_name}' は既に存在します")
            
            # 既存のエイリアスを取得
            try:
                response = bedrock_agent_client.list_agent_aliases(
                    agentId=agent_id
                )
                
                for alias in response.get('agentAliasSummaries', []):
                    if alias.get('agentAliasName') == alias_name:
                        alias_id = alias.get('agentAliasId')
                        logger.info(f"既存のエイリアスを使用: ID={alias_id}")
                        
                        return {
                            'alias_id': alias_id,
                            'alias_name': alias_name,
                            'status': 'exists'
                        }
            except Exception as inner_e:
                logger.error(f"既存のエイリアス取得エラー: {str(inner_e)}")
        
        logger.error(f"エイリアス作成エラー: {e.__class__.__name__} - {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }
    except Exception as e:
        logger.error(f"エイリアス作成エラー: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }

def main():
    """メイン関数"""
    # 設定を読み込む
    config = load_config()
    
    # Bedrock Agentクライアントを作成
    bedrock_agent_client = create_bedrock_agent_client(config)
    
    # エージェントIDを取得
    agent_id = get_agent_id(bedrock_agent_client, config['agent_name'])
    
    if not agent_id:
        logger.error("エージェントIDが取得できないため、処理を終了します")
        return 1
    
    # エージェントバージョンを作成
    agent_version = create_agent_version(bedrock_agent_client, agent_id)
    
    if not agent_version:
        logger.error("エージェントバージョンの作成に失敗したため、処理を終了します")
        return 1
    
    # エイリアスを作成
    alias_info = create_agent_alias(bedrock_agent_client, agent_id, agent_version)
    
    if alias_info['status'] == 'error':
        logger.error(f"エイリアス作成エラー: {alias_info.get('error_message', '不明なエラー')}")
        return 1
    
    logger.info(f"処理完了: バージョン={agent_version}, エイリアス={alias_info}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 