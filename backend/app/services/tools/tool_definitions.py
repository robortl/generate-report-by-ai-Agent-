"""
定义 LLM 可用的工具
"""

def get_tool_definitions():
    """
    获取工具定义列表
    
    Returns:
        list: 工具定义列表
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_data",
                "description": "从文本中提取数据并进行分析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "包含数据的文本段落"}
                    },
                    "required": ["text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "extract_tasks",
                "description": "从文本中提取行动项和任务",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "包含任务和行动项的文本"}
                    },
                    "required": ["text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_timeline",
                "description": "从文本中提取并生成时间表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "包含时间信息的文本"}
                    },
                    "required": ["text"]
                }
            }
        }
    ]
    
    return tools
