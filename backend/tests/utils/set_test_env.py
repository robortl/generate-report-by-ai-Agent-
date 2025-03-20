#!/usr/bin/env python
"""
设置测试环境变量
"""
import os
import sys

def set_test_env():
    """设置测试环境变量"""
    # 设置本地测试模式
    os.environ['USE_LOCAL_MOCK'] = 'true'
    
    # 设置AWS区域
    os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
    
    # 设置S3存储桶名称
    os.environ['S3_BUCKET_NAME'] = 'test-meeting-reports-bucket'
    
    # 设置DynamoDB表名称
    os.environ['DYNAMODB_TABLE'] = 'test-meeting-reports-table'
    
    # 设置Bedrock模型ID
    os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-v2'
    
    print("测试环境变量已设置:")
    print(f"USE_LOCAL_MOCK: {os.environ.get('USE_LOCAL_MOCK')}")
    print(f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION')}")
    print(f"S3_BUCKET_NAME: {os.environ.get('S3_BUCKET_NAME')}")
    print(f"DYNAMODB_TABLE: {os.environ.get('DYNAMODB_TABLE')}")
    print(f"BEDROCK_MODEL_ID: {os.environ.get('BEDROCK_MODEL_ID')}")

if __name__ == "__main__":
    set_test_env() 