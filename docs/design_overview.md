# Report Generation System Design Overview
# レポート生成システム 概要設計書

## 1. System Overview
## 1. システム概要

This system automatically generates reports from meetings and documents using AI. It utilizes the LangChain and Haystack frameworks, leveraging AWS Bedrock's large language models to produce high-quality reports.

本システムは、会議や文書からAIを活用して自動的にレポートを生成するシステムです。LangChainとHaystackフレームワークを利用し、AWS Bedrockの大規模言語モデルを活用して、高品質なレポートを生成します。

### 1.1 Purpose
### 1.1 目的

- Extract and summarize important information from meeting minutes and documents
- Compare multiple AI models for optimal report generation
- Customizable report formats and content
- Efficient document processing workflow

- 会議録や文書からの重要情報の抽出と要約
- 複数のAIモデルを比較し、最適なレポート生成
- カスタマイズ可能なレポート形式と内容
- 効率的なドキュメント処理ワークフロー

### 1.2 Key Features
### 1.2 主要機能

- File upload and categorization
- AI-powered automatic report generation
- Comparison of different AI models
- Customization of report generation parameters
- Report download and sharing

- ファイルアップロードと分類
- AIによるレポート自動生成
- 異なるAIモデルの比較
- レポート生成パラメータのカスタマイズ
- レポートのダウンロードと共有

### 1.3 LangChain and Haystack Integration Points
### 1.3 LangChainとHaystackの活用ポイント

**LangChain Integration Points:**
- Document Processing: Text splitting, preprocessing, embedding generation
- Prompt Management: Report generation prompt template management
- Model Chains: Chain construction for multiple AI tasks
- Memory Management: Conversation history and context retention
- AWS Bedrock Integration: Model invocation interface

**LangChainの活用環節：**
- ドキュメント処理：テキスト分割、前処理、エンベディング生成
- プロンプト管理：レポート生成用のプロンプトテンプレート管理
- モデルチェーン：複数のAIタスクを連携させるチェーン構築
- メモリ管理：会話履歴や文脈の保持
- AWS Bedrockとの統合：モデル呼び出しインターフェース

**Haystack Integration Points:**
- Document Search: Semantic search for relevant information extraction
- Question Answering: Answer generation for specific information in documents
- Information Extraction: Structured data extraction and metadata generation
- Pipeline Management: Coordination of multiple processing steps
- Evaluation Framework: Quality assessment of generated reports

**Haystackの活用環節：**
- ドキュメント検索：セマンティック検索による関連情報抽出
- 質問応答：文書内の特定情報に対する回答生成
- 情報抽出：構造化データの抽出とメタデータ生成
- パイプライン管理：複数の処理ステップの連携
- 評価フレームワーク：生成されたレポートの品質評価

## 2. System Architecture
## 2. システムアーキテクチャ

### 2.1 Overall Structure
### 2.1 全体構成

```
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|  Frontend      |<---->|   Backend      |<---->|  AWS Bedrock   |
|  (React)       |      |  (Flask/Python)|      |  AI Models    |
|                |      |                |      |                |
+----------------+      +----------------+      +----------------+
                               |
                               v
                        +----------------+
                        |                |
                        |  Data Storage  |
                        |                |
                        +----------------+
```

### 2.2 Technology Stack
### 2.2 技術スタック

- **Frontend**: React, Material UI
- **Backend**: Python, Flask
- **AI Frameworks**: LangChain, Haystack
- **AI Models**: AWS Bedrock (Claude, Titan, others)
- **Infrastructure**: Docker, AWS

- **フロントエンド**: React, Material UI
- **バックエンド**: Python, Flask
- **AIフレームワーク**: LangChain, Haystack
- **AIモデル**: AWS Bedrock (Claude, Titan, その他)
- **インフラ**: Docker, AWS

## 3. Frontend Design
## 3. フロントエンド設計

### 3.1 Page Structure
### 3.1 ページ構成

1. **Home Page (HomePage)**
   - System overview display
   - Recent reports list
   - Navigation to main features

1. **ホームページ (HomePage)**
   - システム概要表示
   - 最近のレポート一覧
   - 主要機能へのナビゲーション

2. **Upload Page (UploadPage)**
   - File upload functionality
   - Category selection
   - Recent uploads list

2. **アップロードページ (UploadPage)**
   - ファイルアップロード機能
   - カテゴリ選択
   - 最近のアップロードファイル一覧

3. **Report Page (ReportPage)**
   - Report detail display
   - Tabbed interface (Summary, Details, Key Points, Recommendations)
   - Report operations (Download, Regenerate, etc.)

