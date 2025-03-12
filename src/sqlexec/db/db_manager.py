from typing import Dict, Tuple, Optional
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from ..config.settings import Settings, DatabaseConnection

logger = logging.getLogger(__name__)

class DbManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._engines: Dict[str, Engine] = {}
    
    def get_engine(self, alias: str) -> Optional[Engine]:
        """获取数据库引擎"""
        if alias not in self._engines:
            conn = self.settings.connections.get(alias)
            if not conn:
                logger.error(f"找不到连接：{alias}")
                return None
            
            try:
                self._engines[alias] = create_engine(conn.connection_string)
            except Exception as e:
                logger.error(f"创建数据库引擎失败：{str(e)}")
                return None
        
        return self._engines[alias]
    
    def test_connection(self, alias: str) -> Tuple[bool, str]:
        """测试数据库连接"""
        conn = self.settings.connections.get(alias)
        if not conn:
            return False, f"找不到连接：{alias}"
        
        try:
            engine = create_engine(conn.connection_string)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True, "连接成功"
        except Exception as e:
            return False, str(e)
    
    def execute_query(self, alias: str, query: str) -> Tuple[bool, str, list]:
        """执行查询"""
        engine = self.get_engine(alias)
        if not engine:
            return False, "无法获取数据库连接", []
        
        try:
            with engine.connect() as connection:
                result = connection.execute(text(query))
                if result.returns_rows:
                    columns = result.keys()
                    rows = [dict(row) for row in result]
                    return True, "", {"columns": columns, "rows": rows}
                return True, "", {"affected_rows": result.rowcount}
        except Exception as e:
            return False, str(e), []
    
    def close_all(self):
        """关闭所有连接"""
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear() 