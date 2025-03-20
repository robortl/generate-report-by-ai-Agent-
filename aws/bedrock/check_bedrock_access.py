import boto3
import logging
import json

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_bedrock_access():
    """AWS Bedrockサービスへのアクセスを確認する"""
    try:
        # Bedrockクライアントの作成
        bedrock_client = boto3.client('bedrock')
        logger.info("Bedrockクライアントを作成しました")
        
        # 利用可能なモデルのリストを取得
        response = bedrock_client.list_foundation_models()
        logger.info("Bedrockモデルリストを取得しました")
        
        # モデル情報を表示
        for model in response.get('modelSummaries', []):
            logger.info(f"モデルID: {model.get('modelId')}, 名前: {model.get('modelName')}")
        
        # Bedrock Agentクライアントの作成
        bedrock_agent_client = boto3.client('bedrock-agent')
        logger.info("Bedrock Agentクライアントを作成しました")
        
        # エージェントのリストを取得
        response = bedrock_agent_client.list_agents()
        logger.info("Bedrock Agentリストを取得しました")
        
        # エージェント情報を表示
        for agent in response.get('agentSummaries', []):
            logger.info(f"エージェントID: {agent.get('agentId')}, 名前: {agent.get('agentName')}")
        
        # Bedrock Agent Runtimeクライアントの作成
        bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')
        logger.info("Bedrock Agent Runtimeクライアントを作成しました")
        
        logger.info("AWS Bedrockサービスへのアクセスが確認できました")
        return True
    except Exception as e:
        logger.error(f"AWS Bedrockサービスへのアクセスエラー: {e}")
        return False

if __name__ == "__main__":
    check_bedrock_access() 