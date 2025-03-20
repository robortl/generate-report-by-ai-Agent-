# AWS Bedrock デプロイガイド
# AWS Bedrock Deployment Guide

## 概要 | Overview

このガイドでは、AWS Bedrockを使用するためのセットアップ手順と、レポート生成システムとの統合方法について説明します。

This guide explains the setup procedures for using AWS Bedrock and how to integrate it with the report generation system.

## 前提条件 | Prerequisites

- AWS アカウント（Bedrockサービスへのアクセス権限付き）
- AWS CLI（設定済み）
- AWS認証情報の設定（`~/.aws/credentials`と`~/.aws/config`）
- Python 3.8以上
- 必要なPythonパッケージ（boto3, dotenv）

- AWS account (with access to Bedrock service)
- AWS CLI (configured)
- AWS credentials setup (`~/.aws/credentials` and `~/.aws/config`)
- Python 3.8 or higher
- Required Python packages (boto3, dotenv)

## AWS認証情報の設定 | AWS Credentials Setup

セキュリティのため、環境変数に直接AWS認証情報を設定するのではなく、AWS CLIプロファイルを使用します：

1. AWS CLIをインストールします（まだの場合）：
   ```bash
   pip install awscli
   ```

2. AWS認証情報を設定します：
   ```bash
   aws configure
   ```
   プロンプトに従って、AWS Access Key、Secret Key、デフォルトリージョン（ap-northeast-1）、出力形式（json）を入力します。

3. 特定のプロファイルを設定する場合：
   ```bash
   aws configure --profile myprofile
   ```

For security reasons, we use AWS CLI profiles instead of setting AWS credentials directly in environment variables:

1. Install AWS CLI (if not already installed):
   ```bash
   pip install awscli
   ```

2. Configure AWS credentials:
   ```bash
   aws configure
   ```
   Follow the prompts to enter your AWS Access Key, Secret Key, default region (ap-northeast-1), and output format (json).

3. To configure a specific profile:
   ```bash
   aws configure --profile myprofile
   ```

## 環境変数の設定 | Environment Variables Setup

1. `.env.example`ファイルを`.env`にコピーします。
2. 以下の設定を確認・変更します：

```
# AWS Credentials Configuration
# Note: For security reasons, use AWS configuration file instead of setting credentials directly in environment variables
# Make sure your AWS CLI is properly configured (~/.aws/credentials and ~/.aws/config)
AWS_REGION=ap-northeast-1
AWS_PROFILE=default

# Bedrock Configuration
# No additional configuration needed, using AWS configuration file for access
```

1. Copy the `.env.example` file to `.env`.
2. Verify and modify the following settings:

## IAMロールとポリシーの設定 | IAM Roles and Policies Setup

AWS Bedrockを使用するには、適切なIAMロールとポリシーが必要です。以下のスクリプトを使用して設定できます：

```bash
python aws/iam/create_roles.py
```

このスクリプトは以下を実行します：
- Lambda実行ロールの作成
- S3アクセスポリシーの作成と適用
- DynamoDBアクセスポリシーの作成と適用
- Bedrock呼び出しポリシーの作成と適用

To use AWS Bedrock, appropriate IAM roles and policies are required. You can set them up using the following script:

This script performs the following:
- Creates a Lambda execution role
- Creates and applies S3 access policies
- Creates and applies DynamoDB access policies
- Creates and applies Bedrock invocation policies

## Bedrockモデルのテスト | Testing Bedrock Models

利用可能なBedrockモデルをテストするには：

```bash
python aws/bedrock/test_models.py --list-models
python aws/bedrock/test_models.py --model anthropic.claude-v2 --prompt "こんにちは、今日の天気は？"
```

フレームワークを指定してテストすることも可能です：

```bash
python aws/bedrock/test_models.py --model anthropic.claude-v2 --prompt "Hello, how are you?" --framework langchain
python aws/bedrock/test_models.py --model anthropic.claude-v2 --prompt "Hello, how are you?" --framework haystack
```

To test available Bedrock models:

You can also test with specific frameworks:

## 全リソースのデプロイ | Deploying All Resources

すべてのAWSリソース（IAM、S3、DynamoDB、Lambda、Bedrock設定）を一度にデプロイするには：

```bash
python aws/deploy/deploy_all.py
```

特定のリソースをスキップする場合：

```bash
python aws/deploy/deploy_all.py --skip-iam --skip-s3
```

To deploy all AWS resources (IAM, S3, DynamoDB, Lambda, Bedrock configuration) at once:

To skip specific resources:

## トラブルシューティング | Troubleshooting

### 一般的な問題 | Common Issues

1. **アクセス権限エラー**：IAMロールとポリシーが正しく設定されていることを確認してください。
2. **リージョンの問題**：Bedrockが利用可能なリージョンを使用していることを確認してください（例：`us-east-1`、`us-west-2`など）。
3. **モデルアクセスエラー**：AWS Bedrockコンソールで特定のモデルへのアクセスをリクエストしていることを確認してください。

1. **Access permission errors**: Ensure that IAM roles and policies are correctly configured.
2. **Region issues**: Make sure you are using a region where Bedrock is available (e.g., `us-east-1`, `us-west-2`, etc.).
3. **Model access errors**: Verify that you have requested access to specific models in the AWS Bedrock console.

### ログの確認 | Checking Logs

デプロイスクリプトは詳細なログを出力します。エラーが発生した場合は、ログメッセージを確認して問題を特定してください。

The deployment scripts output detailed logs. If an error occurs, check the log messages to identify the problem.

## 参考リンク | Reference Links

- [AWS Bedrock 公式ドキュメント](https://docs.aws.amazon.com/bedrock/)
- [LangChain AWS Bedrock 統合](https://python.langchain.com/docs/integrations/llms/bedrock)
- [Haystack AWS Bedrock 統合](https://docs.haystack.deepset.ai/docs/integrations)

- [AWS Bedrock Official Documentation](https://docs.aws.amazon.com/bedrock/)
- [LangChain AWS Bedrock Integration](https://python.langchain.com/docs/integrations/llms/bedrock)
- [Haystack AWS Bedrock Integration](https://docs.haystack.deepset.ai/docs/integrations) 