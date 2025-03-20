import os
import logging
from typing import Dict, Any, Optional, List
from app.services.langchain_service import langchain_service
from app.services.haystack_service import haystack_service
from app.services.storage import save_report as save_report_to_db
from app.config.model_config import get_model_config, DEFAULT_MODEL_ID

# Configure logger
# ロガーを構成
logger = logging.getLogger(__name__)

class ReportGenerator:
    """Report generator that integrates LangChain and Haystack functionality
    
    LangChainとHaystackの機能を統合したレポートジェネレーター
    """
    
    def __init__(self):
        """Initialize report generator
        
        レポートジェネレーターを初期化する
        """
        self.default_model_id = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    
    def generate_report(self, content: str, prompt: Optional[str] = None, model_id: Optional[str] = None, use_tools: bool = False) -> str:
        """Generate report, with optional tool usage
        
        レポートを生成し、オプションでツールの使用が可能
        """
        # Use specified model ID or default model ID
        # 指定されたモデルIDまたはデフォルトのモデルIDを使用
        model = model_id if model_id else self.default_model_id
        
        # Get model configuration
        # モデル構成を取得
        model_config = get_model_config(model)
        
        # Log model ID and configuration used
        # 使用されるモデルIDと構成をログに記録
        logger.info(f"Using model ID: {model} to generate report, use_tools={use_tools}")
        logger.info(f"Model configuration: temperature={model_config.get('temperature')}, max_tokens={model_config.get('max_tokens')}")
        
        # Use LangChain's RAG functionality to generate report, based on tool support
        # ツールサポートに基づいて、LangChainのRAG機能を使用してレポートを生成
        if use_tools:
            # Generate report using tools
            # ツールを使用してレポートを生成
            report = langchain_service.generate_report_with_tools(content, prompt, model)
        else:
            # Standard RAG mode
            # 標準RAGモード
            report = langchain_service.generate_report_with_rag(content, prompt, model)
        
        return report
    
    def enhance_report_with_keywords(self, report: str, content: str) -> Dict[str, Any]:
        """Enhance report with keywords
        
        キーワードでレポートを強化する
        """
        # Extract keywords
        # キーワードを抽出
        keywords = haystack_service.extract_keywords(content, top_n=15)
        
        # Return enhanced report
        # 強化されたレポートを返す
        return {
            "report": report,
            "keywords": keywords
        }
    
    def enhance_report_with_structure(self, report: str, content: str) -> Dict[str, Any]:
        """Enhance report with structured data
        
        構造化データでレポートを強化する
        """
        # Analyze meeting structure
        # 会議構造を分析
        structure = haystack_service.analyze_meeting_structure(content)
        
        # Extract entities
        # エンティティを抽出
        entities = haystack_service.extract_entities(content)
        
        # Return enhanced report
        # 強化されたレポートを返す
        return {
            "report": report,
            "structure": structure,
            "entities": entities
        }
    
    def generate_complete_report(self, content: str, prompt: Optional[str] = None, model_id: Optional[str] = None, use_tools: bool = False) -> Dict[str, Any]:
        """Generate complete enhanced report, with tool support
        
        ツールサポート付きの完全な強化レポートを生成する
        """
        # Generate base report
        # 基本レポートを生成
        base_report = self.generate_report(content, prompt, model_id, use_tools)
        
        # Extract keywords
        # キーワードを抽出
        keywords = haystack_service.extract_keywords(content, top_n=15)
        
        # Analyze meeting structure
        # 会議構造を分析
        structure = haystack_service.analyze_meeting_structure(content)
        
        # Extract entities
        # エンティティを抽出
        entities = haystack_service.extract_entities(content)
        
        # Return complete report
        # 完全なレポートを返す
        return {
            "report": base_report,
            "keywords": keywords,
            "structure": structure,
            "entities": entities,
            "model_id": model_id if model_id else self.default_model_id,
            "prompt": prompt,
            "tools_used": use_tools
        }
    
    def compare_models(self, content: str, model_ids: List[str], prompt: Optional[str] = None, model_tool_map: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Compare output results of multiple models, with tool support
        
        ツールサポート付きで複数モデルの出力結果を比較する
        """
        results = {}
        model_tool_map = model_tool_map or {}
        
        for model_id in model_ids:
            # Check if model supports tools
            # モデルがツールをサポートしているかチェック
            use_tools = model_tool_map.get(model_id, False)
            
            # Generate report
            # レポートを生成
            report = self.generate_report(content, prompt, model_id, use_tools=use_tools)
            results[model_id] = {
                "report": report,
                "tools_used": use_tools
            }
        
        return results

# Create report generator instance
# レポートジェネレーターインスタンスを作成
report_generator = ReportGenerator()

# Export functions
# 関数をエクスポート
def generate_report(content: str, prompt: Optional[str] = None, model_id: Optional[str] = None, use_tools: bool = False) -> str:
    """Generate report, with tool support
    
    ツールサポート付きでレポートを生成する
    """
    logger.info(f"Using model ID: {model_id} to generate report")
    return report_generator.generate_report(content, prompt, model_id, use_tools)

def generate_complete_report(content: str, prompt: Optional[str] = None, model_id: Optional[str] = None, use_tools: bool = False) -> Dict[str, Any]:
    """Generate complete enhanced report, with tool support
    
    ツールサポート付きの完全な強化レポートを生成する
    """
    return report_generator.generate_complete_report(content, prompt, model_id, use_tools)

def compare_models(content: str, model_ids: List[str], prompt: Optional[str] = None, model_tool_map: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
    """Compare output results of multiple models, with tool support
    
    ツールサポート付きで複数モデルの出力結果を比較する
    """
    return report_generator.compare_models(content, model_ids, prompt, model_tool_map)

def save_report(report_data: Dict[str, Any]) -> Any:
    """Save report to database
    
    レポートをデータベースに保存する
    """
    return save_report_to_db(report_data)