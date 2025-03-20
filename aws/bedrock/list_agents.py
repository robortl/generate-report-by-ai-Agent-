#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agent一覧表示スクリプト
"""

import os
import sys
import json
import logging
import boto3
from dotenv import load_dotenv

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

def list_agents(bedrock_agent_client):
    """すべてのBedrock Agentsを一覧表示"""
    try:
        response = bedrock_agent_client.list_agents()
        return response.get('agentSummaries', [])
    except Exception as e:
        logger.error(f"Agents一覧取得エラー: {str(e)}")
        return []

def list_agent_action_groups(bedrock_agent_client, agent_id, agent_version="DRAFT"):
    """エージェントのアクショングループを一覧表示"""
    try:
        response = bedrock_agent_client.list_agent_action_groups(
            agentId=agent_id,
            agentVersion=agent_version
        )
        return response.get('actionGroupSummaries', [])
    except Exception as e:
        logger.error(f"アクショングループ一覧取得エラー: {str(e)}")
        return []

def main():
    """メイン関数"""
    # 設定を読み込む
    config = load_config()
    
    # Bedrock Agentクライアントを作成
    bedrock_agent_client = create_bedrock_agent_client(config)
    
    # エージェント一覧を取得
    agents = list_agents(bedrock_agent_client)
    
    if not agents:
        logger.info("エージェントが見つかりませんでした")
        return
    
    # エージェント情報を表示
    logger.info(f"合計 {len(agents)} エージェントが見つかりました:")
    for i, agent in enumerate(agents, 1):
        logger.info(f"\n{i}. エージェント情報:")
        logger.info(f"   ID: {agent.get('agentId')}")
        logger.info(f"   名前: {agent.get('agentName')}")
        logger.info(f"   説明: {agent.get('description')}")
        logger.info(f"   ステータス: {agent.get('agentStatus')}")
        logger.info(f"   最終更新: {agent.get('updatedAt')}")
        
        # アクショングループを取得
        agent_id = agent.get('agentId')
        action_groups = list_agent_action_groups(bedrock_agent_client, agent_id)
        
        if action_groups:
            logger.info(f"   アクショングループ ({len(action_groups)}):")
            for j, action_group in enumerate(action_groups, 1):
                logger.info(f"     {j}. {action_group.get('actionGroupName')} (ID: {action_group.get('actionGroupId')})")
        else:
            logger.info("   アクショングループ: なし")

if __name__ == "__main__":
    main() 