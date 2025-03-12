import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QSystemTrayIcon, QMenu, QMenuBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor
from pathlib import Path

from sqlexec.ui.sidebar import Sidebar
from sqlexec.ui.query_editor import QueryEditor
from sqlexec.ui.settings_dialog import SettingsDialog
from sqlexec.core.db_manager import DatabaseManager

class MainWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.db_manager = DatabaseManager()
        
        self._init_ui()
        self._setup_menu()
        self._setup_tray()
        self._load_connections()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("SQL Exec")
        self.setMinimumSize(1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建侧边栏
        self.sidebar = Sidebar(self)
        splitter.addWidget(self.sidebar)
        
        # 创建查询编辑器
        self.query_editor = QueryEditor(self)
        splitter.addWidget(self.query_editor)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)  # 侧边栏
        splitter.setStretchFactor(1, 4)  # 查询编辑器
        
        main_layout.addWidget(splitter)

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        toggle_sidebar_action = QAction("切换侧边栏", self)
        toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)

    def _setup_tray(self):
        """设置系统托盘"""
        if not self.config.get("general", {}).get("show_system_tray", True):
            return

        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用SVG图标
        icon_path = str(Path(__file__).parent.parent / "resources" / "icons" / "app.svg")
        icon = QIcon(icon_path)
        if icon.isNull():
            # 如果SVG加载失败，创建一个简单的图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#4a90e2"))
            icon = QIcon(pixmap)
        
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _load_connections(self):
        """加载数据库连接"""
        connections = self.config.get("connections", [])
        for conn in connections:
            self.db_manager.add_connection(conn["alias"], conn)
        self.sidebar.refresh_connections()

    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # TODO: 保存设置
            pass

    def _toggle_sidebar(self):
        """切换侧边栏显示状态"""
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def _quit_application(self):
        """退出应用程序"""
        self.db_manager.dispose_all()
        self.tray_icon.hide()
        sys.exit(0)

    def closeEvent(self, event):
        """重写关闭事件"""
        if self.config.get("general", {}).get("show_system_tray", True):
            event.ignore()
            self.hide()
        else:
            self._quit_application() 