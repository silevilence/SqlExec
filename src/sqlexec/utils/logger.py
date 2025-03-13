import logging
import logging.handlers
import os
from pathlib import Path
from typing import NoReturn


def setup_logger() -> None:
    """配置日志系统"""
    # 创建日志目录
    log_dir = Path.home() / ".sqlexec" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "sqlexec.log"

    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 创建文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到根日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 设置第三方库的日志级别
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('PySide6').setLevel(logging.WARNING)
