#!/usr/bin/env python
"""
检查Flask应用是否正在运行
"""
import requests

def check_flask_app():
    """检查Flask应用是否正在运行"""
    try:
        response = requests.get('http://localhost:5000/health')
        print(f'Flask应用状态: {response.status_code} - {response.json()}')
        return True
    except Exception as e:
        print(f'无法连接到Flask应用: {e}')
        return False

if __name__ == "__main__":
    check_flask_app() 