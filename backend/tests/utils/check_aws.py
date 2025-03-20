#!/usr/bin/env python
"""
检查AWS凭证是否有效
"""
import boto3
import botocore.exceptions

def check_aws_credentials():
    """检查AWS凭证是否有效"""
    try:
        # 尝试获取当前身份
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print("AWS凭证有效!")
        print(f"账户ID: {identity['Account']}")
        print(f"用户ARN: {identity['Arn']}")
        print(f"用户ID: {identity['UserId']}")
        
        # 检查是否有Bedrock权限
        try:
            bedrock = boto3.client('bedrock-runtime')
            print("\nBedrock服务可用!")
        except botocore.exceptions.ClientError as e:
            print(f"\nBedrock服务不可用: {e}")
        
        return True
    except botocore.exceptions.NoCredentialsError:
        print("错误: 未找到AWS凭证")
        print("请确保已配置AWS凭证，可以通过以下方式之一配置:")
        print("1. 设置环境变量: AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY")
        print("2. 在~/.aws/credentials文件中配置凭证")
        print("3. 使用AWS IAM角色")
        return False
    except botocore.exceptions.ClientError as e:
        print(f"错误: AWS凭证无效或权限不足: {e}")
        return False

if __name__ == "__main__":
    print("检查AWS凭证...")
    check_aws_credentials() 