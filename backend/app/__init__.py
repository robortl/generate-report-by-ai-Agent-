from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_app(test_config=None):
    """创建并配置Flask应用"""
    # 直接设置环境变量
    os.environ['S3_BUCKET_NAME'] = 'report-langchain-haystack-files'
    os.environ['DYNAMODB_TABLE'] = 'report'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
    
    app = Flask(__name__, instance_relative_config=True)
    
    # 启用CORS
    CORS(app)
    
    # 配置应用
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DEBUG=os.environ.get('DEBUG', 'True') == 'True',
    )
    
    if test_config is None:
        # 加载实例配置（如果存在）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 加载测试配置
        app.config.from_mapping(test_config)
    
    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # 注册蓝图
    from app.api import upload_bp, report_bp, model_bp, files_bp
    app.register_blueprint(upload_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(files_bp)
    
    # 简单的健康检查路由
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}
    
    # API路径下的健康检查路由
    @app.route('/api/health')
    def api_health_check():
        return {'status': 'healthy'}
    
    return app 