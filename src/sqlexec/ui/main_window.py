import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QSystemTrayIcon, QMenu, QMenuBar, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor
from pathlib import Path

from sqlexec.ui.sidebar import Sidebar
from sqlexec.ui.query_editor import QueryEditor
from sqlexec.ui.settings_dialog import SettingsDialog
from sqlexec.core.db_manager import DatabaseManager
from sqlexec.config.config_manager import ConfigManager
from sqlexec.config.settings import Settings
from sqlexec.config.enums import Theme, CloseAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.settings
        self.db_manager = DatabaseManager()
        
        self._init_ui()
        self._setup_menu()
        self._setup_tray()
        self._load_connections()
        self._apply_settings()

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
        if not self.settings.general.show_system_tray:
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
        for conn in self.settings.connections.values():
            self.db_manager.add_connection(conn.alias, {
                "name": conn.name,
                "alias": conn.alias,
                "type": conn.type,
                "connection_string": conn.connection_string,
                "groups": self.settings.get_connection_groups(conn.alias)
            })
        self.sidebar.refresh_connections()

    def _apply_settings(self):
        """应用设置到界面"""
        # 应用主题
        if self.settings.general.theme == Theme.DARK:
            # TODO: 应用深色主题
            pass
        else:
            # TODO: 应用浅色主题
            pass
            
        # 应用系统托盘设置
        if hasattr(self, "tray_icon"):
            if self.settings.general.show_system_tray:
                self.tray_icon.show()
            else:
                self.tray_icon.hide()

    def _show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            # 保存设置到文件
            if self.config_manager.save_config(self.settings):
                # 应用新设置
                self._apply_settings()
                # 重新加载连接
                self._load_connections()
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "保存设置失败",
                    "无法保存设置到配置文件，请检查文件权限或磁盘空间。"
                )

    def _toggle_sidebar(self):
        """切换侧边栏显示状态"""
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def _quit_application(self):
        """退出应用程序"""
        self.db_manager.clear_all_connections()
        self.tray_icon.hide()
        sys.exit(0)

    def closeEvent(self, event):
        """重写关闭事件"""
        if not self.settings.general.show_system_tray:
            # 如果没有启用系统托盘，直接退出
            self._quit_application()
            return
            
        close_action = self.settings.general.close_action
        
        if close_action == CloseAction.ASK:
            # 弹出询问对话框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("关闭确认")
            msg_box.setText("要退出程序还是最小化到系统托盘？")
            # 自定义按钮
            exit_btn = msg_box.addButton("退出程序", QMessageBox.YesRole)
            minimize_btn = msg_box.addButton("最小化到托盘", QMessageBox.NoRole)
            cancel_btn = msg_box.addButton("取消", QMessageBox.RejectRole)
            msg_box.setDefaultButton(cancel_btn)
            
            msg_box.exec()
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == exit_btn:  # 退出程序
                self._quit_application()
            elif clicked_button == minimize_btn:  # 最小化到托盘
                event.ignore()
                self.hide()
            else:  # 取消关闭
                event.ignore()
        elif close_action == CloseAction.MINIMIZE:
            # 最小化到托盘
            event.ignore()
            self.hide()
        else:  # CloseAction.EXIT
            # 退出程序
            self._quit_application() 