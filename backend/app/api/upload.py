from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from app.services.storage import upload_file_to_s3, save_metadata_to_dynamodb
# ブループリントを作成
from datetime import datetime
import traceback

# 許可されるファイル拡張子
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md'}
upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

def allowed_file(filename):
    """ファイル拡張子が許可されているかチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('', methods=['POST'])
def upload_file():
    """ファイルアップロードリクエストを処理"""
    try:
        # ファイルの存在確認
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']

        # ファイル名の確認
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # ファイルタイプの確認
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400


        # カテゴリの取得
        category = request.form.get('category', 'general')

        # 安全なファイル名の生成
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        s3_key = f"uploads/{file_id}_{filename}"

        try:
            # S3にアップロード
            current_app.logger.info(f"Uploading file to S3: {s3_key}")
            s3_url = upload_file_to_s3(file, s3_key)
            current_app.logger.info(f"File uploaded to S3: {s3_url}")

            # メタデータをDynamoDBに保存
            metadata = {
                'file_id': file_id,
                'original_filename': filename,
                'category': category,
                's3_key': s3_key,
                's3_url': s3_url,
                'status': 'uploaded',
                'upload_time': str(datetime.now())
            }
            current_app.logger.info(f"Saving metadata to DynamoDB: {metadata}")
            save_metadata_to_dynamodb(metadata)
            current_app.logger.info("Metadata saved to DynamoDB")

            return jsonify({
                'message': 'File uploaded successfully',
                'file_id': file_id,
                's3_url': s3_url
            }), 201

        except Exception as e:
            current_app.logger.error(f"Error uploading file: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in upload_file: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@upload_bp.route('/categories', methods=['GET'])
def get_categories():
    """利用可能なカテゴリを取得"""
    try:
        current_app.logger.info("Fetching categories")
        # ここでは設定またはデータベースからカテゴリを取得できます
        categories = [
            {'id': 'meeting', 'name': '会議记录'},
            {'id': 'report', 'name': '业务报告'},
            {'id': 'contract', 'name': '契约书'},
            {'id': 'general', 'name': '一般文档'}
        ]
        current_app.logger.info(f"Categories fetched: {categories}")
        return jsonify(categories)
    except Exception as e:
        current_app.logger.error(f"Error fetching categories: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to fetch categories: {str(e)}'}), 500 