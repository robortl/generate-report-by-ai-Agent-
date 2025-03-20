import os
import boto3
import json
import time
import logging
from typing import List, Dict, Any
from botocore.exceptions import ClientError
from app.services.storage import get_file_content_by_id
from app.services.report_generator import generate_report

# Configure logger
# ロガーを構成
logger = logging.getLogger(__name__)

# Authorization cache TTL (seconds)
# 認証キャッシュの有効期間（秒）
AUTHORIZATION_CACHE_TTL = 3600  # 1 hour

# Store authorization check results and timestamps
# 認証チェックの結果とタイムスタンプを保存
_authorized_models_cache = {}


def get_available_models() -> List[Dict[str, Any]]:
    """Get list of available models supported by AWS Bedrock, only return authorized models
    
    AWS Bedrockでサポートされている利用可能なモデルのリストを取得し、認証済みのモデルのみを返す
    """
    try:
        # Create Bedrock client
        # Bedrockクライアントを作成
        bedrock = boto3.client(
            'bedrock',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
        )

        # Create Bedrock Runtime client
        # Bedrock Runtimeクライアントを作成
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
        )

        logger.info("Getting AWS Bedrock model list")
        # Get list of models
        # モデルリストを取得
        response = bedrock.list_foundation_models()

        # Process response
        # レスポンスを処理
        models = []
        total_models = len(response.get('modelSummaries', []))
        logger.info(f"Found {total_models} AWS Bedrock models")

        for model in response.get('modelSummaries', []):
            model_id = model.get('modelId')

            # First check permissions using GetInvokeModelPermissions API
            # まずGetInvokeModelPermissions APIを使用して権限をチェック
            is_authorized = False
            try:
                is_authorized = check_model_permission_with_cache(bedrock_runtime, model_id)
            except Exception as e:
                logger.warning(f"Failed to check model {model_id} permission using primary method: {str(e)}, trying fallback")
                # If primary method fails, try fallback method
                # 主要な方法が失敗した場合、フォールバック方法を試す
                is_authorized = check_model_authorization_fallback(bedrock, model_id)

            # Only add authorized models
            # 認証されたモデルのみを追加
            if not is_authorized:
                logger.info(f"Model {model_id} is not authorized, skipping")
                continue

            logger.info(f"Model {model_id} is authorized, getting details")

            # Check if model supports tool use
            # モデルがツール使用をサポートしているかチェック
            is_tool_supported = False
            try:
                # Get details to check for tool support
                # ツールサポートをチェックするために詳細を取得
                model_details = bedrock.get_foundation_model(modelIdentifier=model_id)
                capabilities = model_details.get('modelDetails', {}).get('inferenceTypesSupported', [])
                properties = model_details.get('modelDetails', {}).get('modelProperties', {})

                # Check for tool support
                # ツールサポートをチェック
                if 'ON_DEMAND' in capabilities and properties.get('toolsSupported', False):
                    is_tool_supported = True
                    logger.info(f"Model {model_id} supports tools")
            except Exception as e:
                logger.warning(f"Error getting model {model_id} details: {str(e)}")

            # Build model info
            # モデル情報を構築
            model_info = {
                "id": model_id,
                "name": model.get('modelName', 'Unknown Model'),
                "provider": model.get('providerName', 'Unknown Provider'),
                "description": model.get('modelDescription', ''),
                "supports_tools": is_tool_supported
            }

            models.append(model_info)

        # If no authorized models, use preset list
        # 認証されたモデルがない場合、プリセットリストを使用
        if not models:
            logger.warning("No authorized models found, returning default model list")
            return get_default_models()

        logger.info(f"Successfully retrieved {len(models)} authorized models")
        return models

    except Exception as e:
        # If API call fails, return predefined list
        # API呼び出しが失敗した場合、事前定義されたリストを返す
        logger.error(f"Error getting models from AWS Bedrock: {str(e)}")
        return get_default_models()


def check_model_permission_with_cache(bedrock_runtime, model_id):
    """Check if there is permission to use a specific model using cache
    
    キャッシュを使用して特定のモデルを使用する権限があるかチェック
    """
    global _authorized_models_cache
    current_time = time.time()

    # Check if this model's authorization info is in cache and within validity period
    # このモデルの認証情報がキャッシュにあり、有効期間内かチェック
    if model_id in _authorized_models_cache:
        cached_time, is_authorized = _authorized_models_cache[model_id]
        if current_time - cached_time < AUTHORIZATION_CACHE_TTL:
            return is_authorized

    # Not in cache or expired, check again
    # キャッシュにないか期限切れの場合、再度チェック
    is_authorized = check_model_permission(bedrock_runtime, model_id)

    # Update cache
    # キャッシュを更新
    _authorized_models_cache[model_id] = (current_time, is_authorized)

    return is_authorized


