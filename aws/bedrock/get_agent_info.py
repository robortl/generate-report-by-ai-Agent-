#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
エージェント情報取得スクリプト
Agent Information Retrieval Script
エージェント情報取得スクリプト
"""

import os
import sys
import json
import logging
import boto3
import argparse
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_bedrock_agent_client(profile_name=None, region_name=None):
    """Bedrock Agentクライアントを作成する"""
    try:
        # AWSセッションの作成
        session = boto3.Session(profile_name=profile_name, region_name=region_name or 'ap-northeast-1')
        
        # 認証情報の確認
        if profile_name:
            logger.info(f"Using AWS configuration profile: {profile_name}")
        else:
            logger.info(f"Using AWS configuration profile: default")
        
        # 環境変数の認証情報を確認
        if os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY'):
            logger.info("Found credentials in environment variables")
        
        # Bedrock Agentクライアントの作成
        return session.client('bedrock-agent')
    
    except Exception as e:
        logger.error(f"Error creating Bedrock Agent client: {e}")
        return None

def get_agent_info(agent_id, client=None):
    """エージェント情報を取得する"""
    if client is None:
        client = create_bedrock_agent_client()
    
    try:
        response = client.get_agent(
            agentId=agent_id
        )
        return response
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        return None

def get_agent_versions(agent_id, client=None):
    """エージェントのバージョン一覧を取得する"""
    if client is None:
        client = create_bedrock_agent_client()
    
    try:
        response = client.list_agent_versions(
            agentId=agent_id
        )
        return response.get('agentVersionSummaries', [])
    except Exception as e:
        logger.error(f"Error getting agent versions: {e}")
        return []

def list_agents(client=None):
    """エージェント一覧を取得する"""
    if client is None:
        client = create_bedrock_agent_client()
    
    try:
        response = client.list_agents()
        return response.get('agentSummaries', [])
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return []

def list_action_groups(agent_id, agent_version=None, client=None):
    """アクショングループ一覧を取得する"""
    if client is None:
        client = create_bedrock_agent_client()
    
    try:
        # エージェント情報を取得してバージョンを確認
        agent_info = get_agent_info(agent_id, client)
        if not agent_info:
            return []
        
        # バージョンが指定されていない場合は、DRAFTを使用
        if not agent_version:
            # バージョン一覧を取得
            versions = get_agent_versions(agent_id, client)
            if versions:
                # 最新のバージョンを使用
                agent_version = versions[0].get('agentVersion')
                logger.info(f"Using latest agent version: {agent_version}")
            else:
                # バージョンがない場合はDRAFTを使用
                agent_version = "DRAFT"
                logger.info("No versions found, using DRAFT")
        
        logger.info(f"Listing action groups for agent {agent_id} with version {agent_version}")
        
        response = client.list_agent_action_groups(
            agentId=agent_id,
            agentVersion=agent_version
        )
        return response.get('agentActionGroupSummaries', [])
    except Exception as e:
        logger.error(f"Error listing action groups: {e}")
        return []

def get_agent_aliases(agent_id, client=None):
    """エージェントのエイリアス一覧を取得する"""
    if client is None:
        client = create_bedrock_agent_client()
    
    try:
        response = client.list_agent_aliases(
            agentId=agent_id
        )
        return response.get('agentAliasSummaries', [])
    except Exception as e:
        logger.error(f"Error getting agent aliases: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Get Bedrock Agent information')
    parser.add_argument('--agent-id', help='Agent ID to get information for')
    parser.add_argument('--list-agents', action='store_true', help='List all agents')
    parser.add_argument('--list-action-groups', action='store_true', help='List action groups for the agent')
    parser.add_argument('--list-aliases', action='store_true', help='List aliases for the agent')
    parser.add_argument('--agent-version', help='Agent version to use (default: latest or DRAFT)')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--region', help='AWS region name')
    
    args = parser.parse_args()
    
    # クライアントの作成
    client = create_bedrock_agent_client(args.profile, args.region)
    
    if args.list_agents:
        agents = list_agents(client)
        print("\nAgents:")
        print(json.dumps(agents, indent=2, default=str))
    
    if args.agent_id:
        agent_info = get_agent_info(args.agent_id, client)
        print("\nAgent Information:")
        print(json.dumps(agent_info, indent=2, default=str))
        
        if args.list_action_groups:
            action_groups = list_action_groups(args.agent_id, args.agent_version, client)
            print("\nAction Groups:")
            print(json.dumps(action_groups, indent=2, default=str))
        
        if args.list_aliases:
            aliases = get_agent_aliases(args.agent_id, client)
            print("\nAgent Aliases:")
            print(json.dumps(aliases, indent=2, default=str))

if __name__ == "__main__":
    main() 