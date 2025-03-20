#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from app import create_app

# 设置环境变量
os.environ['USE_LOCAL_MOCK'] = 'false'  # 确保不使用模拟数据
os.environ['DYNAMODB_TABLE'] = 'report'  # 设置DynamoDB表前缀
os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'  # 设置AWS区域

# 打印环境变量
print(f"环境变量设置:")
print(f"USE_LOCAL_MOCK: {os.environ.get('USE_LOCAL_MOCK')}")
print(f"DYNAMODB_TABLE: {os.environ.get('DYNAMODB_TABLE')}")
print(f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION')}")

# 创建应用
app = create_app()

if __name__ == '__main__':
    # 启动应用
    app.run(debug=True) 