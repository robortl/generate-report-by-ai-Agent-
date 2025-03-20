# Report Generation System
# レポート生成システム
# 报告生成系统

## Overview
## 概要
## 概述

A modern report generation system that leverages AWS Bedrock, Haystack, and LangChain frameworks to automatically generate and manage reports from various document types.

AWS Bedrock、Haystack、LangChainフレームワークを活用し、様々なドキュメントタイプから自動的にレポートを生成・管理する最新のレポート生成システム。

利用AWS Bedrock、Haystack和LangChain框架，自动从各种文档类型生成和管理报告的现代报告生成系统。

## Features
## 機能
## 功能

- **Document Management**
  - Support for multiple file formats (PDF, DOC, DOCX, TXT, MD)
  - Automatic file categorization
  - Secure file storage using AWS S3

- **AI-Powered Report Generation**
  - Integration with AWS Bedrock models
  - Multiple model comparison
  - Customizable prompts
  - Structured data extraction

- **User Interface**
  - Modern, responsive design
  - Real-time report editing
  - Model comparison view
  - Prompt adjustment interface

## Technical Stack
## 技術スタック
## 技术栈

### Frontend
- React.js
- Material-UI
- Docker

### Backend
- Python/Flask
- AWS Bedrock
- Haystack
- LangChain
- Docker

### Infrastructure
- AWS S3 (File Storage)
- AWS DynamoDB (Metadata)
- AWS IAM (Authentication)

## Getting Started
## 開始方法
## 开始使用

### Prerequisites
### 前提条件
### 前置条件

- Docker and Docker Compose
- AWS Account with Bedrock access
- Node.js 16+ (for local development)
- Python 3.8+ (for local development)

### Installation
### インストール
### 安装

1. Clone the repository:
```bash
git clone https://github.com/yourusername/report-langchain-haystack.git
cd report-langchain-haystack
```

2. Configure AWS credentials:
```bash
aws configure
```

3. Start the application:
```bash
cd aws/direct && python start.py
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000/api

## Documentation
## ドキュメント
## 文档

- [System Architecture](architecture/system-overview.md)
- [API Documentation](api/specification.md)
- [Development Guide](development/roadmap.md)
- [Troubleshooting](operations/troubleshooting.md)

## Contributing
## 貢献
## 贡献

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License
## ライセンス
## 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Project Documentation

This directory contains project documentation and guides to help developers understand and use this project.

## Documentation Index

### Troubleshooting

- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions

### Development Checklists

- [Frontend Development Checklist](./frontend-checklist.md) - Frontend development checkpoints
- [Backend Development Checklist](./backend-checklist.md) - Backend development checkpoints

## How to Use These Documents

1. **New Developer Onboarding**:
   - First, read the README.md in the project root directory to understand the project overview
   - Then, review the development checklists to understand the project structure and development process

2. **When Encountering Issues**:
   - Check the troubleshooting guide for solutions to common problems
   - If the issue is not resolved, you can submit an issue or contact team members

3. **Before Developing New Features**:
   - Review the relevant development checklist to ensure the development environment and dependencies are properly configured
   - Follow the checklist during development to avoid common mistakes

## Document Maintenance

These documents should be updated as the project evolves. If you find errors in the documentation or have suggestions for improvements, please submit a pull request or contact the documentation maintainer.

# プロジェクトドキュメント

このディレクトリには、開発者がプロジェクトを理解し使用するためのドキュメントとガイドが含まれています。

## ドキュメントインデックス

### トラブルシューティング

- [トラブルシューティングガイド](./troubleshooting.md) - 一般的な問題と解決策

### 開発チェックリスト

- [フロントエンド開発チェックリスト](./frontend-checklist.md) - フロントエンド開発のチェックポイント
- [バックエンド開発チェックリスト](./backend-checklist.md) - バックエンド開発のチェックポイント

## ドキュメントの使用方法

1. **新規開発者のオンボーディング**:
   - まず、プロジェクトのルートディレクトリにあるREADME.mdを読んで、プロジェクトの概要を理解
   - 次に、開発チェックリストを確認して、プロジェクト構造と開発プロセスを理解

2. **問題が発生した場合**:
   - トラブルシューティングガイドを確認して、一般的な問題の解決策を探す
   - 問題が解決しない場合は、issueを提出するか、チームメンバーに連絡

3. **新機能の開発前**:
   - 関連する開発チェックリストを確認して、開発環境と依存関係が正しく設定されていることを確認
   - チェックリストに従って開発を進め、一般的なミスを避ける

## ドキュメントのメンテナンス

これらのドキュメントは、プロジェクトの発展に合わせて更新する必要があります。ドキュメントに誤りがある場合や改善提案がある場合は、pull requestを提出するか、ドキュメントメンテナンス担当者に連絡してください。 