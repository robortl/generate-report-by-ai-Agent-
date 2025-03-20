from flask import Blueprint, request, jsonify, current_app
from app.services.model_service import get_available_models, compare_models
from app.services.haystack_service import haystack_service

# ブループリントを作成
model_bp = Blueprint('model', __name__, url_prefix='/api/model')

@model_bp.route('/list', methods=['GET'])
def list_models():
    """利用可能なモデルリストを取得"""
    try:
        models = get_available_models()
        # Ensure models is a list
        if not isinstance(models, list):
            current_app.logger.error("Invalid models data format")
            return jsonify({'error': 'Invalid models data format'}), 500
            
        # Ensure each model has required fields
        for model in models:
            if not all(key in model for key in ['id', 'name', 'provider']):
                current_app.logger.error("Invalid model data structure")
                return jsonify({'error': 'Invalid model data structure'}), 500
                
        return jsonify(models), 200
    except Exception as e:
        current_app.logger.error(f"Error listing models: {str(e)}")
        return jsonify({'error': 'Failed to list models'}), 500

@model_bp.route('/compare', methods=['POST'])
def compare_model_outputs():
    """複数のモデルの出力結果を比較"""
    data = request.json
    
    if not data or 'file_id' not in data or 'model_ids' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    file_id = data['file_id']
    model_ids = data['model_ids']
    prompt = data.get('prompt', None)
    
    if not isinstance(model_ids, list) or len(model_ids) < 2:
        return jsonify({'error': 'At least two model IDs are required for comparison'}), 400
    
    try:
        # 比較結果を取得
        results = compare_models(file_id, model_ids, prompt)
        return jsonify(results), 200
    except Exception as e:
        current_app.logger.error(f"Error comparing models: {str(e)}")
        return jsonify({'error': 'Failed to compare models'}), 500

@model_bp.route('/semantic/keywords', methods=['POST'])
def extract_document_keywords():
    """Haystackを使用して文書からキーワードを抽出"""
    data = request.json
    
    if not data or ('file_id' not in data and 'text' not in data):
        return jsonify({'error': 'Missing file_id or text'}), 400
    
    try:
        if 'file_id' in data:
            # ファイルIDから内容を取得
            from app.services.storage import get_file_content_by_id
            file_id = data['file_id']
            content = get_file_content_by_id(file_id)
        else:
            # 直接提供されたテキストを使用
            content = data['text']
        
        # オプションパラメータを設定
        top_n = data.get('top_n', 10)  # デフォルトで上位10個のキーワードを抽出
        
        # Haystackを使用してキーワードを抽出
        keywords = haystack_service.extract_keywords(content, top_n=top_n)
        
        return jsonify({
            'keywords': keywords
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error extracting keywords: {str(e)}")
        return jsonify({'error': 'Failed to extract keywords'}), 500

@model_bp.route('/semantic/structure', methods=['POST'])
def process_document_structure():
    """Haystackを使用して文書の構造化データを処理"""
    data = request.json
    
    if not data or ('file_id' not in data and 'text' not in data):
        return jsonify({'error': 'Missing file_id or text'}), 400
    
    try:
        if 'file_id' in data:
            # ファイルIDから内容を取得
            from app.services.storage import get_file_content_by_id
            file_id = data['file_id']
            content = get_file_content_by_id(file_id)
        else:
            # 直接提供されたテキストを使用
            content = data['text']
        
        # 構造化データのスキーマを設定
        schema = data.get('schema', None)
        
        # Haystackを使用して構造化データを処理
        structured_data = haystack_service.process_structured_data(content, schema=schema)
        
        return jsonify({
            'structured_data': structured_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error processing structured data: {str(e)}")
        return jsonify({'error': 'Failed to process structured data'}), 500 