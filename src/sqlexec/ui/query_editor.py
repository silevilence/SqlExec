from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QSplitter, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QTextCharFormat, QSyntaxHighlighter, QColor

class SqlHighlighter(QSyntaxHighlighter):
    """SQL语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE",
            "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "GROUP", "BY",
            "HAVING", "ORDER", "LIMIT", "OFFSET", "AND", "OR", "NOT",
            "IN", "BETWEEN", "LIKE", "IS", "NULL", "TRUE", "FALSE"
        ]
        
        # 关键字格式
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(700)

    def highlightBlock(self, text):
        """高亮文本块"""
        for word in text.split():
            if word.upper() in self._keywords:
                self.setFormat(
                    text.indexOf(word),
                    len(word),
                    self.keyword_format
                )

class QueryExecutor(QThread):
    """查询执行器"""
    finished = Signal(bool, str, list)  # 成功标志，错误信息，结果列表
    progress = Signal(int, int)  # 当前进度，总数

    def __init__(self, db_manager, connections, query):
        super().__init__()
        self.db_manager = db_manager
        self.connections = connections
        self.query = query

    def run(self):
        """执行查询"""
        total = len(self.connections)
        results = []
        
        for i, alias in enumerate(self.connections, 1):
            self.progress.emit(i, total)
            success, rows, error = self.db_manager.execute_query(alias, self.query)
            
            if success and rows:
                results.extend(rows)
            elif not success:
                self.finished.emit(False, f"在 {alias} 上执行失败: {error}", [])
                return
        
        self.finished.emit(True, "", results)

class QueryEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：查询编辑器
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # SQL编辑器
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("在此输入SQL查询...")
        highlighter = SqlHighlighter(self.editor.document())
        editor_layout.addWidget(self.editor)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("执行")
        self.execute_button.clicked.connect(self._execute_query)
        button_layout.addWidget(self.execute_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        button_layout.addWidget(self.progress_bar)
        
        button_layout.addStretch()
        editor_layout.addLayout(button_layout)
        
        splitter.addWidget(editor_widget)
        
        # 下半部分：结果标签页
        self.results_tab = QTabWidget()
        self.results_tab.setTabsClosable(True)
        self.results_tab.tabCloseRequested.connect(self._close_result_tab)
        splitter.addWidget(self.results_tab)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)

    def _execute_query(self):
        """执行查询"""
        query = self.editor.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "错误", "请输入SQL查询")
            return
        
        connections = self.main_window.sidebar.get_selected_connections()
        if not connections:
            QMessageBox.warning(self, "错误", "请选择至少一个数据库连接")
            return
        
        # 禁用执行按钮
        self.execute_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # 创建并启动查询执行器
        self.executor = QueryExecutor(
            self.main_window.db_manager,
            connections,
            query
        )
        self.executor.finished.connect(self._handle_query_result)
        self.executor.progress.connect(self._update_progress)
        self.executor.start()

    def _handle_query_result(self, success, error, results):
        """处理查询结果"""
        self.execute_button.setEnabled(True)
        self.progress_bar.hide()
        
        if not success:
            QMessageBox.warning(self, "查询失败", error)
            return
        
        if not results:
            QMessageBox.information(self, "查询完成", "查询执行成功，但没有返回数据")
            return
        
        # 创建结果表格
        table = QTableWidget()
        
        # 设置列
        columns = list(results[0].keys())
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 添加数据
        table.setRowCount(len(results))
        for i, row in enumerate(results):
            for j, col in enumerate(columns):
                item = QTableWidgetItem(str(row[col]))
                table.setItem(i, j, item)
        
        # 调整列宽
        table.resizeColumnsToContents()
        
        # 添加新标签页
        tab_index = self.results_tab.addTab(table, f"结果 {self.results_tab.count() + 1}")
        self.results_tab.setCurrentIndex(tab_index)

    def _update_progress(self, current, total):
        """更新进度条"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _close_result_tab(self, index):
        """关闭结果标签页"""
        self.results_tab.removeTab(index) 