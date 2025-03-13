from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QPushButton, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from typing import Dict, Optional, List


class Sidebar(QWidget):
    connection_selected = Signal(str)  # 发出选中的连接别名

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = parent
        self.tree: QTreeWidget = QTreeWidget()
        self.search_box: QLineEdit = QLineEdit()
        self.compact_button: QPushButton = QPushButton("切换紧凑模式")
        self._compact_mode: bool = False
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索连接...")
        self.search_box.textChanged.connect(self._filter_connections)
        layout.addWidget(self.search_box)

        # 连接树
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        # 紧凑模式切换按钮
        self.compact_button = QPushButton("切换紧凑模式")
        self.compact_button.clicked.connect(self._toggle_compact_mode)
        layout.addWidget(self.compact_button)

        self.setMinimumWidth(250)
        self.setMaximumWidth(400)

    def refresh_connections(self):
        """刷新连接列表"""
        self.tree.clear()

        # 获取配置管理器
        config_manager = self.main_window.config_manager
        settings = config_manager.settings

        # 创建所有组的树节点
        group_items = {}
        for group_name, group_info in settings.groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, f"{group_name} ({group_info.description})")
            group_item.setFlags(group_item.flags() |
                                Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)
            group_items[group_name] = group_item

        # 确保"未分组"存在
        if "未分组" not in group_items:
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, "未分组")
            group_item.setFlags(group_item.flags() |
                                Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)
            group_items["未分组"] = group_item

        # 添加连接到对应的组
        for alias, conn in settings.connections.items():
            # 获取连接所属的组
            conn_groups = settings.get_connection_groups(alias)

            # 如果连接不属于任何组，添加到未分组
            if not conn_groups:
                conn_groups = ["未分组"]

            # 为每个组添加连接
            for group_name in conn_groups:
                conn_item = QTreeWidgetItem(group_items[group_name])
                conn_item.setText(0, f"{conn.name} ({alias})")
                conn_item.setData(0, Qt.UserRole, alias)
                conn_item.setFlags(conn_item.flags() | Qt.ItemIsUserCheckable)
                conn_item.setCheckState(0, Qt.Unchecked)

        # 删除空的未分组
        ungrouped = group_items["未分组"]
        if ungrouped.childCount() == 0:
            index = self.tree.indexOfTopLevelItem(ungrouped)
            self.tree.takeTopLevelItem(index)

        self.tree.expandAll()

    def _filter_connections(self, text: str):
        """过滤连接列表"""
        # 遍历所有项目
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            visible_children = False

            # 检查每个连接
            for j in range(group_item.childCount()):
                conn_item = group_item.child(j)
                if text.lower() in conn_item.text(0).lower():
                    conn_item.setHidden(False)
                    visible_children = True
                else:
                    conn_item.setHidden(True)

            # 如果组内没有可见的连接，隐藏组
            group_item.setHidden(not visible_children)

    def _show_context_menu(self, position):
        """显示上下文菜单"""
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu()

        # 如果是连接项
        if item.parent():
            alias = item.data(0, Qt.UserRole)
            test_action = QAction("测试连接", self)
            test_action.triggered.connect(lambda: self._test_connection(alias))
            menu.addAction(test_action)

            remove_action = QAction("删除连接", self)
            remove_action.triggered.connect(
                lambda: self._remove_connection(alias))
            menu.addAction(remove_action)

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def _test_connection(self, alias: str):
        """测试数据库连接"""
        success, error = self.main_window.db_manager.test_connection(alias)
        if success:
            QMessageBox.information(self, "连接测试", "连接成功！")
        else:
            QMessageBox.warning(self, "连接测试", f"连接失败：{error}")

    def _remove_connection(self, alias: str):
        """删除数据库连接"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除连接 {alias} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.main_window.db_manager.remove_connection(alias):
                self.refresh_connections()
            else:
                QMessageBox.warning(self, "错误", "删除连接失败")

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """处理项目双击事件"""
        if item.parent():  # 如果是连接项
            alias = item.data(0, Qt.UserRole)
            self.connection_selected.emit(alias)

    def _toggle_compact_mode(self):
        """切换紧凑模式"""
        self._compact_mode = not self._compact_mode
        if self._compact_mode:
            self.setMaximumWidth(50)
            self.search_box.hide()
            self.compact_button.setText(">>")
        else:
            self.setMaximumWidth(400)
            self.search_box.show()
            self.compact_button.setText("切换紧凑模式")

    def get_selected_connections(self) -> List[str]:
        """获取选中的连接列表"""
        selected: List[str] = []
        root = self.tree.invisibleRootItem()

        # 遍历所有组
        for i in range(root.childCount()):
            group_item = root.child(i)
            # 遍历组内的连接
            for j in range(group_item.childCount()):
                conn_item = group_item.child(j)
                if conn_item.checkState(0) == Qt.Checked:
                    alias = conn_item.data(0, Qt.UserRole)
                    selected.append(alias)

        return selected
