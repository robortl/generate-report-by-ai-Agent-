#!/bin/bash

# This script is used to debug network connectivity issues between Docker containers
# このスクリプトはDockerコンテナ間のネットワーク接続の問題をデバッグするために使用されます

# For Windows, you can run it using the following command:
# Windowsでは、以下のコマンドで実行できます：

# wsl bash -c "./debug-network.sh"

# Get container names
# コンテナ名を取得

FRONTEND_CONTAINER=$(docker ps -q -f name=report-frontend)
BACKEND_CONTAINER=$(docker ps -q -f name=report-backend)

if [ -z "$FRONTEND_CONTAINER" ] || [ -z "$BACKEND_CONTAINER" ]; then
    echo "Error: Frontend or backend container not found"
    echo "エラー：フロントエンドまたはバックエンドコンテナが見つかりません"
    exit 1
fi

# Get container IP addresses
# コンテナのIPアドレスを取得

FRONTEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $FRONTEND_CONTAINER)
BACKEND_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $BACKEND_CONTAINER)

echo "Frontend container IP: $FRONTEND_IP"
echo "フロントエンドコンテナのIP: $FRONTEND_IP"

echo "Backend container IP: $BACKEND_IP"
echo "バックエンドコンテナのIP: $BACKEND_IP"

# Test network connectivity
# ネットワーク接続をテスト

echo "Testing network connectivity..."
echo "ネットワーク接続をテスト中..."

# Test frontend to backend
# フロントエンドからバックエンドへのテスト

echo "Testing frontend to backend connection..."
echo "フロントエンドからバックエンドへの接続をテスト中..."

docker exec $FRONTEND_CONTAINER ping -c 4 $BACKEND_IP

# Test backend to frontend
# バックエンドからフロントエンドへのテスト

echo "Testing backend to frontend connection..."
echo "バックエンドからフロントエンドへの接続をテスト中..."

docker exec $BACKEND_CONTAINER ping -c 4 $FRONTEND_IP

# Check container logs
# コンテナのログをチェック

echo "Checking container logs..."
echo "コンテナのログをチェック中..."

echo "Frontend container logs:"
echo "フロントエンドコンテナのログ:"

docker logs $FRONTEND_CONTAINER --tail 50

echo "Backend container logs:"
echo "バックエンドコンテナのログ:"

docker logs $BACKEND_CONTAINER --tail 50

# Check network configuration
# ネットワーク設定をチェック

echo "Checking network configuration..."
echo "ネットワーク設定をチェック中..."

echo "Frontend container network settings:"
echo "フロントエンドコンテナのネットワーク設定:"

docker inspect $FRONTEND_CONTAINER | grep -A 20 "NetworkSettings"

echo "Backend container network settings:"
echo "バックエンドコンテナのネットワーク設定:"

docker inspect $BACKEND_CONTAINER | grep -A 20 "NetworkSettings"
