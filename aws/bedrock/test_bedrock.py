import boto3
import json

def test_bedrock_access():
    # Bedrockランタイムクライアントを作成
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-1')
    
    # リクエストボディを作成（Titanモデル用）
    request_body = {
        "inputText": "Hello, can you help me with document analysis?",
        "textGenerationConfig": {
            "maxTokenCount": 1000,
            "temperature": 0.7,
            "topP": 0.9
        }
    }
    
    try:
        # モデルを呼び出す
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps(request_body)
        )
        
        # レスポンスを解析
        response_body = json.loads(response['body'].read())
        print("モデルからの応答:")
        print(response_body['results'][0]['outputText'])
        print("\nアクセス成功！BedrockFullAccessポリシーが正しく設定されています。")
        return True
    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    print("AWS Bedrockへのアクセスをテストしています...")
    test_bedrock_access() 