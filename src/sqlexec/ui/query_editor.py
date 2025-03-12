from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QSplitter, QProgressBar, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, QThread, Signal, QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

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
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建查询编辑区
        self.query_edit = QTextEdit()
        self.query_edit.setPlaceholderText("在此输入SQL查询...")
        # 设置等宽字体
        font = QFont("Consolas", 12)
        self.query_edit.setFont(font)
        
        # 应用SQL语法高亮
        self.highlighter = SQLSyntaxHighlighter(self.query_edit.document())
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        
        self.run_btn = QPushButton("运行")
        self.run_btn.clicked.connect(self._run_query)
        toolbar.addWidget(self.run_btn)
        
        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self._clear_query)
        toolbar.addWidget(self.clear_btn)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        toolbar.addWidget(self.progress_bar)
        
        toolbar.addStretch()
        
        # 创建查询结果区
        self.result_table = QTableWidget()
        
        # 创建状态栏
        self.status_bar = QLabel()
        self.status_bar.setStyleSheet("padding: 5px;")
        
        # 添加组件到布局
        query_container = QWidget()
        query_layout = QVBoxLayout(query_container)
        query_layout.addLayout(toolbar)
        query_layout.addWidget(self.query_edit)
        
        splitter.addWidget(query_container)
        splitter.addWidget(self.result_table)
        
        layout.addWidget(splitter)
        layout.addWidget(self.status_bar)
        
        # 设置分割器的初始大小比例
        splitter.setStretchFactor(0, 1)  # 查询编辑区
        splitter.setStretchFactor(1, 2)  # 结果显示区

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
            
        # 清空结果表格
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        
        # 禁用运行按钮，显示进度条
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # 创建并启动查询执行器
        self.executor = QueryExecutor(
            self.main_window.db_manager,
            selected_conns,
            query
        )
        self.executor.finished.connect(self._handle_query_result)
        self.executor.progress.connect(self._update_progress)
        self.executor.start()

    def _handle_query_result(self, success, error, results):
        """处理查询结果"""
        # 恢复UI状态
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if not success:
            self.status_bar.setText(error)
            self.status_bar.setStyleSheet("color: red; padding: 5px;")
            return
            
        if not results:
            self.status_bar.setText("查询执行成功，但没有返回数据")
            self.status_bar.setStyleSheet("color: green; padding: 5px;")
            return
            
        # 显示结果集
        self._display_results(results)
        self.status_bar.setText(f"查询成功，返回 {len(results)} 条记录")
        self.status_bar.setStyleSheet("color: green; padding: 5px;")

    def _update_progress(self, current, total):
        """更新进度条"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_bar.setText(f"正在执行查询... ({current}/{total})")
        self.status_bar.setStyleSheet("color: blue; padding: 5px;")

    def _clear_query(self):
        """清除查询"""
        self.query_edit.clear()
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.status_bar.clear()

    def _display_results(self, results):
        """显示查询结果"""
        if not results:
            return
            
        # 设置表格列
        columns = list(results[0].keys())
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        
        # 添加数据行
        for row_data in results:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            for col, value in enumerate(row_data.values()):
                item = QTableWidgetItem(str(value))
                self.result_table.setItem(row, col, item)
        
        # 调整列宽
        self.result_table.resizeColumnsToContents() 