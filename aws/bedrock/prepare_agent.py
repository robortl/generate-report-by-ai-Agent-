#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agentの準備（Prepare）スクリプト
"""

import os
import sys
import json
import logging
import boto3
import time
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
        max_attempts = 30  # 5分間（10秒 x 30）
        attempts = 0
        
        while status != 'PREPARED' and attempts < max_attempts:
            time.sleep(10)
            attempts += 1
            
            try:
                response = bedrock_agent_client.get_agent(agentId=agent_id)
                status = response.get('agent', {}).get('agentStatus')
                logger.info(f"エージェントステータス: {status} (試行 {attempts}/{max_attempts})")
                
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
    
    # エージェントを準備
    if prepare_agent(bedrock_agent_client, agent_id):
        logger.info("エージェントの準備が完了しました")
        return 0
    else:
        logger.error("エージェントの準備に失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 