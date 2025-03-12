import sys
import logging
from PySide6.QtWidgets import QApplication
from sqlexec.ui.main_window import MainWindow
from sqlexec.config.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """应用程序入口"""
    logger.info("Starting SQL Exec application...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 