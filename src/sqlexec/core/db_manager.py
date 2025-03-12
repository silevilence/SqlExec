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
            
            with self.engines[alias].connect() as conn:
                result = conn.execute(text(query))
                if result.returns_rows:
                    rows = [dict(row) for row in result]
                    return True, rows, ""
                return True, None, ""
        except Exception as e:
            self.logger.error(f"执行查询失败: {str(e)}")
            return False, None, str(e)

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
            
            # 根据数据库类型添加适当的驱动
            if db_type == "mysql":
                if not conn_str.startswith("mysql"):
                    conn_str = f"mysql+mysqldb://{conn_str}"
            elif db_type == "postgresql":
                if not conn_str.startswith("postgresql"):
                    conn_str = f"postgresql+psycopg2://{conn_str}"
            elif db_type == "mssql":
                if not conn_str.startswith("mssql"):
                    conn_str = f"mssql+pymssql://{conn_str}"
            
            return create_engine(
                conn_str,
                pool_pre_ping=True,  # 自动检测断开的连接
                pool_recycle=3600    # 每小时回收连接
            )
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