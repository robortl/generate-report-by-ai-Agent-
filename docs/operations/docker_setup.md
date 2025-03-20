# Docker Setup Guide
# Dockerセットアップガイド
# Docker设置指南

This document provides detailed instructions for running the application using Docker.

## Prerequisites
## 前提条件
## 前置条件

- Install [Docker](https://www.docker.com/get-started)
- Install [Docker Compose](https://docs.docker.com/compose/install/)
- Valid AWS credentials configuration

## AWS Credentials Configuration
## AWS認証情報の設定
## AWS凭证配置

The application needs to access AWS services (such as S3, DynamoDB, and Bedrock). Make sure you have configured AWS credentials.

### Method 1: Using AWS CLI
### 方法1：AWS CLIを使用する
### 方法1：使用AWS CLI

If you have AWS CLI installed, you can run the following command to configure credentials:

```bash
aws configure
```

You will be prompted to enter your AWS Access Key ID, Secret Access Key, default region, and output format.

### Method 2: Manually Creating Credential Files
### 方法2：認証情報ファイルを手動で作成する
### 方法2：手动创建凭证文件

1. Create an `.aws` folder in your home directory
2. Create a `credentials` file in that folder with the following content:

```
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

3. Create a `config` file in that folder with the following content:

```
[default]
region = ap-northeast-1
output = json
```

## Running the Application with Docker Compose
## Docker Composeでアプリケーションを実行する
## 使用Docker Compose运行应用

1. Make sure you are in the project root directory
2. Run the following command to build and start the containers:

```bash
docker-compose up -d
```

3. The application will be available at:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000

## Viewing Logs
## ログの表示
## 查看日志

You can use the following commands to view container logs:

```bash
# View backend logs
docker logs report-backend

# View frontend logs
docker logs report-frontend
```

## Stopping the Application
## アプリケーションの停止
## 停止应用

To stop the application, run:

```bash
docker-compose down
```

## Troubleshooting
## トラブルシューティング
## 故障排除

### AWS Credential Issues
### AWS認証情報の問題
### AWS凭证问题

If you encounter AWS credential-related errors, check:

1. Ensure your AWS credentials are valid and have the necessary permissions
2. Ensure the credential file format is correct
3. Check container logs for detailed error information

### Port Conflicts
### ポートの競合
### 端口冲突

If ports are already in use, you can modify the port mappings in the `docker-compose.yml` file. 