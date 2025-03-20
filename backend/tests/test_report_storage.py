import os
import sys
import json
import uuid
import logging
import boto3
import io
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

# 导入服务
from app.services.storage import (
    get_metadata_from_dynamodb,
    get_file_content_by_id,
    save_report,
    get_report_from_dynamodb,
    update_report_in_dynamodb,
    delete_report_from_dynamodb,
    upload_file_to_s3,
    save_metadata_to_dynamodb,
    update_metadata_in_dynamodb,
    S3_BUCKET_NAME,
    DYNAMODB_TABLE
)
from app.services.agent_service import generate_report

def create_test_file():
    """创建测试文件并上传到S3"""
    logger.info("创建测试文件并上传到S3")
    
    # 测试文本
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
    
    # 生成文件ID
    file_id = f"test-file-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # 上传文件到S3
    file_obj = io.BytesIO(test_content.encode('utf-8'))
    s3_key = f"uploads/{file_id}.txt"
    upload_file_to_s3(file_obj, s3_key)
    logger.info(f"文件已上传到S3，键: {s3_key}")
    
    # 创建文件元数据
    file_metadata = {
        'file_id': file_id,
        'filename': f"test_meeting_{datetime.now().strftime('%Y%m%d')}.txt",
        'category': 'meeting',
        'status': 'uploaded',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        's3_key': s3_key,
        's3_url': f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    }
    
    # 保存文件元数据到DynamoDB
    save_metadata_to_dynamodb(file_metadata)
    logger.info(f"文件元数据已保存到DynamoDB")
    
    # 验证文件元数据是否正确保存到report_files表
    verify_file_metadata(file_id, file_metadata)
    
    return file_id, file_metadata, test_content

def verify_file_metadata(file_id, expected_metadata):
    """验证文件元数据是否正确保存到report_files表"""
    logger.info(f"=== 验证文件元数据 (ID: {file_id}) ===")
    
    # 从DynamoDB获取文件元数据
    metadata = get_metadata_from_dynamodb(file_id)
    if not metadata:
        logger.error(f"文件元数据在DynamoDB中不存在: {file_id}")
        return False
    
    logger.info(f"从DynamoDB获取文件元数据成功: {file_id}")
    logger.info(f"文件名: {metadata.get('filename')}")
    logger.info(f"分类: {metadata.get('category')}")
    logger.info(f"状态: {metadata.get('status')}")
    logger.info(f"S3键: {metadata.get('s3_key')}")
    
    # 验证关键字段
    for key in ['filename', 'category', 'status', 's3_key', 's3_url']:
        if metadata.get(key) != expected_metadata.get(key):
            logger.error(f"文件元数据字段不匹配: {key}, 期望: {expected_metadata.get(key)}, 实际: {metadata.get(key)}")
            return False
    
    logger.info("文件元数据验证成功")
    return True

