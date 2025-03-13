from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QSplitter, QProgressBar, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal, QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from typing import List, Dict

class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """SQL语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # SQL关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))  # 蓝色
        keyword_format.setFontWeight(QFont.Bold)
        
        # SQL关键字列表
        keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER",   
            "DROP", "TABLE", "INDEX", "VIEW", "TRIGGER", "PROCEDURE", "FUNCTION",   
            "DATABASE", "SCHEMA", "AND", "OR", "NOT", "NULL", "IS", "IN", "BETWEEN",   
            "LIKE", "ORDER", "BY", "GROUP", "HAVING", "JOIN", "INNER", "OUTER", "LEFT",   
            "RIGHT", "FULL", "UNION", "ALL", "AS", "ON", "CASE", "WHEN", "THEN", "ELSE",   
            "END", "EXISTS", "DISTINCT", "INTO", "VALUES", "SET", "CONSTRAINT", "PRIMARY",   
            "FOREIGN", "KEY", "REFERENCES", "DEFAULT", "CHECK", "UNIQUE", "LIMIT"  
        ]  
        
        # 添加关键字规则  
        for word in keywords:  
            pattern = QRegularExpression(r'\b' + word + r'\b', QRegularExpression.CaseInsensitiveOption)  
            self.highlighting_rules.append((pattern, keyword_format))  
        
        # 数字格式  
        number_format = QTextCharFormat()  
        number_format.setForeground(QColor("#AA00AA"))  # 紫色  
        self.highlighting_rules.append(  
            (QRegularExpression(r'\b\d+\b'), number_format)  
        )  
        
        # 函数格式  
        function_format = QTextCharFormat()  
        function_format.setForeground(QColor("#644A9B"))  # 紫色  
        function_format.setFontItalic(True)  
        functions = [  
            "AVG", "COUNT", "MAX", "MIN", "SUM", "CONCAT", "SUBSTRING", "TRIM",   
            "UPPER", "LOWER", "LENGTH", "ROUND", "NOW", "DATE", "YEAR", "MONTH",   
            "DAY", "HOUR", "MINUTE", "SECOND", "IFNULL", "COALESCE", "CAST"  
        ]  
        
        for func in functions:  
            pattern = QRegularExpression(r'\b' + func + r'\s*\(', QRegularExpression.CaseInsensitiveOption)  
            self.highlighting_rules.append((pattern, function_format))  
        
        # 单行注释格式  
        single_line_comment_format = QTextCharFormat()  
        single_line_comment_format.setForeground(QColor("#008000"))  # 绿色  
        self.highlighting_rules.append(  
            (QRegularExpression(r'--[^\n]*'), single_line_comment_format)  
        )  
        
        # 多行注释格式 /* ... */  
        self.multi_line_comment_format = QTextCharFormat()  
        self.multi_line_comment_format.setForeground(QColor("#008000"))  # 绿色  
        
        self.comment_start_expression = QRegularExpression(r'/\*')  
        self.comment_end_expression = QRegularExpression(r'\*/')  
        
        # 字符串格式  
        string_format = QTextCharFormat()  
        string_format.setForeground(QColor("#A31515"))  # 红棕色  
        
        # 单引号字符串  
        self.highlighting_rules.append(  
            (QRegularExpression(r"'[^']*'"), string_format)  
        )  
        
        # 双引号字符串  
        self.highlighting_rules.append(  
            (QRegularExpression(r'"[^"]*"'), string_format)  
        )  

    def highlightBlock(self, text):
        """高亮文本块"""
        # 应用基本规则  
        for pattern, format in self.highlighting_rules:  
            expression = QRegularExpression(pattern)  
            match_iterator = expression.globalMatch(text)  
            while match_iterator.hasNext():  
                match = match_iterator.next()  
                self.setFormat(match.capturedStart(), match.capturedLength(), format)  
        
        # 处理多行注释  
        self.setCurrentBlockState(0)  
        
        start_index = 0  
        if self.previousBlockState() != 1:  
            start_index = text.indexOf(self.comment_start_expression)  
            
        while start_index >= 0:  
            match = self.comment_end_expression.match(text, start_index)  
            end_index = match.capturedStart()  
            comment_length = 0  
            
            if end_index == -1:  
                self.setCurrentBlockState(1)  
                comment_length = len(text) - start_index  
            else:  
                comment_length = end_index - start_index + match.capturedLength()  
                
            self.setFormat(start_index, comment_length, self.multi_line_comment_format)  
            start_index = text.indexOf(self.comment_start_expression, start_index + comment_length)

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
            
            if not success:
                self.finished.emit(False, f"在 {alias} 上执行失败: {error}", [])
                return
            
            # 将结果与连接别名一起保存
            results.append((alias, rows))
        
        self.finished.emit(True, "", results)

class QueryEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 查询编辑区
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        
        self.query_edit = QTextEdit()
        self.query_edit.setPlaceholderText("在此输入SQL查询...")
        self.query_edit.setFont(QFont("Consolas", 12))
        
        # 应用SQL语法高亮
        self.highlighter = SQLSyntaxHighlighter(self.query_edit.document())
        
        query_layout.addWidget(self.query_edit)
        
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("执行查询")
        self.run_btn.clicked.connect(self._run_query)
        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self._clear_query)
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        query_layout.addLayout(button_layout)
        
        splitter.addWidget(query_widget)
        
        # 结果显示区
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用标签页显示结果
        self.result_tabs = QTabWidget()
        self.result_tabs.setTabsClosable(True)
        self.result_tabs.tabCloseRequested.connect(self._close_result_tab)
        result_layout.addWidget(self.result_tabs)
        
        # 进度条和状态栏
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        result_layout.addWidget(self.progress_bar)
        
        self.status_bar = QLabel()
        self.status_bar.setStyleSheet("padding: 5px;")
        result_layout.addWidget(self.status_bar)
        
        splitter.addWidget(result_widget)
        
        # 设置分割器的初始大小比例
        splitter.setStretchFactor(0, 1)  # 查询编辑区
        splitter.setStretchFactor(1, 2)  # 结果显示区
        
        layout.addWidget(splitter)

    def _run_query(self):
        """运行查询"""
        query = self.query_edit.toPlainText().strip()
        if not query:
            return
            
        # 获取选中的连接
        selected_conns = self.main_window.sidebar.get_selected_connections()
        if not selected_conns:
            QMessageBox.warning(self, "错误", "请先选择至少一个数据库连接")
            return
        
        # 禁用运行按钮，显示进度条
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # 清空所有结果标签页
        self.result_tabs.clear()
        
        # 创建并启动查询执行器
        self.executor = QueryExecutor(
            self.main_window.db_manager,
            selected_conns,
            query
        )
        self.executor.finished.connect(self._handle_query_result)
        self.executor.progress.connect(self._update_progress)
        self.executor.start()

    def _handle_query_result(self, success: bool, error: str, results: List[Dict]):
        """处理查询结果"""
        # 恢复UI状态
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if not success:
            self.status_bar.setText(error)
            self.status_bar.setStyleSheet("color: red; padding: 5px;")
            return
        
        # 显示结果
        if results:
            for alias, result_data in results:
                if result_data:
                    # 创建新的结果表格
                    table = QTableWidget()
                    self._display_results(table, result_data)
                    # 添加到标签页
                    self.result_tabs.addTab(table, alias)
                    
            self.status_bar.setText(f"查询成功")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
        else:
            self.status_bar.setText("查询执行成功")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")

    def _display_results(self, table: QTableWidget, results: List[Dict]):
        """在表格中显示结果"""
        if not results:
            return
            
        # 设置列
        columns = list(results[0].keys())
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 设置行
        table.setRowCount(len(results))
        
        # 填充数据
        for row, data in enumerate(results):
            for col, key in enumerate(columns):
                value = data[key]
                # 确保正确处理编码
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            value = value.decode('gbk')
                        except UnicodeDecodeError:
                            value = str(value)
                elif value is None:
                    value = ''
                else:
                    value = str(value)
                    
                item = QTableWidgetItem(value)
                table.setItem(row, col, item)
        
        # 调整列宽
        table.resizeColumnsToContents()

    def _close_result_tab(self, index: int):
        """关闭结果标签页"""
        self.result_tabs.removeTab(index)

    def _clear_query(self):
        """清除查询"""
        self.query_edit.clear()
        self.result_tabs.clear()
        self.status_bar.clear()

    def _update_progress(self, current, total):
        """更新进度条"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_bar.setText(f"正在执行查询... ({current}/{total})")
        self.status_bar.setStyleSheet("color: blue; padding: 5px;") 