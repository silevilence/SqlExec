from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt

from sqlexec.config.settings import Settings, DatabaseConnection, GroupInfo
from sqlexec.config.db_types import get_db_types, get_db_type
from sqlexec.config.enums import Theme, Language, CloseAction
from .add_connection_dialog import AddConnectionDialog


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.main_window = parent
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("设置")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

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
        self.theme_combo.setCurrentText(
            "浅色" if self.settings.general.theme == Theme.LIGHT else "深色"
        )
        layout.addRow("主题:", self.theme_combo)

        # 语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.setCurrentText(
            "简体中文" if self.settings.general.language == Language.ZH_CN else "English"
        )
        layout.addRow("语言:", self.language_combo)

        # 系统托盘
        self.tray_check = QCheckBox()
        self.tray_check.setChecked(self.settings.general.show_system_tray)
        layout.addRow("显示系统托盘:", self.tray_check)

        # 通知
        self.notification_check = QCheckBox()
        self.notification_check.setChecked(
            self.settings.general.enable_notifications)
        layout.addRow("启用通知:", self.notification_check)

        # 关闭动作
        self.close_action_combo = QComboBox()
        for action in CloseAction:
            self.close_action_combo.addItem(
                CloseAction.get_display_name(action), action)

        # 设置当前值
        index = self.close_action_combo.findData(
            self.settings.general.close_action)
        if index >= 0:
            self.close_action_combo.setCurrentIndex(index)

        layout.addRow("关闭窗口时:", self.close_action_combo)

        return widget

    def _create_database_tab(self):
        """创建数据库设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 数据库连接表格
        self.db_table = QTableWidget()
        self.db_table.setColumnCount(4)
        self.db_table.setHorizontalHeaderLabels([
            "名称", "别名", "类型", "连接字符串"
        ])

        # 加载现有连接
        connections = list(self.settings.connections.values())
        self.db_table.setRowCount(len(connections))
        for i, conn in enumerate(connections):
            self.db_table.setItem(i, 0, QTableWidgetItem(conn.name))
            self.db_table.setItem(i, 1, QTableWidgetItem(conn.alias))
            self.db_table.setItem(i, 2, QTableWidgetItem(conn.type))
            self.db_table.setItem(
                i, 3, QTableWidgetItem(conn.connection_string))

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
        layout = QHBoxLayout(widget)

        # 左侧：组列表和管理
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 组表格
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(2)
        self.group_table.setHorizontalHeaderLabels(["名称", "描述"])
        self.group_table.currentItemChanged.connect(self._on_group_selected)

        # 加载现有组
        self.group_table.setRowCount(len(self.settings.groups))
        for i, (name, info) in enumerate(self.settings.groups.items()):
            self.group_table.setItem(i, 0, QTableWidgetItem(name))
            self.group_table.setItem(i, 1, QTableWidgetItem(info.description))

        self.group_table.resizeColumnsToContents()
        left_layout.addWidget(self.group_table)

        # 组管理按钮
        group_button_layout = QHBoxLayout()

        add_group_btn = QPushButton("添加组")
        add_group_btn.clicked.connect(self._add_group)
        group_button_layout.addWidget(add_group_btn)

        remove_group_btn = QPushButton("删除组")
        remove_group_btn.clicked.connect(self._remove_group)
        group_button_layout.addWidget(remove_group_btn)

        group_button_layout.addStretch()
        left_layout.addLayout(group_button_layout)

        # 右侧：组内连接管理
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 连接列表
        right_layout.addWidget(QLabel("组内连接:"))
        self.connections_list = QListWidget()
        right_layout.addWidget(self.connections_list)

        # 连接管理按钮
        conn_button_layout = QHBoxLayout()

        add_to_group_btn = QPushButton("添加连接到组")
        add_to_group_btn.clicked.connect(self._add_connection_to_group)
        conn_button_layout.addWidget(add_to_group_btn)

        remove_from_group_btn = QPushButton("从组中移除连接")
        remove_from_group_btn.clicked.connect(
            self._remove_connection_from_group)
        conn_button_layout.addWidget(remove_from_group_btn)

        conn_button_layout.addStretch()
        right_layout.addLayout(conn_button_layout)

        # 添加分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        return widget

    def _on_group_selected(self, current, previous):
        """当选择组时更新连接列表"""
        self.connections_list.clear()
        if not current:
            return

        group_name = self.group_table.item(current.row(), 0).text()
        if group_name not in self.settings.groups:
            return

        group = self.settings.groups[group_name]
        for conn_alias in group.connections:
            if conn_alias in self.settings.connections:
                conn = self.settings.connections[conn_alias]
                item = QListWidgetItem(f"{conn.name} ({conn.alias})")
                item.setData(Qt.UserRole, conn.alias)
                self.connections_list.addItem(item)

    def _add_connection_to_group(self):
        """添加连接到当前选中的组"""
        current_row = self.group_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "错误", "请先选择一个组")
            return

        group_name = self.group_table.item(current_row, 0).text()

        # 创建连接选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择连接")
        layout = QVBoxLayout(dialog)

        conn_list = QListWidget()
        for conn in self.settings.connections.values():
            if conn.alias not in self.settings.groups[group_name].connections:
                item = QListWidgetItem(f"{conn.name} ({conn.alias})")
                item.setData(Qt.UserRole, conn.alias)
                conn_list.addItem(item)

        layout.addWidget(conn_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            current_item = conn_list.currentItem()
            if current_item:
                conn_alias = current_item.data(Qt.UserRole)
                self.settings.add_connection_to_group(group_name, conn_alias)
                self._on_group_selected(self.group_table.currentItem(), None)

    def _remove_connection_from_group(self):
        """从当前组中移除选中的连接"""
        current_group_row = self.group_table.currentRow()
        if current_group_row < 0:
            return

        current_conn_item = self.connections_list.currentItem()
        if not current_conn_item:
            return

        group_name = self.group_table.item(current_group_row, 0).text()
        conn_alias = current_conn_item.data(Qt.UserRole)

        self.settings.remove_connection_from_group(group_name, conn_alias)
        self._on_group_selected(self.group_table.currentItem(), None)

    def _add_connection(self):
        """添加数据库连接"""
        dialog = AddConnectionDialog(self)
        if dialog.exec_():
            conn_info = dialog.get_connection_info()

            # 检查别名是否已存在
            if conn_info["alias"] in self.settings.connections:
                QMessageBox.warning(self, "错误", "连接别名已存在")
                return

            # 添加连接
            self.settings.connections[conn_info["alias"]] = conn_info
            self.db_table.insertRow(self.db_table.rowCount())
            for i, (key, value) in enumerate(conn_info.items()):
                self.db_table.setItem(
                    self.db_table.rowCount() - 1, i, QTableWidgetItem(str(value)))
            self.db_table.resizeColumnsToContents()

    def _remove_connection(self):
        """删除数据库连接"""
        current_row = self.db_table.currentRow()
        if current_row >= 0:
            # 获取要删除的连接别名
            alias = self.db_table.item(current_row, 1).text()

            # 从所有组中移除该连接
            for group in self.settings.groups.values():
                group.connections.discard(alias)

            self.db_table.removeRow(current_row)

    def _test_connection(self):
        """测试数据库连接"""
        current_row = self.db_table.currentRow()
        if current_row < 0:
            return

        # 获取连接信息
        conn = DatabaseConnection(
            name=self.db_table.item(current_row, 0).text(),
            alias=self.db_table.item(current_row, 1).text(),
            type=self.db_table.item(current_row, 2).text(),
            connection_string=self.db_table.item(current_row, 3).text()
        )

        # 测试连接
        success = self.main_window.db_manager.add_connection(conn.alias, {
            "name": conn.name,
            "alias": conn.alias,
            "type": conn.type,
            "connection_string": conn.connection_string
        })
        if success:
            success, error = self.main_window.db_manager.test_connection(
                conn.alias)
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
        self.settings.general.theme = Theme.LIGHT if self.theme_combo.currentText(
        ) == "浅色" else Theme.DARK
        self.settings.general.language = Language.ZH_CN if self.language_combo.currentText(
        ) == "简体中文" else Language.EN_US
        self.settings.general.show_system_tray = self.tray_check.isChecked()
        self.settings.general.enable_notifications = self.notification_check.isChecked()

        # 更新关闭动作
        self.settings.general.close_action = self.close_action_combo.currentData()

        # 更新数据库连接
        new_connections = {}
        for row in range(self.db_table.rowCount()):
            alias = self.db_table.item(row, 1).text()
            conn = DatabaseConnection(
                name=self.db_table.item(row, 0).text(),
                alias=alias,
                type=self.db_table.item(row, 2).text(),
                connection_string=self.db_table.item(row, 3).text()
            )
            new_connections[alias] = conn
        self.settings.connections = new_connections

        # 更新组
        new_groups = {}
        for row in range(self.group_table.rowCount()):
            name = self.group_table.item(row, 0).text()
            if name:  # 只添加有名称的组
                description = self.group_table.item(row, 1).text()
                # 保持原有的连接列表，如果是新组则创建空集合
                connections = self.settings.groups.get(
                    name, GroupInfo(name, "")).connections
                new_groups[name] = GroupInfo(
                    name=name, description=description, connections=connections)
        self.settings.groups = new_groups

        super().accept()
