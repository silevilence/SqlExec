from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DbParameter:
    name: str  # 参数名
    label: str  # 显示名称
    type: str  # 参数类型（text, password, number, etc.）
    required: bool = True  # 是否必填
    default: str = ""  # 默认值
    placeholder: str = ""  # 占位符文本

@dataclass
class DbType:
    id: str  # 数据库类型标识
    name: str  # 显示名称
    parameters: List[DbParameter]  # 连接参数
    connection_string_template: str  # 连接字符串模板

# 支持的数据库类型定义
DB_TYPES: Dict[str, DbType] = {
    "mssql": DbType(
        id="mssql",
        name="SQL Server",
        parameters=[
            DbParameter("host", "主机地址", "text", True, "localhost", "例如：localhost或127.0.0.1"),
            DbParameter("port", "端口", "number", False, "1433", "SQL Server默认端口：1433"),
            DbParameter("database", "数据库名", "text", True, "", "要连接的数据库名"),
            DbParameter("user", "用户名", "text", True, "", "数据库用户名"),
            DbParameter("password", "密码", "password", True, "", "数据库密码")
        ],
        connection_string_template="mssql+pymssql://{user}:{password}@{host}:{port}/{database}"
    ),
    "mysql": DbType(
        id="mysql",
        name="MySQL",
        parameters=[
            DbParameter("host", "主机地址", "text", True, "localhost", "例如：localhost或127.0.0.1"),
            DbParameter("port", "端口", "number", True, "3306", "MySQL默认端口：3306"),
            DbParameter("database", "数据库名", "text", True, "", "要连接的数据库名"),
            DbParameter("user", "用户名", "text", True, "root", "数据库用户名"),
            DbParameter("password", "密码", "password", True, "", "数据库密码"),
        ],
        connection_string_template="mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    ),
    "postgresql": DbType(
        id="postgresql",
        name="PostgreSQL",
        parameters=[
            DbParameter("host", "主机地址", "text", True, "localhost", "例如：localhost或127.0.0.1"),
            DbParameter("port", "端口", "number", True, "5432", "PostgreSQL默认端口：5432"),
            DbParameter("database", "数据库名", "text", True, "", "要连接的数据库名"),
            DbParameter("user", "用户名", "text", True, "postgres", "数据库用户名"),
            DbParameter("password", "密码", "password", True, "", "数据库密码"),
        ],
        connection_string_template="postgresql://{user}:{password}@{host}:{port}/{database}"
    ),
    "sqlite": DbType(
        id="sqlite",
        name="SQLite",
        parameters=[
            DbParameter("database", "数据库文件路径", "file", True, "", "选择或输入SQLite数据库文件路径"),
        ],
        connection_string_template="sqlite:///{database}"
    ),
}

def get_db_types() -> Dict[str, DbType]:
    """获取所有支持的数据库类型"""
    return DB_TYPES

def get_db_type(type_id: str) -> DbType:
    """获取指定数据库类型的定义"""
    return DB_TYPES.get(type_id)

def build_connection_string(db_type: str, params: dict) -> str:
    """根据数据库类型和参数构建连接字符串"""
    db_type_info = get_db_type(db_type)
    if not db_type_info:
        raise ValueError(f"不支持的数据库类型：{db_type}")
    
    # 移除空的可选参数
    clean_params = {k: v for k, v in params.items() if v or any(p.name == k and p.required for p in db_type_info.parameters)}
    
    return db_type_info.connection_string_template.format(**clean_params) 