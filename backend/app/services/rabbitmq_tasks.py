import json
import logging
from typing import Dict, Any

from app.db.session import get_rabbitmq_connection, SessionLocal
from app.services.document_processor import process_document


def submit_document_for_processing(document_id: int, file_path: str, file_type: str) -> None:
    """
    将文档提交到RabbitMQ队列进行异步处理
    """
    try:
        # 建立RabbitMQ连接
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # 声明队列
        channel.queue_declare(queue='document_processing', durable=True)
        
        # 准备消息
        message = {
            'document_id': document_id,
            'file_path': file_path,
            'file_type': file_type
        }
        
        # 发布消息
        channel.basic_publish(
            exchange='',
            routing_key='document_processing',
            body=json.dumps(message),
            properties=channel.basic_publish_pika_properties(
                # 持久化消息，确保消息不会在RabbitMQ重启时丢失
                delivery_mode=2  
            )
        )
        
        logging.info(f"Document {document_id} submitted for processing")
        
        # 关闭连接
        connection.close()
        
    except Exception as e:
        logging.error(f"Error submitting document to processing queue: {e}")
        # 如果RabbitMQ不可用，回退到直接处理
        logging.info("Falling back to direct processing")
        db = SessionLocal()
        try:
            process_document(document_id, file_path, file_type, db)
        finally:
            db.close()


def setup_document_processor() -> None:
    """
    设置文档处理器作为RabbitMQ消费者
    """
    try:
        # 建立RabbitMQ连接
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        # 声明队列
        channel.queue_declare(queue='document_processing', durable=True)
        
        # 设置QoS，防止一次分发过多任务给一个worker
        channel.basic_qos(prefetch_count=1)
        
        # 定义回调函数来处理消息
        def callback(ch, method, properties, body):
            message = json.loads(body)
            document_id = message['document_id']
            file_path = message['file_path']
            file_type = message['file_type']
            
            logging.info(f"Processing document {document_id}")
            
            db = SessionLocal()
            try:
                result = process_document(document_id, file_path, file_type, db)
                if result['success']:
                    logging.info(f"Document {document_id} processed successfully")
                else:
                    logging.error(f"Failed to process document {document_id}: {result.get('error')}")
            finally:
                db.close()
            
            # 确认消息已处理
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        # 注册消费者
        channel.basic_consume(queue='document_processing', on_message_callback=callback)
        
        logging.info("Document processor started. Waiting for messages...")
        
        # 开始消费消息
        channel.start_consuming()
        
    except Exception as e:
        logging.error(f"Error setting up document processor: {e}") 