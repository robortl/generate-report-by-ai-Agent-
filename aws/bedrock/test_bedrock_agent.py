import boto3
import json
import time

def test_bedrock_agent_access():
    # Bedrockエージェントランタイムクライアントを作成
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-northeast-1')
    
    # エージェントID
    agent_id = 'LPJVAYJAK2'
    agent_alias_id = 'YK1IJ32MHH'
    
    # リクエストボディを作成
    request = {
        "inputText": "Can you help me generate a report based on document analysis?",
        "enableTrace": True
    }
    
    try:
        # エージェントを呼び出す
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=f"test-session-{int(time.time())}",
            inputText=request["inputText"],
            enableTrace=request["enableTrace"]
        )
        
        # ストリーミングレスポンスを処理
        print("エージェントからの応答:")
        full_response = ""
        
        for event in response['completion']:
            chunk = event.get('chunk')
            if chunk:
                chunk_obj = json.loads(chunk.get('bytes').decode('utf-8'))
                if 'text' in chunk_obj:
                    text = chunk_obj['text']
                    full_response += text
                    print(text, end='', flush=True)
        
        print("\n\nアクセス成功！Bedrockエージェントが正しく設定されています。")
        return True
    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    print("AWS Bedrockエージェントへのアクセスをテストしています...")
    test_bedrock_agent_access() 