def test_save_report():
    """测试保存报告到S3和DynamoDB"""
    logger.info("=== 测试保存报告到S3和DynamoDB ===")
    
    # 创建测试文件
    file_id, file_metadata, file_content = create_test_file()
    
    # 生成报告ID
    report_id = str(uuid.uuid4())
    logger.info(f"生成报告ID: {report_id}")
    
    # 创建报告数据
    report_data = {
        'report_id': report_id,
        'file_id': file_id,
        'title': f"测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # 保存报告元数据（状态为处理中）
    save_report(report_data)
    logger.info(f"报告元数据已保存到DynamoDB，状态: processing")
    
    # 生成报告内容
    logger.info("生成报告内容...")
    try:
        # 使用模拟内容，避免实际调用Bedrock
        report_content = f"""# 会议摘要报告

## 基本信息
- 会议日期：2023年10月15日
- 参会人员：张三、李四、王五、赵六
- 会议主题：2023年第四季度销售策略会议

## 主要内容
1. 第三季度销售额达到1500万元，同比增长15%
2. 华东地区是主要增长来源
3. 第四季度将增加社交媒体广告投入和参加行业展会
4. 两款新产品将于11月初发布
5. 第四季度将适当增加营销预算

## 决策事项
1. 第四季度销售目标：1800万元
2. 华东地区销售人员增加至12人
3. 年终促销活动追加20万元预算
4. 新产品发布会：11月15日在上海
5. 下次跟进会议：11月1日

## 行动项目
1. 张三：制定区域销售计划（10月25日前）
2. 李四：准备营销活动方案（10月20日前）
3. 王五：协调产品发布会准备（11月10日前）
4. 赵六：审核分配预算（10月30日前）
"""
        
        # 更新报告内容和状态
        report_data['content'] = report_content
        report_data['status'] = 'completed'
        report_data['updated_at'] = datetime.now().isoformat()
        
        # 保存报告到DynamoDB和S3
        update_report_in_dynamodb(report_data)
        logger.info(f"报告内容已更新到DynamoDB和S3，状态: completed")
        
        # 验证报告是否正确保存
        verify_report_storage(report_id)
        
        # 模拟API行为，更新文件元数据中的report_id字段
        file_metadata['report_id'] = report_id
        file_metadata['status'] = 'processed'
        file_metadata['updated_at'] = datetime.now().isoformat()
        update_metadata_in_dynamodb(file_metadata)
        logger.info(f"文件元数据已更新，添加report_id: {report_id}")
        
        # 验证文件元数据中的report_id是否已更新
        verify_file_metadata_update(file_id, report_id)
        
        return report_id, file_id
        
    except Exception as e:
        logger.error(f"生成报告时出错: {str(e)}")
        raise e

def verify_file_metadata_update(file_id, report_id):
    """验证文件元数据中的report_id是否已更新"""
    logger.info(f"=== 验证文件元数据更新 (ID: {file_id}) ===")
    
    # 从DynamoDB获取文件元数据
    metadata = get_metadata_from_dynamodb(file_id)
    if not metadata:
        logger.error(f"文件元数据在DynamoDB中不存在: {file_id}")
        return False
    
    # 验证report_id字段
    if 'report_id' in metadata:
        if metadata['report_id'] == report_id:
            logger.info(f"文件元数据中的report_id已正确更新: {report_id}")
            return True
        else:
            logger.warning(f"文件元数据中的report_id不匹配: 期望: {report_id}, 实际: {metadata.get('report_id')}")
            return False
    else:
        logger.warning(f"文件元数据中没有report_id字段")
        return False

def verify_report_storage(report_id):
    """验证报告是否正确保存到S3和DynamoDB"""
    logger.info(f"=== 验证报告存储 (ID: {report_id}) ===")
    
    # 从DynamoDB获取报告
    report = get_report_from_dynamodb(report_id)
    if not report:
        logger.error(f"报告在DynamoDB中不存在: {report_id}")
        return False
    
    logger.info(f"从DynamoDB获取报告成功: {report_id}")
    logger.info(f"报告标题: {report.get('title')}")
    logger.info(f"报告状态: {report.get('status')}")
    logger.info(f"S3键: {report.get('s3_key')}")
    
    # 验证报告内容
    if 'content' not in report:
        logger.error(f"报告内容不存在")
        return False
    
    logger.info(f"报告内容长度: {len(report.get('content'))} 字符")
    logger.info(f"报告内容前100个字符: {report.get('content')[:100]}")
    
    # 验证S3中的报告
    s3_key = report.get('s3_key')
    if not s3_key:
        logger.error(f"报告S3键不存在")
        return False
    
    try:
        # 直接从S3获取内容
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        s3_content = response['Body'].read().decode('utf-8')
        
        logger.info(f"从S3获取报告内容成功: {s3_key}")
        logger.info(f"S3内容长度: {len(s3_content)} 字符")
        logger.info(f"S3内容前100个字符: {s3_content[:100]}")
        
        # 验证内容是否一致
        if s3_content == report.get('content'):
            logger.info("DynamoDB和S3中的报告内容一致")
            return True
        else:
            logger.error("DynamoDB和S3中的报告内容不一致")
            return False
    except Exception as e:
        logger.error(f"从S3获取报告内容时出错: {str(e)}")
        return False

def list_s3_reports():
    """列出S3中的报告文件"""
    logger.info("=== 列出S3中的报告文件 ===")
    
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix='reports/'
        )
        
        if 'Contents' in response:
            files = response['Contents']
            logger.info(f"S3中共有 {len(files)} 个报告文件")
            
            for file in files:
                logger.info(f"  - {file['Key']} ({file['Size']} 字节)")
            
            return files
        else:
            logger.warning(f"S3中没有报告文件")
            return []
    except Exception as e:
        logger.error(f"列出S3报告文件时出错: {str(e)}")
        return []

def list_dynamodb_reports():
    """列出DynamoDB中的报告"""
    logger.info("=== 列出DynamoDB中的报告 ===")
    
    try:
        # 直接从DynamoDB获取
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{DYNAMODB_TABLE}-reports")
        response = table.scan()
        reports = response.get('Items', [])
        
        logger.info(f"DynamoDB中共有 {len(reports)} 个报告")
        for report in reports:
            logger.info(f"  - {report.get('report_id')} | {report.get('title')} | {report.get('status')}")
        
        return reports
    except Exception as e:
        logger.error(f"从DynamoDB获取报告时出错: {str(e)}")
        return []

def list_dynamodb_files():
    """列出DynamoDB中的文件元数据"""
    logger.info("=== 列出DynamoDB中的文件元数据 ===")
    
    try:
        # 直接从DynamoDB获取
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(f"{DYNAMODB_TABLE}-files")
        response = table.scan()
        files = response.get('Items', [])
        
        logger.info(f"DynamoDB中共有 {len(files)} 个文件元数据")
        for file in files:
            logger.info(f"  - {file.get('file_id')} | {file.get('filename')} | {file.get('status')} | 报告ID: {file.get('report_id', 'None')}")
        
        return files
    except Exception as e:
        logger.error(f"从DynamoDB获取文件元数据时出错: {str(e)}")
        return []

def cleanup_test_data(report_id, file_id):
    """清理测试数据"""
    logger.info("=== 清理测试数据 ===")
    
    try:
        # 删除报告
        delete_report_from_dynamodb(report_id)
        logger.info(f"报告已删除: {report_id}")
        
        # 删除文件（可选）
        # delete_file_from_dynamodb(file_id)
        # logger.info(f"文件已删除: {file_id}")
        
        return True
    except Exception as e:
        logger.error(f"清理测试数据时出错: {str(e)}")
        return False

def main():
    """主函数"""
    try:
        logger.info("开始测试报告存储")
        
        # 列出当前的报告和文件
        list_s3_reports()
        list_dynamodb_reports()
        list_dynamodb_files()
        
        # 测试保存报告
        report_id, file_id = test_save_report()
        
        # 再次列出报告和文件，验证新报告和文件是否已添加
        list_s3_reports()
        list_dynamodb_reports()
        list_dynamodb_files()
        
        # 清理测试数据（可选）
        # cleanup_test_data(report_id, file_id)
        
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 