from typing import Dict, List, Tuple, Any, Optional
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class DatabaseManager:
    """数据库管理器类，用于管理数据库连接和执行查询"""

    def __init__(self):
        """初始化数据库管理器"""
        self.connections: Dict[str, Dict] = {}  # 存储连接配置
        self.engines: Dict[str, Any] = {}      # 存储数据库引擎
        self.logger = logging.getLogger(__name__)

    def add_connection(self, alias: str, config: Dict) -> bool:
        """
        添加数据库连接

        Args:
            alias: 连接别名
            config: 连接配置，包含类型、连接字符串等信息

        Returns:
            bool: 是否成功添加连接
        """
        try:
            # 保存连接配置
            self.connections[alias] = config

            # 创建数据库引擎
            engine = self._create_engine(config)
            if engine:
                self.engines[alias] = engine
                return True
            return False
        except Exception as e:
            self.logger.error(f"添加连接失败: {str(e)}")
            return False

    def remove_connection(self, alias: str) -> bool:
        """
        移除数据库连接

        Args:
            alias: 连接别名

        Returns:
            bool: 是否成功移除连接
        """
        try:
            if alias in self.engines:
                self.engines[alias].dispose()
                del self.engines[alias]
            if alias in self.connections:
                del self.connections[alias]
            return True
        except Exception as e:
            self.logger.error(f"移除连接失败: {str(e)}")
            return False

    def test_connection(self, alias: str) -> Tuple[bool, str]:
        """
        测试数据库连接

        Args:
            alias: 连接别名

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            if alias not in self.engines:
                return False, "连接不存在"

            # 尝试执行简单查询
            with self.engines[alias].connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, ""
        except Exception as e:
            return False, str(e)

    def execute_query(self, alias: str, query: str) -> Tuple[bool, Optional[List[Dict]], str]:
        """
        执行SQL查询

        Args:
            alias: 连接别名
            query: SQL查询语句

        Returns:
            Tuple[bool, Optional[List[Dict]], str]: (是否成功, 查询结果, 错误信息)
        """
        try:
            if alias not in self.engines:
                return False, None, "连接不存在"

            max_retries = 3  # 最大重试次数
            retry_count = 0

            while retry_count < max_retries:
                try:
                    with self.engines[alias].begin() as conn:  # 使用事务
                        self.logger.info(f"执行查询: {query}")
                        result = conn.execute(text(query))

                        if result.returns_rows:
                            # 使用_mapping属性获取字典，并确保字符串编码正确
                            rows = []
                            for row in result:
                                data = {}
                                # 检查是否有列名
                                if hasattr(row, '_mapping'):
                                    items = row._mapping.items()
                                else:
                                    # 如果没有列名，使用列号作为键
                                    items = enumerate(row)

                                for key, value in items:
                                    # 如果键是数字（没有列名的情况），使用 "Column_N" 作为键名
                                    if isinstance(key, int):
                                        key = f"Column_{key}"

                                    # 记录每个字段的值和类型
                                    self.logger.debug(
                                        f"字段 {key}: 值 = {value}, 类型 = {type(value)}")

                                    if isinstance(value, bytes):
                                        try:
                                            # 使用 cp936 (GBK) 解码
                                            value = value.decode('cp936')
                                            self.logger.debug(
                                                f"字段 {key} 已从 bytes 解码为 cp936: {value}")
                                        except UnicodeDecodeError as e:
                                            self.logger.warning(
                                                f"字段 {key} cp936 解码失败: {e}")
                                            try:
                                                value = value.decode('utf8')
                                                self.logger.debug(
                                                    f"字段 {key} 已从 bytes 解码为 utf8: {value}")
                                            except UnicodeDecodeError as e:
                                                self.logger.error(
                                                    f"字段 {key} utf8 解码也失败: {e}")
                                                value = str(value)
                                    data[key] = value
                                rows.append(data)

                            self.logger.info(f"查询返回 {len(rows)} 行数据")
                            return True, rows, ""

                        # 对于非查询语句，返回操作类型和影响的行数
                        query_type = query.strip().split(None, 1)[0].upper()
                        if query_type in ('CREATE', 'DROP', 'ALTER', 'TRUNCATE'):
                            self.logger.info(f"执行 {query_type} 操作成功")
                            return True, [{"operation": query_type, "status": "SUCCESS"}], ""
                        else:
                            affected = result.rowcount
                            self.logger.info(
                                f"执行 {query_type} 操作成功，影响 {affected} 行")
                            return True, [{"operation": query_type, "affected_rows": affected}], ""

                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        self.logger.warning(
                            f"执行查询失败，正在尝试第{retry_count}次重连: {str(e)}")
                        # 重新创建引擎
                        if alias in self.connections:
                            self.engines[alias] = self._create_engine(
                                self.connections[alias])
                    else:
                        raise e

        except Exception as e:
            self.logger.error(f"执行查询失败: {str(e)}")
            return False, None, f"执行失败: {str(e)}"

    def _create_engine(self, config: Dict) -> Any:
        """
        创建数据库引擎

        Args:
            config: 连接配置

        Returns:
            Any: SQLAlchemy引擎实例
        """
        try:
            db_type = config["type"].lower()
            conn_str = config["connection_string"]
            engine_kwargs = {
                "pool_pre_ping": True,  # 自动检测断开的连接
                "pool_recycle": 3600,   # 每小时回收连接
                "echo": False           # 关闭SQL日志
            }

            # 根据数据库类型添加适当的驱动和编码设置
            if db_type == "mssql":
                if not conn_str.startswith("mssql"):
                    conn_str = f"mssql+pymssql://{conn_str}"
                # SQL Server 的特殊编码设置
                engine_kwargs["connect_args"] = {
                    "charset": "cp936",  # 使用 cp936 (GBK) 编码，这是 pymssql 推荐的中文编码
                    "autocommit": False
                }
                self.logger.info(
                    f"创建 SQL Server 连接，连接字符串: {conn_str}, 参数: {engine_kwargs}")
            elif db_type == "mysql":
                if not conn_str.startswith("mysql"):
                    conn_str = f"mysql+pymysql://{conn_str}"
                if "?" in conn_str:
                    conn_str += "&charset=utf8mb4"
                else:
                    conn_str += "?charset=utf8mb4"
                engine_kwargs["encoding"] = "utf8mb4"
                engine_kwargs["connect_args"] = {"charset": "utf8mb4"}
            elif db_type == "postgresql":
                if not conn_str.startswith("postgresql"):
                    conn_str = f"postgresql+psycopg2://{conn_str}"
                if "?" in conn_str:
                    conn_str += "&client_encoding=utf8"
                else:
                    conn_str += "?client_encoding=utf8"
                engine_kwargs["encoding"] = "utf8"

            return create_engine(conn_str, **engine_kwargs)
        except Exception as e:
            self.logger.error(f"创建数据库引擎失败: {str(e)}")
            return None

    def get_connection_info(self, alias: str) -> Optional[Dict]:
        """
        获取连接信息

        Args:
            alias: 连接别名

        Returns:
            Optional[Dict]: 连接配置信息
        """
        return self.connections.get(alias)

    def get_all_connections(self) -> Dict[str, Dict]:
        """
        获取所有连接

        Returns:
            Dict[str, Dict]: 所有连接的配置信息
        """
        return self.connections.copy()

    def clear_all_connections(self):
        """清除所有连接"""
        for engine in self.engines.values():
            engine.dispose()
        self.engines.clear()
        self.connections.clear()
