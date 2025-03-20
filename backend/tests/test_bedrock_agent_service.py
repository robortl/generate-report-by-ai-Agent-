import os
import sys
import json
import logging
import argparse
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Agent服务
from app.services.agent_service import generate_report, BedrockAgentService

# 导入存储服务
from app.services.storage import (
    save_report_to_dynamodb,
    get_report_from_dynamodb,
    save_file_to_s3,
    get_file_content_from_s3
)

def create_test_file(content, file_name=None):
    """创建测试文件"""
    if file_name is None:
        file_name = f"test_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"创建测试文件: {file_path}")
    return file_path, content

def test_agent_service():
    """测试Bedrock Agent服务"""
    # 创建测试文件
    test_content = """
    会议主题：2023年第四季度销售策略会议
    日期：2023年10月15日
    参与者：张三（销售总监）、李四（市场经理）、王五（产品经理）、赵六（财务主管）

    会议要点：
    1. 张三介绍了第三季度销售情况，总销售额达到1500万元，比去年同期增长15%。
    2. 主要增长来自于华东地区，特别是上海和杭州市场。
    3. 李四提出第四季度市场推广计划，包括增加社交媒体广告投入和参加行业展会。
    4. 王五介绍了两款新产品的上市计划，预计11月初发布。
    5. 赵六报告了第三季度的成本控制情况，建议第四季度适当增加营销预算。

    决定事项：
    1. 第四季度销售目标定为1800万元。
    2. 增加华东地区的销售人员配置，从8人增加到12人。
    3. 批准了20万元的额外营销预算用于年终促销活动。
    4. 新产品发布会定于11月15日在上海举行。
    5. 下次跟进会议定于11月1日。

    行动项目：
    1. 张三负责制定详细的区域销售计划（截止日期：10月25日）
    2. 李四准备营销活动方案和预算明细（截止日期：10月20日）
    3. 王五协调产品发布会的各项准备工作（截止日期：11月10日）
    4. 赵六审核并分配增加的预算（截止日期：10月30日）
    """
    
    file_path, content = create_test_file(test_content)
    
    try:
        # 创建Bedrock Agent服务实例
        agent_service = BedrockAgentService()
        
        # 测试直接调用模型生成报告
        logger.info("测试直接调用模型生成报告...")
        model_report = agent_service._generate_report_with_model(content)
        logger.info(f"模型生成报告成功，长度: {len(model_report)}")
        logger.info(f"报告前200个字符: {model_report[:200]}...")
        
        # 保存报告到DynamoDB和S3
        report_id = f"test-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        file_id = f"test-file-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # 保存文件到S3
        s3_key = save_file_to_s3(content, file_id)
        logger.info(f"文件保存到S3，键: {s3_key}")
        
        # 保存报告到DynamoDB
        report_data = {
            'report_id': report_id,
            'file_id': file_id,
            'title': '测试报告',
            'content': model_report,
            'status': 'completed',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        save_report_to_dynamodb(report_data)
        logger.info(f"报告保存到DynamoDB，ID: {report_id}")
        
        # 获取报告
        saved_report = get_report_from_dynamodb(report_id)
        logger.info(f"从DynamoDB获取报告: {saved_report}")
        
        # 测试使用Agent生成报告
        try:
            logger.info("测试使用Agent生成报告...")
            agent_report = agent_service._generate_report_with_agent(content)
            logger.info(f"Agent生成报告成功，长度: {len(agent_report)}")
            logger.info(f"报告前200个字符: {agent_report[:200]}...")
            
            # 保存Agent生成的报告
            agent_report_id = f"agent-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            agent_report_data = {
                'report_id': agent_report_id,
                'file_id': file_id,
                'title': 'Agent测试报告',
                'content': agent_report,
                'status': 'completed',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            save_report_to_dynamodb(agent_report_data)
            logger.info(f"Agent报告保存到DynamoDB，ID: {agent_report_id}")
            
        except Exception as e:
            logger.error(f"使用Agent生成报告失败: {str(e)}")
        
        # 测试通用函数生成报告
        logger.info("测试通用函数生成报告...")
        general_report = generate_report(content)
        logger.info(f"通用函数生成报告成功，长度: {len(general_report)}")
        logger.info(f"报告前200个字符: {general_report[:200]}...")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise e
    finally:
        # 清理测试文件
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"删除测试文件: {file_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试Bedrock Agent服务')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("启用调试日志")
    
    # 运行测试
    test_agent_service()

if __name__ == "__main__":
    main() 