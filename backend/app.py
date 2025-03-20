import os
# 设置环境变量，确保不使用模拟数据
os.environ['USE_LOCAL_MOCK'] = 'false'
os.environ['DYNAMODB_TABLE'] = 'report'  # 修正表名前缀，实际表名为report_files, report_models, report_reports

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 