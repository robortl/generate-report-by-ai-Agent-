import boto3
import json
import time
import os
from datetime import datetime

# 配置
AGENT_ID = "LPJVAYJAK2"
AGENT_ALIAS_ID = "TSTALIASID"
SESSION_ID = f"report-session-{int(time.time())}"

# 创建Bedrock Agent Runtime客户端
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

def save_to_file(content, filename):
    """保存内容到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n报告已保存到 {filename}\n")

# 从文件读取会议记录
def read_meeting_notes(file_path):
    """读取会议记录文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

# 主函数
def main():
    print("正在调用Bedrock Agent生成看护报告...\n")
    
    # 读取会议记录
    meeting_notes = read_meeting_notes("meeting_notes.txt")
    if not meeting_notes:
        print("无法读取会议记录，退出程序")
        return
    
    print(f"Agent ID: {AGENT_ID}")
    print(f"Alias ID: {AGENT_ALIAS_ID}")
    print(f"Session ID: {SESSION_ID}\n")
    
    # 构建提示
    prompt = f"根据以下会议记录生成一份看护报告：{meeting_notes}"
    
    try:
        # 调用Bedrock Agent
        print("发送请求到Bedrock Agent...")
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=SESSION_ID,
            inputText=prompt,
            enableTrace=True
        )
        
        print("\n响应元数据:", response['ResponseMetadata'])
        
        # 处理流式响应
        print("\n--- 开始处理响应流 ---\n")
        
        final_response = ""
        
        for event in response['completion']:
            event_type = list(event.keys())[0] if event else None
            
            if event_type == 'trace':
                trace_data = event['trace']
                print("\n--- 跟踪信息 ---")
                print(json.dumps(trace_data, indent=2))
                
                # 检查是否有错误
                if 'error' in trace_data:
                    print(f"\n错误: {trace_data['error']}")
            
            elif event_type == 'chunk':
                chunk_data = event['chunk']['bytes'].decode('utf-8')
                print(chunk_data, end='')
                final_response += chunk_data
        
        print("\n--- 完整响应 ---")
        print(final_response)
        
        # 保存生成的报告
        save_to_file(final_response, "generated_care_report.txt")
        
        print("\n--- 响应处理完成 ---\n")
        
    except Exception as e:
        print(f"调用Bedrock Agent时出错: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("测试完成")

if __name__ == "__main__":
    main()