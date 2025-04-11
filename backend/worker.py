import os
import sys
import logging
import time
import signal
import threading

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.rabbitmq_tasks import setup_document_processor


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# 全局变量，用于控制工作线程
running = True


def signal_handler(signum, frame):
    """处理信号，优雅地关闭工作线程"""
    global running
    logging.info(f"Received signal {signum}, shutting down...")
    running = False


def start_worker():
    """启动工作线程"""
    try:
        # 启动文档处理器
        logging.info("Starting document processor...")
        setup_document_processor()
    except Exception as e:
        logging.error(f"Error in document processor: {e}")


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info("Starting worker process...")
    
    # 在单独的线程中启动工作线程
    worker_thread = threading.Thread(target=start_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    # 主线程保持活跃状态，直到收到信号
    try:
        while running and worker_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    
    logging.info("Worker shutdown complete")


if __name__ == "__main__":
    main() 