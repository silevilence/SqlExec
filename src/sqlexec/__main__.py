import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from sqlexec.ui.main_window import MainWindow
from sqlexec.config.config_manager import ConfigManager
from sqlexec.utils.logger import setup_logger

def main():
    # 设置日志
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting SQL Exec application...")

    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.load_config()

    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("SQL Exec")
    app.setApplicationVersion("0.1.0")

    # 创建主窗口
    main_window = MainWindow(config)
    main_window.show()

    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 