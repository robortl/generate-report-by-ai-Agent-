# Meeting Report Generation System

Automated meeting report generation system utilizing AWS Bedrock, Haystack, and LangChain

*[English](#overview) | [日本語](#概要)*

## Overview

This project is a system that analyzes meeting records and business documents with AI to automatically generate editable reports. It is built using AWS Bedrock's powerful AI models and the Haystack/LangChain frameworks.

Key features:
- Upload and management of meeting records and business documents
- Automatic report generation using AI
- Editing and modification of generated reports
- Comparison of multiple AI models
- Prompt adjustment functionality

## Technology Stack

- **Frontend**: React/Vue.js
- **Backend**: Python/Flask
- **AI Processing**: Haystack/LangChain
- **Cloud Services**: AWS (S3, DynamoDB, Bedrock)
- **Containerization**: Docker

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed
- AWS account with appropriate permissions
- AWS CLI configured

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/meeting-report-generator.git
cd meeting-report-generator
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit the .env file to set AWS credentials and other settings
```

3. Build and start Docker containers:
```bash
docker-compose up -d
```

4. Access the application:
Open your browser and navigate to `http://localhost:3000`

## Documentation

Detailed documentation can be found in the `docs` directory:

- [Requirements Document](docs/requirements.md)
- [System Architecture](docs/system_architecture.md)
- [Development Roadmap](docs/development_roadmap.md)

## Starting the Application

The project provides unified start and stop scripts:

### Start the Application

```bash
# Start the application
python start.py
```

This script will:
1. Check if AWS credentials are available
2. Check Bedrock service access permissions
3. Create necessary environment variable files
4. Start Docker containers, connecting to real AWS services

### Stop the Application

```bash
# Stop the application
python stop.py
```

This script will:
1. Stop all Docker containers
2. Check if any containers are still running, force stop if necessary
3. Clean up environment variable files

### Environment Variables

The application uses the following environment variables:

- `AWS_REGION` - AWS region, default is ap-northeast-1
- `S3_BUCKET_NAME` - S3 bucket name, default is report-langchain-haystack-files
- `DYNAMODB_FILES_TABLE` - DynamoDB files table name, default is report_files
- `DYNAMODB_REPORTS_TABLE` - DynamoDB reports table name, default is report_reports
- `DYNAMODB_MODELS_TABLE` - DynamoDB models table name, default is report_models

## License

MIT

---

# 会議レポート生成システム

AWS Bedrock、Haystack、LangChainを活用した会議記録の自動レポート生成システム

## 概要

このプロジェクトは、会議記録や業務文書をAIで分析し、編集可能なレポートを自動生成するシステムです。AWS Bedrockの強力なAIモデルを活用し、Haystack/LangChainフレームワークを用いて構築されています。

主な機能：
- 会議記録や業務文書のアップロードと管理
- AIによるレポート自動生成
- 生成されたレポートの編集・修正
- 複数AIモデルの比較
- プロンプト調整機能

## 技術スタック

- **フロントエンド**: React/Vue.js
- **バックエンド**: Python/Flask
- **AI処理**: Haystack/LangChain
- **クラウドサービス**: AWS (S3, DynamoDB, Bedrock)
- **コンテナ化**: Docker

## セットアップ手順

### 前提条件
- Docker と Docker Compose がインストールされていること
- AWS アカウントと適切な権限
- AWS CLI の設定

### 開発環境のセットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/yourusername/meeting-report-generator.git
cd meeting-report-generator
```

2. 環境変数の設定:
```bash
cp .env.example .env
# .envファイルを編集してAWS認証情報などを設定
```

3. Dockerコンテナのビルドと起動:
```bash
docker-compose up -d
```

4. アプリケーションへのアクセス:
ブラウザで `http://localhost:3000` にアクセス

## ドキュメント

詳細なドキュメントは `docs` ディレクトリにあります:

- [要件定義書](docs/requirements.md)
- [システムアーキテクチャ](docs/system_architecture.md)
- [開発ロードマップ](docs/development_roadmap.md)

## アプリケーションの起動

プロジェクトは統一された起動・停止スクリプトを提供しています：

### アプリケーションの起動

```bash
# アプリケーションを起動
python start.py
```

このスクリプトは以下を実行します：
1. AWS認証情報が利用可能かチェック
2. Bedrockサービスへのアクセス権限を確認
3. 必要な環境変数ファイルを作成
4. Dockerコンテナを起動し、実際のAWSサービスに接続

### アプリケーションの停止

```bash
# アプリケーションを停止
python stop.py
```

このスクリプトは以下を実行します：
1. すべてのDockerコンテナを停止
2. コンテナが依然稼働中の場合、強制的に停止
3. 環境変数ファイルをクリーンアップ

### 環境変数

アプリケーションは以下の環境変数を使用します：

- `AWS_REGION` - AWSリージョン、デフォルトはap-northeast-1
- `S3_BUCKET_NAME` - S3バケット名、デフォルトはreport-langchain-haystack-files
- `DYNAMODB_FILES_TABLE` - DynamoDBファイルテーブル名、デフォルトはreport_files
- `DYNAMODB_REPORTS_TABLE` - DynamoDBレポートテーブル名、デフォルトはreport_reports
- `DYNAMODB_MODELS_TABLE` - DynamoDBモデルテーブル名、デフォルトはreport_models

## ライセンス

MIT

## ローカル環境での展開方法

### Docker を使用したローカル展開

1. `aws/direct` ディレクトリに移動:
```bash
cd aws/direct
```

2. Docker イメージのビルドと起動:
```bash
docker-compose -f docker-compose.local.yml up --build
```

3. アプリケーションへのアクセス:
- フロントエンド: http://localhost:3000
- バックエンド API: http://localhost:5000

### バックエンドアーキテクチャの特徴

#### LangChain フレームワークの活用
- 複数のAIモデルを統一的なインターフェースで操作
- プロンプトチェーンの柔軟な構築と管理
- 文書処理パイプラインの最適化

#### モデル比較機能
- 複数のAIモデルの性能を同時に評価
- レポート生成結果の質的比較
- コスト効率の分析と最適なモデルの選択

#### AWS Agent による高度なAI処理
- AWS Bedrock の強力なAIモデルを活用
- インテリジェントなエージェントによる文書理解
- コンテキストを考慮した高品質なレポート生成

#### 主な機能
1. **インテリジェントな文書解析**
   - 会議の文脈を理解
   - 重要なポイントの自動抽出
   - 構造化されたレポートの生成

2. **カスタマイズ可能なレポート生成**
   - テンプレートベースの出力形式
   - 多言語対応（日本語・英語）
   - ユーザー指定の重点項目への対応

3. **高度な比較分析**
   - 複数モデルの同時実行
   - 結果の質的評価
   - パフォーマンス分析