def check_model_permission(bedrock_runtime, model_id):
    """Check if there is permission to use a specific model using GetInvokeModelPermissions API

    Reference: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_GetInvokeModelPermissions.html
    
    GetInvokeModelPermissions APIを使用して特定のモデルを使用する権限があるかチェック
    """
    try:
        # Check permissions using GetInvokeModelPermissions API
        # GetInvokeModelPermissions APIを使用して権限をチェック
        response = bedrock_runtime.get_invoke_model_permissions(
            modelId=model_id
        )

        # Check permissions
        # 権限をチェック
        permissions = response.get('permissions', [])

        # If the permissions list includes "bedrock:InvokeModel", there is permission
        # パーミッションリストに "bedrock:InvokeModel" が含まれている場合、権限がある
        has_permission = "bedrock:InvokeModel" in permissions

        logger.info(f"Model {model_id} permission check result: {has_permission}")
        return has_permission

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', '')

        if error_code == 'AccessDeniedException':
            logger.info(f"Model {model_id} access denied: {error_message}")
            return False
        elif error_code == 'ValidationException':
            logger.info(f"Model {model_id} validation error: {error_message}")
            return False
        else:
            logger.warning(f"Error checking model {model_id} permission: {error_code} - {error_message}")
            raise e


def check_model_authorization_fallback(bedrock, model_id):
    """Fallback method used when primary method fails to check model authorization

    Attempts to get model details, if successful, assumes user has permission to use that model
    
    モデル認証をチェックする際に主要な方法が失敗した場合に使用するフォールバック方法
    
    モデルの詳細を取得しようとし、成功した場合はユーザーがそのモデルを使用する権限があると仮定
    """
    try:
        # Try to get model details
        # モデルの詳細を取得してみる
        bedrock.get_foundation_model(
            modelIdentifier=model_id
        )

        # If no exception, assume there is permission
        # 例外がなければ、権限があると仮定
        logger.info(f"Confirmed model {model_id} may have permission using fallback method")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')

        if error_code == 'AccessDeniedException':
            logger.info(f"Fallback method confirmed model {model_id} has no permission")
            return False
        else:
            # For other errors, conservatively return no permission
            # 他のエラーの場合、保守的に権限なしを返す
            logger.warning(f"Error checking model {model_id} permission using fallback method: {str(e)}")
            return False


def get_default_models() -> List[Dict[str, Any]]:
    """Return preset model list as fallback
    
    フォールバックとしてプリセットモデルリストを返す
    """
    models = [
        {
            "id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "name": "Claude 3 Sonnet",
            "provider": "Anthropic",
            "description": "Anthropic's Claude 3 Sonnet model, balancing performance and speed.",
            "supports_tools": True
        },
        {
            "id": "anthropic.claude-3-haiku-20240307-v1:0",
            "name": "Claude 3 Haiku",
            "provider": "Anthropic",
            "description": "Anthropic's Claude 3 Haiku model, faster and lower cost.",
            "supports_tools": True
        },
        {
            "id": "anthropic.claude-3-opus-20240229-v1:0",
            "name": "Claude 3 Opus",
            "provider": "Anthropic",
            "description": "Anthropic's Claude 3 Opus model, offering highest performance and intelligence capabilities.",
            "supports_tools": True
        },
        {
            "id": "meta.llama3-70b-instruct-v1:0",
            "name": "Llama 3 70B",
            "provider": "Meta",
            "description": "Meta's Llama 3 70B large language model with powerful text understanding and generation capabilities.",
            "supports_tools": False
        },
        {
            "id": "amazon.titan-text-express-v1",
            "name": "Titan Text Express",
            "provider": "Amazon",
            "description": "Amazon's Titan Text Express model, providing efficient text generation capabilities.",
            "supports_tools": False
        }
    ]

    return models


def get_model_by_id(model_id: str) -> Dict[str, Any]:
    """Get model information by ID
    
    IDによってモデル情報を取得する
    """
    models = get_available_models()
    for model in models:
        if model["id"] == model_id:
            return model

    # If not found, try to get from preset model list
    # 見つからない場合、プリセットモデルリストから取得を試みる
    default_models = get_default_models()
    for model in default_models:
        if model["id"] == model_id:
            return model

    return None


