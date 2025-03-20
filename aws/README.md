# AWS Resource Management | AWSリソース管理

This directory contains scripts and configurations for managing AWS resources used in the project.
このディレクトリには、プロジェクトで使用するAWSリソースを管理するためのスクリプトと設定が含まれています。

## Directory Structure | ディレクトリ構造

```
aws/
├── README.md                 # This file | このファイル
├── s3/                       # S3 bucket management scripts | S3バケット管理スクリプト
│   ├── create_buckets.py     # Create S3 buckets | S3バケットを作成
│   └── configure_cors.py     # Configure S3 CORS policy | S3 CORSポリシーを設定
├── dynamodb/                 # DynamoDB table management scripts | DynamoDBテーブル管理スクリプト
│   ├── create_tables.py      # Create DynamoDB tables | DynamoDBテーブルを作成
│   └── seed_data.py          # Seed test data | テストデータを投入
├── lambda/                   # Lambda function management | Lambda関数管理
│   ├── functions/            # Lambda function source code | Lambda関数のソースコード
│   │   ├── report_generator/ # Report generation function | レポート生成関数
│   │   ├── file_processor/   # File processing function | ファイル処理関数
│   │   └── model_manager/    # Model management function | モデル管理関数
│   └── deploy.py             # Deployment script | デプロイスクリプト
└── iam/                      # IAM role and policy management | IAMロールとポリシー管理
    ├── create_roles.py       # Create IAM roles | IAMロールを作成
    └── create_policies.py    # Create IAM policies | IAMポリシーを作成
```

## Usage | 使用方法

1. Set up AWS credentials | AWS認証情報を設定
```bash
aws configure
```

2. Create S3 buckets | S3バケットを作成
```bash
cd s3
python create_buckets.py
python configure_cors.py
```

3. Create DynamoDB tables | DynamoDBテーブルを作成
```bash
cd dynamodb
python create_tables.py
python seed_data.py
```

4. Create IAM roles and policies | IAMロールとポリシーを作成
```bash
cd iam
python create_roles.py
python create_policies.py
```

5. Deploy Lambda functions | Lambda関数をデプロイ
```bash
cd lambda
python deploy.py
```

## Configuration | 設定

The AWS resources are configured using environment variables and configuration files.
AWSリソースは環境変数と設定ファイルを使用して設定されます。

### Environment Variables | 環境変数

- `AWS_REGION` - AWS region (default: ap-northeast-1) | AWSリージョン（デフォルト：ap-northeast-1）
- `AWS_PROFILE` - AWS profile name (default: default) | AWSプロファイル名（デフォルト：default）
- `S3_BUCKET_NAME` - S3 bucket name | S3バケット名
- `DYNAMODB_TABLE_PREFIX` - DynamoDB table name prefix | DynamoDBテーブル名のプレフィックス

### Configuration Files | 設定ファイル

- `s3/config.json` - S3 bucket configuration | S3バケット設定
- `dynamodb/config.json` - DynamoDB table configuration | DynamoDBテーブル設定
- `lambda/config.json` - Lambda function configuration | Lambda関数設定
- `iam/config.json` - IAM role and policy configuration | IAMロールとポリシー設定

## Troubleshooting | トラブルシューティング

Common issues and solutions | 一般的な問題と解決策

1. AWS Credentials | AWS認証情報
   - Ensure AWS credentials are properly configured | AWS認証情報が正しく設定されていることを確認
   - Check AWS profile permissions | AWSプロファイルの権限を確認

2. S3 Access | S3アクセス
   - Verify bucket names and regions | バケット名とリージョンを確認
   - Check CORS configuration | CORS設定を確認

3. DynamoDB Access | DynamoDBアクセス
   - Verify table names and regions | テーブル名とリージョンを確認
   - Check IAM permissions | IAM権限を確認

4. Lambda Deployment | Lambdaデプロイ
   - Check function timeout and memory settings | 関数のタイムアウトとメモリ設定を確認
   - Verify dependencies in requirements.txt | requirements.txtの依存関係を確認

## Contributing | 貢献

When adding new AWS resources or modifying existing ones, please follow these guidelines:
新しいAWSリソースを追加する場合や既存のリソースを修正する場合は、以下のガイドラインに従ってください：

1. Update configuration files | 設定ファイルを更新
2. Add appropriate IAM permissions | 適切なIAM権限を追加
3. Update documentation | ドキュメントを更新
4. Test thoroughly | 十分にテスト

## License | ライセンス

MIT 