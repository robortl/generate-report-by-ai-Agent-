import os
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
import boto3
import json

from app.services.model_service import get_model_by_id
from app.services.storage import (
    get_metadata_from_dynamodb,
    get_file_content_by_id,
    save_report,
    get_report_from_dynamodb,
    update_report_in_dynamodb,
    delete_report_from_dynamodb,
    update_metadata_in_dynamodb,
    S3_BUCKET_NAME,
    DYNAMODB_TABLE
)
from app.services.agent_service import generate_report

# 配置日志
def setup_logging():
    """设置日志配置"""
    # 创建logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # 确保没有重复的处理器
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        logger.addHandler(console_handler)
    
    return logger

# 获取logger实例
logger = setup_logging()

# 创建蓝图 - 修改url_prefix以匹配API文档
report_bp = Blueprint('report', __name__, url_prefix='/api/report')

@report_bp.route('/generate', methods=['POST'])
def create_report():
    """创建报告"""
    data = request.json
    file_id = data.get('file_id')
    prompt = data.get('prompt')
    model_id = data.get('model_id')
    
    if not file_id:
        return jsonify({'error': 'Missing file_id'}), 400
    
    # 获取文件元数据
    file_metadata = get_metadata_from_dynamodb(file_id)
    if not file_metadata:
        return jsonify({'error': f'File with ID {file_id} not found'}), 404
    
    # 获取文件内容
    file_content = get_file_content_by_id(file_id)
    if not file_content:
        return jsonify({'error': f'Content for file with ID {file_id} not found'}), 404
    
    # 生成报告ID
    report_id = str(uuid.uuid4())
    
    # 创建报告数据
    report_data = {
        'report_id': report_id,
        'file_id': file_id,
        'prompt': prompt,
        'model_id': model_id,
        'title': f"AIエージェントのモデルIDはanthropic.claude-3-5-sonnet-20240620-v1:0",
        'status': 'processing',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        # 保存初始报告状态到DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1'))
        table = dynamodb.Table(f"{DYNAMODB_TABLE}_reports")
        table.put_item(Item=report_data)
        logger.info(f"初始报告状态已保存到DynamoDB，状态: processing")
        
        # 调用Bedrock Agent生成报告
        logger.info(f"调用Bedrock Agent生成报告，文件ID: {file_id}")
        report_content = generate_report(file_content, prompt, model_id)
        
        # 提取摘要（取第一段非空内容作为摘要）
        content_lines = report_content.split('\n')
        summary = ''
        
        # 查找第一段非空内容作为摘要
        for line in content_lines:
            if line.strip() and not line.startswith(('#', '-', '•', '1.', '2.', '3.', '4.', '5.')):
                summary = line.strip()
                break
        
        # 如果没有找到合适的摘要，使用前100个字符
        if not summary:
            summary = report_content[:100] + '...' if len(report_content) > 100 else report_content
        
        # 保存报告内容到S3（保持原始Markdown格式）
        s3_client = boto3.client('s3', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1'))
        s3_key = f"reports/{report_id}.txt"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=report_content.encode('utf-8'),
            ContentType='text/markdown; charset=utf-8'
        )
        logger.info(f"报告内容已保存到S3，键: {s3_key}")
        
        # 更新DynamoDB中的报告状态
        report_data.update({
            'status': 'completed',
            'report_s3_key': s3_key,
            'summary': summary,  # 添加摘要字段
            'updated_at': datetime.now().isoformat()
        })
        table.put_item(Item=report_data)
        logger.info(f"报告状态已更新到DynamoDB，状态: completed")
        
        # 更新文件元数据中的report_id字段
        file_metadata.update({
            'report_id': report_id,
            'status': 'processed',
            'updated_at': datetime.now().isoformat()
        })
        update_metadata_in_dynamodb(file_metadata)
        logger.info(f"文件元数据已更新，添加report_id: {report_id}")
        
        logger.info(f"报告生成成功，报告ID: {report_id}")
        return jsonify({
            'message': 'Report generated successfully',
            'report_id': report_id,
            'status': 'completed'
        }), 201
        
    except Exception as e:
        # 更新报告状态为失败
        logger.error(f"报告生成失败: {str(e)}")
        report_data.update({
            'status': 'failed',
            'error': str(e),
            'updated_at': datetime.now().isoformat()
        })
        table.put_item(Item=report_data)
        
        return jsonify({
            'error': f'Failed to generate report: {str(e)}'
        }), 500

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id):
    """获取报告"""
    try:
        logger.info(f"[REPORT_GET] 开始获取报告 | 报告ID: {report_id}")
        
        # 获取报告数据
        response = get_report_from_dynamodb(report_id)
        if not response or 'Item' not in response:
            logger.error(f"[REPORT_GET] 未找到报告元数据 | 报告ID: {report_id}")
            return jsonify({'error': f'Report with ID {report_id} not found'}), 404
            
        report_metadata = response['Item']
        logger.info(f"[REPORT_GET] 报告元数据 : {report_metadata}")
        
        # 从S3获取报告内容
        s3_key = report_metadata.get('report_s3_key')
        if not s3_key:
            logger.error(f"[REPORT_GET] 元数据中没有S3键 | 报告ID: {report_id}")
            return jsonify({'error': f'Report S3 key not found for ID {report_id}'}), 404
            
        # 创建S3客户端
        s3_client = boto3.client('s3', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1'))
        
        try:
            # 从S3获取报告内容
            response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            report_content = response['Body'].read().decode('utf-8')
            
            # 构建响应数据
            report_data = {
                'report_id': report_id,
                'content': report_content,  # 完整的报告内容
                'summary': report_metadata.get('summary', ''),  # 报告摘要
                'file_id': report_metadata.get('file_id'),
                'status': report_metadata.get('status', 'completed'),
                'title': report_metadata.get('title'),
                'created_at': report_metadata.get('created_at'),
                'updated_at': report_metadata.get('updated_at'),
                'model_id': report_metadata.get('model_id'),
                'prompt': report_metadata.get('prompt')
            }
            
            logger.info(f"[REPORT_GET] 报告获取成功 | 报告ID: {report_id}")
            return jsonify(report_data), 200
            
        except Exception as e:
            logger.error(f"[REPORT_GET] 从S3获取报告失败: {str(e)}")
            return jsonify({'error': f'Failed to get report from S3: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"[REPORT_GET] 获取报告时发生错误: {str(e)}")
        return jsonify({'error': f'Error getting report: {str(e)}'}), 500

@report_bp.route('/<report_id>', methods=['PUT'])
def update_report(report_id):
    """更新报告"""
    data = request.json
    
    # 检查是否有报告内容
    if 'content' not in data:
        return jsonify({'error': 'Missing report content'}), 400
    
    # 获取现有报告
    report = get_report_from_dynamodb(report_id)
    if not report:
        return jsonify({'error': f'Report with ID {report_id} not found'}), 404
    
    # 更新报告内容
    report['content'] = data['content']
    report['updated_at'] = datetime.now().isoformat()
    
    # 如果有标题，也更新标题
    if 'title' in data:
        report['title'] = data['title']
    
    # 保存更新后的报告
    update_report_in_dynamodb(report)
    
    return jsonify({
        'message': 'Report updated successfully',
        'report_id': report_id
    }), 200

@report_bp.route('/<report_id>/regenerate', methods=['POST'])
def regenerate_report(report_id):
    """重新生成报告"""
    data = request.json
    prompt = data.get('prompt')
    model_id = data.get('model_id')
    
    # 获取现有报告
    report = get_report_from_dynamodb(report_id)
    if not report:
        return jsonify({'error': f'Report with ID {report_id} not found'}), 404
        
    try:
        # 获取文件内容
        file_content = get_file_content_by_id(report['file_id'])
        if not file_content:
            return jsonify({'error': f'Content for file with ID {report["file_id"]} not found'}), 404
            
        # 调用Bedrock Agent重新生成报告
        logger.info(f"重新生成报告，报告ID: {report_id}")
        report_content = generate_report(file_content, prompt, model_id)
        
        # 更新报告内容和状态
        report['content'] = report_content
        report['prompt'] = prompt
        report['model_id'] = model_id
        report['status'] = 'completed'
        report['updated_at'] = datetime.now().isoformat()
        
        # 保存更新后的报告
        update_report_in_dynamodb(report)
        
        return jsonify({
            'message': 'Report regenerated successfully',
            'report_id': report_id
        }), 200
        
    except Exception as e:
        logger.error(f"报告重新生成失败: {str(e)}")
        report['status'] = 'failed'
        report['error'] = str(e)
        report['updated_at'] = datetime.now().isoformat()
        update_report_in_dynamodb(report)
        
        return jsonify({
            'error': f'Failed to regenerate report: {str(e)}'
        }), 500

@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id):
    """下载报告"""
    format = request.args.get('format', 'pdf')
    
    try:
        # 获取报告数据
        response = get_report_from_dynamodb(report_id)
        if not response or 'Item' not in response:
            return jsonify({'error': f'Report with ID {report_id} not found'}), 404
            
        report_metadata = response['Item']
        file_id = report_metadata.get('file_id')
        
        # 如果是下载原始文件
        if format == 's3':
            if not file_id:
                return jsonify({'error': 'File ID not found in report metadata'}), 404
                
            # 获取文件元数据
            file_metadata = get_metadata_from_dynamodb(file_id)
            if not file_metadata:
                return jsonify({'error': f'File metadata not found for ID {file_id}'}), 404
                
            s3_key = file_metadata.get('s3_key')
            if not s3_key:
                return jsonify({'error': f'S3 key not found for file with ID {file_id}'}), 404
                
            # 创建S3客户端
            s3_client = boto3.client('s3', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1'))
            
            # 从S3获取文件
            response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            file_content = response['Body'].read()
            
            # 设置响应头
            filename = file_metadata.get('original_filename', f"file_{file_id}")
            headers = {
                'Content-Type': response.get('ContentType', 'application/octet-stream'),
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
            
            return file_content, 200, headers
            
        # 从S3获取报告内容
        s3_key = report_metadata.get('report_s3_key')
        if not s3_key:
            return jsonify({'error': f'Report S3 key not found for ID {report_id}'}), 404
            
        # 创建S3客户端
        s3_client = boto3.client('s3', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1'))
        
        # 从S3获取报告内容
        s3_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        report_content = s3_response['Body'].read().decode('utf-8')
        
        if format.lower() == 'pdf':
            from fpdf import FPDF
            
            # 创建PDF对象，使用A4大小
            pdf = FPDF(format='A4')
            pdf.add_page()
            
            # 添加字体支持
            fonts_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
            pdf.add_font('SimSun', '', os.path.join(fonts_dir, 'SimSun.ttf'), uni=True)  # 中文
            pdf.add_font('MSMincho', '', os.path.join(fonts_dir, 'MSMincho.ttf'), uni=True)  # 日文
            pdf.add_font('Arial', '', os.path.join(fonts_dir, 'Arial.ttf'), uni=True)  # 英文
            
            # 设置页边距
            margin = 20
            pdf.set_margins(margin, margin, margin)
            
            # 添加标题
            pdf.set_font('Arial', 'B', 16)
            title = report_metadata.get('title', 'Report')
            pdf.cell(0, 15, title, 0, 1, 'C')
            pdf.ln(5)
            
            # 添加元数据
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, f"Report ID: {report_id}", 0, 1, 'L')
            pdf.cell(0, 8, f"Created: {report_metadata.get('created_at', '')[:10]}", 0, 1, 'L')
            pdf.ln(5)
            
            # 直接使用报告内容，不需要JSON解析
            content = report_content
            
            # 分段处理内容
            paragraphs = content.split('\n')
            current_font = None
            
            for paragraph in paragraphs:
                # 跳过空行
                if not paragraph.strip():
                    pdf.ln(5)
                    continue
                
                # 检测是否是标题行
                is_title = False
                if paragraph.startswith('#'):
                    is_title = True
                    # 根据#的数量确定标题级别
                    level = len(paragraph.split()[0])
                    if level == 1:
                        pdf.set_font('Arial', 'B', 14)
                    elif level == 2:
                        pdf.set_font('Arial', 'B', 12)
                    else:
                        pdf.set_font('Arial', 'B', 11)
                    # 移除#号
                    paragraph = paragraph.lstrip('#').strip()
                else:
                    # 普通段落使用正常字体
                    pdf.set_font('Arial', '', 10)
                
                # 设置段落格式
                if is_title:
                    pdf.ln(5)
                    pdf.multi_cell(0, 8, paragraph.strip(), 0, 'L')
                    pdf.ln(3)
                else:
                    # 对于列表项，添加缩进
                    if paragraph.strip().startswith(('-', '•')):
                        pdf.cell(10, 8, '', 0, 0)  # 添加缩进
                        pdf.multi_cell(0, 8, paragraph.strip(), 0, 'L')
                    else:
                        pdf.multi_cell(0, 8, paragraph.strip(), 0, 'L')
                    pdf.ln(2)
            
            # 生成PDF文件内容
            try:
                pdf_output = pdf.output(dest='S').encode('latin-1')
            except UnicodeEncodeError:
                # 如果出现编码错误，尝试使用替代字符
                pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')
            
            # 设置响应头
            filename = f"report_{report_id}.pdf"
            headers = {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
            
            return pdf_output, 200, headers
            
        else:
            return jsonify({'error': f'Unsupported format: {format}'}), 400
            
    except Exception as e:
        logger.error(f"[REPORT_DOWNLOAD] 下载报告时发生错误: {str(e)}")
        return jsonify({'error': f'Error downloading report: {str(e)}'}), 500

@report_bp.route('/compare', methods=['POST'])
def compare_report():
    """比较不同模型生成的报告"""
    data = request.json
    report_id = data.get('report_id')
    model_id = data.get('model_id')
    
    if not report_id or not model_id:
        logger.error(f"[REPORT_COMPARE] 缺少必要参数: report_id={report_id}, model_id={model_id}")
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # 获取原始报告信息
    report_response = get_report_from_dynamodb(report_id)
    if not report_response or 'Item' not in report_response:
        logger.error(f"[REPORT_COMPARE] 未找到原始报告: {report_id}")
        return jsonify({'error': f'Report with ID {report_id} not found'}), 404
    
    # 获取原始报告数据
    original_report = report_response['Item']
    file_id = original_report.get('file_id')
    original_prompt = original_report.get('prompt')
    
    if not file_id:
        logger.error(f"[REPORT_COMPARE] 原始报告中未找到file_id: {report_id}")
        return jsonify({'error': 'File ID not found in original report'}), 404
    
    # 获取文件内容
    file_content = get_file_content_by_id(file_id)
    if not file_content:
        logger.error(f"[REPORT_COMPARE] 未找到文件内容: {file_id}")
        return jsonify({'error': f'Content for file with ID {file_id} not found'}), 404
    
    # 使用相同的prompt生成新报告
    try:
        logger.info(f"[REPORT_COMPARE] 开始生成比较报告: 文件ID={file_id}, 模型ID={model_id}")
        # 检查原始提示词，如果没有包含文件相关的提示，添加使用文件内容的提示
        prompt_to_use = original_prompt
        if original_prompt and "文件" not in original_prompt and "内容" not in original_prompt and "记录" not in original_prompt and "报告" not in original_prompt:
            # 如果提示词看起来不像是要求处理文件内容，增加提示
            prompt_to_use = f"{original_prompt}\n\n请基于上传的文件内容生成分析报告。"
            logger.info(f"[REPORT_COMPARE] 在提示词中添加了使用文件内容的明确指示: {prompt_to_use}")
            
        # 调用Bedrock Agent生成新报告
        report_content = generate_report(file_content, prompt_to_use, model_id)
        
        # 从原始报告的模型名称
        original_model_id = original_report.get('model_id', '未知模型')
        
        # 获取新模型的详细信息
        original_model_info = get_model_by_id(original_model_id)
        new_model_info = get_model_by_id(model_id)
        
        # 构造简单的响应结构
        response = {
            'content': report_content,
            'model_id': model_id,
            'model_name': new_model_info.get('name', model_id) if new_model_info else model_id,
            'original_model_id': original_model_id,
            'original_model_name': original_model_info.get('name', original_model_id) if original_model_info else original_model_id,
            'file_id': file_id,
            'report_id': report_id,
            'generated_at': datetime.now().isoformat()
        }
        
        # 提取摘要（取第一段非空内容作为摘要）
        content_lines = report_content.split('\n')
        summary = ''
        for line in content_lines:
            if line.strip() and not line.startswith(('#', '-', '•', '1.', '2.', '3.', '4.', '5.')):
                summary = line.strip()
                break
        
        # 如果没有找到合适的摘要，使用前100个字符
        if not summary:
            summary = report_content[:100] + '...' if len(report_content) > 100 else report_content
        
        response['summary'] = summary
        
        logger.info(f"[REPORT_COMPARE] 比较报告生成成功: {model_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"[REPORT_COMPARE] 生成比较报告失败: {str(e)}")
        return jsonify({'error': f'Failed to generate comparison report: {str(e)}'}), 500


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """获取报告列表"""
    try:
        logger.info("[REPORT_LIST] 开始获取报告列表")
        
        # 创建DynamoDB客户端
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_DEFAULT_REGION', 'ap-northeast-1'))
        table = dynamodb.Table(f"{DYNAMODB_TABLE}_reports")
        
        # 获取所有报告
        response = table.scan()
        reports = response.get('Items', [])
        
        logger.info(f"[REPORT_LIST] 从DynamoDB获取到 {len(reports)} 个报告")
        
        # 处理报告列表，只返回必要的字段
        processed_reports = []
        for report in reports:
            try:
                processed_report = {
                    'report_id': report.get('report_id'),
                    'file_id': report.get('file_id'),
                    'title': report.get('title'),
                    'status': report.get('status'),
                    'created_at': report.get('created_at'),
                    'updated_at': report.get('updated_at'),
                    'summary': report.get('summary', '')
                }
                # 验证必要字段
                if not all([processed_report['report_id'], processed_report['title']]):
                    logger.warning(f"[REPORT_LIST] 发现无效的报告数据: {report}")
                    continue
                    
                processed_reports.append(processed_report)
            except Exception as e:
                logger.error(f"[REPORT_LIST] 处理报告数据时出错: {str(e)}")
                logger.error(f"[REPORT_LIST] 问题数据: {report}")
                continue
        
        # 按创建时间降序排序
        processed_reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"[REPORT_LIST] 返回 {len(processed_reports)} 个有效报告")
        
        return jsonify({
            'items': processed_reports,
            'total': len(processed_reports)
        }), 200
        
    except Exception as e:
        logger.error(f"[REPORT_LIST] 获取报告列表失败: {str(e)}")
        return jsonify({
            'error': f'Failed to get reports list: {str(e)}'
        }), 500 