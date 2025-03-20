#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シンプルなBedrock Agentテストスクリプト
"""

import boto3
import json
import sys
import time
from botocore.exceptions import ClientError

def main():
    # Bedrockクライアントを作成
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
    
    # エージェントIDとエイリアスID
    agent_id = "LPJVAYJAK2"
    agent_alias_id = "TSTALIASID"
    
    # テストプロンプト
    prompt = "東京の天気はどうですか？"
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    
    # セッションID（一意の値を使用）
    session_id = f"test-session-{int(time.time())}"
    
    print(f"エージェントID: {agent_id}")
    print(f"エイリアスID: {agent_alias_id}")
    print(f"セッションID: {session_id}")
    print(f"テストプロンプト: {prompt}")
    
    try:
        # エージェントを呼び出す
        print("\nエージェントを呼び出しています...")
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=prompt,
            enableTrace=True  # トレース情報を有効化
        )
        
        # レスポンスのメタデータを表示
        print("\nレスポンスメタデータ:")
        print(json.dumps({
            "contentType": response.get("contentType"),
            "sessionId": response.get("sessionId"),
            "ResponseMetadata": response.get("ResponseMetadata")
        }, indent=2, default=str))
        
        # completionキーがあるか確認
        if 'completion' in response:
            print("\ncompletionキーが見つかりました")
            completion = response['completion']
            
            # completionの型を確認
            print(f"completion型: {type(completion)}")
            
            # EventStreamオブジェクトを処理
            try:
                print("\nストリーミングレスポンスを処理中...")
                full_response = ""
                
                # EventStreamからイベントを読み取る
                for event in completion:
                    # イベントの型と内容を表示
                    print(f"\nイベント型: {type(event)}")
                    
                    # イベントの内容に基づいて処理
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            try:
                                text = chunk['bytes'].decode('utf-8')
                                full_response += text
                                print(f"チャンク: {text}")
                            except Exception as e:
                                print(f"チャンクのデコードエラー: {e}")
                    
                    # トレース情報があれば表示
                    if 'trace' in event:
                        print(f"トレース情報: {json.dumps(event['trace'], indent=2, default=str)}")
                
                print(f"\n完全なレスポンス:\n{full_response}")
            
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
                print(f"AWS APIエラー: {error_code} - {error_message}")
                
                if error_code == 'AccessDeniedException':
                    print("\n権限エラーが発生しました。以下を確認してください:")
                    print("1. IAMユーザーに 'bedrock-agent-runtime:InvokeAgent' アクションの権限があること")
                    print("2. エージェントが正しく準備(PREPARED)されていること")
                    print("3. 指定したエージェントIDとエイリアスIDが正しいこと")
            
            except Exception as e:
                print(f"ストリーム処理エラー: {str(e)}")
        else:
            print("completionキーが見つかりません。レスポンス全体:")
            print(json.dumps(response, indent=2, default=str))
    
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
        print(f"AWS APIエラー: {error_code} - {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("\n権限エラーが発生しました。以下を確認してください:")
            print("1. IAMユーザーに 'bedrock-agent-runtime:InvokeAgent' アクションの権限があること")
            print("2. エージェントが正しく準備(PREPARED)されていること")
            print("3. 指定したエージェントIDとエイリアスIDが正しいこと")
    
    except Exception as e:
        print(f"エラー: {str(e)}")
    
    print("\nテスト完了")

if __name__ == "__main__":
    main() 