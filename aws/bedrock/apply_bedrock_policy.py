import boto3
import json
import os
import logging
import argparse
from botocore.exceptions import ClientError

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_policy(iam_client, policy_name, policy_document_path):
    """IAMポリシーを作成する"""
    try:
        with open(policy_document_path, 'r') as file:
            policy_document = file.read()
        
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy_document
        )
        policy_arn = response['Policy']['Arn']
        logger.info(f"ポリシー {policy_name} を作成しました。ARN: {policy_arn}")
        return policy_arn
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            logger.warning(f"ポリシー {policy_name} は既に存在します。")
            # 既存のポリシーのARNを取得
            response = iam_client.list_policies(
                Scope='Local',
                PathPrefix='/'
            )
            for policy in response['Policies']:
                if policy['PolicyName'] == policy_name:
                    logger.info(f"既存のポリシー {policy_name} のARN: {policy['Arn']}")
                    return policy['Arn']
        else:
            logger.error(f"ポリシー作成エラー: {e}")
            raise

def attach_policy_to_user(iam_client, user_name, policy_arn):
    """ユーザーにポリシーをアタッチする"""
    try:
        iam_client.attach_user_policy(
            UserName=user_name,
            PolicyArn=policy_arn
        )
        logger.info(f"ポリシー {policy_arn} をユーザー {user_name} にアタッチしました。")
    except ClientError as e:
        logger.error(f"ポリシーアタッチエラー: {e}")
        raise

def get_current_user(sts_client):
    """現在のIAMユーザー名を取得する"""
    try:
        response = sts_client.get_caller_identity()
        arn = response['Arn']
        # ARNからユーザー名を抽出
        user_name = arn.split('/')[-1]
        logger.info(f"現在のユーザー: {user_name}")
        return user_name
    except ClientError as e:
        logger.error(f"ユーザー情報取得エラー: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Bedrock Agent用のIAMポリシーを作成して適用します。')
    parser.add_argument('--policy-name', default='BedrockAgentPolicy', help='作成するポリシーの名前')
    parser.add_argument('--policy-file', default='bedrock_agent_policy.json', help='ポリシードキュメントのファイルパス')
    args = parser.parse_args()

    # AWSクライアントの作成
    iam_client = boto3.client('iam')
    sts_client = boto3.client('sts')

    # 現在のユーザー名を取得
    user_name = get_current_user(sts_client)

    # ポリシーファイルのパスを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    policy_file_path = os.path.join(current_dir, args.policy_file)

    # ポリシーを作成
    policy_arn = create_policy(iam_client, args.policy_name, policy_file_path)

    # ユーザーにポリシーをアタッチ
    attach_policy_to_user(iam_client, user_name, policy_arn)

    logger.info("ポリシーの適用が完了しました。")

if __name__ == "__main__":
    main() 