3. **レポートページ (ReportPage)**
   - レポート詳細表示
   - タブ付きインターフェース（要約、詳細、キーポイント、提案）
   - レポート操作（ダウンロード、再生成など）

4. **Model Comparison Page (ComparePage)**
   - Report comparison using different models
   - Model selection
   - Comparison results display

4. **モデル比較ページ (ComparePage)**
   - 異なるモデルによるレポート比較
   - モデル選択
   - 比較結果の表示

5. **Settings Page (SettingsPage)**
   - Report generation parameter settings
   - Prompt template customization
   - Model settings

5. **設定ページ (SettingsPage)**
   - レポート生成パラメータ設定
   - プロンプトテンプレートカスタマイズ
   - モデル設定

### 3.2 Component Design
### 3.2 コンポーネント設計

- **Common Components**
  - Navigation bar
  - File list
  - Loading indicator
  - Error display

- **共通コンポーネント**
  - ナビゲーションバー
  - ファイルリスト
  - ローディングインジケータ
  - エラー表示

- **Page-Specific Components**
  - File uploader
  - Report viewer
  - Model comparison viewer
  - Settings form

- **ページ固有コンポーネント**
  - ファイルアップローダー
  - レポートビューア
  - モデル比較ビューア
  - 設定フォーム

## 4. Backend Design
## 4. バックエンド設計

### 4.1 API Endpoints
### 4.1 APIエンドポイント

1. **File Management**
   - `POST /api/files` - File upload
   - `GET /api/files` - Get file list
   - `GET /api/files/{file_id}` - Get file details
   - `GET /api/categories` - Get category list

1. **ファイル管理**
   - `POST /api/files` - ファイルアップロード
   - `GET /api/files` - ファイル一覧取得
   - `GET /api/files/{file_id}` - ファイル詳細取得
   - `GET /api/categories` - カテゴリ一覧取得

2. **Report Generation**
   - `POST /api/reports` - Generate report
   - `GET /api/reports/{report_id}` - Get report
   - `PUT /api/reports/{report_id}` - Update report
   - `GET /api/reports/{report_id}/download` - Download report

2. **レポート生成**
   - `POST /api/reports` - レポート生成
   - `GET /api/reports/{report_id}` - レポート取得
   - `PUT /api/reports/{report_id}` - レポート更新
   - `GET /api/reports/{report_id}/download` - レポートダウンロード

3. **Model Management**
   - `GET /api/models` - Get available models list
   - `POST /api/compare` - Compare models

3. **モデル管理**
   - `GET /api/models` - 利用可能なモデル一覧
   - `POST /api/compare` - モデル比較

4. **Settings Management**
   - `GET /api/reports/{report_id}/settings` - Get report settings
   - `PUT /api/reports/{report_id}/settings` - Update report settings

4. **設定管理**
   - `GET /api/reports/{report_id}/settings` - レポート設定取得
   - `PUT /api/reports/{report_id}/settings` - レポート設定更新

### 4.2 Data Models
### 4.2 データモデル

1. **File**
   - file_id: Unique identifier
   - original_filename: Original filename
   - file_path: Storage path
   - category: Category
   - upload_date: Upload timestamp
   - status: Processing status

1. **File**
   - file_id: 一意識別子
   - original_filename: 元のファイル名
   - file_path: 保存パス
   - category: カテゴリ
   - upload_date: アップロード日時
   - status: 処理状態

2. **Report**
   - report_id: Unique identifier
   - file_id: Related file ID
   - model_id: Used model ID
   - summary: Summary
   - content: Detailed content
   - key_points: Key points
   - recommendations: Recommendations
   - generated_at: Generation timestamp

2. **Report**
   - report_id: 一意識別子
   - file_id: 関連ファイルID
   - model_id: 使用モデルID
   - summary: 要約
   - content: 詳細内容
   - key_points: キーポイント
   - recommendations: 提案
   - generated_at: 生成日時

3. **Model**
   - model_id: Model identifier
   - name: Model name
   - description: Description
   - provider: Provider

3. **Model**
   - model_id: モデル識別子
   - name: モデル名
   - description: 説明
   - provider: プロバイダ

4. **Settings**
   - report_id: Related report ID
   - model_id: Model ID
   - temperature: Temperature parameter
   - include_summary: Include summary flag
   - include_key_points: Include key points flag
   - include_recommendations: Include recommendations flag
   - prompts: Custom prompts

