#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bedrock Agent DRAFTバージョンテストスクリプト
"""

import os
import sys
import json
import logging
import boto3
import argparse
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import traceback
import time

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
    """エージェントIDを取得する"""
    try:
        response = bedrock_agent_client.list_agents()
        agents = response.get('agentSummaries', [])
        
        for agent in agents:
            if agent.get('agentName') == agent_name:
                logger.info(f"エージェントID: {agent.get('agentId')}")
                return agent.get('agentId')
        
        logger.error(f"エージェント '{agent_name}' が見つかりません")
        return None
    except Exception as e:
        logger.error(f"エージェントID取得エラー: {e}")
        return None

def get_agent_alias_id(bedrock_agent_client, agent_id):
    """エージェントエイリアスIDを取得する"""
    try:
        response = bedrock_agent_client.list_agent_aliases(
            agentId=agent_id
        )
        aliases = response.get('agentAliasSummaries', [])
        
        if aliases:
            # 最初のエイリアスを使用
            alias_id = aliases[0].get('agentAliasId')
            logger.info(f"エージェントエイリアスID: {alias_id}")
            return alias_id
        
        logger.error(f"エージェントID '{agent_id}' のエイリアスが見つかりません")
        return "TSTALIASID"  # フォールバックとしてデフォルト値を使用
    except Exception as e:
        logger.error(f"エージェントエイリアスID取得エラー: {e}")
        return "TSTALIASID"  # エラー時はデフォルト値を使用

def test_bedrock_model_access():
    """Bedrockモデルへのアクセスをテストする"""
    try:
        # Bedrockクライアントを作成
        bedrock_client = boto3.client('bedrock')
        logger.info("Bedrockクライアントを作成しました")
        
        # モデルリストを取得
        response = bedrock_client.list_foundation_models()
        logger.info(f"モデル数: {len(response.get('modelSummaries', []))}")
        
        # Titan Text Express モデルを使用してテキスト生成をテスト
        bedrock_runtime = boto3.client('bedrock-runtime')
        logger.info("Bedrock Runtimeクライアントを作成しました")
        
        model_id = "amazon.titan-text-express-v1"
        body = json.dumps({
            "inputText": "Hello, world!",
            "textGenerationConfig": {
                "maxTokenCount": 100,
                "temperature": 0.7,
                "topP": 0.9
            }
        })
        
        try:
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body
            )
            response_body = json.loads(response.get('body').read())
            logger.info(f"モデルレスポンス: {response_body}")
            return True
        except ClientError as e:
            logger.error(f"モデル呼び出しエラー: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Bedrockモデルアクセステストエラー: {e}")
        return False

def invoke_agent(config, agent_id, agent_alias_id, session_id, input_text, enable_trace=False):
    """エージェントを呼び出す"""
    try:
        # Bedrock Agent Runtimeクライアントを作成
        bedrock_agent_runtime_client = create_bedrock_agent_runtime_client(config)
        logger.info(f"エージェント呼び出し: {input_text}")
        
        # エージェントを呼び出す
        response = bedrock_agent_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=enable_trace
        )
        
        return response
    except Exception as e:
        logger.error(f"エージェント呼び出しエラー: {e}")
        raise

def test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, agent_alias_id, prompt, debug=False):
    """プロンプトでエージェントをテストする"""
    if debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"プロンプト: {prompt}")
    
    # Bedrockモデルへのアクセスをテスト
    test_bedrock_model_access()
    
    # セッションIDを生成
    session_id = f"test-session-{int(time.time())}"
    logger.info(f"セッションID: {session_id}")
    
    try:
        # エージェントを呼び出す
        response = bedrock_agent_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,  # 動的に取得したエイリアスIDを使用
            sessionId=session_id,
            inputText=prompt,
            enableTrace=True
        )
        
        # レスポンス処理の開始をログに記録
        logging.info("レスポンス処理を開始します...")
        
        # レスポンスの型と利用可能なキーをログに記録
        logging.debug(f"レスポンスの型: {type(response)}")
        if isinstance(response, dict):
            logging.debug(f"レスポンスのキー: {response.keys()}")
            if 'ResponseMetadata' in response:
                logging.debug(f"ResponseMetadata: {response['ResponseMetadata']}")
        
        completion = ""
        trace_info = []
        event_count = 0
        
        # EventStreamがレスポンスに含まれているか確認
        if 'completion' in response:
            logging.debug("EventStreamを処理します...")
            
            # イベントストリームを処理
            for event in response['completion']:
                event_count += 1
                logging.debug(f"イベント {event_count} の型: {type(event)}")
                
                # イベントの内容をダンプ
                if isinstance(event, dict):
                    logging.debug(f"イベント内容: {json.dumps(event, default=str)}")
                else:
                    logging.debug(f"イベント内容 (非dict): {event}")
                
                # チャンクデータの処理
                if isinstance(event, dict) and 'chunk' in event:
                    chunk = event['chunk']
                    logging.debug(f"チャンクデータ: {chunk}")
                    
                    if 'bytes' in chunk:
                        try:
                            # バイナリデータをデコード
                            chunk_data = chunk['bytes'].decode('utf-8')
                            logging.debug(f"デコードされたチャンクデータ: {chunk_data}")
                            
                            # JSONとしてパース
                            try:
                                json_data = json.loads(chunk_data)
                                logging.debug(f"JSONデータ: {json_data}")
                                
                                # 'completion'または'content'キーを確認
                                if 'completion' in json_data:
                                    completion += json_data['completion']
                                    logging.debug(f"completionを追加: {json_data['completion']}")
                                elif 'content' in json_data:
                                    completion += json_data['content']
                                    logging.debug(f"contentを追加: {json_data['content']}")
                                
                                # トレース情報があれば保存
                                if 'trace' in json_data:
                                    trace_info.append(json_data['trace'])
                                    logging.debug(f"トレース情報を追加")
                                
                            except json.JSONDecodeError as e:
                                logging.warning(f"JSONデコードエラー: {e}")
                                # JSON形式でない場合は生のテキストとして追加
                                completion += chunk_data
                                logging.debug(f"生テキストとして追加: {chunk_data}")
                        
                        except Exception as e:
                            logging.error(f"チャンクデータのデコード中にエラーが発生しました: {e}")
                            logging.debug(f"生のチャンクデータ: {chunk}")
                
                # 文字列イベントの処理
                elif isinstance(event, str):
                    logging.debug(f"文字列イベント: {event}")
                    
                    # JSONとしてパースを試みる
                    try:
                        json_data = json.loads(event)
                        logging.debug(f"パースされたJSON: {json_data}")
                        
                        # メタデータフィールドでないか確認
                        if not any(key in json_data for key in ['ResponseMetadata', 'contentType', 'sessionId']):
                            completion += event
                            logging.debug(f"文字列イベントを追加: {event}")
                    
                    except json.JSONDecodeError:
                        # JSON形式でない場合は生のテキストとして追加
                        completion += event
                        logging.debug(f"非JSONテキストを追加: {event}")
                
                # その他のタイプのイベント
                else:
                    logging.debug(f"その他のイベント: {str(event)}")
                    completion += str(event)
        
        # レスポンスヘッダーの確認
        if isinstance(response, dict) and 'ResponseMetadata' in response:
            headers = response['ResponseMetadata'].get('HTTPHeaders', {})
            logging.debug(f"レスポンスヘッダー: {headers}")
            
            # コンテンツタイプの確認
            if 'content-type' in headers:
                logging.debug(f"コンテンツタイプ: {headers['content-type']}")
        
        # 処理したイベントの総数をログに記録
        logging.info(f"処理したイベントの総数: {event_count}")
        
        # 最終的なエージェントのレスポンスを表示
        if completion:
            logging.info("=== エージェントのレスポンス ===")
            logging.info(completion)
            logging.info("=============================")
        else:
            logging.warning("レスポンスが空です")
            logging.debug(f"生のレスポンス: {response}")
        
        return completion, trace_info
    
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        traceback.print_exc()
        return "", []

def test_agent_conversation(bedrock_agent_client, bedrock_agent_runtime_client, agent_id, debug=False):
    """エージェントとの会話テスト"""
    try:
        # セッションIDを生成
        session_id = f"test-session-{int(time.time())}"
        logger.info(f"セッションID: {session_id}")
        
        # エージェントエイリアスIDを取得
        agent_alias_id = get_agent_alias_id(bedrock_agent_client, agent_id)
        
        # 会話履歴を初期化
        conversation_history = []
        
        while True:
            # ユーザー入力を取得
            user_input = input("あなた: ")
            
            # 終了コマンドをチェック
            if user_input.lower() in ['exit', 'quit', '終了']:
                break
            
            # エージェントを呼び出す
            response = bedrock_agent_runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,  # 動的に取得したエイリアスIDを使用
                sessionId=session_id,
                inputText=user_input,
                enableTrace=True,
                streamFinalResponse=True  # ストリーミングレスポンスを有効化
            )
            
            # レスポンスを処理
            completion, trace_info = test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, agent_alias_id, user_input, debug)
            print(f"エージェント: {completion}")
            
            # 会話履歴に追加
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": completion})
        
        return conversation_history
    except ClientError as e:
        logger.error(f"エージェント対話エラー: {e}")
        raise

def parse_args():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(description='AWS Bedrock Agentをテストします。')
    parser.add_argument('--profile', help='使用するAWSプロファイル')
    parser.add_argument('--agent-name', help='テストするエージェントの名前')
    parser.add_argument('--prompt', help='エージェントに送信するプロンプト')
    parser.add_argument('--conversation', action='store_true', help='対話モードでエージェントをテスト')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効にする')
    return parser.parse_args()

def main():
    """メイン関数"""
    # コマンドライン引数をパース
    args = parse_args()
    
    # デバッグモードが有効な場合、ログレベルをDEBUGに設定
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        # boto3のデバッグログも有効にする
        boto3.set_stream_logger('', logging.DEBUG)
    
    # 環境変数を読み込む
    load_dotenv()
    
    # 設定を読み込む
    config = load_config()
    
    # コマンドライン引数で設定を上書き
    if args.profile:
        config['aws_profile'] = args.profile
        logger.info(f"AWS設定プロファイル: {args.profile}")
    
    if args.agent_name:
        config['agent_name'] = args.agent_name
    
    # Bedrock Agentクライアントを作成
    bedrock_agent_client = create_bedrock_agent_client(config)
    
    # Bedrock Agent Runtimeクライアントを作成
    bedrock_agent_runtime_client = create_bedrock_agent_runtime_client(config)
    
    # エージェントIDを取得
    agent_id = get_agent_id(bedrock_agent_client, config['agent_name'])
    
    if not agent_id:
        logger.error("エージェントIDが取得できないため、処理を終了します")
        return 1
    
    # エージェントエイリアスIDを取得
    agent_alias_id = get_agent_alias_id(bedrock_agent_client, agent_id)
    
    # テスト実行
    if args.conversation:
        # 対話テスト
        test_agent_conversation(bedrock_agent_client, bedrock_agent_runtime_client, agent_id, args.debug)
    elif args.prompt:
        # 単一プロンプトテスト
        test_agent_with_prompt(bedrock_agent_runtime_client, agent_id, agent_alias_id, args.prompt, args.debug)
    else:
        logger.error("--prompt または --conversation オプションを指定してください")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 