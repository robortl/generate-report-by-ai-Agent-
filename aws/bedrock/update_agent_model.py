#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agentの基盤モデル更新スクリプト
"""

import os
import sys
import json
import logging
import boto3
import time
import argparse
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# 設定ログ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ツール使用をサポートするモデル
TOOL_SUPPORTED_MODELS = [
    # Claude 3モデル
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    # Claude 2モデル
    "anthropic.claude-v2",
    "anthropic.claude-v2:1",
    # Claude Instantモデル
    "anthropic.claude-instant-v1",
    # Amazon Titanモデル
    "amazon.titan-text-premier-v1:0",
    "amazon.titan-text-express-v1",
    # Cohere Command
    "cohere.command-text-v14",
    "cohere.command-r-v1:0",
    # AI21 Jurassic
    "ai21.j2-ultra-v1",
    "ai21.j2-mid-v1"
]

def load_config():
    """設定を読み込む"""
    # .envファイルを読み込む
    load_dotenv()
    
    # 環境変数を取得
    config = {
        'aws_region': os.getenv('AWS_REGION', 'ap-northeast-1'),
        'aws_profile': os.getenv('AWS_PROFILE', 'default'),
        'agent_name': os.getenv('BEDROCK_AGENT_NAME', 'report-generator-agent'),
        'foundation_model': os.getenv('BEDROCK_FOUNDATION_MODEL', 'anthropic.claude-3-sonnet-20240229-v1:0'),
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

def update_agent_model(bedrock_agent_client, agent_id, foundation_model):
    """エージェントの基盤モデルを更新"""
    try:
        logger.info(f"エージェント {agent_id} の基盤モデルを {foundation_model} に更新中...")
        
        # 現在のエージェント情報を取得
        response = bedrock_agent_client.get_agent(
            agentId=agent_id
        )
        
        current_agent = response.get('agent', {})
        current_model = current_agent.get('foundationModel')
        
        logger.info(f"現在の基盤モデル: {current_model}")
        
        if current_model == foundation_model:
            logger.info(f"基盤モデルは既に {foundation_model} に設定されています。更新は不要です。")
            return {
                'agent_id': agent_id,
                'agent_name': current_agent.get('agentName'),
                'foundation_model': current_model,
                'status': 'unchanged'
            }
        
        # エージェントを更新
        update_response = bedrock_agent_client.update_agent(
            agentId=agent_id,
            agentName=current_agent.get('agentName'),
            description=current_agent.get('description'),
            instruction=current_agent.get('instruction'),
            foundationModel=foundation_model,
            agentResourceRoleArn=current_agent.get('agentResourceRoleArn'),
            idleSessionTTLInSeconds=current_agent.get('idleSessionTTLInSeconds', 1800)
        )
        
        updated_agent = update_response.get('agent', {})
        logger.info(f"エージェント更新成功: 名前={updated_agent.get('agentName')}, モデル={updated_agent.get('foundationModel')}")
        
        return {
            'agent_id': agent_id,
            'agent_name': updated_agent.get('agentName'),
            'foundation_model': updated_agent.get('foundationModel'),
            'status': 'updated'
        }
    except Exception as e:
        logger.error(f"エージェント更新エラー: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e)
        }

def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description='AWS Bedrock Agentの基盤モデルを更新')
    
    # AWS設定
    parser.add_argument('--profile', type=str, help='AWS設定プロファイル名')
    
    # エージェント設定
    parser.add_argument('--agent-name', type=str, help='エージェント名')
    
    # モデル設定
    parser.add_argument('--model', type=str, choices=TOOL_SUPPORTED_MODELS, 
                        help='使用する基盤モデル')
    
    parser.add_argument('--list-models', action='store_true', 
                        help='ツール使用をサポートするモデル一覧を表示')
    
    return parser.parse_args()

def main():
    """メイン関数"""
    # コマンドライン引数を解析
    args = parse_args()
    
    # モデル一覧表示
    if args.list_models:
        logger.info("ツール使用をサポートするモデル一覧:")
        for i, model in enumerate(TOOL_SUPPORTED_MODELS, 1):
            logger.info(f"{i}. {model}")
        return 0
    
    # 設定を読み込む
    config = load_config()
    
    # コマンドライン引数で設定を上書き
    if args.profile:
        config['aws_profile'] = args.profile
    
    if args.agent_name:
        config['agent_name'] = args.agent_name
    
    if args.model:
        config['foundation_model'] = args.model
    
    # 選択されたモデルがサポートされているか確認
    if config['foundation_model'] not in TOOL_SUPPORTED_MODELS:
        logger.warning(f"選択されたモデル '{config['foundation_model']}' はツール使用をサポートしていない可能性があります")
        logger.info("サポートされているモデル:")
        for i, model in enumerate(TOOL_SUPPORTED_MODELS, 1):
            logger.info(f"{i}. {model}")
        
        # 続行確認
        confirm = input("続行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            logger.info("処理を中止します")
            return 0
    
    # Bedrock Agentクライアントを作成
    bedrock_agent_client = create_bedrock_agent_client(config)
    
    # エージェントIDを取得
    agent_id = get_agent_id(bedrock_agent_client, config['agent_name'])
    
    if not agent_id:
        logger.error("エージェントIDが取得できないため、処理を終了します")
        return 1
    
    # エージェントの基盤モデルを更新
    result = update_agent_model(bedrock_agent_client, agent_id, config['foundation_model'])
    
    if result['status'] == 'error':
        logger.error(f"エージェント更新エラー: {result.get('error_message', '不明なエラー')}")
        return 1
    
    logger.info(f"エージェント更新完了: {json.dumps(result, indent=2)}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 