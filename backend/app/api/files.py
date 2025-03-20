from flask import Blueprint, request, jsonify, current_app
import traceback
from app.services.storage import list_files_from_dynamodb, get_metadata_from_dynamodb

# 创建蓝图
files_bp = Blueprint('files', __name__, url_prefix='/api/files')

@files_bp.route('', methods=['GET'])
def get_files():
    """获取文件列表或单个文件的元数据"""
    try:
        # 获取查询参数
        file_id = request.args.get('file_id')
        
        # 如果提供了file_id，则获取单个文件的元数据
        if file_id:
            current_app.logger.info(f"Fetching file metadata for file_id: {file_id}")
            
            try:
                # 添加详细日志
                current_app.logger.info(f"Calling get_metadata_from_dynamodb with file_id: {file_id}")
                file_metadata = get_metadata_from_dynamodb(file_id)
                current_app.logger.info(f"Result from get_metadata_from_dynamodb: {file_metadata}")
                
                if not file_metadata:
                    current_app.logger.error(f"File not found: {file_id}")
                    return jsonify({'error': 'File not found'}), 404
                
                current_app.logger.info(f"File metadata fetched: {file_metadata}")
                # 返回文件列表格式，保持API一致性
                return jsonify({'items': [file_metadata]})
            except Exception as e:
                current_app.logger.error(f"Error getting file metadata from DynamoDB: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                return jsonify({'error': f'Failed to fetch file metadata: {str(e)}'}), 500
        
        # 否则获取文件列表
        current_app.logger.info("Fetching files list")

        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        last_key = request.args.get('last_key')

        current_app.logger.info(f"Query params: category={category}, limit={limit}, last_key={last_key}")

        try:
            # 从DynamoDB获取文件列表
            result = list_files_from_dynamodb(category=category, limit=limit, last_evaluated_key=last_key)
            
            # 格式化结果
            formatted_result = {
                'items': result.get('Items', []),
                'last_evaluated_key': result.get('LastEvaluatedKey')
            }
            current_app.logger.info(f"Files fetched: {len(formatted_result['items'])} items")
            return jsonify(formatted_result)
        except Exception as e:
            current_app.logger.error(f"Error listing files from DynamoDB: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({'error': f'Failed to fetch files list: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in get_files: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to fetch files: {str(e)}'}), 500

@files_bp.route('/<file_id>', methods=['GET'])
def get_file(file_id):
    """获取单个文件的元数据"""
    try:
        current_app.logger.info(f"Fetching file metadata for file_id: {file_id}")

        # 添加详细日志
        current_app.logger.info(f"Calling get_metadata_from_dynamodb with file_id: {file_id}")
        file_metadata = get_metadata_from_dynamodb(file_id)
        current_app.logger.info(f"Result from get_metadata_from_dynamodb: {file_metadata}")
        
        if not file_metadata:
            current_app.logger.error(f"File not found: {file_id}")
            return jsonify({'error': 'File not found'}), 404
        
        current_app.logger.info(f"File metadata fetched: {file_metadata}")
        return jsonify(file_metadata)
    except Exception as e:
        current_app.logger.error(f"Error getting file metadata from DynamoDB: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to fetch file metadata: {str(e)}'}), 500 