4. **Settings**
   - report_id: 関連レポートID
   - model_id: モデルID
   - temperature: 温度パラメータ
   - include_summary: 要約含むフラグ
   - include_key_points: キーポイント含むフラグ
   - include_recommendations: 提案含むフラグ
   - prompts: カスタムプロンプト

## 5. AI Model Integration
## 5. AIモデル統合

### 5.1 LangChain Integration
### 5.1 LangChain統合

- **Document Processing Pipeline**
  - Text Splitting (TextSplitter): Split long documents into appropriate chunks
  - Embedding Generation: Generate document meaning representations
  - Vector Store: Efficient document search and retrieval

- **ドキュメント処理パイプライン**
  - テキスト分割（TextSplitter）：長文書を適切なチャンクに分割
  - エンベディング生成：文書の意味表現を生成
  - ベクトルストア：文書の効率的な検索と取得

- **Prompt Template Management**
  - Custom Prompt Templates: Templates for report generation
  - Prompt Variables: Dynamic prompt generation
  - Output Parsers: Processing structured outputs

- **プロンプトテンプレート管理**
  - カスタムプロンプトテンプレート：レポート生成用のテンプレート
  - プロンプト変数：動的なプロンプト生成
  - 出力パーサー：構造化された出力の処理

- **Model Invocation Chains**
  - Sequential Chains: Execute multiple AI tasks in sequence
  - Router Chains: Select different processing paths based on conditions
  - Summary Chains: Generate document summaries
  - QA Chains: Question answering processing

- **モデル呼び出しチェーン**
  - シーケンシャルチェーン：複数のAIタスクを順次実行
  - ルーターチェーン：条件に基づいて異なる処理パスを選択
  - 要約チェーン：文書要約の生成
  - QAチェーン：質問応答処理

### 5.2 Haystack Integration
### 5.2 Haystack統合

- **Document Search and Extraction**
  - Indexer: Document index creation
  - Retriever: Search and retrieve relevant documents
  - Ranker: Search result ranking

- **ドキュメント検索・抽出**
  - インデクサー：文書のインデックス作成
  - リトリーバー：関連文書の検索と取得
  - ランカー：検索結果のランキング

- **Question Answering Pipeline**
  - Reader: Answer extraction from documents
  - Generator: Answer generation
  - Evaluator: Answer evaluation

- **質問応答パイプライン**
  - リーダー：文書からの回答抽出
  - ジェネレーター：回答の生成
  - エバリュエーター：回答の評価

- **情報抽出**
  - エンティティ抽出：重要な名前や概念の識別
  - キーワード抽出：重要なキーワードの抽出
  - メタデータ生成：文書のメタデータ作成

### 5.3 AWS Bedrock Integration
### 5.3 AWS Bedrock統合

- Model invocation interface
- Authentication and permission management
- Response processing

- モデル呼び出しインターフェース
- 認証と権限管理
- レスポンス処理

### 5.4 Processing Flow
### 5.4 処理フロー

1. **File Upload**
   - File parsing (LangChain DocumentLoader)
   - Text extraction and preprocessing
   - Embedding generation and index creation (Haystack DocumentStore)

1. **ファイルアップロード時**
   - ファイル解析（LangChain DocumentLoader）
   - テキスト抽出と前処理
   - エンベディング生成とインデックス作成（Haystack DocumentStore）

2. **Report Generation**
   - Prompt generation (LangChain PromptTemplate)
   - Related information search (Haystack Retriever)
   - Report generation chain execution (LangChain Chain)
   - Result post-processing and storage

2. **レポート生成時**
   - プロンプト生成（LangChain PromptTemplate）
   - 関連情報検索（Haystack Retriever）
   - レポート生成チェーン実行（LangChain Chain）
   - 結果の後処理と保存

3. **Model Comparison**
   - Parallel processing with multiple models (LangChain)
   - Result evaluation and comparison (Haystack Evaluator)
   - Comparison report generation

3. **モデル比較時**
   - 複数モデルでの並列処理（LangChain）
   - 結果の評価と比較（Haystack Evaluator）
   - 比較レポートの生成

## 6. Deployment
## 6. デプロイメント

### 6.1 Development Environment
### 6.1 開発環境

- Local Docker environment
- Development configuration files
- Mock data and tests

- ローカルDocker環境
- 開発用設定ファイル
- モックデータとテスト

### 6.2 Production Environment
### 6.2 本番環境

- AWS environment deployment
- Security settings
- Scaling configuration

- AWS環境へのデプロイ
- セキュリティ設定
- スケーリング設定 