def compare_models(file_id: str, model_ids: List[str], prompt: str = None) -> Dict[str, Any]:
    """Compare output results of multiple models, ensuring to use provided model IDs
    
    複数のモデルの出力結果を比較し、提供されたモデルIDを使用することを確保
    """
    try:
        # Get file content
        # ファイル内容を取得
        content = get_file_content_by_id(file_id)
        
        if not content:
            logger.error(f"Unable to get file content, file ID: {file_id}")
            raise Exception(f"Unable to get file content, file ID: {file_id}")
            
        logger.info(f"Successfully got file content, file ID: {file_id}, content length: {len(content)}")
        
        # Store results for each model
        # 各モデルの結果を保存
        results = {}
        comparisons = []
        
        logger.info(f"Starting to compare the following models: {model_ids}")
        
        # Generate report for each model
        # 各モデルのレポートを生成
        for model_id in model_ids:
            # Get model information
            # モデル情報を取得
            model_info = get_model_by_id(model_id)
            if not model_info:
                error_msg = f"Could not find model with ID {model_id}"
                logger.error(error_msg)
                results[model_id] = {
                    "error": error_msg
                }
                comparisons.append({
                    "model_id": model_id,
                    "model_name": "Unknown Model",
                    "error": error_msg,
                    "content": ""
                })
                continue
                
            logger.info(f"Generating report for model {model_id}")
            
            # Generate report, considering if model supports tools
            # モデルがツールをサポートしているかを考慮し、レポートを生成
            try:
                supports_tools = model_info.get("supports_tools", False)
                
                # Check prompt, if it doesn't include file-related prompting, add prompt to use file content
                # プロンプトをチェックし、ファイル関連のプロンプトが含まれていない場合、ファイル内容を使用するようプロンプトを追加
                prompt_to_use = prompt
                if prompt and "file" not in prompt.lower() and "content" not in prompt.lower() and "record" not in prompt.lower() and "report" not in prompt.lower():
                    # If prompt doesn't look like it's asking to process file content, add prompting
                    # プロンプトがファイル内容の処理を要求しているように見えない場合、プロンプトを追加
                    prompt_to_use = f"{prompt}\n\nPlease generate an analysis report based on the uploaded file content."
                    logger.info(f"Added explicit instruction to use file content in prompt: {prompt_to_use}")
                    
                # Ensure to directly pass model ID, not using default value
                # モデルIDを直接渡し、デフォルト値を使用しないようにする
                from app.services.report_generator import generate_report as gen_report
                report = gen_report(
                    content, 
                    prompt_to_use, 
                    model_id=model_id,  # Explicitly specify model ID
                    use_tools=supports_tools
                )
                
                logger.info(f"Report generation for model {model_id} successful")
                
                results[model_id] = {
                    "model_info": model_info,
                    "report": report
                }
                
                comparisons.append({
                    "model_id": model_id,
                    "model_name": model_info.get("name", "Unknown"),
                    "content": report,
                    "supports_tools": supports_tools
                })
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error generating report using model {model_id}: {error_msg}")
                results[model_id] = {
                    "model_info": model_info,
                    "error": error_msg
                }
                comparisons.append({
                    "model_id": model_id,
                    "model_name": model_info.get("name", "Unknown"),
                    "error": error_msg,
                    "content": ""
                })
        
        # Analyze comparison results
        # 比較結果を分析
        analysis = f"Completed comparison of {len(model_ids)} models. Please review the application effect and characteristics of each model."
        
        return {
            "file_id": file_id,
            "prompt": prompt,
            "model_ids": model_ids,  # Add list of used model IDs for tracking
            "results": results,
            "comparisons": comparisons,
            "analysis": analysis
        }
        
    except Exception as e:
        error_msg = f"Error comparing models: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def get_bedrock_models_from_aws() -> List[Dict[str, Any]]:
    """Get list of models supported by Bedrock from AWS
    
    AWSからBedrockでサポートされているモデルのリストを取得
    """
    try:
        # Create Bedrock client
        # Bedrockクライアントを作成
        bedrock = boto3.client(
            'bedrock',
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        )

        # Get model list
        # モデルリストを取得
        response = bedrock.list_foundation_models()

        # Process response
        # レスポンスを処理
        models = []
        for model in response.get('modelSummaries', []):
            models.append({
                "id": model.get('modelId'),
                "name": model.get('modelName'),
                "provider": model.get('providerName'),
                "description": model.get('modelDescription', '')
            })

        return models

    except Exception as e:
        # If API call fails, return predefined list
        # API呼び出しが失敗した場合、事前定義されたリストを返す
        print(f"Error getting models from AWS: {str(e)}")
        return get_available_models()