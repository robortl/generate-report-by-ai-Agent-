"""
向量存储和嵌入处理模块
"""

import logging
import traceback
from typing import List, Any
from langchain.vectorstores import VectorStore

# 初始化日志
logger = logging.getLogger(__name__)

# 定义向量存储类和其实现
vector_store_options = [
    {"name": "FAISS", "import_path": "langchain_community.vectorstores.faiss.FAISS"},
    {"name": "Chroma", "import_path": "langchain_community.vectorstores.chroma.Chroma"},
    {"name": "DocArray", "import_path": "langchain_community.vectorstores.docarray.DocArrayInMemorySearch"}
]

# 尝试导入各种向量存储实现
vector_store_cls = None
for option in vector_store_options:
    try:
        module_path, class_name = option["import_path"].rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        vector_store_cls = getattr(module, class_name)
        logger.info(f"成功导入 {option['name']} 向量存储")
        break
    except (ImportError, AttributeError) as e:
        logger.warning(f"导入 {option['name']} 失败: {str(e)}")

if vector_store_cls is None:
    logger.error("所有向量存储导入失败，系统将无法正常运行")


def create_vector_store(texts: List[str], embeddings: Any) -> VectorStore:
    """
    创建向量存储
    
    Args:
        texts: 文本列表
        embeddings: 嵌入模型
        
    Returns:
        VectorStore: 向量存储实例
    
    Raises:
        Exception: 如果创建向量存储失败
    """
    try:
        if vector_store_cls is None:
            raise ImportError("未能找到可用的向量存储实现")
        
        # 使用选定的向量存储类
        vectorstore = vector_store_cls.from_texts(texts, embeddings)
        logger.info(f"成功使用 {vector_store_cls.__name__} 创建向量存储")
        return vectorstore
    except Exception as e:
        logger.error(f"创建向量存储失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"创建向量存储失败: {str(e)}") from e
