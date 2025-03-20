#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Lambda Function Deployment Script
Lambda関数デプロイスクリプト
"""

import os
import sys
import argparse
import logging
import json
import shutil
import tempfile
import subprocess
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import time
import zipfile
from pathlib import Path

# Add project root directory to Python path
# プロジェクトのルートディレクトリをPythonパスに追加

# Configure logging
# ログの設定

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lambda function configuration
# Lambda関数の設定

LAMBDA_FUNCTIONS = {
    'report_generator': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.12',
        'timeout': 300,
        'memory_size': 1024,
        'description': 'Report generation function using LangChain and Haystack',
        'environment_variables': {
            'PYTHONPATH': '/var/task',
            'LOG_LEVEL': 'INFO'
        },
        'requirements': [
            'boto3',
            'langchain==0.0.267',
            'farm-haystack==1.20.0'
        ]
    },
    'keyword_extractor': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.12',
        'timeout': 60,
        'memory_size': 512,
        'description': 'Keyword extraction function using Haystack',
        'environment_variables': {
            'PYTHONPATH': '/var/task',
            'LOG_LEVEL': 'INFO'
        },
        'requirements': [
            'boto3',
            'farm-haystack==1.20.0'
        ]
    },
    'model_comparator': {
        'handler': 'lambda_function.lambda_handler',
        'runtime': 'python3.12',
        'timeout': 120,
        'memory_size': 512,
        'description': 'Model comparison function using LangChain',
        'environment_variables': {
            'PYTHONPATH': '/var/task',
            'LOG_LEVEL': 'INFO'
        },
        'requirements': [
            'boto3',
            'langchain==0.0.267'
        ]
    }
}

def load_config():
    """Load configuration"""
    # Load .env file
    # .envファイルを読み込む
    
    load_dotenv()
    
    # Get environment variables
    # 環境変数を取得
    
    config = {
        'aws_region': os.getenv('AWS_REGION', 'ap-northeast-1'),
        'aws_profile': os.getenv('AWS_PROFILE', 'default'),
        'lambda_role_arn': os.getenv('LAMBDA_ROLE_ARN', ''),
        'lambda_functions': {
            'report_generator': {
                'handler': 'lambda_function.lambda_handler',
                'runtime': 'python3.12',
                'memory_size': 1024,
                'timeout': 300,
                'environment_variables': {
                    'APP_AWS_REGION': os.getenv('AWS_REGION', 'ap-northeast-1'),
                    'S3_BUCKET_NAME': os.getenv('S3_BUCKET_NAME', 'report-langchain-haystack-files'),
                    'DYNAMODB_TABLE_PREFIX': os.getenv('DYNAMODB_TABLE_PREFIX', 'report_')
                },
                'dependencies': [
                    'boto3',
                    'langchain==0.0.267',
                    'farm-haystack==1.20.0'
                ]
            }
        }
    }
    
    return config

def create_lambda_client(config, profile=None):
    """Create Lambda client"""
    # Use provided profile or environment variable profile
    profile_to_use = profile or config['aws_profile']
    logger.info(f"Using AWS profile: {profile_to_use}")
    session = boto3.Session(profile_name=profile_to_use, region_name=config['aws_region'])
    
    lambda_client = session.client('lambda')
    
    return lambda_client

def package_lambda_function(function_name, function_config, config):
    """Package Lambda function"""
    logger.info(f"Packaging Lambda function: {function_name}")
    
    # Create temporary directory
    # 一時ディレクトリを作成
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Source code directory
        # ソースコードディレクトリ
        
        source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'functions', function_name)
        
        # Copy source code to temporary directory
        # ソースコードを一時ディレクトリにコピー
        
        for item in os.listdir(source_dir):
            source_item = os.path.join(source_dir, item)
            dest_item = os.path.join(temp_dir, item)
            
            if os.path.isdir(source_item):
                shutil.copytree(source_item, dest_item)
            else:
                shutil.copy2(source_item, dest_item)
        
        # Create requirements.txt
        # requirements.txtを作成
        
        with open(os.path.join(temp_dir, 'requirements.txt'), 'w') as f:
            # Exclude tokenizers package
            # tokenizersパッケージを除外
            
            # Add comment explaining excluded dependencies
            # 除外された依存関係の説明を追加
            
            f.write('# The following dependencies are excluded: tokenizers (requires Rust compiler)\n')
            f.write('# 以下の依存関係は除外されています：tokenizers（Rustコンパイラが必要）\n')
            
            # Install dependencies
            # 依存関係をインストール
            
            try:
                os.system(f'pip freeze > {temp_dir}/requirements.txt')
            except Exception as e:
                logger.warning(f'Failed to generate requirements.txt: {e}')
                # Try to install dependencies but ignore errors
                # 依存関係のインストールを試みるが、エラーは無視
                
                # Install basic dependencies separately
                # 基本的な依存関係を個別にインストール
                
                with open(os.path.join(temp_dir, 'requirements.txt'), 'w') as f:
                    f.write('boto3==1.26.137\n')
                    f.write('requests==2.31.0\n')
                    f.write('python-dotenv==1.0.0\n')
        
        # Create zip file
        # zipファイルを作成
        
        zip_file = os.path.join(os.path.dirname(temp_dir), f"{function_name}.zip")
        shutil.make_archive(zip_file[:-4], 'zip', temp_dir)
        
        # Read zip file content
        # zipファイルの内容を読み込む
        
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        return zip_content

def create_or_update_lambda_function(lambda_client, function_name, function_config, zip_content, config):
    """Create or update Lambda function"""
    # Set environment variables
    # 環境変数を設定
    
    env_vars = function_config['environment_variables'].copy()
    env_vars.update({
        # Remove AWS_REGION to keep environment variable
        # 環境変数を保持するためにAWS_REGIONを削除
        
        'APP_AWS_REGION': config['aws_region'],  # Use custom name
        'S3_BUCKET_NAME': config['lambda_functions']['report_generator']['environment_variables']['S3_BUCKET_NAME'],
        'DYNAMODB_FILES_TABLE': config['lambda_functions']['report_generator']['environment_variables']['DYNAMODB_TABLE_PREFIX'] + 'files',
        'DYNAMODB_REPORTS_TABLE': config['lambda_functions']['report_generator']['environment_variables']['DYNAMODB_TABLE_PREFIX'] + 'reports',
        'DYNAMODB_MODELS_TABLE': config['lambda_functions']['report_generator']['environment_variables']['DYNAMODB_TABLE_PREFIX'] + 'models'
    })
    
    # Maximum retry attempts
    # 最大リトライ回数
    
    max_retries = 3
    retry_count = 0
    retry_delay = 10  # Initial retry delay (seconds)
    # 初期リトライ遅延（秒）
    
    while retry_count < max_retries:
        try:
            # Check if function exists
            # 関数が存在するかチェック
            
            try:
                lambda_client.get_function(FunctionName=function_name)
                logger.info(f"Updating Lambda function: {function_name}")
                
                # Update function code
                # 関数コードを更新
                
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                # Wait for function update to complete
                # 関数の更新が完了するのを待つ
                
                logger.info(f"Waiting for Lambda function {function_name} code update to complete...")
                waiter = lambda_client.get_waiter('function_updated')
                waiter.wait(FunctionName=function_name)
                
                # Update function configuration
                # 関数の設定を更新
                
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime=function_config['runtime'],
                    Role=config['lambda_role_arn'],
                    Handler=function_config['handler'],
                    Description=function_config['description'],
                    Timeout=function_config['timeout'],
                    MemorySize=function_config['memory_size'],
                    Environment={
                        'Variables': env_vars
                    }
                )
                
                logger.info(f"Lambda function {function_name} updated successfully")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info(f"Creating Lambda function: {function_name}")
                    
                    # Create function
                    # 関数を作成
                    
                    lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime=function_config['runtime'],
                        Role=config['lambda_role_arn'],
                        Handler=function_config['handler'],
                        Code={'ZipFile': zip_content},
                        Description=function_config['description'],
                        Timeout=function_config['timeout'],
                        MemorySize=function_config['memory_size'],
                        Environment={
                            'Variables': env_vars
                        }
                    )
                    
                    logger.info(f"Lambda function {function_name} created successfully")
                else:
                    raise
            
            # Operation successful, break loop
            # 操作が成功したらループを抜ける
            
            break
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Lambda function {function_name} is being updated, waiting {retry_delay} seconds before retry ({retry_count}/{max_retries})...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    # 指数バックオフ
                else:
                    logger.error(f"Error creating/updating Lambda function: {e}")
                    return False
            else:
                logger.error(f"Error creating/updating Lambda function: {e}")
                return False
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Deploy Lambda functions')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--role-arn', help='Lambda execution role ARN')
    parser.add_argument('--function', help='Specific function name to deploy')
    args = parser.parse_args()
    
    # Load configuration
    # 設定を読み込む
    
    config = load_config()
    
    # Set Lambda execution role ARN
    # Lambda実行ロールARNを設定
    
    if args.role_arn:
        config['lambda_role_arn'] = args.role_arn
    
    # Create Lambda client
    # Lambdaクライアントを作成
    
    lambda_client = create_lambda_client(config, args.profile)
    
    # Check which function directories exist
    # どの関数ディレクトリが存在するかチェック
    
    available_functions = {}
    functions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'functions')
    for function_name in LAMBDA_FUNCTIONS:
        function_dir = os.path.join(functions_dir, function_name)
        if os.path.exists(function_dir):
            available_functions[function_name] = LAMBDA_FUNCTIONS[function_name]
    
    if not available_functions:
        logger.error("No Lambda function source code directories found")
        return 1
    
    logger.info(f"Found the following Lambda functions: {', '.join(available_functions.keys())}")
    
    # Deploy specific function or all functions
    # 特定の関数またはすべての関数をデプロイ
    
    if args.function:
        if args.function not in available_functions:
            logger.error(f"Function {args.function} does not exist or source code directory is missing")
            return 1
        functions_to_deploy = {args.function: available_functions[args.function]}
    else:
        functions_to_deploy = available_functions
    
    # Deploy function
    # 関数をデプロイ
    
    for function_name, function_config in functions_to_deploy.items():
        logger.info(f"Deploying function: {function_name}")
        # Package function
        # 関数をパッケージ化
        
        zip_content = package_lambda_function(function_name, function_config, config)
        
        # Create or update function
        # 関数を作成または更新
        
        if not create_or_update_lambda_function(lambda_client, function_name, function_config, zip_content, config):
            logger.error(f"Failed to deploy function {function_name}")
            return 1
    
    logger.info("Lambda function deployment completed")
    return 0

if __name__ == '__main__':
    sys.exit(main()) 