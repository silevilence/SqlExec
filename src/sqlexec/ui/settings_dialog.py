from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.main_window = parent
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 常规设置
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "常规")
        
        # 数据库设置
        database_tab = self._create_database_tab()
        tab_widget.addTab(database_tab, "数据库")
        
        # 组设置
        groups_tab = self._create_groups_tab()
        tab_widget.addTab(groups_tab, "组")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_general_tab(self):
        """创建常规设置标签页"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色"])
        current_theme = self.config.get("general", {}).get("theme", "light")
        self.theme_combo.setCurrentText("浅色" if current_theme == "light" else "深色")
        layout.addRow("主题:", self.theme_combo)
        
        # 语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        current_lang = self.config.get("general", {}).get("language", "zh_CN")
        self.language_combo.setCurrentText(
            "简体中文" if current_lang == "zh_CN" else "English"
        )
        layout.addRow("语言:", self.language_combo)
        
        # 系统托盘
        self.tray_check = QCheckBox()
        self.tray_check.setChecked(
            self.config.get("general", {}).get("show_system_tray", True)
        )
        layout.addRow("显示系统托盘:", self.tray_check)
        
        # 通知
        self.notification_check = QCheckBox()
        self.notification_check.setChecked(
            self.config.get("general", {}).get("enable_notifications", True)
        )
        layout.addRow("启用通知:", self.notification_check)
        
        return widget

    def _create_database_tab(self):
        """创建数据库设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 数据库连接表格
        self.db_table = QTableWidget()
        self.db_table.setColumnCount(5)
        self.db_table.setHorizontalHeaderLabels([
            "名称", "别名", "类型", "连接字符串", "组"
        ])
        
        # 加载现有连接
        connections = self.config.get("connections", [])
        self.db_table.setRowCount(len(connections))
        for i, conn in enumerate(connections):
            self.db_table.setItem(i, 0, QTableWidgetItem(conn["name"]))
            self.db_table.setItem(i, 1, QTableWidgetItem(conn["alias"]))
            self.db_table.setItem(i, 2, QTableWidgetItem(conn["type"]))
            self.db_table.setItem(i, 3, QTableWidgetItem(conn["connection_string"]))
            self.db_table.setItem(
                i, 4,
                QTableWidgetItem(", ".join(conn.get("group", ["未分组"])))
            )
        
        self.db_table.resizeColumnsToContents()
        layout.addWidget(self.db_table)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_connection)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self._remove_connection)
        button_layout.addWidget(remove_btn)
        
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return widget

    def _create_groups_tab(self):
        """创建组设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 组表格
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(2)
        self.group_table.setHorizontalHeaderLabels(["名称", "描述"])
        
        # 加载现有组
        groups = self.config.get("groups", {})
        self.group_table.setRowCount(len(groups))
        for i, (name, info) in enumerate(groups.items()):
            self.group_table.setItem(i, 0, QTableWidgetItem(name))
            self.group_table.setItem(i, 1, QTableWidgetItem(info["description"]))
        
        self.group_table.resizeColumnsToContents()
        layout.addWidget(self.group_table)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_group)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self._remove_group)
        button_layout.addWidget(remove_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return widget

    def _add_connection(self):
        """添加数据库连接"""
        row = self.db_table.rowCount()
        self.db_table.insertRow(row)
        for i in range(5):
            self.db_table.setItem(row, i, QTableWidgetItem(""))

    def _remove_connection(self):
        """删除数据库连接"""
        current_row = self.db_table.currentRow()
        if current_row >= 0:
            self.db_table.removeRow(current_row)

    def _test_connection(self):
        """测试数据库连接"""
        current_row = self.db_table.currentRow()
        if current_row < 0:
            return
        
        # 获取连接信息
        conn_info = {
            "name": self.db_table.item(current_row, 0).text(),
            "alias": self.db_table.item(current_row, 1).text(),
            "type": self.db_table.item(current_row, 2).text(),
            "connection_string": self.db_table.item(current_row, 3).text(),
            "group": [g.strip() for g in self.db_table.item(current_row, 4).text().split(",")]
        }
        
        # 测试连接
        success = self.main_window.db_manager.add_connection(conn_info["alias"], conn_info)
        if success:
            success, error = self.main_window.db_manager.test_connection(conn_info["alias"])
            if success:
                QMessageBox.information(self, "连接测试", "连接成功！")
            else:
                QMessageBox.warning(self, "连接测试", f"连接失败：{error}")
        else:
            QMessageBox.warning(self, "连接测试", "无法创建连接")

    def _add_group(self):
        """添加组"""
        row = self.group_table.rowCount()
        self.group_table.insertRow(row)
        for i in range(2):
            self.group_table.setItem(row, i, QTableWidgetItem(""))

    def _remove_group(self):
        """删除组"""
        current_row = self.group_table.currentRow()
        if current_row >= 0:
            self.group_table.removeRow(current_row)

    def accept(self):
        """保存设置"""
        # 更新常规设置
        if "general" not in self.config:
            self.config["general"] = {}
        
        self.config["general"].update({
            "theme": "light" if self.theme_combo.currentText() == "浅色" else "dark",
            "language": "zh_CN" if self.language_combo.currentText() == "简体中文" else "en_US",
            "show_system_tray": self.tray_check.isChecked(),
            "enable_notifications": self.notification_check.isChecked()
        })
        
        # 更新数据库连接
        connections = []
        for row in range(self.db_table.rowCount()):
            conn = {
                "name": self.db_table.item(row, 0).text(),
                "alias": self.db_table.item(row, 1).text(),
                "type": self.db_table.item(row, 2).text(),
                "connection_string": self.db_table.item(row, 3).text(),
                "group": [
                    g.strip()
                    for g in self.db_table.item(row, 4).text().split(",")
                    if g.strip()
                ]
            }
            connections.append(conn)
        self.config["connections"] = connections
        
        # 更新组
        groups = {}
        for row in range(self.group_table.rowCount()):
            name = self.group_table.item(row, 0).text()
            description = self.group_table.item(row, 1).text()
            if name:
                groups[name] = {"description": description}
        self.config["groups"] = groups
        
        super().accept() 