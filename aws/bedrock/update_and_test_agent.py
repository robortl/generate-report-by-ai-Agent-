#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agentの更新、準備、テストを一連の流れで実行するスクリプト
"""

import os
import sys
import json
import logging
import boto3
import time
import argparse
import subprocess
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
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "anthropic.claude-instant-v1",
    "amazon.titan-text-premier-v1:0"
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

def create_bedrock_agent_runtime_client(config):
    """Bedrock Agent Runtimeクライアントを作成"""
    session = boto3.Session(
        profile_name=config.get('aws_profile'),
        region_name=config.get('aws_region')
    )
    
    client = session.client('bedrock-agent-runtime')
    logger.info("Bedrock Agent Runtimeクライアントを作成しました")
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

def create_agent_version(bedrock_agent_client, agent_id):
    """エージェントバージョンを作成"""
    try:
        logger.info(f"エージェント {agent_id} のバージョンを作成中...")
        response = bedrock_agent_client.create_agent_version(
            agentId=agent_id
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
            ]
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

def test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, prompt):
    """プロンプトでエージェントをテスト"""
    try:
        logger.info(f"エージェント {agent_id} をテスト中...")
        logger.info(f"プロンプト: {prompt}")
        
        response = bedrock_agent_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId="TSTALIASID",  # テスト用エイリアスID
            sessionId="test-session-" + os.urandom(8).hex(),
            inputText=prompt
        )
        
        # レスポンスを処理
        completion = ""
        for event in response.get('completion'):
            chunk = event.get('chunk')
            if chunk:
                chunk_obj = json.loads(chunk.read().decode('utf-8'))
                if 'chunk' in chunk_obj:
                    completion += chunk_obj['chunk']['content']
        
        logger.info("エージェントの応答:")
        logger.info(completion)
        
        return completion
    except Exception as e:
        logger.error(f"エージェントテストエラー: {str(e)}")
        return None

def parse_args():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description='AWS Bedrock Agentの更新、準備、テスト')
    
    # AWS設定
    parser.add_argument('--profile', type=str, help='AWS設定プロファイル名')
    
    # エージェント設定
    parser.add_argument('--agent-name', type=str, help='エージェント名')
    
    # モデル設定
    parser.add_argument('--model', type=str, choices=TOOL_SUPPORTED_MODELS, 
                        help='使用する基盤モデル')
    
    parser.add_argument('--list-models', action='store_true', 
                        help='ツール使用をサポートするモデル一覧を表示')
    
    # 処理オプション
    parser.add_argument('--skip-update', action='store_true', 
                        help='モデル更新をスキップ')
    
    parser.add_argument('--skip-prepare', action='store_true', 
                        help='エージェント準備をスキップ')
    
    parser.add_argument('--skip-version', action='store_true', 
                        help='バージョン作成をスキップ')
    
    parser.add_argument('--skip-alias', action='store_true', 
                        help='エイリアス作成をスキップ')
    
    parser.add_argument('--skip-test', action='store_true', 
                        help='テストをスキップ')
    
    parser.add_argument('--prompt', type=str, default="レポートを生成してください", 
                        help='テスト用プロンプト')
    
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
    
    # 1. エージェントの基盤モデルを更新
    if not args.skip_update:
        result = update_agent_model(bedrock_agent_client, agent_id, config['foundation_model'])
        
        if result['status'] == 'error':
            logger.error(f"エージェント更新エラー: {result.get('error_message', '不明なエラー')}")
            return 1
        
        logger.info(f"エージェント更新完了: {json.dumps(result, indent=2)}")
    else:
        logger.info("モデル更新をスキップします")
    
    # 2. エージェントを準備
    if not args.skip_prepare:
        if prepare_agent(bedrock_agent_client, agent_id):
            logger.info("エージェントの準備が完了しました")
        else:
            logger.error("エージェントの準備に失敗しました")
            return 1
    else:
        logger.info("エージェント準備をスキップします")
    
    # 3. エージェントバージョンを作成
    agent_version = None
    if not args.skip_version:
        agent_version = create_agent_version(bedrock_agent_client, agent_id)
        
        if not agent_version:
            logger.error("エージェントバージョンの作成に失敗しました")
            return 1
        
        logger.info(f"エージェントバージョン作成完了: {agent_version}")
    else:
        logger.info("バージョン作成をスキップします")
    
    # 4. エイリアスを作成
    if not args.skip_alias and agent_version:
        alias_info = create_agent_alias(bedrock_agent_client, agent_id, agent_version)
        
        if alias_info['status'] == 'error':
            logger.error(f"エイリアス作成エラー: {alias_info.get('error_message', '不明なエラー')}")
            return 1
        
        logger.info(f"エイリアス作成完了: {json.dumps(alias_info, indent=2)}")
    else:
        logger.info("エイリアス作成をスキップします")
    
    # 5. エージェントをテスト
    if not args.skip_test:
        # Bedrock Agent Runtimeクライアントを作成
        bedrock_agent_runtime_client = create_bedrock_agent_runtime_client(config)
        
        # テスト実行
        test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, args.prompt)
    else:
        logger.info("テストをスキップします")
    
    logger.info("処理が完了しました")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 