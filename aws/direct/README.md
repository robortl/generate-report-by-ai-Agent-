# 本地Docker部署（直接访问AWS服务）

本目录包含在本地部署前后端应用程序的Docker配置，同时允许应用程序直接访问AWS的S3、DynamoDB和Bedrock等服务。

## 前提条件

1. 安装Docker和Docker Compose
2. 配置AWS CLI凭证（`~/.aws/credentials`和`~/.aws/config`）
3. 确保您的AWS账户有足够的权限访问S3、DynamoDB和Bedrock服务
4. Python 3.9+

## 环境变量

在项目根目录的`.env`文件中配置以下环境变量：

```
# AWS区域
AWS_REGION=ap-northeast-1

# S3配置
S3_BUCKET_NAME=your-s3-bucket-name

# DynamoDB配置
DYNAMODB_FILES_TABLE=report_files
DYNAMODB_REPORTS_TABLE=report_reports
DYNAMODB_MODELS_TABLE=report_models
```

## 使用方法

### 启动应用程序

```bash
python start.py
```

这将启动前端和后端Docker容器，并自动从AWS配置文件或环境变量中获取AWS凭证。

启动后，可以通过以下URL访问应用程序：
- 前端：http://localhost:3000
- 后端API：http://localhost:5000/api

### 停止应用程序

```bash
python stop.py
```

这将停止并移除所有Docker容器。

## 开发环境说明

本配置使用了开发环境的Dockerfile（Dockerfile.dev），具有以下特点：

1. **前端**：
   - 使用Node.js开发服务器，支持热重载
   - 代码修改后自动刷新浏览器
   - 挂载本地目录，无需重新构建容器

2. **后端**：
   - 使用Flask开发服务器，支持调试模式
   - 代码修改后自动重启服务
   - 挂载本地目录，无需重新构建容器

## 架构说明

- **前端**：React应用程序，运行在本地Docker容器中
- **后端**：Flask应用程序，运行在本地Docker容器中
- **AWS服务**：应用程序直接访问AWS的S3、DynamoDB和Bedrock服务

## 故障排除

1. **AWS凭证问题**：确保您已正确配置AWS CLI或设置了相应的环境变量
2. **权限问题**：确保您的AWS账户有足够的权限访问所需的服务
3. **Docker问题**：检查Docker和Docker Compose是否正确安装和配置

## 注意事项

- 本地运行时会产生AWS服务使用费用
- 请确保在不使用时停止容器，以避免不必要的费用
- 建议在开发/测试环境中使用，不建议用于生产环境 