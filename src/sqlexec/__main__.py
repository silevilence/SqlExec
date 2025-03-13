import sys
import logging
from PySide6.QtWidgets import QApplication
from sqlexec.ui.main_window import MainWindow
from sqlexec.config.config_manager import ConfigManager
from sqlexec.utils.logger import setup_logger


def main() -> None:
    """应用程序入口"""
    # 初始化日志系统
    setup_logger()

    logger = logging.getLogger(__name__)
    logger.info("Starting SQL Exec application...")

    app = QApplication(sys.argv)

    # 创建主窗口
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
