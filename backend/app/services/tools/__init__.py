"""
工具服务模块，用于支持 LLM 报告生成的工具功能
"""

from .report_generator import generate_report_with_tools
from .tool_definitions import get_tool_definitions

__all__ = ['generate_report_with_tools', 'get_tool_definitions']
