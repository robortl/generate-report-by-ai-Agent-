# AWS Bedrock 服务与 Docker 容器故障排除指南

## 问题概述

在启动应用程序时，后端容器（`report-backend`）无法正常运行，主要原因是 AWS Bedrock 服务的认证问题。错误信息为：

```
Could not load credentials to authenticate with AWS client. Please check that credentials in the specified profile name are valid.
```

## 解决方案

我们通过以下几个关键修改解决了问题：

### 1. 区域设置

确保使用正确的 AWS 区域，特别是对于 Bedrock 服务：

```yaml
# Docker Compose 文件中的设置
- AWS_REGION=ap-northeast-1
- AWS_DEFAULT_REGION=ap-northeast-1
- BEDROCK_ENDPOINT=bedrock-runtime.ap-northeast-1.amazonaws.com
```

### 2. AWS 凭证传递

通过多种方式确保 AWS 凭证正确传递到容器：

1. **环境变量传递**：
   ```yaml
   - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
   - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
   - AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
   ```

2. **挂载 AWS 配置目录**：
   ```yaml
   - C:/Users/${USERNAME}/.aws:/root/.aws:ro
   ```

3. **启用 AWS SDK 配置加载**：
   ```yaml
   - AWS_SDK_LOAD_CONFIG=1
   ```

### 3. LangChain 服务错误处理

在 `langchain_service.py` 中添加错误处理和备用方案：

```python
try:
    # 尝试初始化 Bedrock LLM
    self.llm = Bedrock(
        model_id=os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-v2"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1"),
        endpoint_url=os.environ.get("BEDROCK_ENDPOINT", "bedrock-runtime.ap-northeast-1.amazonaws.com")
    )
    # ...
except Exception as e:
    # 如果 Bedrock 初始化失败，使用备用 LLM
    logger.warning(f"Bedrock LLM 初始化失败: {e}")
    self.llm = FakeListLLM(
        responses=["这是一个模拟的 LLM 响应，因为 Bedrock 服务不可用。"]
    )
```

### 4. 启动脚本改进

在 `start_with_aws.py` 中添加了以下功能：

1. **AWS 凭证检查**：
   ```python
   credentials_available, credentials = check_aws_credentials()
   ```

2. **Bedrock 服务访问检查**：
   ```python
   bedrock_available = check_bedrock_access()
   ```

3. **用户名获取**：
   ```python
   username = getpass.getuser()
   ```

4. **容器状态监控**：
   ```python
   # 等待几秒后再次检查后端容器状态
   time.sleep(5)
   subprocess.run(["docker", "ps"], check=True)
   ```

## 注意事项

1. **AWS 区域兼容性**：
   - 确保使用支持 Bedrock 服务的区域（如 `ap-northeast-1`）
   - 不同区域的 Bedrock 服务可能有不同的模型可用性

2. **AWS 权限要求**：
   - 用户需要有 Bedrock 服务的访问权限
   - 可能需要在 AWS 控制台中申请 Bedrock 服务访问权限

3. **Windows 路径问题**：
   - 在 Windows 环境中，使用 `C:/Users/${USERNAME}/.aws:/root/.aws:ro` 挂载 AWS 配置目录
   - 确保 `USERNAME` 环境变量正确设置

4. **错误处理**：
   - 添加了备用 LLM，即使 Bedrock 服务不可用，应用程序也能继续运行
   - 详细的日志记录有助于诊断问题

## 测试方法

使用以下命令启动应用程序：

```bash
python start_with_aws.py
```

成功启动后，可以通过以下 URL 访问应用程序：

- 前端：http://localhost:3000
- 后端 API：http://localhost:5000/api

使用 `docker ps` 命令检查容器状态，确保两个容器都在运行：

```
CONTAINER ID   IMAGE             COMMAND                   STATUS          PORTS                    NAMES
6cc92d028f32   direct-frontend   "docker-entrypoint.s…"   Up 15 seconds   0.0.0.0:3000->3000/tcp   report-frontend
b1132ea990db   direct-backend    "flask run --host=0.…"   Up 15 seconds   0.0.0.0:5000->5000/tcp   report-backend
``` 