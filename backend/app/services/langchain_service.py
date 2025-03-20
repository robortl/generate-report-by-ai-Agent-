"""
LangChain Service - Provides AI generation capabilities
Refactored Version - Functionality split into various modules

LangChainサービス - AI生成機能を提供する
リファクタリング版 - 機能を複数のモジュールに分割
"""

import logging
from typing import List, Dict, Any, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import HumanMessage
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever

# Import refactored modules
# リファクタリングされたモジュールをインポート
from app.services.modules.model_handlers import initialize_bedrock_client, create_model, get_model_for_generation
from app.services.modules.report_generators import generate_report_with_rag as module_generate_report_with_rag
from app.services.modules.vector_store import create_vector_store
from app.services.tools.report_generator import generate_report_with_tools as tool_generate_report_with_tools

# Initialize logging
# ログの初期化
logger = logging.getLogger(__name__)

class LangChainService:
    """LangChain service providing AI generation capabilities
    
    AI生成機能を提供するLangChainサービス
    """
    
    def __init__(self):
        """Initialize LangChain service
        
        LangChainサービスを初期化する
        """
        # Initialize text splitter
        # テキスト分割器を初期化
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize Bedrock client and model
        # Bedrockクライアントとモデルを初期化
        self.bedrock_client, self.default_model_id, init_success = initialize_bedrock_client()
        
        # Create model
        # モデルを作成
        self.llm, self.chat_model, self.embeddings, self.use_fake_embeddings = create_model(
            self.bedrock_client, 
            self.default_model_id, 
            not init_success
        )
    
    def create_prompt_template(self, template: str, input_variables: List[str]) -> PromptTemplate:
        """Create prompt template
        
        プロンプトテンプレートを作成する
        """
        return PromptTemplate(
            template=template,
            input_variables=input_variables
        )
    
    def generate_with_prompt(self, prompt_template: str, input_variables: Dict[str, str], model_id: Optional[str] = None) -> str:
        """Generate text using a prompt
        
        プロンプトを使用してテキストを生成する
        """
        try:
            # Create prompt template
            # プロンプトテンプレートを作成
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=list(input_variables.keys())
            )
            
            # Create LLM chain
            # LLMチェーンを作成
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Generate text
            # テキストを生成
            return chain.run(**input_variables)
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error generating text: {e}. Please ensure your AWS account has Bedrock service enabled and has sufficient permissions."
    
    def create_rag_chain(self, documents: List[str], query: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RAG enhanced retrieval chain and generate answer
        
        RAG強化検索チェーンを作成し、回答を生成する
        """
        # Get appropriate model
        # 適切なモデルを取得
        llm = get_model_for_generation(self, model_id)
        
        # Split documents
        # ドキュメントを分割
        texts = []
        for doc in documents:
            texts.extend(self.text_splitter.split_text(doc))
        
        # Create vector store
        # ベクトルストアを作成
        try:
            vectorstore = create_vector_store(texts, self.embeddings)
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            return {"answer": f"Failed to create vector store: {str(e)}", "source_documents": []}
        
        # Create retriever
        # 検索機を作成
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # Create contextual compression retriever
        # コンテキスト圧縮検索機を作成
        compressor = LLMChainExtractor.from_llm(llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=retriever
        )
        
        # Create RAG chain
        # RAGチェーンを作成
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=compression_retriever,
            return_source_documents=True
        )
        
        # Generate answer
        # 回答を生成
        result = qa_chain({"question": query, "chat_history": []})
        
        return {
            "answer": result["answer"],
            "source_documents": [doc.page_content for doc in result["source_documents"]]
        }
    
    def create_interactive_chain(self, documents: List[str], model_id: Optional[str] = None):
        """Create interactive conversation chain
        
        インタラクティブな会話チェーンを作成する
        """
        # Get appropriate model
        # 適切なモデルを取得
        llm = get_model_for_generation(self, model_id)
        
        # Split documents
        # ドキュメントを分割
        texts = []
        for doc in documents:
            texts.extend(self.text_splitter.split_text(doc))
        
        # Create vector store
        # ベクトルストアを作成
        try:
            vectorstore = create_vector_store(texts, self.embeddings)
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            raise Exception(f"Failed to create vector store: {str(e)}") from e
        
        # Create retriever
        # 検索機を作成
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        # Create conversation memory
        # 会話メモリを作成
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create interactive conversation chain
        # インタラクティブな会話チェーンを作成
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory
        )
        
        return qa_chain
    
    def optimize_prompt(self, base_prompt: str, context: str, feedback: str) -> str:
        """Optimize prompt based on feedback
        
        フィードバックに基づいてプロンプトを最適化する
        """
        optimization_prompt = f"""
        You are a professional prompt engineer. Please optimize the prompt based on the following information:
        
        Original prompt: {base_prompt}
        
        Context information: {context}
        
        User feedback: {feedback}
        
        Please provide an optimized prompt that better meets user needs. Only return the optimized prompt without any explanation.
        """
        
        return self.llm(optimization_prompt)
    
    def generate_report_with_rag(self, document: str, prompt: Optional[str] = None, model_id: Optional[str] = None) -> str:
        """Generate report using RAG
        
        RAGを使用してレポートを生成する
        """
        return module_generate_report_with_rag(self, document, prompt, model_id)
    
    def generate_report_with_tools(self, document: str, prompt: Optional[str] = None, model_id: Optional[str] = None) -> str:
        """Generate report using tools
        
        ツールを使用してレポートを生成する
        """
        return tool_generate_report_with_tools(self, document, prompt, model_id)

# Create service instance
# サービスインスタンスを作成
langchain_service = LangChainService()
