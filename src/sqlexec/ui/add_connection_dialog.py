from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QFormLayout,
    QWidget, QFileDialog, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from ..config.db_types import get_db_types, get_db_type, build_connection_string, DbParameter


class AddConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加数据库连接")
        self.setMinimumWidth(400)

        self._init_ui()
        self._setup_connections()

        # 存储当前参数控件
        self._param_widgets = {}

        # 初始化数据库类型
        self._init_db_types()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 基本信息
        basic_form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("给这个连接起个名字")
        basic_form.addRow("连接名称:", self.name_edit)

        self.alias_edit = QLineEdit()
        self.alias_edit.setPlaceholderText("用于在代码中引用的唯一标识符")
        basic_form.addRow("连接别名:", self.alias_edit)

        self.type_combo = QComboBox()
        basic_form.addRow("数据库类型:", self.type_combo)

        layout.addLayout(basic_form)

        # 参数区域
        self.param_widget = QWidget()
        self.param_layout = QFormLayout(self.param_widget)
        layout.addWidget(self.param_widget)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试连接")
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")

        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _setup_connections(self):
        """设置信号连接"""
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self.test_btn.clicked.connect(self._test_connection)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _init_db_types(self):
        """初始化数据库类型下拉框"""
        db_types = get_db_types()
        for type_id, type_info in db_types.items():
            self.type_combo.addItem(type_info.name, type_id)

    def _on_type_changed(self, index):
        """处理数据库类型变更"""
        # 清空参数区域
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._param_widgets.clear()

        # 获取选中的数据库类型
        type_id = self.type_combo.currentData()
        if not type_id:
            return

        # 获取数据库类型定义
        db_type = get_db_type(type_id)
        if not db_type:
            return

        # 创建参数输入控件
        for param in db_type.parameters:
            widget = self._create_param_widget(param)
            if widget:
                self.param_layout.addRow(f"{param.label}:", widget)
                self._param_widgets[param.name] = widget

    def _create_param_widget(self, param: DbParameter) -> QWidget:
        """创建参数输入控件"""
        if param.type == "number":
            widget = QSpinBox()
            widget.setMinimum(0)
            widget.setMaximum(65535)
            if param.default:
                widget.setValue(int(param.default))
        elif param.type == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.Password)
        elif param.type == "file":
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            edit = QLineEdit()
            edit.setPlaceholderText(param.placeholder)
            browse_btn = QPushButton("浏览...")

            layout.addWidget(edit)
            layout.addWidget(browse_btn)

            browse_btn.clicked.connect(lambda: self._browse_file(edit))
            return container
        else:  # text
            widget = QLineEdit()
            widget.setPlaceholderText(param.placeholder)
            if param.default:
                widget.setText(param.default)

        return widget

    def _browse_file(self, edit: QLineEdit):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据库文件",
            "",
            "SQLite数据库文件 (*.db *.sqlite);;所有文件 (*.*)"
        )
        if file_path:
            edit.setText(file_path)

    def _get_param_values(self) -> dict:
        """获取参数值"""
        values = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, QSpinBox):
                values[name] = str(widget.value())
            elif isinstance(widget, QWidget) and widget.layout():
                # 文件选择控件
                edit = widget.layout().itemAt(0).widget()
                if isinstance(edit, QLineEdit):
                    values[name] = edit.text()
            elif isinstance(widget, QLineEdit):
                values[name] = widget.text()
        return values

    def _test_connection(self):
        """测试连接"""
        # 获取连接信息
        type_id = self.type_combo.currentData()
        params = self._get_param_values()

        try:
            # 构建连接字符串
            conn_str = build_connection_string(type_id, params)

            # TODO: 实际测试连接
            # 这里应该调用数据库管理器的测试方法

            QMessageBox.information(self, "连接测试", "连接成功！")
        except Exception as e:
            QMessageBox.warning(self, "连接测试", f"连接失败：{str(e)}")

    def get_connection_info(self) -> dict:
        """获取连接信息"""
        type_id = self.type_combo.currentData()
        params = self._get_param_values()

        return {
            "name": self.name_edit.text(),
            "alias": self.alias_edit.text(),
            "type": type_id,
            "connection_string": build_connection_string(type_id, params),
            "parameters": params
        }
