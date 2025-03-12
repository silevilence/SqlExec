from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from pathlib import Path
import logging
from .enums import Theme, Language, CloseAction

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConnection:
    name: str
    alias: str
    type: str
    connection_string: str

@dataclass
class GroupInfo:
    name: str
    description: str
    connections: Set[str] = field(default_factory=set)  # 存储连接的alias

@dataclass
class GeneralSettings:
    theme: Theme = Theme.LIGHT
    language: Language = Language.ZH_CN
    show_system_tray: bool = True
    enable_notifications: bool = True
    close_action: CloseAction = CloseAction.ASK

@dataclass
class Settings:
    version: int = 2
    general: GeneralSettings = field(default_factory=GeneralSettings)
    connections: Dict[str, DatabaseConnection] = field(default_factory=dict)  # 使用alias作为key
    groups: Dict[str, GroupInfo] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> 'Settings':
        """从字典创建设置实例"""
        # 获取配置版本，默认为1（旧版本）
        version = data.get("version", 1)
        
        # 如果是旧版本配置，先进行转换
        if version < 2:
            data = cls._convert_v1_to_v2(data)
        
        # 转换枚举值
        general_data = data.get("general", {})
        general_data["theme"] = Theme(general_data.get("theme", Theme.LIGHT.value))
        general_data["language"] = Language(general_data.get("language", Language.ZH_CN.value))
        general_data["close_action"] = CloseAction(general_data.get("close_action", CloseAction.ASK.value))
        
        general = GeneralSettings(**general_data)
        
        # 加载连接
        connections = {}
        for conn_data in data.get("connections", []):
            alias = conn_data["alias"]
            conn = DatabaseConnection(
                name=conn_data["name"],
                alias=alias,
                type=conn_data["type"],
                connection_string=conn_data["connection_string"]
            )
            connections[alias] = conn
            
        # 加载组
        groups = {}
        for name, info in data.get("groups", {}).items():
            groups[name] = GroupInfo(
                name=name,
                description=info["description"],
                connections=set(info.get("connections", []))
            )
            
        return cls(
            version=2,  # 总是使用最新版本
            general=general,
            connections=connections,
            groups=groups
        )
    
    @staticmethod
    def _convert_v1_to_v2(data: dict) -> dict:
        """将V1版本的配置转换为V2版本"""
        logger.info("正在转换V1版本配置到V2版本")
        
        # 复制原始数据
        new_data = data.copy()
        
        # 设置版本号
        new_data["version"] = 2
        
        # 清理旧版本中不再使用的字段
        if "general" in new_data:
            general = new_data["general"]
            # 移除不再使用的字段
            general.pop("compact_mode", None)
        
        # 处理连接的组信息
        groups = {}
        for conn in new_data.get("connections", []):
            # 获取连接的组信息
            conn_groups = conn.pop("group", ["未分组"])  # 移除group字段
            
            # 为每个组创建或更新组信息
            for group_name in conn_groups:
                if group_name not in groups:
                    groups[group_name] = {
                        "description": f"{group_name}组",
                        "connections": []
                    }
                groups[group_name]["connections"].append(conn["alias"])
        
        # 如果原配置中已有groups，合并信息
        existing_groups = new_data.get("groups", {})
        for name, info in existing_groups.items():
            if name not in groups:
                groups[name] = {
                    "description": info.get("description", f"{name}组"),
                    "connections": []
                }
        
        # 更新组信息
        new_data["groups"] = groups
        
        logger.info("配置转换完成")
        return new_data
    
    def to_dict(self) -> dict:
        """将设置转换为字典"""
        return {
            "version": self.version,
            "general": {
                "theme": self.general.theme.value,
                "language": self.general.language.value,
                "show_system_tray": self.general.show_system_tray,
                "enable_notifications": self.general.enable_notifications,
                "close_action": self.general.close_action.value
            },
            "connections": [
                {
                    "name": conn.name,
                    "alias": conn.alias,
                    "type": conn.type,
                    "connection_string": conn.connection_string
                }
                for conn in self.connections.values()
            ],
            "groups": {
                name: {
                    "description": group.description,
                    "connections": list(group.connections)
                }
                for name, group in self.groups.items()
            }
        }
    
    def add_connection_to_group(self, group_name: str, connection_alias: str) -> bool:
        """将连接添加到组"""
        if group_name not in self.groups or connection_alias not in self.connections:
            return False
        self.groups[group_name].connections.add(connection_alias)
        return True
    
    def remove_connection_from_group(self, group_name: str, connection_alias: str) -> bool:
        """从组中移除连接"""
        if group_name not in self.groups:
            return False
        self.groups[group_name].connections.discard(connection_alias)
        return True
    
    def get_connection_groups(self, connection_alias: str) -> List[str]:
        """获取连接所属的所有组"""
        return [
            name for name, group in self.groups.items()
            if connection_alias in group.connections
        ] 